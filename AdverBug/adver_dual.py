"""
adver_dual.py —— 双大模型过滤的错误代码生成流程。

与 adver.py（旧流程）的区别（详见分析报告）：
1. 删除"原测试套件"过滤闸门，改由两个不同厂商的大模型按评测协议生成测试并过滤；
   原测试套件降级为元数据：验收时跑一次，记录 escaped_original_suite / 失败用例，
   被其检出即作为"非等效"的强证据。
2. 过滤协议与评测管线同源：复用 gen_test/llm_gentests.py 的 TestCodeGenerator
   （specification 模式模板、temperature=0、max_K=3 重试），输入为"错误代码 + 规范"，
   与被评测模型看到的信息一致——过滤准则即"在评测协议下该模型未检出此 bug"。
3. 默认只在错误代码上运行过滤测试；仅当运行失败时补跑一次原代码做 per-test 差分仲裁：
   - 差分失败（原代码过 ∧ bug 版挂）= 真检出 → 反馈给 bug 生成器重试；
   - 纯误报（原代码上也挂）= 套件问题 → 反馈修复测试套件，bug 保留；
   - 编译始终失败 / 空套件 = 套件问题 → 重新生成套件，不判检出。
4. 等效判定沿用 valid_agent.py 的语义行为一致性判定。

用法（容器内，WORKDIR=/testbed 为项目根目录）：
    python3 /testbed/adver_dual.py --data-path /testbed/<data>.json \
        --filter-model-a deepseek-v3.2 --filter-model-b qwen3-coder-480b-a35b-instruct

建议通过环境变量 LLM_API_KEY / LLM_API_ENDPOINT 配置凭证（未设置时回退到
历史内置 key，仅供过渡；该 key 已出现在仓库历史中，应尽快吊销轮换）。

输出：
    /testbed/final_results.json   仅收录被接受的条目（ schema 与旧流程兼容，额外字段见下）
    /testbed/filter_stats.json    全部条目的尝试轨迹（用于新旧流程 A/B 对比）
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

from llm_config import LLMConfig
from bug_generation_agent import BugGenerationAgent
from valid_agent import ValidAgent
from filter_test_gen import FilterTestGenerationAgent

TESTBED = "/testbed"
MVN_SKIP_ARGS = ["-Drat.skip=true", "-Dformatter.skip=true", "-DforkCount=0"]

DEFAULT_API_KEY = "sk-f9iJyNvXH7W8Zc4TC6k3c7gzEpN42jpBOhyqgGfGsay4iEkB"
DEFAULT_ENDPOINT = "https://api.agicto.cn/v1"


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def sh(cmd, timeout=1800):
    try:
        return subprocess.run(cmd, cwd=TESTBED, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else (e.stdout or b"").decode("utf-8", "ignore")
        err = e.stderr if isinstance(e.stderr, str) else (e.stderr or b"").decode("utf-8", "ignore")
        return subprocess.CompletedProcess(cmd, returncode=-1, stdout=out, stderr=err)


def mvn(goal_args, timeout=1800):
    return sh(["mvn"] + goal_args + MVN_SKIP_ARGS, timeout=timeout)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def set_src_code(src_file, new_code, old_code):
    """把 src_file 中的 old_code 片段替换为 new_code。返回是否替换成功。"""
    src = read_text(src_file)
    if old_code not in src:
        return False
    write_text(src_file, src.replace(old_code, new_code))
    return True


def test_class_name(test_file):
    return os.path.splitext(os.path.basename(test_file))[0]


# ---------------------------------------------------------------------------
# Surefire 结果解析（per-test 差分仲裁）
# ---------------------------------------------------------------------------

def surefire_xml_files():
    # 多模块项目的 surefire 报告分散在各模块 target/ 下，需要递归
    return glob.glob(os.path.join(TESTBED, "**", "surefire-reports", "TEST-*.xml"),
                     recursive=True)


def clean_surefire_reports():
    for path in surefire_xml_files():
        try:
            os.remove(path)
        except OSError:
            pass


def parse_surefire_results():
    """解析 surefire XML，返回 {(classname, testname): passed|failed|skipped}。"""
    results = {}
    for path in surefire_xml_files():
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for tc in root.iter("testcase"):
            key = (tc.get("classname", ""), tc.get("name", ""))
            if tc.find("failure") is not None or tc.find("error") is not None:
                results[key] = "failed"
            elif tc.find("skipped") is not None:
                results[key] = "skipped"
            else:
                results[key] = "passed"
    return results


def diff_surefire(buggy_results, orig_results):
    """差分：检出的定义为"原代码通过 ∧ bug 版失败"。

    返回 (differential, false_positives)：真检出的用例名列表 / 误报用例名列表。
    """
    differential, false_positives = [], []
    for key, status in buggy_results.items():
        if status != "failed":
            continue
        if orig_results.get(key) == "passed":
            differential.append(key)
        else:
            false_positives.append(key)
    return differential, false_positives


def declared_class_names(tests_src):
    return sorted(set(re.findall(r"\bclass\s+(\w+)", tests_src)))


def purge_stale_test_classes(names):
    """删除已编译的测试类文件，避免删除/替换 .java 后残留 .class 被后续运行执行。"""
    prefixes = set(names)
    for root, _dirs, files in os.walk(TESTBED):
        if f"{os.sep}target{os.sep}test-classes" not in root:
            continue
        for fn in files:
            if any(fn == f"{n}.class" or fn.startswith(f"{n}$") for n in prefixes):
                try:
                    os.remove(os.path.join(root, fn))
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# bug 生成相关的 prompt 上下文
# ---------------------------------------------------------------------------

def find_related_test_sources(entry, max_chars=6000, max_files=1):
    """在 src/test 下查找涉及该函数的既有测试源码（尽力而为）。

    让 bug 生成器看到"必须保持通过"的测试，从源头提高逃逸率
    （旧 prompt 要求保持测试通过却不给看测试）。
    """
    name = (entry.get("name") or "").strip()
    if len(name) < 4:
        return ""
    test_root = os.path.join(TESTBED, "src", "test")
    if not os.path.isdir(test_root):
        test_root = os.path.join(TESTBED, "src", "test", "java")
        if not os.path.isdir(test_root):
            return ""
    snippets = []
    for dirpath, _dirnames, filenames in os.walk(test_root):
        for fn in filenames:
            if not fn.endswith(".java"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                content = open(path, "r", encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if name in content:
                snippets.append(content[:max_chars])
                if len(snippets) >= max_files:
                    return "\n\n".join(snippets)
    return "\n\n".join(snippets)


# ---------------------------------------------------------------------------
# 各阶段
# ---------------------------------------------------------------------------

def compile_bug(bug_agent, src_file, original_code, bug_code, fix_attempts=3):
    """编译注入 bug 后的源码，失败时调用模型修复。返回 (ok, 最终bug代码, 错误信息)。"""
    last_error = ""
    for _ in range(fix_attempts + 1):
        result = mvn(["compile"], timeout=1800)
        if result.returncode == 0:
            return True, bug_code, ""
        last_error = result.stdout
        fixed = bug_agent.fix_bug_prompt(bug_code, result.stdout)
        if not fixed or fixed == bug_code:
            break
        if not set_src_code(src_file, fixed, bug_code):
            break
        bug_code = fixed
    return False, bug_code, last_error[-4000:]


def compile_test_suite(agent, test_file, tests, fix_attempts=5):
    """编译测试套件，失败时调用模型修复。返回 (ok, 最终测试代码, 错误信息)。"""
    last_error = ""
    for _ in range(fix_attempts + 1):
        purge_stale_test_classes([test_class_name(test_file)] + declared_class_names(tests))
        write_text(test_file, tests)
        result = mvn(["test-compile"], timeout=1800)
        if result.returncode == 0:
            return True, tests, ""
        last_error = result.stdout
        fixed = agent.fix_compile(tests, result.stdout)
        if not fixed or fixed == tests:
            break
        tests = fixed
    return False, tests, last_error[-4000:]


def evaluate_filter_model(agent, entry, bug_code, src_file, original_code,
                          test_file, suite_retries):
    """用一个过滤模型评估当前 bug（Stage 2 单模型分支）。

    返回 (undetected, tests, info)：
    - undetected=True ：套件在 bug 版上全部通过 → 未检出；
    - undetected=False 且 info["detected"]=True ：真检出（差分）；
    - undetected=False 且 info["detected"]=False ：套件本身失败（编译不过/空/纯误报未修复）。
    """
    tests = agent.generate_tests(entry, bug_code)
    last_feedback = ""
    total_false_positives = None
    for _suite_try in range(suite_retries + 1):
        if not tests:
            tests = agent.generate_tests(entry, bug_code)
            if not tests:
                continue
        compile_ok, tests, compile_err = compile_test_suite(agent, test_file, tests)
        if not compile_ok:
            last_feedback = compile_err
            tests = ""
            continue

        clean_surefire_reports()
        buggy_run = mvn(["test", f"-Dtest={test_class_name(test_file)}"], timeout=1800)
        buggy_results = parse_surefire_results()

        if buggy_run.returncode == 0 and buggy_results:
            return True, tests, {"detected": False, "total_cases": len(buggy_results),
                                 "false_positives": None, "note": "passed_on_buggy"}
        if not buggy_results:
            # 没有任何用例被执行（空套件/类名不匹配/全部被跳过）
            last_feedback = buggy_run.stdout[-4000:] or "no tests were executed"
            tests = agent.repair_tests(tests, last_feedback)
            continue

        # bug 版运行失败 → 补跑一次原代码做 per-test 差分仲裁
        set_src_code(src_file, original_code, bug_code)
        clean_surefire_reports()
        mvn(["test", f"-Dtest={test_class_name(test_file)}"], timeout=1800)
        orig_results = parse_surefire_results()
        set_src_code(src_file, bug_code, original_code)  # 恢复 bug 版

        differential, false_positives = diff_surefire(buggy_results, orig_results)
        total_false_positives = len(false_positives)
        if differential:
            names = ", ".join(f"{c}.{n}" for c, n in differential)
            return False, tests, {"detected": True, "total_cases": len(buggy_results),
                                  "false_positives": len(false_positives),
                                  "note": f"detected_by: {names}",
                                  "feedback": buggy_run.stdout[-6000:]}
        # 纯误报：问题在套件不在 bug → 修复套件后重试，bug 保留
        last_feedback = buggy_run.stdout[-4000:] or \
            "tests fail on the correct implementation (false positives)"
        tests = agent.repair_tests(tests, last_feedback)

    return False, tests or "", {"detected": False, "total_cases": 0,
                                "false_positives": total_false_positives,
                                "note": "suite_generation_failed"}


def process_entry(entry, agents, opts):
    """处理单个函数条目。返回 (accepted: bool, attempt_traces: list)。"""
    code = entry.get("code", "")
    src_file = entry.get("src_file", "")
    test_file = entry.get("test_file", "")
    test_class = test_class_name(test_file) if test_file else ""
    tests_context = find_related_test_sources(entry)

    current_bug = ""
    test_info = ""
    attempt_traces = []

    for attempt in range(opts.attempts):
        trace = {"attempt": attempt + 1}

        # ---- Stage 1：生成 bug（对抗循环，反馈源为过滤套件的失败输出）----
        if attempt == 0:
            bug_json = agents["bug"].init_bug_prompt(code, tests_context=tests_context)
        else:
            bug_json = agents["bug"].enhance_bug_prompt(
                code, current_bug, test_info, tests_context=tests_context)
        if not isinstance(bug_json, dict):
            trace["outcome"] = "bug_generation_error"
            attempt_traces.append(trace)
            continue
        current_bug = (bug_json.get("buggy_code") or "").strip()
        bug_summary = bug_json.get("bug_summary", "")
        if not current_bug or current_bug == code:
            trace["outcome"] = "bug_generation_empty"
            attempt_traces.append(trace)
            continue
        if not set_src_code(src_file, current_bug, code):
            trace["outcome"] = "patch_failed"
            attempt_traces.append(trace)
            continue

        compile_ok, current_bug, compile_err = compile_bug(
            agents["bug"], src_file, code, current_bug)
        if not compile_ok:
            set_src_code(src_file, code, current_bug)
            trace["outcome"] = "compile_failed"
            trace["compile_error"] = compile_err
            attempt_traces.append(trace)
            continue

        # ---- Stage 2：双模型过滤 ----
        filter_results = {}
        suites = {}
        accepted_phase2 = True
        phase2_reason = ""
        for model_key in ("model_a", "model_b"):
            undetected, suite_tests, info = evaluate_filter_model(
                agents[model_key], entry, current_bug, src_file, code,
                test_file, opts.suite_retries)
            info["model"] = agents[model_key].model_name
            filter_results[model_key] = info
            suites[model_key] = suite_tests
            trace[model_key] = {k: v for k, v in info.items() if k != "feedback"}
            if info["detected"]:
                accepted_phase2 = False
                phase2_reason = "detected_by_filter"
                test_info = f"{info['note']}\n{info.get('feedback', '')}"
                break
            if not undetected:
                accepted_phase2 = False
                phase2_reason = "suite_generation_failed"
                test_info = f"filter suite generation failed: {info['note']}\n{compile_err if not suite_tests else ''}"
                break
        if not accepted_phase2:
            set_src_code(src_file, code, current_bug)
            if test_file and os.path.exists(test_file):
                os.remove(test_file)
            trace["outcome"] = phase2_reason
            attempt_traces.append(trace)
            continue

        # ---- Stage 3：原测试套件作为元数据（不过滤）----
        purge_stale_test_classes([test_class] + declared_class_names(suites["model_a"])
                                 + declared_class_names(suites["model_b"]))
        if test_file and os.path.exists(test_file):
            os.remove(test_file)  # 过滤套件不参与原套件运行
        clean_surefire_reports()
        full_run = mvn(["test"], timeout=3600)
        full_results = parse_surefire_results()
        escaped = full_run.returncode == 0
        original_failing = [f"{c}.{n}" for (c, n), s in full_results.items() if s == "failed"]
        trace["original_suite"] = {"escaped": escaped, "failing": original_failing}

        # ---- Stage 4：等效判定（沿用语义行为一致性）----
        validation = agents["judge"].validate(
            code, current_bug, (suites["model_a"] + "\n\n" + suites["model_b"]).strip())
        if not isinstance(validation, dict):
            validation = {"is_valid_bug": False, "reason": "judge returned non-dict"}

        # 还原项目状态
        set_src_code(src_file, code, current_bug)
        if test_file and os.path.exists(test_file):
            os.remove(test_file)

        is_valid_bug = bool(validation.get("is_valid_bug", False))
        trace["outcome"] = "accepted" if is_valid_bug else "equivalent_mutation"
        attempt_traces.append(trace)

        if is_valid_bug:
            return True, {
                "bug_code": current_bug,
                "bug_summary": bug_summary,
                "suites": suites,
                "filter_results": filter_results,
                "escaped_original_suite": escaped,
                "original_failing_tests": original_failing,
                "validation": validation,
            }, attempt_traces

    return False, {}, attempt_traces


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(args):
    api_key = os.getenv("LLM_API_KEY", DEFAULT_API_KEY)
    endpoint = os.getenv("LLM_API_ENDPOINT", DEFAULT_ENDPOINT)
    if not os.getenv("LLM_API_KEY"):
        print("警告：未设置 LLM_API_KEY 环境变量，回退到内置默认 key"
              "（该 key 已进入仓库历史，建议吊销轮换并改用环境变量）")

    agents = {
        "bug": BugGenerationAgent(LLMConfig(api_key, endpoint, args.bug_model)),
        "judge": ValidAgent(LLMConfig(api_key, endpoint, args.judge_model)),
        "model_a": FilterTestGenerationAgent(
            LLMConfig(api_key, endpoint, args.filter_model_a), args.suite_retries),
        "model_b": FilterTestGenerationAgent(
            LLMConfig(api_key, endpoint, args.filter_model_b), args.suite_retries),
    }
    print(f"bug 模型: {args.bug_model} | 等效判定: {args.judge_model} | "
          f"过滤模型: {args.filter_model_a} / {args.filter_model_b}")

    with open(args.data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"共 {len(data)} 个函数待处理")

    final_results = []
    stats = []
    for idx, entry in enumerate(data):
        name = entry.get("name", f"entry_{idx}")
        print(f"\n===== [{idx + 1}/{len(data)}] {name} =====")
        if not entry.get("code") or not entry.get("src_file"):
            stats.append({"name": name, "status": "skipped_missing_fields"})
            continue

        accepted, accepted_data, traces = process_entry(entry, agents, args)
        outcome = traces[-1]["outcome"] if traces else "no_attempts"

        stats.append({"name": name, "status": "accepted" if accepted else outcome,
                      "attempts": traces})

        if accepted:
            entry["buggy_code"] = [accepted_data["bug_code"]]
            entry["tests"] = [accepted_data["suites"]["model_a"],
                              accepted_data["suites"]["model_b"]]
            entry["bug_summary"] = accepted_data["bug_summary"]
            entry["flag"] = "dual_filter_pass"
            entry["status"] = "accepted"
            entry["filter_results"] = accepted_data["filter_results"]
            entry["escaped_original_suite"] = accepted_data["escaped_original_suite"]
            entry["original_failing_tests"] = accepted_data["original_failing_tests"]
            entry["validation_result"] = accepted_data["validation"]
            entry["filter_attempts"] = len(traces)
            final_results.append(entry)
            with open(args.results_path, "w", encoding="utf-8") as f:
                json.dump(final_results, f, ensure_ascii=False, indent=4)
            try:
                os.makedirs(args.results_dir, exist_ok=True)
                shutil.copy(args.results_path, args.results_dir)
            except OSError as e:
                print(f"复制结果文件失败: {e}")
            print(f"已接受错误代码（尝试 {len(traces)} 次）:\n{accepted_data['bug_code'][:500]}")
        else:
            entry["flag"] = "not_accepted"
            entry["status"] = outcome
            entry["filter_attempts"] = len(traces)
            print(f"未接受（{outcome}，尝试 {len(traces)} 次）")

        with open(args.stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)

    print(f"\n完成：接受 {len(final_results)}/{len(data)} 条。"
          f"明细见 {args.results_path} / {args.stats_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="双大模型过滤的错误代码生成流程（Java/Maven）")
    parser.add_argument("--data-path", type=str, required=True,
                        help="输入 JSON 数据文件路径（需含 specification 字段）")
    parser.add_argument("--bug-model", type=str, default="gpt-5.4-mini",
                        help="bug 生成模型")
    parser.add_argument("--judge-model", type=str, default="gpt-5.4-mini",
                        help="等效判定模型")
    parser.add_argument("--filter-model-a", type=str, default="deepseek-v3.2",
                        help="过滤模型 A（应与被评测模型不同厂商/代际）")
    parser.add_argument("--filter-model-b", type=str, default="qwen3-coder-480b-a35b-instruct",
                        help="过滤模型 B")
    parser.add_argument("--attempts", type=int, default=5,
                        help="每个函数的 bug 对抗尝试次数上限")
    parser.add_argument("--suite-retries", type=int, default=2,
                        help="每个 bug 尝试内测试套件的重新生成次数上限")
    parser.add_argument("--results-path", type=str, default="/testbed/final_results.json")
    parser.add_argument("--stats-path", type=str, default="/testbed/filter_stats.json")
    parser.add_argument("--results-dir", type=str, default="/testbed/results")
    main(parser.parse_args())

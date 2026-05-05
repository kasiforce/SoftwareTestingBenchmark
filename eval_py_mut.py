# import argparse
# import json
# import os
# import subprocess
# from pathlib import Path


# def _to_module_path(path_str: str) -> str:
#     path = path_str.replace("\\", "/")
#     if path.endswith(".py"):
#         path = path[:-3]
#     return path.strip("/").replace("/", ".")


# def detect_target_module(data_file: str) -> str:
#     try:
#         with open(data_file, "r", encoding="utf-8") as f:
#             data = json.load(f)
#     except Exception:
#         return ""

#     for item in data:
#         src_file = item.get("src_file", "")
#         if src_file.endswith(".py"):
#             module = _to_module_path(src_file)
#             if module:
#                 return module
#     return ""


# def detect_test_module(project_root: str) -> str:
#     root = Path(project_root)
#     if not root.exists():
#         return ""

#     ignore_tokens = {".venv", "venv", "site-packages", "node_modules", ".git", "__pycache__"}
#     for py_file in root.rglob("*.py"):
#         if any(token in py_file.parts for token in ignore_tokens):
#             continue
#         name_low = py_file.name.lower()
#         if name_low.startswith("test_") or name_low.endswith("_test.py"):
#             rel = py_file.relative_to(root).as_posix()
#             return _to_module_path(rel)
#     return ""


# def run_mutpy(target: str, unit_test: str, output_file: str, project_root: str) -> int:
#     cmd = [
#         "mut.py",
#         "--target", target,
#         "--unit-test", unit_test,
#         "--runner", "pytest",
#     ]

#     try:
#         result = subprocess.run(
#             cmd,
#             cwd=project_root,
#             capture_output=True,
#             text=True,
#             check=False,
#         )
#         content = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
#     except FileNotFoundError:
#         content = "skip mutpy: mut.py not found in PATH\n"
#         result = None

#     with open(output_file, "w", encoding="utf-8") as f:
#         f.write(content)

#     return 0 if result is None else result.returncode


# def main():
#     parser = argparse.ArgumentParser(description="Run mutpy in best-effort mode and save stdout.")
#     parser.add_argument("--data-file", required=True, help="Path to data_file.json")
#     parser.add_argument("--project-root", default=".", help="Project root for test/module discovery")
#     parser.add_argument("--output", required=True, help="Output path to write mutpy stdout")
#     args = parser.parse_args()

#     target = detect_target_module(args.data_file)
#     test_module = detect_test_module(args.project_root)

#     if not target or not test_module:
#         with open(args.output, "w", encoding="utf-8") as f:
#             f.write("skip mutpy: target or unit-test not found\n")
#         return

#     run_mutpy(target=target, unit_test=test_module, output_file=args.output, project_root=args.project_root)


# if __name__ == "__main__":
#     main()




import subprocess
import os
import sys
import json
import re
from argparse import ArgumentParser
from pathlib import Path


# def syntax_analyse(project_root, gen_tests_dir):
#     test_dir = os.path.join(project_root, gen_tests_dir)
#     # 查找 test/tests 目录
#     test_dirs = []
#     for root, dirs, files in os.walk(test_dir):
#         root_path = Path(root)

#         # 如果是 test 或 tests 目录
#         if root_path.name.lower() in ['test', 'tests', 'gen_tests']:
#             test_dirs.append(root_path)

#     if not test_dirs:
#         print("未找到 test 或 tests 目录")
#         return

#     total = 0
#     syntax_correct = 0

#     # 查找并删除有语法错误的测试文件
#     for test_dir in test_dirs:
#         for py_file in test_dir.rglob('*.py'):
#             if 'test_' in py_file.name.lower() or '_test' in py_file.name.lower():
#                 try:
#                     total += 1
#                     with open(py_file, 'r', encoding='utf-8') as f:
#                         content = f.read()
#                     res = compile(content, '<string>', 'exec')
#                     syntax_correct += 1

#                 except Exception as e:
#                     os.remove(py_file)
#                     pass

#     return {"total": total, "syntax_correct": syntax_correct, "syntax_correct_rate": syntax_correct / total}

def syntax_analyse(data_file):
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = 0
    syntax_correct = 0

    for item in data:
        test_code = item.get("generated_tests", "")
        for test in test_code:
            if not test.strip():
                continue

            total += 1
            try:
                compile(test, '<string>', 'exec')
                syntax_correct += 1
            except Exception as e:
                pass

    return {"total": total, "syntax_correct": syntax_correct, "syntax_correct_rate": syntax_correct / total}


def create_and_run_py(dockerfile_path, gen_tests_dir, cover_source, project_root, data_file):
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")

    syntax_report = syntax_analyse(data_file)

    project_dir = os.path.join(cwd, project_root)

    # 确保 test_results 目录
    test_results_dir = os.path.join(cwd, "test_results", "python")
    repo_name = project_root
    if "/" in project_root:
        repo_name = project_root.split("/")[1]
    test_results_dir = os.path.join(test_results_dir, repo_name)

    spec = "specification" if "specification" in data_file else ""
    model = data_file.replace(".json","").split('_')[-1]
    framework = data_file.replace(".json","").split('_')[-2]
    mut_dir = framework + '_' + model + "_mut"
    if spec:
        mut_dir = spec + '_' + mut_dir
    test_results_dir = os.path.join(test_results_dir, mut_dir)
    print(test_results_dir)
    os.makedirs(test_results_dir, exist_ok=True)

    


    # 构建镜像
    print("开始构建镜像...")
    try:
        subprocess.run([
            "docker", "build",
            "-t", "repo-with-test",
            "-f", dockerfile_path,
            "."  # 构建上下文是当前目录
        ], check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"镜像构建失败: {e}")
        sys.exit(1)

    print("镜像构建成功")

    # 运行测试
    print("运行测试...")
    try:
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{test_results_dir}:/results",
            "-v", "./gen_test/gen_py_test.py:/testbed/gentests_files.py",
            "-v", "setup.cfg:/testbed/setup.cfg",
            "-v", f"./{data_file}:/testbed/{data_file}",
            "-v", "./gen_test/delete_py_fail_test.py:/testbed/delete_fail.py",
            "repo-with-test",
            "bash", "-c", f"""
            cd /testbed

            pip install pytest pytest-json-report pytest-timeout coverage pytest-asyncio pytest-mock pycares mutmut==2.5.1

            python /testbed/gentests_files.py \
                --project-root /testbed \
                --data-path /testbed/{data_file}

            # ======================
            # 1. coverage + pytest
            #  --source=markitdown_sample_plugin\
            # ======================
            coverage run \
                --omit="test_*.py,*_test.py,*/tests/*,*/test/*,*/gen_tests/*" \
                -m pytest \
                --import-mode=importlib \
                --continue-on-collection-errors \
                --timeout=2 \
                -q --disable-warnings --tb=no \
                --json-report \
                --json-report-file=/results/report.json

            # coverage json -o /results/coverage.json

            python /testbed/delete_fail.py /results/report.json --yes

            # mutmut run || true
            # MUTMUT_RUNNER="python -m pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no" \
            # mutmut run packages/  || true
            mutmut run --paths-to-mutate "packages/markitdown/src/markitdown/converters/_transcribe_audio.py,packages/markitdown/src/markitdown/_stream_info.py,packages/markitdown/src/markitdown/converters/_youtube_converter.py,packages/markitdown/src/markitdown/converters/_outlook_msg_converter.py,packages/markitdown/src/markitdown/converter_utils/docx/pre_process.py,packages/markitdown/src/markitdown/converters/_doc_intel_converter.py,packages/markitdown-sample-plugin/src/markitdown_sample_plugin/_plugin.py,packages/markitdown/src/markitdown/converter_utils/docx/math/omml.py,packages/markitdown-mcp/src/markitdown_mcp/__main__.py,packages/markitdown/src/markitdown/_markitdown.py,packages/markitdown/src/markitdown/converters/_epub_converter.py" --runner "python -m pytest /testbed/packages/markitdown-sample-plugin/test /testbed/packages/markitdown/test /testbed/packages/markitdown-mcp/test --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no"
            mutmut results > /results/mutmut_results.txt
            mutmut junitxml > /results/test.xml

#             # ======================
#             # 2. mutmut config
#             # ======================

#             cat >> setup.cfg << 'EOF'
# [mutmut]
# paths_to_mutate = packages/markitdown/src
# backup = False
# runner = python -m pytest --rootdir=/testbed --import-mode=importlib \
#                 --continue-on-collection-errors \
#                 --timeout=10 \
#                 -q --disable-warnings --tb=no 
# do_not_mutate=
#     */tests/*
#     */test/*
#     */gen_tests/*
# EOF


#             # export MUTMUT_CONFIG=mutmut.cfg

#             # ======================
#             # 3. run mutmut
#             # ======================
#             mutmut run || true

#             # ======================
#             # 4. save results
#             # ======================
#             mutmut results > /results/mutmut_results.txt
            
            """
        ], check=True, cwd=cwd)


        # compile, testcase = calculate_compile_pass_rate(test_results_dir + "/report.json")
        # compile["compile_pass_rate"] = compile["compile_pass"] / syntax_report["total"]
        # coverage = get_coverage_rate(test_results_dir + "/coverage.json", data_file, project_root)
        # summary = syntax_report | compile | testcase | coverage
        # summary = compile | coverage
        mutation = parse_mutmut_results(os.path.join(test_results_dir, "mutmut_results.txt"))
        with open(test_results_dir + "/mut.json", 'w', encoding='utf-8') as f:
            json.dump(mutation, f, indent=2, ensure_ascii=False)

    except subprocess.CalledProcessError as e:
        print(f"测试运行失败: {e}")
        sys.exit(1)

    print("测试完成")
    print(f"报告位置: {test_results_dir}")

def parse_mutmut_results(results_file):
    """
    解析 mutmut results 文本输出，尽可能提取总变异数、杀死数、存活数与得分。
    """
    if not os.path.exists(results_file):
        return {
            "tool": "mutmut",
            "total_mutants": 0,
            "killed_mutants": 0,
            "survived_mutants": 0,
            "timeout_mutants": 0,
            "suspicious_mutants": 0,
            "mutation_score": 0
        }

    with open(results_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 尝试匹配 mutmut 的 emoji 概览行，如：
    # "3/10 🎉 7 ⏰ 0 🤔 0 🙁 3 🔇 0"
    emoji_pattern = re.search(
        r"(?P<tested>\d+)\s*/\s*(?P<total>\d+)\s*🎉\s*(?P<killed>\d+)\s*⏰\s*(?P<timeout>\d+)\s*🤔\s*(?P<suspicious>\d+)\s*🙁\s*(?P<survived>\d+)",
        content
    )

    if emoji_pattern:
        total = int(emoji_pattern.group("total"))
        killed = int(emoji_pattern.group("killed"))
        survived = int(emoji_pattern.group("survived"))
        timeout = int(emoji_pattern.group("timeout"))
        suspicious = int(emoji_pattern.group("suspicious"))
    else:
        # 兜底：按关键字计数
        killed = len(re.findall(r"\bkilled\b", content, flags=re.IGNORECASE))
        survived = len(re.findall(r"\bsurvived\b", content, flags=re.IGNORECASE))
        timeout = len(re.findall(r"\btimeout\b", content, flags=re.IGNORECASE))
        suspicious = len(re.findall(r"\bsuspicious\b", content, flags=re.IGNORECASE))
        total = killed + survived + timeout + suspicious

    mutation_score = (killed / total) if total > 0 else 0
    return {
        "tool": "mutmut",
        "total_mutants": total,
        "killed_mutants": killed,
        "survived_mutants": survived,
        "timeout_mutants": timeout,
        "suspicious_mutants": suspicious,
        "mutation_score": round(mutation_score, 4)
    }

def load_data_file(data_path, project_root):
    """加载 data_file.json，返回文件路径集合和函数标识集合"""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    file_paths = set()
    func_keys = set()
    print(project_root)

    for entry in data:
        # print(entry.get("project_root", ''))
        src_file = entry.get('src_file')
        if not src_file:
            continue
        project_root1 = entry.get('project_root').split(project_root)[-1].split('/', 1)[-1]  # 提取相对路径
        src_file = os.path.join(project_root1, src_file)
        file_paths.add(src_file)

        name = entry.get('name', '')
        class_name = entry.get('class_name')
        if class_name:
            func_name = f"{class_name}.{name}"
        else:
            func_name = name
        func_key = f"{src_file}:{func_name}"
        func_keys.add(func_key)

    return file_paths, func_keys

import json

def get_coverage_rate(coverage_file, data_file, project_root):
    """
    仅统计：
      - 文件级：行覆盖率、分支覆盖率
      - 函数级：行覆盖率、分支覆盖率
      - 汇总：所有文件 / 所有函数的行、分支覆盖率
    """

    focal_files, focal_funcs = load_data_file(data_file, project_root)

    with open(coverage_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    result = {
        "filtered_stats": {
            "file": {
                "total_lines": 0,
                "covered_lines": 0,
                "total_branches": 0,
                "covered_branches": 0
            },
            "function": {
                "total_lines": 0,
                "covered_lines": 0,
                "total_branches": 0,
                "covered_branches": 0
            }
        },
        "file_coverage": {},
        "function_coverage": {}
    }

    # ===== 文件级汇总计数 =====
    total_file_lines = 0
    covered_file_lines = 0
    total_file_branches = 0
    covered_file_branches = 0

    # ===== 函数级汇总计数 =====
    total_func_lines = 0
    covered_func_lines = 0
    total_func_branches = 0
    covered_func_branches = 0

    for file_path, file_data in report.get("files", {}).items():
        if file_path not in focal_files:
            continue
        summary = file_data.get("summary", {})

        # ---------- 文件级 ----------
        f_total_lines = int(summary.get("num_statements", 0) or 0)
        f_covered_lines = int(summary.get("covered_lines", 0) or 0)
        f_total_branches = int(summary.get("num_branches", 0) or 0)
        f_covered_branches = int(summary.get("covered_branches", 0) or 0)

        file_line_pct = round((f_covered_lines / f_total_lines) * 100, 2) if f_total_lines else 0.0
        file_branch_pct = round((f_covered_branches / f_total_branches) * 100, 2) if f_total_branches else 0.0

        result["file_coverage"][file_path] = {
            "covered_line": f_covered_lines,
            "total_line": f_total_lines,
            "line_coverage": file_line_pct,
            "covered_branch": f_covered_branches,
            "total_branch": f_total_branches,
            "branch_coverage": file_branch_pct
        }

        total_file_lines += f_total_lines
        covered_file_lines += f_covered_lines
        total_file_branches += f_total_branches
        covered_file_branches += f_covered_branches

        # ---------- 函数级 ----------
        for func_name, func_data in (file_data.get("functions") or {}).items():
            if f"{file_path}:{func_name}" not in focal_funcs:
                continue
            if not func_name:
                continue

            s = func_data.get("summary", {})
            fn_total_lines = int(s.get("num_statements", 0) or 0)
            fn_covered_lines = int(s.get("covered_lines", 0) or 0)
            fn_total_branches = int(s.get("num_branches", func_data.get("num_branches", 0)) or 0)
            fn_covered_branches = int(s.get("covered_branches", func_data.get("covered_branches", 0)) or 0)

            fn_line_pct = round((fn_covered_lines / fn_total_lines) * 100, 2) if fn_total_lines else 0.0
            fn_branch_pct = round((fn_covered_branches / fn_total_branches) * 100, 2) if fn_total_branches else 0.0

            key = f"{file_path}:{func_name}"
            result["function_coverage"][key] = {
                "covered_line": fn_covered_lines,
                "total_line": fn_total_lines,
                "line_coverage": fn_line_pct,
                "covered_branch": fn_covered_branches,
                "total_branch": fn_total_branches,
                "branch_coverage": fn_branch_pct
            }

            total_func_lines += fn_total_lines
            covered_func_lines += fn_covered_lines
            total_func_branches += fn_total_branches
            covered_func_branches += fn_covered_branches

    # ===== 汇总覆盖率 =====
    if total_file_lines > 0:
        # result["filtered_stats"]["file_line_coverage"] = round(
        #     covered_file_lines / total_file_lines * 100, 2
        # )
        result["filtered_stats"]["file"]["total_lines"] = total_file_lines
        result["filtered_stats"]["file"]["covered_lines"] = covered_file_lines
    if total_file_branches > 0:
        # result["filtered_stats"]["file_branch_coverage"] = round(
        #     covered_file_branches / total_file_branches * 100, 2
        # )
        result["filtered_stats"]["file"]["total_branches"] = total_file_branches
        result["filtered_stats"]["file"]["covered_branches"] = covered_file_branches
    if total_func_lines > 0:
        # result["filtered_stats"]["function_line_coverage"] = round(
        #     covered_func_lines / total_func_lines * 100, 2
        # )
        result["filtered_stats"]["function"]["total_lines"] = total_func_lines
        result["filtered_stats"]["function"]["covered_lines"] = covered_func_lines
    if total_func_branches > 0:
        # result["filtered_stats"]["function_branch_coverage"] = round(
        #     covered_func_branches / total_func_branches * 100, 2
        # )
        result["filtered_stats"]["function"]["total_branches"] = total_func_branches
        result["filtered_stats"]["function"]["covered_branches"] = covered_func_branches

    return result


def calculate_compile_pass_rate(report_file):
    with open(report_file, 'r') as f:
        report = json.load(f)

    # 统计模块级收集器
    modules = []
    for collector in report.get('collectors', []):
        nodeid = collector.get('nodeid', '')

        # 判断是否为模块（文件）收集器
        # 1. nodeid以.py结尾
        # 2. 不包含::（不是类或函数收集器）
        # 3. 不是目录（type不是Dir）
        if (nodeid.endswith('.py') and
                '::' not in nodeid and
                collector.get('result') is not None):  # 确保是收集器节点
            print(nodeid)
            modules.append({
                'nodeid': nodeid,
                'outcome': collector.get('outcome'),
                'longrepr': collector.get('longrepr', '')
            })

    total = len(modules)
    passed = sum(1 for m in modules if m['outcome'] == 'passed')
    # failed = total - passed

    # print(f"总模块数: {total}")
    print(f"成功导入: {passed}")
    # print(f"导入失败: {failed}")
    # print(f"编译通过率: {passed/total*100:.2f}%")
    testcase = report.get('summary', {})
    if testcase['total']==0:
        testcase['test_pass_rate'] = 0
        testcase['run_pass_rate'] = 0
    else:
        testcase['test_pass_rate'] = testcase.get('passed', 0) / testcase['total']
        testcase['run_pass_rate'] = (testcase.get('total', 0) - testcase.get('error', 0)) / testcase['total']
    testcase = {
        "testcase": testcase
    }
    compile = {
        # "total files": total,
        "compile_pass": passed
    }



    return compile, testcase



if __name__ == "__main__":
    # parser = ArgumentParser()
    # parser.add_argument(
    #     "--dockerfile-path",
    #     type=str,
    #     help="Path to dockerfile.",
    # )
    # parser.add_argument(
    #     "--test-dir",
    #     type=str,
    #     help="Path to the genarated tests.",
    # )
    # parser.add_argument(
    #     "--cover-source",
    #     type=str,
    #     help="The dir of source code that should be covered",
    # )
    # parser.add_argument(
    #     "--project-root",
    #     type=str,
    #     help="The root dir of project.",
    # )
    # args = parser.parse_args()

    # for root, dirs, files in os.walk("tests/test_gen/python/markitdown"):
    #     for file in files:
    #         full_path = os.path.join(root, file)
    #         print(full_path)
    #         create_and_run_py("output/markitdown/dockerfile", gen_tests_dir="",
    #                   cover_source="", project_root="projects/markitdown", 
    #                   data_file=full_path)
    create_and_run_py("output/markitdown/dockerfile", gen_tests_dir="",
                      cover_source="", project_root="projects/markitdown", 
                      data_file="tests/test_gen/python/markitdown/markitdown_lite_specification_pytest_CodeLlama-7b.json")
    



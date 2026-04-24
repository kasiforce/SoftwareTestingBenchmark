# import argparse
# import concurrent.futures
# import json
# import os
# import subprocess
# import tempfile
# import time
# import traceback
# import re
# from copy import deepcopy
# from pathlib import Path
# from typing import Any, Dict, List, Optional, Tuple

# import openai
# from openai import OpenAI


# SYSTEM_PROMPT = "You are a professional test engineer specializing in writing high-quality unit test code."


# class PythonGeneratedTestRepairer:
#     def __init__(
#         self,
#         api_key: str,
#         model: str,
#         dockerfile_path: str,
#         data_file: str,
#         max_rounds: int = 3,
#         base_url: Optional[str] = None,
#         reuse_container: bool = True,
#         parallel_workers: int = 1,
#         collect_coverage_after_repair: bool = True,
#         _skip_client_init: bool = False,
#     ):
#         self.api_key = api_key
#         self.model = model
#         self.base_url = base_url
#         self.dockerfile_path = dockerfile_path
#         self.data_file = data_file
#         self.max_rounds = max_rounds
#         self.client = None if _skip_client_init else (
#             OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
#         )
#         openai.api_key = api_key
#         self.reuse_container = reuse_container
#         self.parallel_workers = max(1, parallel_workers)
#         self.collect_coverage_after_repair = collect_coverage_after_repair
#         self.container_name: Optional[str] = None
#         self._run_id = f"{os.getpid()}_{int(time.time())}"

#         # Token 统计
#         self.usage_stats = {
#             "prompt_tokens": 0,
#             "completion_tokens": 0,
#             "total_tokens": 0,
#             "cost": 0.0,
#         }
        
#         # 模型定价（人民币/百万 tokens），可根据实际使用的模型调整
#         self.model_pricing = {
#             "gpt-5-nano": {"prompt": 0.35, "completion": 2.80},
#             "gpt-4o": {"prompt": 17.5, "completion": 70.00},
#             "deepseek-v3.2": {"prompt": 2.00, "completion": 3.00},
#             "glm-4.7": {"prompt": 4.00, "completion": 16.00},
#             "qwen3-coder-480b-a35b-instruct": {"prompt": 6.00, "completion": 24.00},
#             # 可自行添加其他模型
#         }.get(self.model, {"prompt": 0.0, "completion": 0.0})  # 默认免费

#     @staticmethod
#     def _extract_code(text: str) -> str:
#         if not text:
#             return ""
#         if "```python" in text:
#             return text.split("```python", 1)[1].split("```", 1)[0].strip()
#         if "```" in text:
#             return text.split("```", 1)[1].split("```", 1)[0].strip()
#         return text.strip()

#     @staticmethod
#     def _build_initial_prompt(item: Dict[str, Any], category: str, test_framework: str) -> str:
#         function_name = item.get("name", "")
#         function_code = item.get("code", "")
#         file_path = item.get("src_file", "")
#         test_path = item.get("test_file", "")
#         signature = function_code.split(':\n')[0]
        

#         match = re.search(r'^def\s+\w+\([^)]*\)(?:\s*->\s*[^:]+)?:', function_code, re.MULTILINE)
#         if match:
#             signature = match.group(0)

#         print(signature)

#         class_name = None
#         class_info = {}
#         if item['type'] == "method":
#             class_name = item.get('class_name')
#             class_info['class_name'] = class_name
#             if item['class_constructor']:
#                 class_info['class_constructor'] = item['class_constructor']
#             if item['class_fields']:
#                 class_info['class_fields'] = item['class_fields']
#             if item['class_variables']:
#                 class_info['class_variables'] = item['class_variables']

#         specification = item.get('specification', '')

#         if category == "specification":
#             return f"""
# Please generate a test class for the following function.

# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {item.get('is_async', False)}

# Function Specification:
# ```python
# {signature}
# ```{specification}```

# Requirements:
# Use {test_framework} framework for writing tests.
# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# Each test case must be a function starting with test_.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.

# ```python
# <test code>
# """.strip()
#         else:
#             return f"""
# Please generate a test class for the following function.

# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {item.get('is_async', False)}

# Function Code:
# ```python
# {function_code}

# Requirements:
# Use {test_framework} framework for writing tests.
# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# Each test case must be a function starting with test_.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.

# ```python
# <test code>
# """.strip()

#     @staticmethod
#     def _build_error_feedback(error_messages: str) -> str:
#         return (
#             "Here are the error messages from the tests:\n"
#             f"{error_messages}\n\n"
#             "Errors exist in the generated unit tests.\n\n"
#             "Please fix the unit tests to address these errors and return ONLY the entire unit tests."
#         )

#     @staticmethod
#     def _build_runtime_feedback(test_errors: List[Dict[str, Any]]) -> str:
#         snippets = []
#         for case in test_errors:  # 处理所有失败用例
#             nodeid = case.get("nodeid", "").split("::")[-1]  # 获取测试函数名
#             outcome = case.get("outcome", "")
#             crash = (
#                 case.get("setup", {}).get("crash")
#                 or case.get("call", {}).get("crash")
#                 or case.get("teardown", {}).get("crash")
#             )
#             if crash:
#                 message = crash.get("message", "")
#             else:
#                 call = case.get("call", {})
#                 message = call.get("longrepr", "")
#             snippets.append(f"- {nodeid} ({outcome})\n{message}")
#         joined_snippets = "\n\n".join(snippets)
#         # runtime_error_messages = (
#         #     f"Pytest summary:\n{json.dumps(summary, ensure_ascii=False)}\n\n"
#         #     f"Failing test details:\n{joined_snippets}"
#         # )
#         return PythonGeneratedTestRepairer._build_error_feedback(joined_snippets)

#     @staticmethod
#     def _compile_check(code: str) -> Tuple[bool, str]:
#         try:
#             compile(code, "<string>", "exec")
#             return True, ""
#         except Exception as e:
#             return False, "".join(traceback.format_exception_only(type(e), e)).strip()

#     # def _call_llm(self, messages: List[Dict[str, str]]) -> str:
#     #     if self.client is None:
#     #         self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)
#     #     response = self.client.chat.completions.create(
#     #         model=self.model,
#     #         messages=messages,
#     #         temperature=0.0,
#     #         max_tokens=16384,
#     #     )
#     #     content = response.choices[0].message.content if response.choices else ""
#     #     return self._extract_code(content or "")

#     def _call_llm(self, messages: List[Dict[str, str]]) -> str:
#         if self.client is None:
#             self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=messages,
#             temperature=0.0,
#             max_tokens=16384,
#         )
        
#         # 提取 token 使用量
#         if response.usage:
#             prompt_tokens = response.usage.prompt_tokens
#             completion_tokens = response.usage.completion_tokens
#             total_tokens = response.usage.total_tokens
            
#             # 计算花费（美元）
#             prompt_cost = (prompt_tokens / 1_000_000) * self.model_pricing["prompt"]
#             completion_cost = (completion_tokens / 1_000_000) * self.model_pricing["completion"]
#             call_cost = prompt_cost + completion_cost
            
#             # 累加到实例统计
#             self.usage_stats["prompt_tokens"] += prompt_tokens
#             self.usage_stats["completion_tokens"] += completion_tokens
#             self.usage_stats["total_tokens"] += total_tokens
#             self.usage_stats["cost"] += call_cost
        
#         content = response.choices[0].message.content if response.choices else ""
#         return self._extract_code(content or "")

#     def _build_docker_image(self) -> None:
#         subprocess.run(
#             [
#                 "docker",
#                 "build",
#                 "-t",
#                 "repo-with-test",
#                 "-f",
#                 self.dockerfile_path,
#                 ".",
#             ],
#             check=True,
#         )

#     def _start_reusable_container(self) -> None:
#         if not self.reuse_container:
#             return
#         self.container_name = f"py-test-repair-{self._run_id}"
#         subprocess.run(
#             [
#                 "docker",
#                 "run",
#                 "-d",
#                 "--name",
#                 self.container_name,
#                 "repo-with-test",
#                 "bash",
#                 "-c",
#                 "sleep infinity",
#             ],
#             check=True,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#         )
#         subprocess.run(
#             [
#                 "docker",
#                 "exec",
#                 self.container_name,
#                 "bash",
#                 "-c",
#                 "pip install pytest pytest-json-report pytest-timeout pytest-asyncio pycares coverage",
#             ],
#             check=True,
#         )

#     def _stop_reusable_container(self) -> None:
#         if not self.container_name:
#             return
#         subprocess.run(["docker", "rm", "-f", self.container_name], check=False)
#         self.container_name = None

#     def _evaluate_single_test(self, item: Dict[str, Any], test_code: str, item_idx: int) -> Dict[str, Any]:
#         with tempfile.TemporaryDirectory(prefix="py_repair_") as td:
#             td_path = Path(td)
#             item_data = deepcopy(item)
#             item_data["generated_tests"] = [test_code]
#             item_json = td_path / "item.json"
#             item_json.write_text(json.dumps([item_data], ensure_ascii=False, indent=2), encoding="utf-8")

#             results_dir = td_path / "results"
#             results_dir.mkdir(parents=True, exist_ok=True)
#             report_path = results_dir / "report.json"
#             if self.reuse_container and self.container_name:
#                 container_report = f"/tmp/repair_report_{item_idx}.json"
#                 subprocess.run(
#                     ["docker", "cp", str(Path("gen_test/gen_tests_files.py").resolve()), f"{self.container_name}:/testbed/gentests_files.py"],
#                     check=True,
#                 )
#                 subprocess.run(["docker", "cp", str(item_json.resolve()), f"{self.container_name}:/testbed/item.json"], check=True)
                
#                 test_file = item.get("test_file", "")
#                 project_root = item.get("project_root", "").split('/')
#                 if len(project_root) > 2 and project_root[-1] != 'src':
#                     test_file = os.path.join(project_root[-1], test_file)
                
#                 cmd = f"""
# set -e
# cd /testbed
# python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
# pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no \
#   {test_file} --json-report --json-report-file={container_report} || true
# """
#                 subprocess.run(["docker", "exec", self.container_name, "bash", "-c", cmd], check=True)
#                 subprocess.run(["docker", "cp", f"{self.container_name}:{container_report}", str(report_path)], check=True)
#             else:
#                 cmd = f"""
# set -e
# cd /testbed
# pip install pytest pytest-json-report pytest-timeout pytest-asyncio pycares
# python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
# pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no \
#   {test_file} --json-report --json-report-file=/results/report.json || true
# """
#                 subprocess.run(
#                     [
#                         "docker",
#                         "run",
#                         "--rm",
#                         "-v",
#                         f"{results_dir.resolve()}:/results",
#                         "-v",
#                         f"{Path('gen_test/gen_tests_files.py').resolve()}:/testbed/gentests_files.py",
#                         "-v",
#                         f"{item_json.resolve()}:/testbed/item.json",
#                         "repo-with-test",
#                         "bash",
#                         "-c",
#                         cmd,
#                     ],
#                     check=True,
#                 )

#             if not report_path.exists():
#                 return {
#                     "ok": False,
#                     "stage": "run",
#                     "error": "pytest did not generate report.json",
#                     "summary": {},
#                     "collect_longrepr": "pytest did not generate report.json",
#                     "tests": [],
#                 }

#             report = json.loads(report_path.read_text(encoding="utf-8"))
#             collectors = report.get("collectors", [])
#             test_rel_path = item.get("test_file", "")
#             target_collectors = []
#             for c in collectors:
#                 nodeid = c.get("nodeid", "")
#                 if nodeid.endswith(test_rel_path) or nodeid == test_rel_path or nodeid.endswith(Path(test_rel_path).name):
#                     target_collectors.append(c)

#             if not target_collectors and collectors:
#                 target_collectors = collectors

#             collect_ok = all(c.get("outcome") == "passed" for c in target_collectors) if target_collectors else False
#             first_collect_err = ""
#             if not collect_ok and target_collectors:
#                 for c in target_collectors:
#                     if c.get("outcome") != "passed":
#                         first_collect_err = c.get("longrepr", "") or str(c)
#                         break

#             tests = report.get("tests", [])
#             failing_tests = [t for t in tests if t.get("outcome") in {"failed", "error"}]
#             summary = report.get("summary", {})
#             runtime_ok = not failing_tests and summary.get("error", 0) == 0 and summary.get("failed", 0) == 0

#             return {
#                 "ok": collect_ok and runtime_ok,
#                 "stage": "collect" if not collect_ok else ("run" if not runtime_ok else "done"),
#                 "collect_longrepr": first_collect_err,
#                 "tests": failing_tests,
#                 "summary": summary,
#                 "report": report,
#                 "item_idx": item_idx,
#             }

#     # def _repair_chunk(self, chunk: List[Tuple[int, Dict[str, Any]]], worker_id: int, category: str) -> List[Tuple[int, Dict[str, Any]]]:
#     #     worker = PythonGeneratedTestRepairer(
#     #         api_key=self.api_key,
#     #         model=self.model,
#     #         dockerfile_path=self.dockerfile_path,
#     #         data_file=self.data_file,
#     #         max_rounds=self.max_rounds,
#     #         base_url=self.base_url,
#     #         reuse_container=self.reuse_container,
#     #         parallel_workers=1,
#     #         collect_coverage_after_repair=self.collect_coverage_after_repair,
#     #         _skip_client_init=True,
#     #     )
#     #     worker._run_id = f"{self._run_id}_w{worker_id}"
#     #     worker._start_reusable_container()
#     #     outputs: List[Tuple[int, Dict[str, Any]]] = []
#     #     try:
#     #         for idx, item in chunk:
#     #             outputs.append((idx, worker.repair_item(item, idx, category)))
#     #     finally:
#     #         worker._stop_reusable_container()
#     #     return outputs

#     def _repair_chunk(self, chunk: List[Tuple[int, Dict[str, Any]]], worker_id: int, category: str, test_framework: str) -> Tuple[List[Tuple[int, Dict[str, Any]]], Dict[str, Any]]:
#         worker = PythonGeneratedTestRepairer(
#             api_key=self.api_key,
#             model=self.model,
#             dockerfile_path=self.dockerfile_path,
#             data_file=self.data_file,
#             max_rounds=self.max_rounds,
#             base_url=self.base_url,
#             reuse_container=self.reuse_container,
#             parallel_workers=1,
#             collect_coverage_after_repair=self.collect_coverage_after_repair,
#             _skip_client_init=True,
#         )
#         worker._run_id = f"{self._run_id}_w{worker_id}"
#         worker._start_reusable_container()
#         outputs: List[Tuple[int, Dict[str, Any]]] = []
#         try:
#             for idx, item in chunk:
#                 outputs.append((idx, worker.repair_item(item, idx, category, test_framework)))
#         finally:
#             worker._stop_reusable_container()
#         # 返回修复结果和该 worker 的 token 统计
#         return outputs, worker.usage_stats

#     def _collect_coverage(self, item: Dict[str, Any], test_code: str, item_idx: int, stage: str) -> Dict[str, Any]:
#         compile_ok, compile_err = self._compile_check(test_code)
#         if not compile_ok:
#             return {"ok": False, "stage": stage, "error": f"compile_error: {compile_err}"}

#         with tempfile.TemporaryDirectory(prefix="py_cov_") as td:
#             td_path = Path(td)
#             item_data = deepcopy(item)
#             item_data["generated_tests"] = [test_code]
#             item_json = td_path / "item.json"
#             item_json.write_text(json.dumps([item_data], ensure_ascii=False, indent=2), encoding="utf-8")
#             results_dir = td_path / "results"
#             results_dir.mkdir(parents=True, exist_ok=True)
#             cov_path = results_dir / "coverage.json"

#             if self.reuse_container and self.container_name:
#                 container_cov = f"/tmp/repair_cov_{item_idx}_{stage}.json"
#                 subprocess.run(
#                     ["docker", "cp", str(Path("gen_test/gen_tests_files.py").resolve()), f"{self.container_name}:/testbed/gentests_files.py"],
#                     check=True,
#                 )
#                 subprocess.run(["docker", "cp", str(item_json.resolve()), f"{self.container_name}:/testbed/item.json"], check=True)
#                 test_file = item_data.get("test_file", "")
#                 project_root = item_data.get("project_root", "").split('/')
#                 if len(project_root) > 2 and project_root[-1] != 'src':
#                     test_file = os.path.join(project_root[-1], test_file)
#                 cmd = f"""
# set -e
# cd /testbed
# python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
# coverage erase
# coverage run -m pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no {test_file} || true
# coverage json -o {container_cov} || true
# """
#                 subprocess.run(["docker", "exec", self.container_name, "bash", "-c", cmd], check=True)
#                 subprocess.run(["docker", "cp", f"{self.container_name}:{container_cov}", str(cov_path)], check=True)
#             else:
#                 cmd = f"""
# set -e
# cd /testbed
# pip install pytest pytest-timeout pytest-asyncio pycares coverage
# python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
# coverage erase
# coverage run -m pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no {test_file} || true
# coverage json -o /results/coverage.json || true
# """
#                 subprocess.run(
#                     [
#                         "docker",
#                         "run",
#                         "--rm",
#                         "-v",
#                         f"{results_dir.resolve()}:/results",
#                         "-v",
#                         f"{Path('gen_test/gen_tests_files.py').resolve()}:/testbed/gentests_files.py",
#                         "-v",
#                         f"{item_json.resolve()}:/testbed/item.json",
#                         "repo-with-test",
#                         "bash",
#                         "-c",
#                         cmd,
#                     ],
#                     check=True,
#                 )

#             if not cov_path.exists():
#                 return {"ok": False, "stage": stage, "error": "coverage.json not generated"}

#             coverage_report = json.loads(cov_path.read_text(encoding="utf-8"))
#             totals = coverage_report.get("totals", {})
#             return {
#                 "ok": True,
#                 "stage": stage,
#                 "line_covered": totals.get("covered_lines", 0),
#                 "line_total": totals.get("num_statements", 0),
#                 "line_rate": totals.get("percent_covered", 0),
#                 "branch_covered": totals.get("covered_branches", 0),
#                 "branch_total": totals.get("num_branches", 0),
#                 "branch_rate": totals.get("percent_covered_branches", 0),
#             }

#     def repair_item(self, item: Dict[str, Any], item_idx: int, category: str, test_framework: str) -> Dict[str, Any]:
#         tests = item.get("generated_tests") or []
#         current_test = "\n\n".join(tests) if isinstance(tests, list) else str(tests)
#         initial_test = current_test

#         messages = [
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": self._build_initial_prompt(item, category, test_framework)},
#             {"role": "assistant", "content": current_test},
#         ]

#         history = []
#         final_status = "max_rounds_reached"
#         for round_idx in range(0, self.max_rounds):
#             compile_ok, compile_err = self._compile_check(current_test)
#             if not compile_ok:
#                 user_feedback = self._build_error_feedback(compile_err)
#                 messages.append({"role": "user", "content": user_feedback})
#                 fixed = self._call_llm(messages)
#                 messages.append({"role": "assistant", "content": fixed})
#                 current_test = fixed
#                 history.append({"round": round_idx, "stage": "syntax", "feedback": compile_err})
#                 continue

#             eval_result = self._evaluate_single_test(item, current_test, item_idx)
#             if eval_result["ok"]:
#                 final_status = "success"
#                 history.append({"round": round_idx, "stage": "done"})
#                 break

#             if eval_result["stage"] == "collect":
#                 user_feedback = self._build_error_feedback(eval_result.get("collect_longrepr", ""))
#                 history.append({
#                     "round": round_idx,
#                     "stage": "collect",
#                     "feedback": eval_result.get("collect_longrepr", ""),
#                 })
#             else:
#                 user_feedback = self._build_runtime_feedback(eval_result.get("tests", []))
#                 history.append({
#                     "round": round_idx,
#                     "stage": "run",
#                     "feedback": eval_result.get("summary", {}),
#                 })

#             messages.append({"role": "user", "content": user_feedback})
#             fixed = self._call_llm(messages)
#             messages.append({"role": "assistant", "content": fixed})
#             current_test = fixed

#         out = deepcopy(item)
#         out["generated_tests"] = [current_test]
#         out["repair_status"] = final_status
#         out["repair_history"] = history
#         if self.collect_coverage_after_repair:
#             baseline_cov = self._collect_coverage(item, initial_test, item_idx, "initial")
#             final_cov = self._collect_coverage(item, current_test, item_idx, "final")
#             out["coverage_initial"] = baseline_cov
#             out["coverage_final"] = final_cov
#             if baseline_cov.get("ok") and final_cov.get("ok"):
#                 out["coverage_delta"] = {
#                     "line_rate_delta": final_cov.get("line_rate", 0) - baseline_cov.get("line_rate", 0),
#                     "line_covered_delta": final_cov.get("line_covered", 0) - baseline_cov.get("line_covered", 0),
#                     "branch_rate_delta": final_cov.get("branch_rate", 0) - baseline_cov.get("branch_rate", 0),
#                     "branch_covered_delta": final_cov.get("branch_covered", 0) - baseline_cov.get("branch_covered", 0),
#                 }
#         return out

#     # def repair_file(self, output_file: str) -> None:
#     #     with open(self.data_file, "r", encoding="utf-8") as f:
#     #         data = json.load(f)

#     #     if "specification" in data_file:
#     #         category = "specification"
#     #     else:            
#     #         category = "code"

#     #     self._build_docker_image()
#     #     if self.parallel_workers == 1:
#     #         self._start_reusable_container()
#     #         try:
#     #             repaired = []
#     #             for idx, item in enumerate(data):
#     #                 repaired_item = self.repair_item(item, idx, category)
#     #                 repaired.append(repaired_item)
#     #                 with open(output_file, "w", encoding="utf-8") as wf:
#     #                     json.dump(repaired, wf, ensure_ascii=False, indent=2)
#     #         finally:
#     #             self._stop_reusable_container()
#     #         return

#     #     indexed = list(enumerate(data))
#     #     chunks: List[List[Tuple[int, Dict[str, Any]]]] = [[] for _ in range(self.parallel_workers)]
#     #     for i, pair in enumerate(indexed):
#     #         chunks[i % self.parallel_workers].append(pair)
#     #     chunks = [c for c in chunks if c]

#     #     results_map: Dict[int, Dict[str, Any]] = {}
#     #     with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
#     #         futures = [
#     #             executor.submit(self._repair_chunk, chunk, wid)
#     #             for wid, chunk in enumerate(chunks)
#     #         ]
#     #         for fut in concurrent.futures.as_completed(futures):
#     #             for idx, repaired_item in fut.result():
#     #                 results_map[idx] = repaired_item
#     #             ordered = [results_map[i] for i in sorted(results_map.keys())]
#     #             with open(output_file, "w", encoding="utf-8") as wf:
#     #                 json.dump(ordered, wf, ensure_ascii=False, indent=2)

#     def repair_file(self, output_file: str) -> None:
#         with open(self.data_file, "r", encoding="utf-8") as f:
#             data = json.load(f)
        
#         category = "code"
#         if "specification" in self.data_file:
#             category = "specification"

        
#         test_framework = "pytest"
#         if "unittest" in self.data_file:
#             test_framework = "unittest"

#         self._build_docker_image()
        
#         if self.parallel_workers == 1:
#             self._start_reusable_container()
#             try:
#                 repaired = []
#                 for idx, item in enumerate(data):
#                     repaired_item = self.repair_item(item, idx, category, test_framework)
#                     repaired.append(repaired_item)
#                     with open(output_file, "w", encoding="utf-8") as wf:
#                         json.dump(repaired, wf, ensure_ascii=False, indent=2)
#             finally:
#                 self._stop_reusable_container()
            
#             # 打印统计
#             self._print_usage_summary(self.usage_stats)
#             return

#         # 并行模式
#         indexed = list(enumerate(data))
#         chunks: List[List[Tuple[int, Dict[str, Any]]]] = [[] for _ in range(self.parallel_workers)]
#         for i, pair in enumerate(indexed):
#             chunks[i % self.parallel_workers].append(pair)
#         chunks = [c for c in chunks if c]

#         results_map: Dict[int, Dict[str, Any]] = {}
#         total_usage = deepcopy(self.usage_stats)  # 主实例可能没有调用

#         with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
#             futures = [
#                 executor.submit(self._repair_chunk, chunk, wid, category, test_framework)
#                 for wid, chunk in enumerate(chunks)
#             ]
#             for fut in concurrent.futures.as_completed(futures):
#                 chunk_results, worker_usage = fut.result()
#                 for key in total_usage:
#                     total_usage[key] += worker_usage.get(key, 0)
                
#                 for idx, repaired_item in chunk_results:
#                     results_map[idx] = repaired_item
#                 ordered = [results_map[i] for i in sorted(results_map.keys())]
#                 summary_data = {
#                     "items": ordered,
#                     "_usage_summary": total_usage
#                 }
#                 with open(output_file, "w", encoding="utf-8") as wf:
#                     json.dump(summary_data, wf, ensure_ascii=False, indent=2)

       

# def main() -> None:
#     # parser = argparse.ArgumentParser()
#     # parser.add_argument("--data-file", required=True, help="Input json file under tests/test_gen/python")
#     # parser.add_argument("--output-file", required=True, help="Output repaired json file")
#     # parser.add_argument("--dockerfile-path", required=True, help="Project dockerfile used to run pytest")
#     # parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", ""), help="LLM API key")
#     # parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", ""), help="Optional OpenAI base url")
#     # parser.add_argument("--model", default="gpt-5-nano", help="Model for repair")
#     # parser.add_argument("--max-rounds", type=int, default=3, help="Max repair rounds")
#     # parser.add_argument("--no-reuse-container", action="store_true", help="Disable long-lived docker container reuse")
#     # parser.add_argument("--parallel-workers", type=int, default=1, help="Parallel worker count for large datasets")
#     # parser.add_argument("--no-coverage-after-repair", action="store_true", help="Disable coverage collection after repair ends")
#     # args = parser.parse_args()

#     # if not args.api_key:
#     #     raise ValueError("Please provide --api-key or set OPENAI_API_KEY")

#     # repairer = PythonGeneratedTestRepairer(
#     #     api_key=args.api_key,
#     #     model=args.model,
#     #     dockerfile_path=args.dockerfile_path,
#     #     data_file=args.data_file,
#     #     max_rounds=args.max_rounds,
#     #     base_url=args.base_url or None,
#     #     reuse_container=not args.no_reuse_container,
#     #     parallel_workers=args.parallel_workers,
#     #     collect_coverage_after_repair=not args.no_coverage_after_repair,
#     # )

#     repairer = PythonGeneratedTestRepairer(
#         api_key="sk-YWFOQUUEmAJpfzAlLRfKqUvYF3zkP4IFXbtO7GqYZTa1agtD",
#         model="gpt-5-nano",
#         dockerfile_path="output/markitdown/dockerfile",
#         data_file="tests/test_gen/python/markitdown/markitdown_lite_pytest_gpt5nano.json",
#         max_rounds=3,
#         base_url="https://api.agicto.cn/v1",
#         reuse_container=True,
#         parallel_workers=2,
#         collect_coverage_after_repair=False,
#     )

#     repairer.repair_file("test_results/python/markitdown/pytest_gpt-5_fix.json")


# if __name__ == "__main__":
#     main()




import argparse
import concurrent.futures
import json
import os
import subprocess
import tempfile
import time
import traceback
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openai
from openai import OpenAI


SYSTEM_PROMPT = "You are a professional test engineer specializing in writing high-quality unit test code."


class PythonGeneratedTestRepairer:
    def __init__(
        self,
        api_key: str,
        model: str,
        dockerfile_path: str,
        data_file: str,
        max_rounds: int = 3,
        base_url: Optional[str] = None,
        reuse_container: bool = True,
        parallel_workers: int = 1,
        collect_coverage_after_repair: bool = True,
        _skip_client_init: bool = False,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.dockerfile_path = dockerfile_path
        self.data_file = data_file
        self.max_rounds = max_rounds
        self.client = None if _skip_client_init else (
            OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        )
        openai.api_key = api_key
        self.reuse_container = reuse_container
        self.parallel_workers = max(1, parallel_workers)
        self.collect_coverage_after_repair = collect_coverage_after_repair
        self.container_name: Optional[str] = None
        self._run_id = f"{os.getpid()}_{int(time.time())}"

        # Token 统计
        self.usage_stats = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
        }

        # 模型定价（人民币/百万 tokens），可根据实际使用的模型调整
        self.model_pricing = {
            "gpt-5-nano": {"prompt": 0.35, "completion": 2.80},
            "gpt-4o": {"prompt": 17.5, "completion": 70.00},
            "deepseek-v3.2": {"prompt": 2.00, "completion": 3.00},
            "glm-4.7": {"prompt": 4.00, "completion": 16.00},
            "qwen3-coder-480b-a35b-instruct": {"prompt": 6.00, "completion": 24.00},
            # 可自行添加其他模型
        }.get(self.model, {"prompt": 0.0, "completion": 0.0})  # 默认免费

    @staticmethod
    def _extract_code(text: str) -> str:
        if not text:
            return ""
        if "```python" in text:
            return text.split("```python", 1)[1].split("```", 1)[0].strip()
        if "```" in text:
            return text.split("```", 1)[1].split("```", 1)[0].strip()
        return text.strip()

    @staticmethod
    def _build_initial_prompt(item: Dict[str, Any], category: str, test_framework: str) -> str:
        function_name = item.get("name", "")
        function_code = item.get("code", "")
        file_path = item.get("src_file", "")
        test_path = item.get("test_file", "")
        signature = function_code.split(':\n')[0]

        match = re.search(r'^def\s+\w+\([^)]*\)(?:\s*->\s*[^:]+)?:', function_code, re.MULTILINE)
        if match:
            signature = match.group(0)

        class_name = None
        class_info = {}
        if item.get('type') == "method":
            class_name = item.get('class_name')
            class_info['class_name'] = class_name
            if item.get('class_constructor'):
                class_info['class_constructor'] = item['class_constructor']
            if item.get('class_fields'):
                class_info['class_fields'] = item['class_fields']
            if item.get('class_variables'):
                class_info['class_variables'] = item['class_variables']

        specification = item.get('specification', '')

        if category == "specification":
            return f"""
Please generate a test class for the following function.

Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {item.get('is_async', False)}

Function Specification:
```python
{signature}
```{specification}```

Requirements:
Use {test_framework} framework for writing tests.
Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
Each test case must be a function starting with test_.
The test code should be written into {test_path}. Please make sure the imports are correct.
Return ONLY code without explanations, non-code text, or markdown formatting.

```python
<test code>
""".strip()
        else:
            return f"""
Please generate a test class for the following function.

Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {item.get('is_async', False)}

Function Code:
```python
{function_code}

Requirements:
Use {test_framework} framework for writing tests.
Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
Each test case must be a function starting with test_.
The test code should be written into {test_path}. Please make sure the imports are correct.
Return ONLY code without explanations, non-code text, or markdown formatting.

```python
<test code>
""".strip()

    @staticmethod
    def _build_error_feedback(error_messages: str) -> str:
        return (
            "Here are the error messages from the tests:\n"
            f"{error_messages}\n\n"
            "Errors exist in the generated unit tests.\n\n"
            "Please fix the unit tests to address these errors and return ONLY the entire unit tests."
        )

    @staticmethod
    def _build_runtime_feedback(test_errors: List[Dict[str, Any]]) -> str:
        snippets = []
        for case in test_errors:  # 处理所有失败用例
            nodeid = case.get("nodeid", "").split("::")[-1]  # 获取测试函数名
            outcome = case.get("outcome", "")
            crash = (
                case.get("setup", {}).get("crash")
                or case.get("call", {}).get("crash")
                or case.get("teardown", {}).get("crash")
            )
            if crash:
                message = crash.get("message", "")
            else:
                call = case.get("call", {})
                message = call.get("longrepr", "")
            snippets.append(f"- {nodeid} ({outcome})\n{message}")
        joined_snippets = "\n\n".join(snippets)
        return PythonGeneratedTestRepairer._build_error_feedback(joined_snippets)

    @staticmethod
    def _compile_check(code: str) -> Tuple[bool, str]:
        try:
            compile(code, "<string>", "exec")
            return True, ""
        except Exception as e:
            return False, "".join(traceback.format_exception_only(type(e), e)).strip()

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        if self.client is None:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            max_tokens=16384,
        )

        # 提取 token 使用量
        if response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # 计算花费（人民币）
            prompt_cost = (prompt_tokens / 1_000_000) * self.model_pricing["prompt"]
            completion_cost = (completion_tokens / 1_000_000) * self.model_pricing["completion"]
            call_cost = prompt_cost + completion_cost

            # 累加到实例统计
            self.usage_stats["prompt_tokens"] += prompt_tokens
            self.usage_stats["completion_tokens"] += completion_tokens
            self.usage_stats["total_tokens"] += total_tokens
            self.usage_stats["cost"] += call_cost

        content = response.choices[0].message.content if response.choices else ""
        return self._extract_code(content or "")

    def _build_docker_image(self) -> None:
        subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "repo-with-test",
                "-f",
                self.dockerfile_path,
                ".",
            ],
            check=True,
        )

    def _start_reusable_container(self) -> None:
        if not self.reuse_container:
            return
        self.container_name = f"py-test-repair-{self._run_id}"
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                self.container_name,
                "repo-with-test",
                "bash",
                "-c",
                "sleep infinity",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            [
                "docker",
                "exec",
                self.container_name,
                "bash",
                "-c",
                "pip install pytest pytest-json-report pytest-timeout pytest-asyncio pytest-mock pycares coverage",
            ],
            check=True,
        )

    def _stop_reusable_container(self) -> None:
        if not self.container_name:
            return
        subprocess.run(["docker", "rm", "-f", self.container_name], check=False)
        self.container_name = None

    def _evaluate_single_test(self, item: Dict[str, Any], test_code: str, item_idx: int) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="py_repair_") as td:
            td_path = Path(td)
            item_data = deepcopy(item)
            item_data["generated_tests"] = [test_code]
            item_json = td_path / "item.json"
            item_json.write_text(json.dumps([item_data], ensure_ascii=False, indent=2), encoding="utf-8")

            results_dir = td_path / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            report_path = results_dir / "report.json"
            if self.reuse_container and self.container_name:
                container_report = f"/tmp/repair_report_{item_idx}.json"
                subprocess.run(
                    ["docker", "cp", str(Path("gen_test/gen_tests_files.py").resolve()), f"{self.container_name}:/testbed/gentests_files.py"],
                    check=True,
                )
                subprocess.run(["docker", "cp", str(item_json.resolve()), f"{self.container_name}:/testbed/item.json"], check=True)

                test_file = item.get("test_file", "")
                project_root = item.get("project_root", "").split('/')
                if len(project_root) > 2 and project_root[-1] != 'src':
                    test_file = os.path.join(project_root[-1], test_file)

                cmd = f"""
set -e
cd /testbed
python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no \
  {test_file} --json-report --json-report-file={container_report} || true
"""
                subprocess.run(["docker", "exec", self.container_name, "bash", "-c", cmd], check=True)
                subprocess.run(["docker", "cp", f"{self.container_name}:{container_report}", str(report_path)], check=True)
            else:
                test_file = item.get("test_file", "")
                project_root = item.get("project_root", "").split('/')
                if len(project_root) > 2 and project_root[-1] != 'src':
                    test_file = os.path.join(project_root[-1], test_file)

                cmd = f"""
set -e
cd /testbed
pip install pytest pytest-json-report pytest-timeout pytest-asyncio pytest-mock pycares
python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no \
  {test_file} --json-report --json-report-file=/results/report.json || true
"""
                subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "-v",
                        f"{results_dir.resolve()}:/results",
                        "-v",
                        f"{Path('gen_test/gen_tests_files.py').resolve()}:/testbed/gentests_files.py",
                        "-v",
                        f"{item_json.resolve()}:/testbed/item.json",
                        "repo-with-test",
                        "bash",
                        "-c",
                        cmd,
                    ],
                    check=True,
                )

            if not report_path.exists():
                return {
                    "ok": False,
                    "stage": "run",
                    "error": "pytest did not generate report.json",
                    "summary": {},
                    "collect_longrepr": "pytest did not generate report.json",
                    "tests": [],
                }

            report = json.loads(report_path.read_text(encoding="utf-8"))
            collectors = report.get("collectors", [])
            test_rel_path = item.get("test_file", "")
            target_collectors = []
            for c in collectors:
                nodeid = c.get("nodeid", "")
                if nodeid.endswith(test_rel_path) or nodeid == test_rel_path or nodeid.endswith(Path(test_rel_path).name):
                    target_collectors.append(c)

            if not target_collectors and collectors:
                target_collectors = collectors

            collect_ok = all(c.get("outcome") == "passed" for c in target_collectors) if target_collectors else False
            first_collect_err = ""
            if not collect_ok and target_collectors:
                for c in target_collectors:
                    if c.get("outcome") != "passed":
                        first_collect_err = c.get("longrepr", "") or str(c)
                        break

            tests = report.get("tests", [])
            failing_tests = [t for t in tests if t.get("outcome") in {"failed", "error"}]
            summary = report.get("summary", {})
            runtime_ok = not failing_tests and summary.get("error", 0) == 0 and summary.get("failed", 0) == 0

            return {
                "ok": collect_ok and runtime_ok,
                "stage": "collect" if not collect_ok else ("run" if not runtime_ok else "done"),
                "collect_longrepr": first_collect_err,
                "tests": failing_tests,
                "summary": summary,
                "report": report,
                "item_idx": item_idx,
            }

    def _repair_chunk(self, chunk: List[Tuple[int, Dict[str, Any]]], worker_id: int, category: str, test_framework: str) -> Tuple[List[Tuple[int, Dict[str, Any]]], Dict[str, Any]]:
        worker = PythonGeneratedTestRepairer(
            api_key=self.api_key,
            model=self.model,
            dockerfile_path=self.dockerfile_path,
            data_file=self.data_file,
            max_rounds=self.max_rounds,
            base_url=self.base_url,
            reuse_container=self.reuse_container,
            parallel_workers=1,
            collect_coverage_after_repair=self.collect_coverage_after_repair,
            _skip_client_init=True,
        )
        worker._run_id = f"{self._run_id}_w{worker_id}"
        worker._start_reusable_container()
        outputs: List[Tuple[int, Dict[str, Any]]] = []
        try:
            for idx, item in chunk:
                outputs.append((idx, worker.repair_item(item, idx, category, test_framework)))
        finally:
            worker._stop_reusable_container()
        # 返回修复结果和该 worker 的 token 统计
        return outputs, worker.usage_stats

    def _collect_coverage(self, item: Dict[str, Any], test_code: str, item_idx: int, stage: str) -> Dict[str, Any]:
        compile_ok, compile_err = self._compile_check(test_code)
        if not compile_ok:
            return {"ok": False, "stage": stage, "error": f"compile_error: {compile_err}"}

        with tempfile.TemporaryDirectory(prefix="py_cov_") as td:
            td_path = Path(td)
            item_data = deepcopy(item)
            item_data["generated_tests"] = [test_code]
            item_json = td_path / "item.json"
            item_json.write_text(json.dumps([item_data], ensure_ascii=False, indent=2), encoding="utf-8")
            results_dir = td_path / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            cov_path = results_dir / "coverage.json"

            if self.reuse_container and self.container_name:
                container_cov = f"/tmp/repair_cov_{item_idx}_{stage}.json"
                subprocess.run(
                    ["docker", "cp", str(Path("gen_test/gen_tests_files.py").resolve()), f"{self.container_name}:/testbed/gentests_files.py"],
                    check=True,
                )
                subprocess.run(["docker", "cp", str(item_json.resolve()), f"{self.container_name}:/testbed/item.json"], check=True)
                test_file = item_data.get("test_file", "")
                project_root = item_data.get("project_root", "").split('/')
                if len(project_root) > 2 and project_root[-1] != 'src':
                    test_file = os.path.join(project_root[-1], test_file)
                cmd = f"""
set -e
cd /testbed
python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
coverage erase
coverage run -m pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no {test_file} || true
coverage json -o {container_cov} || true
"""
                subprocess.run(["docker", "exec", self.container_name, "bash", "-c", cmd], check=True)
                subprocess.run(["docker", "cp", f"{self.container_name}:{container_cov}", str(cov_path)], check=True)
            else:
                test_file = item_data.get("test_file", "")
                project_root = item_data.get("project_root", "").split('/')
                if len(project_root) > 2 and project_root[-1] != 'src':
                    test_file = os.path.join(project_root[-1], test_file)
                cmd = f"""
set -e
cd /testbed
pip install pytest pytest-timeout pytest-asyncio pycares pytest-mock coverage
python /testbed/gentests_files.py --project-root /testbed --data-path /testbed/item.json
coverage erase
coverage run -m pytest --import-mode=importlib --continue-on-collection-errors --timeout=2 -q --disable-warnings --tb=no {test_file} || true
coverage json -o /results/coverage.json || true
"""
                subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "-v",
                        f"{results_dir.resolve()}:/results",
                        "-v",
                        f"{Path('gen_test/gen_tests_files.py').resolve()}:/testbed/gentests_files.py",
                        "-v",
                        f"{item_json.resolve()}:/testbed/item.json",
                        "repo-with-test",
                        "bash",
                        "-c",
                        cmd,
                    ],
                    check=True,
                )

            if not cov_path.exists():
                return {"ok": False, "stage": stage, "error": "coverage.json not generated"}

            coverage_report = json.loads(cov_path.read_text(encoding="utf-8"))
            totals = coverage_report.get("totals", {})
            return {
                "ok": True,
                "stage": stage,
                "line_covered": totals.get("covered_lines", 0),
                "line_total": totals.get("num_statements", 0),
                "line_rate": totals.get("percent_covered", 0),
                "branch_covered": totals.get("covered_branches", 0),
                "branch_total": totals.get("num_branches", 0),
                "branch_rate": totals.get("percent_covered_branches", 0),
            }

    def repair_item(self, item: Dict[str, Any], item_idx: int, category: str, test_framework: str) -> Dict[str, Any]:
        tests = item.get("generated_tests") or []
        current_test = "\n\n".join(tests) if isinstance(tests, list) else str(tests)
        initial_test = current_test

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._build_initial_prompt(item, category, test_framework)},
            {"role": "assistant", "content": current_test},
        ]

        history = []
        final_status = "max_rounds_reached"
        for round_idx in range(0, self.max_rounds + 1):
            compile_ok, compile_err = self._compile_check(current_test)
            if not compile_ok:
                user_feedback = self._build_error_feedback(compile_err)
                messages.append({"role": "user", "content": user_feedback})
                fixed = self._call_llm(messages)
                messages.append({"role": "assistant", "content": fixed})
                current_test = fixed
                history.append({
                    "round": round_idx,
                    "stage": "syntax",
                    "feedback": compile_err,
                    "test_code": current_test
                })
                continue

            eval_result = self._evaluate_single_test(item, current_test, item_idx)
            if eval_result["ok"]:
                final_status = "success"
                history.append({
                    "round": round_idx,
                    "stage": "done",
                    "test_code": current_test
                })
                break

            if eval_result["stage"] == "collect":
                user_feedback = self._build_error_feedback(eval_result.get("collect_longrepr", ""))
                history.append({
                    "round": round_idx,
                    "stage": "collect",
                    "feedback": eval_result.get("collect_longrepr", ""),
                    "test_code": current_test
                })
            else:
                # 提取详细的运行时错误信息
                error_details = []
                for t in eval_result.get("tests", []):
                    crash = (
                        t.get("setup", {}).get("crash")
                        or t.get("call", {}).get("crash")
                        or t.get("teardown", {}).get("crash")
                    )
                    error_details.append({
                        "nodeid": t.get("nodeid"),
                        "outcome": t.get("outcome"),
                        "message": crash.get("message") if crash else t.get("call", {}).get("longrepr")
                    })
                user_feedback = self._build_runtime_feedback(eval_result.get("tests", []))
                history.append({
                    "round": round_idx,
                    "stage": "run",
                    "feedback": {
                        # "summary": eval_result.get("summary"),
                        "errors": error_details
                    },
                    "test_code": current_test
                })

            messages.append({"role": "user", "content": user_feedback})
            fixed = self._call_llm(messages)
            messages.append({"role": "assistant", "content": fixed})
            current_test = fixed

        out = deepcopy(item)
        out["generated_tests"] = [current_test]
        out["repair_status"] = final_status
        out["repair_history"] = history
        if self.collect_coverage_after_repair:
            baseline_cov = self._collect_coverage(item, initial_test, item_idx, "initial")
            final_cov = self._collect_coverage(item, current_test, item_idx, "final")
            out["coverage_initial"] = baseline_cov
            out["coverage_final"] = final_cov
            if baseline_cov.get("ok") and final_cov.get("ok"):
                out["coverage_delta"] = {
                    "line_rate_delta": final_cov.get("line_rate", 0) - baseline_cov.get("line_rate", 0),
                    "line_covered_delta": final_cov.get("line_covered", 0) - baseline_cov.get("line_covered", 0),
                    "branch_rate_delta": final_cov.get("branch_rate", 0) - baseline_cov.get("branch_rate", 0),
                    "branch_covered_delta": final_cov.get("branch_covered", 0) - baseline_cov.get("branch_covered", 0),
                }
        return out

    def _print_usage_summary(self, usage: Dict[str, Any]) -> None:
        print("\n" + "=" * 50)
        print("API 使用统计:")
        print(f"  输入 tokens:     {usage.get('prompt_tokens', 0):,}")
        print(f"  输出 tokens:     {usage.get('completion_tokens', 0):,}")
        print(f"  总 tokens:       {usage.get('total_tokens', 0):,}")
        print(f"  预估花费:        ¥{usage.get('cost', 0.0):.4f} 人民币")
        print("=" * 50)

    # def repair_file(self, output_file: str) -> None:
    #     with open(self.data_file, "r", encoding="utf-8") as f:
    #         data = json.load(f)

    #     category = "code"
    #     if "specification" in self.data_file:
    #         category = "specification"

    #     test_framework = "pytest"
    #     if "unittest" in self.data_file:
    #         test_framework = "unittest"

    #     self._build_docker_image()

    #     if self.parallel_workers == 1:
    #         self._start_reusable_container()
    #         try:
    #             repaired = []
    #             for idx, item in enumerate(data):
    #                 repaired_item = self.repair_item(item, idx, category, test_framework)
    #                 repaired.append(repaired_item)
    #                 with open(output_file, "w", encoding="utf-8") as wf:
    #                     json.dump(repaired, wf, ensure_ascii=False, indent=2)
    #         finally:
    #             self._stop_reusable_container()

    #         # 打印统计
    #         self._print_usage_summary(self.usage_stats)
    #         return

    #     # 并行模式
    #     indexed = list(enumerate(data))
    #     chunks: List[List[Tuple[int, Dict[str, Any]]]] = [[] for _ in range(self.parallel_workers)]
    #     for i, pair in enumerate(indexed):
    #         chunks[i % self.parallel_workers].append(pair)
    #     chunks = [c for c in chunks if c]

    #     results_map: Dict[int, Dict[str, Any]] = {}
    #     total_usage = deepcopy(self.usage_stats)  # 主实例可能没有调用

    #     with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
    #         futures = [
    #             executor.submit(self._repair_chunk, chunk, wid, category, test_framework)
    #             for wid, chunk in enumerate(chunks)
    #         ]
    #         for fut in concurrent.futures.as_completed(futures):
    #             chunk_results, worker_usage = fut.result()
    #             for key in total_usage:
    #                 total_usage[key] += worker_usage.get(key, 0)

    #             for idx, repaired_item in chunk_results:
    #                 results_map[idx] = repaired_item
    #             ordered = [results_map[i] for i in sorted(results_map.keys())]
    #             summary_data = {
    #                 "items": ordered,
    #                 "_usage_summary": total_usage
    #             }
    #             with open(output_file, "w", encoding="utf-8") as wf:
    #                 json.dump(summary_data, wf, ensure_ascii=False, indent=2)

    #     self._print_usage_summary(total_usage)

    def repair_file(self, output_file: str) -> None:
        
        start_time = time.time()
        
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not os.path.exists(output_file):
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

        category = "code"
        if "specification" in self.data_file:
            category = "specification"

        test_framework = "pytest"
        if "unittest" in self.data_file:
            test_framework = "unittest"

        self._build_docker_image()

        if self.parallel_workers == 1:
            self._start_reusable_container()
            total_usage = deepcopy(self.usage_stats)
            try:
                results_map = {}
                for idx, item in enumerate(data):
                    repaired_item, usage = self.repair_item(item, idx, category, test_framework, return_usage=True)
                    results_map[idx] = repaired_item
                    # 累加使用量
                    for key in total_usage:
                        total_usage[key] += usage.get(key, 0)
                    # 实时写入
                    ordered = [results_map[i] for i in sorted(results_map.keys())]
                    elapsed = time.time() - start_time
                    summary_data = {
                        "items": ordered,
                        "_usage_summary": total_usage,
                        "_elapsed_seconds": elapsed,
                    }
                    with open(output_file, "w", encoding="utf-8") as wf:
                        json.dump(summary_data, wf, ensure_ascii=False, indent=2)
            finally:
                self._stop_reusable_container()

            elapsed = time.time() - start_time
            self._print_usage_summary(total_usage, elapsed)
            return

        # 并行模式
        indexed = list(enumerate(data))
        chunks: List[List[Tuple[int, Dict[str, Any]]]] = [[] for _ in range(self.parallel_workers)]
        for i, pair in enumerate(indexed):
            chunks[i % self.parallel_workers].append(pair)
        chunks = [c for c in chunks if c]

        results_map: Dict[int, Dict[str, Any]] = {}
        total_usage = deepcopy(self.usage_stats)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            futures = [
                executor.submit(self._repair_chunk, chunk, wid, category, test_framework)
                for wid, chunk in enumerate(chunks)
            ]
            for fut in concurrent.futures.as_completed(futures):
                chunk_results, worker_usage = fut.result()
                for key in total_usage:
                    total_usage[key] += worker_usage.get(key, 0)

                for idx, repaired_item in chunk_results:
                    results_map[idx] = repaired_item
                ordered = [results_map[i] for i in sorted(results_map.keys())]
                elapsed = time.time() - start_time
                summary_data = {
                    "items": ordered,
                    "_usage_summary": total_usage,
                    "_elapsed_seconds": elapsed,
                }
                with open(output_file, "w", encoding="utf-8") as wf:
                    json.dump(summary_data, wf, ensure_ascii=False, indent=2)


def main() -> None:
    # 示例用法，可根据需要取消注释命令行参数解析部分


    for root, dirs, files in os.walk("tests/test_gen/python/pylint"):
        for file in files:
            if "codellama" in  file.lower() or "ds6.7b" in file.lower():
                continue
            if  "specification_unittest_DSv" in file or "pylint_pytest_qwen" in file or "specification_pytest_gpt5" in file:
                if "qwen" in file.lower() :
                    model_name = "qwen3-coder-480b-a35b-instruct"
                if "glm" in file.lower():
                    model_name = "glm-4.7"
                if "gpt5" in file.lower():
                    model_name = "gpt-5-nano"
                if "gpt4o" in file.lower():
                    model_name = "gpt-4o"
                if "dsv3.2" in file.lower():
                    model_name = "deepseek-v3.2"

                full_path = os.path.join(root, file)
                print(full_path)
                print(model_name)
                repairer = PythonGeneratedTestRepairer(
                    api_key="",
                    model=model_name,
                    dockerfile_path="output/pylint/dockerfile",
                    data_file=full_path,
                    max_rounds=3,
                    base_url="",
                    reuse_container=True,
                    parallel_workers=2,
                    collect_coverage_after_repair=False,
                )

                repairer.repair_file("tests/test_gen/python/fix_pylint/repaired_" + file)

                time.sleep(10)  # 每个文件处理完后等待10秒，避免过于频繁的API调用


if __name__ == "__main__":
    main()
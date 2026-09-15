"""
使用 Copilot CLI 批量为数据集中的函数生成单元测试，并保存生成的测试代码。

增强功能：
- 执行后自动读取生成的测试文件内容，存入结果 JSON。
- 完善的错误处理与超时控制。
"""

import json
import subprocess
import time
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime


def setup_logging(log_file: str):
    """配置日志，同时输出到文件和终端"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def build_prompt(function_info: dict) -> str:
    """根据数据集条目构建发送给 Copilot CLI 的提示"""
    
    function_name = function_info['name']

    function_code = function_info['buggy_code'][-1]
    imports = function_info.get('import', '')

    # signature = function_code.split(':\n')[0]
    signature = function_code.split('{', 1)[0].rstrip()
    print(signature)

    # match = re.search(r'^def\s+\w+\([^)]*\)(?:\s*->\s*[^:]+)?:', function_code, re.MULTILINE)
    # if match:
    #     signature = match.group(0)

    class_name = None
    class_info = {}
    if function_info['type'] == "method":
        class_name = function_info.get('class_name')
        class_info['class_name'] = class_name
        if function_info['class_constructor']:
            class_info['class_constructor'] = function_info['class_constructor']
        if function_info['class_fields']:
            class_info['class_fields'] = function_info['class_fields']
        # if function_info['class_variables']:
        #     class_info['class_variables'] = function_info['class_variables']

    specification = function_info['specification']
    file_path = function_info['src_file']
    test_path = function_info['test_file']

    
    prompt = f"""
Your task is to design tests that ensure only correct implementations (following the specification) pass, while incorrect implementations would fail.
You are given the following information:
- Function
- Specification

Your tasks:
1. Infer the **intended behavior** from the specification.
2. Design a set of **test cases** that cover:
- Basic functionality with valid inputs and expected outputs.
- Boundary conditions and edge cases.
- Invalid inputs and error handling.
- Potential issues with dependency interactions.
3. Write executable test code using Java 21 and JUnit 4.
4. The test code should be written into {test_path}. Please make sure the imports are correct.
5. Ensure tests are designed to differentiate between correct and incorrect implementations:
- At least one test should be able to expose an incorrect implementation if the code were incorrect.
- A correct implementation should pass all tests.

## Function ({function_name}):
```java
{function_code}
```

## Specification:
{specification}

## Method Context:
- Src file: {file_path}
- Imports: {imports}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {function_info.get('is_async', False)}

<<<<<<< HEAD
Function Code:
```java
{function_code}


Requirements:
- You MUST use JUnit 4 framework for writing tests.
- Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
- The test code should be written into {test_path}. Please make sure the imports are correct.
- Do not modify any source code files in the project. 
- Do not read any existing tests files. Only create or modify the target test file.
- After writing the test file, run the tests with `mvn test -Drat.skip=true`.
- If the tests have compilation errors, analyze the errors and attempt to fix the test file. Stop after 3 repair attempts.
- Work autonomously and complete the task without asking for further input.
=======

Requirements:
Do not modify any source code files in the project. Only create or modify the target test file.
After writing the file, run the tests with mvn (e.g., mvn test).
Work autonomously and complete the task without asking for further input.
>>>>>>> refs/remotes/origin/main
"""

    
    return prompt

def run_copilot_for_entry(entry: dict, base_path: Path, timeout: int = 3600) -> dict:
    """为单个条目执行 Copilot CLI 并返回详细结果（含生成的测试代码）"""
    start_time = datetime.now()
    project_root = entry.get("project_root", ".")
    name = entry.get("name", "unknown")
    code = entry.get("code", "")
    buggy_code = entry.get("buggy_code", [""])[-1]
    src_file = entry.get("src_file", "")
    test_file = entry.get("test_file", "")
<<<<<<< HEAD
    code = entry.get("buggy_code", "")
=======

    with open(src_file, "r", encoding="utf-8") as f:
        src_code = f.read()
    src_code = src_code.replace(code, buggy_code)
    with open(src_file, "w", encoding="utf-8") as f:
        f.write(src_code)
>>>>>>> refs/remotes/origin/main
    prompt = build_prompt(entry)

    # project_dir = (base_path / project_root).resolve()
    # if not project_dir.exists():
    #     msg = f"Project directory not found: {project_dir}"
    #     logging.error(msg)
    #     return {
    #         "name": name,
    #         "project_root": project_root,
    #         "test_file": test_file,
    #         "returncode": -1,
    #         "stdout": "",
    #         "stderr": msg,
    #         "generated_test_code": "",
    #         "timestamp": datetime.now().isoformat()
    #     }
    project_dir = str(Path.cwd())
    cmd = [
        "copilot",
        "-p", prompt,  
        "--allow-all-tools",
        "--share", "/results/"  
    ]

    logging.info(f" Running Copilot for '{name}' in {project_dir}")
    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        msg = f"Timeout after {timeout}s"
        logging.error(f" {msg} for '{name}'")
        return {
            "name": name,
            "project_root": project_root,
            "src_file": src_file,
<<<<<<< HEAD
=======
            "code": code,
            "buggy_code": buggy_code,
>>>>>>> refs/remotes/origin/main
            "test_file": test_file,
            "code": code,
            "returncode": -1,
            "stdout": "",
            "stderr": msg,
            "generated_test_code": "",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        msg = f"Unexpected error: {e}"
        logging.error(f" {msg} for '{name}'")
        return {
            "name": name,
            "project_root": project_root,
            "src_file": src_file,
<<<<<<< HEAD
=======
            "code": code,
            "buggy_code": buggy_code,
>>>>>>> refs/remotes/origin/main
            "test_file": test_file,
            "code": code,
            "returncode": -1,
            "stdout": "",
            "stderr": msg,
            "generated_test_code": "",
            "timestamp": datetime.now().isoformat()
        }

    # ========== 增强部分：读取生成的测试文件内容 ==========
    generated_code = ""
    if test_file:
        # test_file_path = project_dir / test_file
        test_file_path = Path(project_dir) / test_file
        if test_file_path.exists():
            try:
                generated_code = test_file_path.read_text(encoding="utf-8")
                logging.info(f" 成功读取生成的测试文件: {test_file_path}")
            except Exception as e:
                logging.warning(f" 无法读取测试文件 {test_file_path}: {e}")
        else:
            logging.warning(f" 测试文件未找到: {test_file_path}")

    # ===================================================
    end_time = datetime.now()
    return {
        "name": name,
        "project_root": project_root,
        "src_file": src_file,
<<<<<<< HEAD
=======
        "code": code,
        "buggy_code": buggy_code,
>>>>>>> refs/remotes/origin/main
        "test_file": test_file,
        "code": code,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "generated_test_code": generated_code,
        "time": (end_time - start_time).total_seconds(), 
    }

def main():
    parser = argparse.ArgumentParser(description="使用 Copilot CLI 批量生成单元测试（保存生成代码）")
    parser.add_argument("--dataset", help="数据集 JSON 文件的路径")
    parser.add_argument("--base-path", default=".", help="项目根目录所在的基础路径（默认为当前目录）")
    parser.add_argument("--log-file", default="/results/copilot_testgen.log", help="日志文件路径")
    parser.add_argument("--timeout", type=int, default=3600, help="每个任务的超时秒数（默认600）")
    parser.add_argument("--delay", type=int, default=10, help="任务之间的延迟秒数（默认5，避免触发速率限制）")
    args = parser.parse_args()

    setup_logging(args.log_file)

    # 读取数据集
    with open(args.dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total = len(dataset)
    logging.info(f" 加载了 {total} 个待处理条目")

    results = []
    output_file = "/results/copilot_testgen_results.json"
    for i, entry in enumerate(dataset, 1):
        logging.info(f"[{i}/{total}] 正在处理: {entry.get('name', 'unknown')}")
        result = run_copilot_for_entry(entry, Path(args.base_path), timeout=args.timeout)
        results.append(result)

        rc = result["returncode"]
        if rc == 0:
            logging.info(f" 成功 (返回码=0)")
        else:
            logging.warning(f" 未完全成功 (返回码={rc})，请检查日志详情")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        if i < total:
            time.sleep(args.delay)

    # 保存详细结果（包含生成的测试代码）
    logging.info(f" 详细结果已保存至 {output_file}")

    # 汇总统计
    success_count = sum(1 for r in results if r["returncode"] == 0)
    logging.info(f" 处理完成：成功 {success_count}/{total}")

if __name__ == "__main__":
    main()
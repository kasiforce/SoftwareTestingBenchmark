import subprocess
import os
import sys
import json
import re
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from pathlib import Path


def syntax_analyse_rust(project_root, gen_tests_dir):
    """
    分析Rust测试文件的语法
    """
    test_dir = os.path.join(project_root, gen_tests_dir)

    # 查找测试目录
    test_dirs = []
    for root, dirs, files in os.walk(test_dir):
        root_path = Path(root)
        if root_path.name.lower() in ['test', 'tests', 'gen_tests']:
            test_dirs.append(root_path)

    if not test_dirs:
        print("未找到 test 或 tests 目录")
        return {"total": 0, "syntax_correct": 0, "syntax_correct_rate": 0}

    total = 0
    syntax_correct = 0

    for test_dir in test_dirs:
        for rs_file in test_dir.rglob('*.rs'):
            if 'test' in rs_file.name.lower():
                try:
                    total += 1
                    # 使用 rustc 检查语法
                    result = subprocess.run(
                        ['rustc', '--edition', '2021', '--crate-type', 'lib', '--out-dir', '/tmp', str(rs_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        syntax_correct += 1
                    else:
                        print(f"语法错误在 {rs_file}: {result.stderr[:200]}")
                        os.remove(rs_file)
                except Exception as e:
                    print(f"检查 {rs_file} 时出错: {e}")
                    try:
                        os.remove(rs_file)
                    except:
                        pass

    rate = syntax_correct / total if total > 0 else 0
    return {"total": total, "syntax_correct": syntax_correct, "syntax_correct_rate": rate}


def calculate_compile_pass_rate_rust(cargo_check_output):
    """
    从cargo check输出计算编译通过率
    """
    lines = cargo_check_output.split('\n')
    total = 0
    passed = 0

    for line in lines:
        if line.strip().endswith('.rs:'):
            total += 1
            if 'error' not in line.lower() and 'warning' not in line.lower():
                passed += 1

    return {
        "compile_pass": passed,
        "compile_total": total,
        "compile_pass_rate": passed / total if total > 0 else 0
    }


def parse_cargo_test_output(output_file):
    """
    解析cargo test的输出结果
    """
    with open(output_file, 'r') as f:
        content = f.read()

    # 提取测试结果
    test_summary = {
        "passed": 0,
        "failed": 0,
        "ignored": 0,
        "measured": 0,
        "filtered_out": 0,
        "total": 0
    }

    # 查找测试结果行
    lines = content.split('\n')
    for line in lines:
        if 'test result:' in line:
            # 解析类似: test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
            parts = line.split(':')[1].strip()
            if 'passed' in parts:
                passed_match = re.search(r'(\d+)\s+passed', parts)
                failed_match = re.search(r'(\d+)\s+failed', parts)
                ignored_match = re.search(r'(\d+)\s+ignored', parts)
                measured_match = re.search(r'(\d+)\s+measured', parts)

                if passed_match:
                    test_summary["passed"] = int(passed_match.group(1))
                if failed_match:
                    test_summary["failed"] = int(failed_match.group(1))
                if ignored_match:
                    test_summary["ignored"] = int(ignored_match.group(1))
                if measured_match:
                    test_summary["measured"] = int(measured_match.group(1))

    test_summary["total"] = (test_summary["passed"] + test_summary["failed"] +
                             test_summary["ignored"] + test_summary["measured"])

    if test_summary["total"] > 0:
        test_summary["test_pass_rate"] = test_summary["passed"] / test_summary["total"]
    else:
        test_summary["test_pass_rate"] = 0

    return test_summary


def parse_tarpaulin_coverage(coverage_file):
    """
    解析tarpaulin覆盖率报告
    """
    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)

    result = {
        "total_line_coverage": coverage_data.get("coverage_percent", 0),
        "total_branch_coverage": 0,  # tarpaulin默认不包含分支覆盖率
        "total_function_coverage": 0,
        "total_class_coverage": 0,
        "file_coverage": {},
        "summary": {
            "total_lines": 0,
            "covered_lines": 0,
            "total_branches": 0,
            "covered_branches": 0,
            "total_functions": 0,
            "covered_functions": 0,
            "total_classes": 0,
            "covered_classes": 0
        }
    }

    # 处理文件级别的覆盖率
    if "files" in coverage_data:
        for file_path, file_data in coverage_data["files"].items():
            line_coverage = file_data.get("covered_percent", 0)
            covered_lines = file_data.get("covered", 0)
            total_lines = file_data.get("coverable", 0)

            result["file_coverage"][file_path] = {
                "line_coverage": line_coverage,
                "covered_lines": covered_lines,
                "total_lines": total_lines
            }

            result["summary"]["total_lines"] += total_lines
            result["summary"]["covered_lines"] += covered_lines

    return result


def create_and_run_rust(dockerfile_path, gen_tests_dir, project_root, data_file):
    """
    创建并运行Rust项目的测试
    """
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")

    # 语法分析
    # syntax_report = syntax_analyse_rust(project_root, gen_tests_dir)

    project_dir = os.path.join(cwd, project_root)

    # 确保test_results目录存在
    test_results_dir = os.path.join(cwd, "test_results", "rust")
    repo_name = project_root
    if "/" in project_root:
        repo_name = project_root.split("/")[1]
    test_results_dir = os.path.join(test_results_dir, repo_name)
    test_results_dir = os.path.join(test_results_dir, "ground_truth")
    os.makedirs(test_results_dir, exist_ok=True)

    # 构建Docker镜像
    print("开始构建Rust测试镜像...")
    try:
        subprocess.run([
            "docker", "build",
            "-t", "rust-with-test",
            "-f", dockerfile_path,
            "."
        ], check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"镜像构建失败: {e}")
        sys.exit(1)

    print("镜像构建成功")

    # 运行测试
    print("运行Rust测试...")
    try:
        # 运行容器执行测试
        # subprocess.run([
        #     "docker", "run", "--rm",
        #     "-v", f"{test_results_dir}:/results",
        #     # "-v", f"{project_dir}:/project",
        #     "rust-with-test",
        #     "bash", "-c", f"""
        #     # cd /project

        #     # 1. 先运行cargo check检查语法
        #     echo "=== Running cargo check ==="
        #     cargo check --tests --message-format=json > /results/cargo_check.json 2>&1

        #     # 2. 复制生成的测试文件到tests目录（如果需要）
        #     # if [ -d "{gen_tests_dir}" ]; then
        #     #     echo "Copying generated tests..."
        #     #     find {gen_tests_dir} -name "*.rs" -exec cp {{}} tests/ 2>/dev/null || true
        #     # fi

        #     # 3. 运行测试并生成覆盖率
        #     echo "=== Running tests with tarpaulin ==="

        #     # 安装tarpaulin（如果镜像中没有）
        #     if ! command -v cargo-tarpaulin &> /dev/null; then
        #         echo "Installing cargo-tarpaulin..."
        #         cargo install cargo-tarpaulin --locked
        #     fi

        #     # 运行测试并生成覆盖率报告
        #     cargo tarpaulin --disable-aslr --out Json --output-dir /results --timeout 120

        #     # 4. 运行普通测试获取详细结果
        #     echo "=== Running cargo test ==="
        #     cargo test -- --test-threads=1 --nocapture 2>&1 | tee /results/cargo_test_output.txt

        #     # 5. 生成测试的JSON报告（使用cargo test --message-format=json）
        #     cargo test --message-format=json > /results/test_results.json 2>&1

        #     echo "=== Test execution completed ==="
        #     """
        # ], check=True, cwd=cwd)

        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{test_results_dir}:/results",
            # "-v", f"{project_dir}:/project",
            "-v", "./gen_test/gen_tests_files.py:/testbed/gentests_files.py",
            "-v", f"./{data_file}:/testbed/{data_file}",
            "rust-with-test",
            "bash", "-c", f"""
            # cd /project

            # 1. 基础语法检查
            echo "=== Running cargo check ==="
            # cargo check --tests --message-format=json > /results/cargo_check.json 2>&1

            if ! command -v python3 &> /dev/null; then
                apt-get update && apt-get install -y python3
            fi

            echo "生成测试文件..."
            python3 /testbed/gentests_files.py \
                --project-root /testbed \
                --data-path /testbed/{data_file}

            # 2. 确保覆盖率工具可用
            # echo "=== Ensuring coverage tools ==="
            # rustup component add llvm-tools-preview 2>/dev/null || echo "LLVM tools already installed"
            # cargo install cargo-llvm-cov --locked 2>/dev/null || echo "cargo-llvm-cov already installed"

            # # 4. 获取测试详细输出（可选，保留用于调试）
            # echo "=== Running verbose unit tests ==="
            # cargo test -- --test-threads=1 --nocapture 2>&1 | tee /results/cargo_test_output.txt

            # 5. 生成JSON测试结果
            # cargo test  --message-format=json > /results/test_results.json 2>&1

            # 3. 核心命令：仅运行单元测试，仅生成JSON格式覆盖率报告
            # echo "=== Running unit tests with JSON coverage output ==="
            # cargo llvm-cov \
            #     --json \
            #     --output-path /results/coverage.json \
            #     --ignore-filename-regex='/.cargo/registry' \
            #     --quiet
            # cargo llvm-cov --output-dir /results/coverage.json --json --ignore-filename-regex='/.cargo/registry' --quiet
            # cargo llvm-cov \
            #     # --lib \                           # 仅单元测试
            #     --output-dir /results \           # 直接输出到/results目录
            #     --json \                          # 生成JSON格式
            #     --ignore-filename-regex='/.cargo/registry' \  # 过滤依赖
            #     # --no-report \                     # 不生成汇总报告（纯JSON输出）
            #     --quiet                           # 减少终端输出

            echo "=== JSON coverage report generated ==="
            echo "Primary JSON coverage: /results/coverage.json"
            echo "Test results JSON: /results/test_results.json"
            """
        ], check=True, cwd=cwd)

        # 解析结果
        compile_report = {"compile_pass": 0, "compile_total": 0, "compile_pass_rate": 0}

        # 解析cargo check输出
        cargo_check_file = os.path.join(test_results_dir, "cargo_check.json")
        if os.path.exists(cargo_check_file):
            with open(cargo_check_file, 'r') as f:
                cargo_check_output = f.read()
                compile_report = calculate_compile_pass_rate_rust(cargo_check_output)

        # 解析测试输出
        testcase_report = parse_cargo_test_output(
            os.path.join(test_results_dir, "cargo_test_output.txt")
        )

        # 解析覆盖率
        coverage_report = {"total_line_coverage": 0}
        coverage_file = os.path.join(test_results_dir, "coverage.json")
        if os.path.exists(coverage_file):
            coverage_report = parse_tarpaulin_coverage(coverage_file)

        # 生成总报告
        summary = {
            # "syntax_analysis": syntax_report,
            "compilation": compile_report,
            "test_execution": testcase_report,
            "coverage": coverage_report
        }

        with open(os.path.join(test_results_dir, "summary.json"), 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print("\n=== 测试结果摘要 ===")
        # print(f"语法分析: {syntax_report['syntax_correct']}/{syntax_report['total']} 文件通过")
        print(f"编译通过率: {compile_report['compile_pass_rate']:.2%}")
        print(f"测试通过率: {testcase_report.get('test_pass_rate', 0):.2%}")
        print(f"行覆盖率: {coverage_report.get('total_line_coverage', 0):.2f}%")

    except subprocess.CalledProcessError as e:
        print(f"测试运行失败: {e}")
        sys.exit(1)

    print(f"\n测试完成")
    print(f"报告位置: {test_results_dir}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--dockerfile-path",
        type=str,
        help="Path to dockerfile.",
    )
    parser.add_argument(
        "--test-dir",
        type=str,
        help="Path to the generated tests.",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        help="The root dir of project.",
    )
    args = parser.parse_args()

    # 示例用法
    create_and_run_rust(
        dockerfile_path="output/vaultwarden/dockerfile",
        gen_tests_dir="",
        project_root="projects/vaultwarden",
        data_file="data_file.json"
    )
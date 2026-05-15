# import os
# import json
# import subprocess
# import sys
# import xml.etree.ElementTree as ET
# import datetime
# import glob

# def test_existing_java_project(dockerfile_path, repo_name):
#     """
#     只测试项目原有的 Java 代码，不添加额外测试
#     """
#     cwd = os.getcwd()
#     print(f"当前工作目录: {cwd}")

#     # 确保 test_results 目录
#     test_results_dir = os.path.join(cwd, "test_results")
#     test_results_dir = os.path.join(test_results_dir, repo_name)
#     os.makedirs(test_results_dir, exist_ok=True)

#     # 构建镜像
#     print("开始构建镜像...")
#     try:
#         subprocess.run([
#             "docker", "build",
#             "-t", f"{repo_name}-test",
#             "-f", dockerfile_path,
#             "."
#         ], check=True, cwd=cwd)
#     except subprocess.CalledProcessError as e:
#         print(f"镜像构建失败: {e}")
#         sys.exit(1)

#     print("镜像构建成功")

#     # 运行测试
#     print("运行项目原有测试...")
#     try:
#         test_script = """
#         set -x
#         echo "当前目录: $(pwd)"
#         echo "目录内容:"
#         ls -la

#         # 切换到项目目录
#         cd /testbed

#         # 检查项目结构
#         echo "项目结构:"
#         find . -maxdepth 2 -type f -name "pom.xml" | head -20

#         # 运行所有测试
#         echo "运行 Maven 测试..."

#         # 方法1: 直接运行所有测试
#         mvn clean test -DskipITs || echo "测试运行完成"

#         # 收集测试报告
#         echo "收集测试结果..."
#         mkdir -p /results

#         # 查找所有测试报告
#         find /testbed -name "surefire-reports" -type d 2>/dev/null | while read report_dir; do
#             module_path=$(dirname "$report_dir")
#             module_name=$(basename "$module_path")

#             if [ "$module_name" = "target" ]; then
#                 module_path=$(dirname "$module_path")
#                 module_name=$(basename "$module_path")
#             fi

#             target_dir="/results/$module_name"
#             mkdir -p "$target_dir"
#             cp -r "$report_dir" "$target_dir/" 2>/dev/null || true
#             echo "复制测试报告: $module_name"
#         done

#         # 如果找不到测试报告，尝试从 Maven 输出中提取
#         if [ ! -d "/results/surefire-reports" ] && [ $(find /results -name "*.xml" 2>/dev/null | wc -l) -eq 0 ]; then
#             echo "从 Maven 输出中提取测试结果..."

#             # 重新运行测试并捕获详细输出
#             mvn test 2>&1 | tee /results/maven_output.txt

#             # 从输出中提取测试统计
#             tests_line=$(grep "Tests run:" /results/maven_output.txt | tail -1)
#             if [ -n "$tests_line" ]; then
#                 tests_run=$(echo "$tests_line" | sed -n 's/.*Tests run: \([0-9]*\),.*/\1/p')
#                 failures=$(echo "$tests_line" | sed -n 's/.*Failures: \([0-9]*\),.*/\1/p')
#                 errors=$(echo "$tests_line" | sed -n 's/.*Errors: \([0-9]*\),.*/\1/p')
#                 skipped=$(echo "$tests_line" | sed -n 's/.*Skipped: \([0-9]*\).*/\1/p')

#                 cat > /results/test_summary.json << EOF
# {
#     "tests_run": ${tests_run:-0},
#     "failures": ${failures:-0},
#     "errors": ${errors:-0},
#     "skipped": ${skipped:-0},
#     "source": "maven_output",
#     "timestamp": "$(date -Iseconds)"
# }
# EOF
#             fi
#         fi

#         # 列出找到的测试文件
#         echo "项目中的测试文件:"
#         find /testbed -name "*Test.java" -o -name "*Tests.java" 2>/dev/null | head -20 > /results/test_files.txt

#         echo "测试完成"
#         """

#         subprocess.run([
#             "docker", "run", "--rm",
#             "-v", f"{test_results_dir}:/results",
#             f"{repo_name}-test",
#             "bash", "-c", test_script
#         ], check=False, cwd=cwd)  # 允许测试失败

#     except subprocess.CalledProcessError as e:
#         print(f"测试运行失败: {e}")

#     # 处理测试结果
#     process_test_results(test_results_dir, repo_name)

#     print(f"测试完成！报告位置: {test_results_dir}")
#     return test_results_dir


# def process_test_results(results_dir, repo_name):
#     """
#     处理测试结果目录，生成最终摘要
#     """
#     print(f"处理测试结果: {results_dir}")

#     # 首先尝试读取解析的摘要
#     parsed_summary_path = os.path.join(results_dir, "test_summary.json")
#     if os.path.exists(parsed_summary_path):
#         try:
#             with open(parsed_summary_path, 'r', encoding='utf-8') as f:
#                 parsed_data = json.load(f)

#             # 计算通过率
#             tests_run = parsed_data.get("tests_run", 0)
#             failures = parsed_data.get("failures", 0)
#             errors = parsed_data.get("errors", 0)
#             skipped = parsed_data.get("skipped", 0)

#             passed = tests_run - failures - errors - skipped
#             if tests_run > 0:
#                 pass_rate = round((passed / tests_run) * 100, 2)
#             else:
#                 pass_rate = 0.0

#             summary = {
#                 "repo": repo_name,
#                 "timestamp": datetime.datetime.now().isoformat(),
#                 "test_results": {
#                     "compile_pass_rate": pass_rate,
#                     "tests_passed": passed,
#                     "tests_total": tests_run,
#                     "tests_failed": failures + errors,
#                     "tests_skipped": skipped,
#                     "source": "existing_tests"
#                 }
#             }

#             with open(os.path.join(results_dir, "summary.json"), 'w', encoding='utf-8') as f:
#                 json.dump(summary, f, indent=2, ensure_ascii=False)

#             print(f"从现有测试中解析到结果: {tests_run} 个测试")
#             return
#         except Exception as e:
#             print(f"解析 test_summary.json 失败: {e}")

#     # 尝试解析 XML 测试报告
#     compile_result = analyze_existing_test_reports(results_dir)

#     summary = {
#         "repo": repo_name,
#         "timestamp": datetime.datetime.now().isoformat(),
#         "test_results": compile_result
#     }

#     summary_path = os.path.join(results_dir, "summary.json")
#     with open(summary_path, 'w', encoding='utf-8') as f:
#         json.dump(summary, f, indent=2, ensure_ascii=False)

#     print(f"处理完成: {compile_result.get('tests_total', 0)} 个测试")


# def analyze_existing_test_reports(results_dir):
#     """
#     分析现有测试报告
#     """
#     total_tests = 0
#     passed_tests = 0
#     failed_tests = 0
#     skipped_tests = 0
#     errors = 0

#     # 查找所有测试报告 XML 文件
#     xml_files = []

#     # 查找 surefire-reports 目录
#     for root, dirs, files in os.walk(results_dir):
#         for file in files:
#             if file.endswith(".xml") and "TEST-" in file:
#                 xml_files.append(os.path.join(root, file))

#     print(f"找到 {len(xml_files)} 个测试报告文件")

#     for xml_file in xml_files:
#         try:
#             tree = ET.parse(xml_file)
#             root = tree.getroot()

#             # 解析测试套件
#             if root.tag == "testsuite":
#                 tests = int(root.get("tests", 0))
#                 errors_count = int(root.get("errors", 0))
#                 failures = int(root.get("failures", 0))
#                 skipped = int(root.get("skipped", 0))

#                 total_tests += tests
#                 failed_tests += (errors_count + failures)
#                 skipped_tests += skipped
#                 errors += errors_count

#             # 检查是否有嵌套的 testsuite
#             for testsuite in root.findall("testsuite"):
#                 tests = int(testsuite.get("tests", 0))
#                 errors_count = int(testsuite.get("errors", 0))
#                 failures = int(testsuite.get("failures", 0))
#                 skipped = int(testsuite.get("skipped", 0))

#                 total_tests += tests
#                 failed_tests += (errors_count + failures)
#                 skipped_tests += skipped
#                 errors += errors_count

#         except Exception as e:
#             print(f"解析测试报告 {xml_file} 时出错: {e}")
#             continue

#     passed_tests = total_tests - failed_tests - skipped_tests

#     if total_tests > 0:
#         pass_rate = round((passed_tests / total_tests) * 100, 2)
#     else:
#         pass_rate = 0.0

#     result = {
#         "compile_pass_rate": pass_rate,
#         "tests_passed": passed_tests,
#         "tests_total": total_tests,
#         "tests_failed": failed_tests,
#         "tests_skipped": skipped_tests,
#         "tests_errors": errors,
#         "test_reports_found": len(xml_files)
#     }

#     return result


# # 更简单的版本，只运行测试不收集复杂结果
# def simple_java_project_test(dockerfile_path, repo_name):
#     """
#     最简单的测试函数：只构建镜像和运行测试
#     """
#     cwd = os.getcwd()
#     test_results_dir = os.path.join(cwd, "test_results", repo_name)
#     os.makedirs(test_results_dir, exist_ok=True)

#     # 构建镜像
#     print("构建 Docker 镜像...")
#     subprocess.run([
#         "docker", "build",
#         "-t", f"{repo_name}-test",
#         "-f", dockerfile_path,
#         "."
#     ], check=True, cwd=cwd)

#     # 运行测试
#     print("运行项目测试...")

#     # 简单的测试脚本
#     test_script = """
#     echo "开始测试项目..."
#     cd /testbed

#     # 运行所有测试，忽略失败
#     mvn clean test -DskipTests=false -Dmaven.test.failure.ignore=true 2>&1 | tee /results/test_output.txt

#     # 从输出中提取结果
#     LAST_LINE=$(tail -20 /results/test_output.txt | grep "Tests run:" | tail -1)

#     if [ -n "$LAST_LINE" ]; then
#         TESTS_RUN=$(echo "$LAST_LINE" | sed -n 's/.*Tests run: \([0-9]*\),.*/\1/p')
#         FAILURES=$(echo "$LAST_LINE" | sed -n 's/.*Failures: \([0-9]*\),.*/\1/p')
#         ERRORS=$(echo "$LAST_LINE" | sed -n 's/.*Errors: \([0-9]*\),.*/\1/p')
#         SKIPPED=$(echo "$LAST_LINE" | sed -n 's/.*Skipped: \([0-9]*\).*/\1/p')

#         PASSED=$((TESTS_RUN - FAILURES - ERRORS - SKIPPED))

#         echo '{
#             "tests_run": '$TESTS_RUN',
#             "passed": '$PASSED',
#             "failures": '$FAILURES',
#             "errors": '$ERRORS',
#             "skipped": '$SKIPPED',
#             "timestamp": "'$(date -Iseconds)'"
#         }' > /results/simple_summary.json
#     else
#         echo '{"status": "no_tests_found", "timestamp": "'$(date -Iseconds)'"}' > /results/simple_summary.json
#     fi

#     echo "测试完成"
#     """

#     subprocess.run([
#         "docker", "run", "--rm",
#         "-v", f"{test_results_dir}:/results",
#         f"{repo_name}-test",
#         "bash", "-c", test_script
#     ], check=False, cwd=cwd)

#     # 读取结果
#     summary_path = os.path.join(test_results_dir, "simple_summary.json")
#     if os.path.exists(summary_path):
#         try:
#             with open(summary_path, 'r', encoding='utf-8') as f:
#                 result = json.load(f)

#             # 计算通过率
#             tests_run = result.get("tests_run", 0)
#             if tests_run > 0:
#                 passed = result.get("passed", 0)
#                 pass_rate = round((passed / tests_run) * 100, 2)
#             else:
#                 pass_rate = 0.0

#             final_summary = {
#                 "repo": repo_name,
#                 # "timestamp": datetime.datetime.now().isoformat(),
#                 "test_results": {
#                     "compile_pass_rate": pass_rate,
#                     "tests_passed": result.get("passed", 0),
#                     "tests_total": tests_run,
#                     "tests_failed": result.get("failures", 0) + result.get("errors", 0),
#                     "tests_skipped": result.get("skipped", 0),
#                     "source": "simple_test"
#                 }
#             }
#         except Exception as e:
#             final_summary = {
#                 "repo": repo_name,
#                 # "timestamp": datetime.datetime.now().isoformat(),
#                 "test_results": {
#                     "compile_pass_rate": 0.0,
#                     "tests_passed": 0,
#                     "tests_total": 0,
#                     "tests_failed": 0,
#                     "tests_skipped": 0,
#                     "error": str(e)
#                 }
#             }
#     else:
#         final_summary = {
#             "repo": repo_name,
#             # "timestamp": datetime.datetime.now().isoformat(),
#             "test_results": {
#                 "compile_pass_rate": 0.0,
#                 "tests_passed": 0,
#                 "tests_total": 0,
#                 "tests_failed": 0,
#                 "tests_skipped": 0,
#                 "message": "未生成测试摘要"
#             }
#         }

#     # 保存最终结果
#     with open(os.path.join(test_results_dir, "summary.json"), 'w', encoding='utf-8') as f:
#         json.dump(final_summary, f, indent=2, ensure_ascii=False)

#     print(f"测试完成！结果保存到: {test_results_dir}/summary.json")
#     return test_results_dir


# # 主函数
# if __name__ == "__main__":
#     import argparse

#     parser = argparse.ArgumentParser(description="测试 Java 项目原有代码")
#     parser.add_argument("--dockerfile", required=True, help="Dockerfile 路径")
#     parser.add_argument("--repo", required=True, help="仓库名称")

#     args = parser.parse_args()

#     # 使用简单版本
#     test_results_dir = simple_java_project_test(args.dockerfile, args.repo)

#     # 读取并显示结果
#     summary_path = os.path.join(test_results_dir, "summary.json")
#     if os.path.exists(summary_path):
#         with open(summary_path, 'r', encoding='utf-8') as f:
#             summary = json.load(f)

#         print("\n" + "="*50)
#         print("测试结果摘要:")
#         print("="*50)
#         print(f"仓库: {summary['repo']}")
#         print(f"时间: {summary['timestamp']}")

#         test_results = summary['test_results']
#         print(f"\n测试统计:")
#         print(f"  总测试数: {test_results['tests_total']}")
#         print(f"  通过数: {test_results['tests_passed']}")
#         print(f"  失败数: {test_results['tests_failed']}")
#         print(f"  跳过数: {test_results['tests_skipped']}")
#         print(f"  通过率: {test_results['compile_pass_rate']}%")
#         print("="*50)


import subprocess
import os
import sys
import json
import time
import xml.etree.ElementTree as ET
from argparse import ArgumentParser

import csv
import xml.etree.ElementTree as ET

from pathlib import Path
import javalang
from collections import defaultdict
from jacoco_xml import parse_jacoco_xml
from filter_java_file_mut import cal_mut

# def syntax_analyse(
#         root_dir,
#         pattern="*.java",
#         dry_run=False,
# ):
#     test_dirs = []
#     for root, dirs, files in os.walk(root_dir):
#         root_path = Path(root)
#         # 如果是 test 或 tests 目录
#         if root_path.name.lower() in ['test', 'tests']:
#             test_dirs.append(root_path)

#     if not test_dirs:
#         print("未找到 test 或 tests 目录")
#         return

#     total = 0
#     syntax_correct = 0

#     # 查找并删除有语法错误的测试文件
#     for test_dir in test_dirs:
#         # print(test_dir)
#         for file in test_dir.rglob('*.java'):
#             # print(file)
#             if 'Test' in file.name:
#                 try:
#                     total += 1
#                     with open(file, 'r', encoding='utf-8') as f:
#                         content = f.read()
#                     javalang.parse.parse(content)
#                     syntax_correct += 1

#                 except Exception as e:
#                     os.remove(file)
#                     print(f"{file}语法错误：{e}")
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
                javalang.parse.parse(test)
                syntax_correct += 1
            except Exception as e:
                pass

    return {"total": total, "syntax_correct": syntax_correct, "syntax_correct_rate": syntax_correct / total}


def calculate_test_pass_rate(report_dir):
    """解析 /results/reports 下所有的 JUnit XML"""
    total = 0
    passed = 0
    failures = 0
    errors = 0

    if not os.path.exists(report_dir):
        return {"total": 0, "passed": 0, "failures": 0, "errors": 0, "pass_rate": 0}

    for filename in os.listdir(report_dir):
        if filename.endswith(".xml"):
            try:
                tree = ET.parse(os.path.join(report_dir, filename))
                root = tree.getroot()
                # 有些报告 root 是 testsuite，有些是 testsuites
                suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
                for suite in suites:
                    total += int(suite.attrib.get('tests', 0))
                    failures += int(suite.attrib.get('failures', 0))
                    errors += int(suite.attrib.get('errors', 0))
            except Exception as e:
                print(f"解析 {filename} 失败: {e}")

    passed = total - failures - errors
    pass_rate = (passed / total) if total > 0 else 0
    return {
        "total": total,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "pass_rate": pass_rate
    }


# def get_coverage_rates(results_dir):
#     """
#     累加所有子模块的 JaCoCo CSV 覆盖率报告。
#     基于表头提取：指令、分支、行、复杂度、方法的覆盖率和未覆盖率。
#     返回一个包含所有覆盖率类型百分比的字典。
#     """
#     # 初始化所有指标的累加器
#     coverage_totals = {
#         'instruction': {'missed': 0, 'covered': 0},
#         'branch': {'missed': 0, 'covered': 0},
#         'line': {'missed': 0, 'covered': 0},
#         'complexity': {'missed': 0, 'covered': 0},
#         'method': {'missed': 0, 'covered': 0}
#     }

#     found_any = False

#     # 遍历目录，查找所有覆盖率CSV文件
#     for filename in os.listdir(results_dir):
#         if not filename.endswith("_coverage.csv"):
#             continue

#         filepath = os.path.join(results_dir, filename)
#         found_any = True

#         try:
#             with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
#                 reader = csv.DictReader(csvfile)

#                 for row in reader:
#                     # 可选：通常我们只累加类（CLASS）级别的明细，忽略分组和包级别的汇总行
#                     # 如果希望包含所有级别，可以移除这个判断
#                     if row['CLASS'] == '':
#                         continue

#                     # 累加各项指标
#                     coverage_totals['instruction']['missed'] += int(row['INSTRUCTION_MISSED'])
#                     coverage_totals['instruction']['covered'] += int(row['INSTRUCTION_COVERED'])

#                     coverage_totals['branch']['missed'] += int(row['BRANCH_MISSED'])
#                     coverage_totals['branch']['covered'] += int(row['BRANCH_COVERED'])

#                     coverage_totals['line']['missed'] += int(row['LINE_MISSED'])
#                     coverage_totals['line']['covered'] += int(row['LINE_COVERED'])

#                     coverage_totals['complexity']['missed'] += int(row['COMPLEXITY_MISSED'])
#                     coverage_totals['complexity']['covered'] += int(row['COMPLEXITY_COVERED'])

#                     coverage_totals['method']['missed'] += int(row['METHOD_MISSED'])
#                     coverage_totals['method']['covered'] += int(row['METHOD_COVERED'])

#         except (KeyError, ValueError, FileNotFoundError) as e:
#             print(f"警告：处理文件 {filename} 时出错: {e}")
#             continue

#     if not found_any:
#         # 没有找到任何覆盖率文件，返回0值
#         return {f"{cov_type}_coverage": 0.0 for cov_type in coverage_totals.keys()}

#     # 计算每种覆盖率的百分比
#     coverage_rates = {}
#     for cov_type, totals in coverage_totals.items():
#         total = totals['covered'] + totals['missed']
#         if total > 0:
#             rate = (totals['covered'] / total) * 100
#             coverage_rates[f'{cov_type}_coverage'] = round(rate, 2)
#         else:
#             coverage_rates[f'{cov_type}_coverage'] = 0.0

#     return coverage_rates

def get_coverage_rates(xml_path, output_methods='function_coverage.csv', output_files='file_coverage.csv'):
    """
    解析JaCoCo XML报告，提取方法级和文件级行/分支覆盖率。
    
    Args:
        xml_path (str): jacoco.xml文件路径
        output_methods (str): 输出的方法级CSV文件名
        output_files (str): 输出的文件级CSV文件名
    """
    if not os.path.exists(xml_path):
        return 

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 存储方法级数据
    methods_data = []
    # 存储文件级行覆盖率（从<sourcefile>解析）
    file_line_coverage = {}
    # 存储文件级分支覆盖率（从<class>累加）
    file_branch_coverage = defaultdict(lambda: {'missed': 0, 'covered': 0})

    # 遍历所有package
    for package in root.findall('package'):
        package_name = package.get('name')  # 如 "org/apache/commons/cli/help"

        # --- 处理每个<class>，提取方法级数据，并累加分⽀到文件级 ---
        for cls in package.findall('class'):
            source_file = cls.get('sourcefilename')
            if source_file:
                file_key = f"{package_name}/{source_file}"  # 用包路径+文件名作为唯一键

                # 累加该类的分支覆盖率（用于文件级）
                branch_counter = cls.find("./counter[@type='BRANCH']")
                if branch_counter is not None:
                    file_branch_coverage[file_key]['missed'] += int(branch_counter.get('missed'))
                    file_branch_coverage[file_key]['covered'] += int(branch_counter.get('covered'))

                # 处理该类下的每个方法
                for method in cls.findall('method'):
                    method_name = method.get('name')
                    method_desc = method.get('desc')  # 方法描述，用于区分重载

                    # 方法行覆盖率
                    line_counter = method.find("./counter[@type='LINE']")
                    if line_counter is not None:
                        line_missed = int(line_counter.get('missed'))
                        line_covered = int(line_counter.get('covered'))
                    else:
                        line_missed = line_covered = 0

                    # 方法分支覆盖率
                    branch_counter_m = method.find("./counter[@type='BRANCH']")
                    if branch_counter_m is not None:
                        branch_missed = int(branch_counter_m.get('missed'))
                        branch_covered = int(branch_counter_m.get('covered'))
                    else:
                        branch_missed = branch_covered = 0

                    methods_data.append({
                        'package': package_name.replace('/', '.'),
                        'class': cls.get('name').replace('/', '.'),
                        'method': method_name,
                        'desc': method_desc,
                        'line_missed': line_missed,
                        'line_covered': line_covered,
                        'branch_missed': branch_missed,
                        'branch_covered': branch_covered
                    })

        # --- 处理<sourcefile>，获取文件级行覆盖率 ---
        for sourcefile in package.findall('sourcefile'):
            sourcefile_name = sourcefile.get('name')
            file_key = f"{package_name}/{sourcefile_name}"

            # 统计该文件中的行覆盖
            total_lines = 0
            covered_lines = 0
            for line in sourcefile.findall('line'):
                total_lines += 1
                ci = int(line.get('ci', 0))
                if ci > 0:  # 只要该行有指令被覆盖，即视为已覆盖
                    covered_lines += 1

            file_line_coverage[file_key] = {
                'total_lines': total_lines,
                'covered_lines': covered_lines,
                'missed_lines': total_lines - covered_lines
            }

    # --- 合并文件级数据（行覆盖 + 分支覆盖） ---
    # 最终文件级列表
    file_data = []
    # 所有出现在<sourcefile>中的文件（可能会有部分文件没有分支，但需要输出）
    all_file_keys = set(file_line_coverage.keys()) | set(file_branch_coverage.keys())
    for file_key in sorted(all_file_keys):
        # 行覆盖
        line_info = file_line_coverage.get(file_key, {'total_lines': 0, 'covered_lines': 0, 'missed_lines': 0})
        total_lines = line_info['total_lines']
        covered_lines = line_info['covered_lines']
        missed_lines = line_info['missed_lines']

        # 分支覆盖
        branch_info = file_branch_coverage.get(file_key, {'missed': 0, 'covered': 0})
        branch_missed = branch_info['missed']
        branch_covered = branch_info['covered']
        total_branches = branch_missed + branch_covered

        # 计算百分比
        line_coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        branch_coverage_percent = (branch_covered / total_branches * 100) if total_branches > 0 else 0

        file_data.append({
            'file': file_key,
            'line_missed': missed_lines,
            'line_covered': covered_lines,
            'total_lines': total_lines,
            'line_coverage': f"{line_coverage_percent:.2f}",
            'branch_missed': branch_missed,
            'branch_covered': branch_covered,
            'total_branches': total_branches,
            'branch_coverage': f"{branch_coverage_percent:.2f}"
        })

    method_line_total = sum(m['line_missed'] + m['line_covered'] for m in methods_data)
    method_line_covered = sum(m['line_covered'] for m in methods_data)
    overall_line_coverage = (method_line_covered / method_line_total * 100) if method_line_total > 0 else 0
    method_branch_total = sum(m['branch_missed'] + m['branch_covered'] for m in methods_data)
    method_branch_covered = sum(m['branch_covered'] for m in methods_data)
    overall_branch_coverage = (method_branch_covered / method_branch_total * 100) if method_branch_total > 0 else 0
    file_line_total = sum(f['total_lines'] for f in file_data)
    file_line_covered = sum(f['line_covered'] for f in file_data)
    overall_file_line_coverage = (file_line_covered / file_line_total * 100) if file_line_total > 0 else 0
    file_branch_total = sum(f['total_branches'] for f in file_data)
    file_branch_covered = sum(f['branch_covered'] for f in file_data)
    overall_file_branch_coverage = (file_branch_covered / file_branch_total * 100) if file_branch_total > 0 else 0
    # --- 写入方法级CSV ---
    with open(output_methods, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Package', 'Class', 'Method', 'Desc', 
                         'Line_Missed', 'Line_Covered', 'Branch_Missed', 'Branch_Covered'])
        for m in methods_data:
            writer.writerow([
                m['package'], m['class'], m['method'], m['desc'],
                m['line_missed'], m['line_covered'],
                m['branch_missed'], m['branch_covered']
            ])
        writer.writerow([method_line_total, method_line_covered, overall_line_coverage, method_branch_total, method_branch_covered, overall_branch_coverage])

    # --- 写入文件级CSV ---
    with open(output_files, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Line_Missed', 'Line_Covered', 'Total_Lines', 'Line_Coverage%',
                         'Branch_Missed', 'Branch_Covered', 'Total_Branches', 'Branch_Coverage%'])
        for file in file_data:
            writer.writerow([
                file['file'],
                file['line_missed'], file['line_covered'], file['total_lines'], file['line_coverage'],
                file['branch_missed'], file['branch_covered'], file['total_branches'], file['branch_coverage']
            ])
        writer.writerow(['Total', '', file_line_covered, file_line_total, overall_file_line_coverage, '', file_branch_covered, file_branch_total, overall_file_branch_coverage])

    print(f"完成！已生成 {output_methods} 和 {output_files}")

def parse_junit_xml(report_dir):
    """解析 JUnit XML 报告以获取编译/通过率"""
    total_tests = 0
    failures = 0
    errors = 0

    # 遍历目录下所有的 XML 测试报告
    if not os.path.exists(report_dir):
        return {"compile_status": "failed", "pass_rate": 0}

    for filename in os.listdir(report_dir):
        if filename.endswith(".xml") and filename.startswith("TEST-"):
            tree = ET.parse(os.path.join(report_dir, filename))
            root = tree.getroot()
            total_tests += int(root.attrib.get('tests', 0))
            failures += int(root.attrib.get('failures', 0))
            errors += int(root.attrib.get('errors', 0))

    passed = total_tests - failures - errors
    pass_rate = (passed / total_tests) if total_tests > 0 else 0
    return {
        "total": total_tests,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "pass_rate": pass_rate
    }


def parse_jacoco_csv(csv_path):
    """解析 JaCoCo CSV 报告获取覆盖率"""
    if not os.path.exists(csv_path):
        return {"line_coverage": 0, "branch_coverage": 0}

    # JaCoCo CSV 结构: [0]GROUP, [1]PACKAGE, [2]CLASS, [3]INSTRUCTION_MISSED, [4]INSTRUCTION_COVERED...
    # [5]BRANCH_MISSED, [6]BRANCH_COVERED, [7]LINE_MISSED, [8]LINE_COVERED...
    try:
        missed_lines = 0
        covered_lines = 0
        missed_branches = 0
        covered_branches = 0

        with open(csv_path, 'r') as f:
            lines = f.readlines()[1:]  # 跳过表头
            for line in lines:
                parts = line.split(',')
                missed_branches += int(parts[5])
                covered_branches += int(parts[6])
                missed_lines += int(parts[7])
                covered_lines += int(parts[8])

        line_cov = covered_lines / (covered_lines + missed_lines) if (covered_lines + missed_lines) > 0 else 0
        branch_cov = covered_branches / (covered_branches + missed_branches) if (
                                                                                            covered_branches + missed_branches) > 0 else 0

        return {
            "line_coverage": line_cov,
            "branch_coverage": branch_cov
        }
    except Exception as e:
        print(f"解析覆盖率失败: {e}")
        return {"line_coverage": 0, "branch_coverage": 0}


def get_compiled_tests_count(test_results_dir):
    """读取成功编译的测试文件数量"""
    count_file = os.path.join(test_results_dir, "compiled_tests_count.txt")

    if os.path.exists(count_file):
        try:
            with open(count_file, 'r') as f:
                count = int(f.read().strip())
            return count
        except (ValueError, IOError) as e:
            print(f"读取编译测试计数失败: {e}")
            return 0
    else:
        print("未找到编译测试计数文件")
        return 0

def parse_pitest_reports(results_dir):
    """解析收集到 /results 的 PIT 变异测试 XML 报告。"""
    mutation_xml_files = []
    for filename in os.listdir(results_dir):
        if filename.endswith("_pitest_mutations.xml"):
            mutation_xml_files.append(os.path.join(results_dir, filename))

    if not mutation_xml_files:
        return {
            "total_mutations": 0,
            "killed_mutations": 0,
            "survived_mutations": 0,
            "no_coverage_mutations": 0,
            "run_error_mutations": 0,
            "mutation_score": 0,
            "reports_found": 0
        }

    total_mutations = 0
    killed_mutations = 0
    survived_mutations = 0
    no_coverage_mutations = 0
    run_error_mutations = 0

    for xml_file in mutation_xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for mutation in root.findall("mutation"):
                total_mutations += 1
                status = mutation.get("status", "")
                detected = mutation.get("detected", "false").lower() == "true"

                if detected:
                    killed_mutations += 1
                elif status == "NO_COVERAGE":
                    no_coverage_mutations += 1
                elif status in {"RUN_ERROR", "TIMED_OUT", "MEMORY_ERROR", "NON_VIABLE"}:
                    run_error_mutations += 1
                else:
                    survived_mutations += 1
        except Exception as e:
            print(f"解析 PIT 报告失败 {xml_file}: {e}")

    mutation_score = (killed_mutations / total_mutations) if total_mutations > 0 else 0
    return {
        "total_mutations": total_mutations,
        "killed_mutations": killed_mutations,
        "survived_mutations": survived_mutations,
        "no_coverage_mutations": no_coverage_mutations,
        "run_error_mutations": run_error_mutations,
        "mutation_score": mutation_score,
        "reports_found": len(mutation_xml_files)
    }


def create_and_run_java(dockerfile_path, repo_dir, data_file):
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")

    # 1. 准备目录
    repo_name = repo_dir
    if "/" in repo_dir:
        repo_name = repo_dir.split("/")[1]

    spec = "specification" if "specification" in data_file else ""
    model = data_file.replace(".json","").split('_')[-1]
    framework = data_file.replace(".json","").split('_')[-2]
    mut_dir = framework + '_' + model + "_mut_fix"
    if spec:
        mut_dir = spec + '_' + mut_dir

    test_results_dir = os.path.join(cwd, "test_results", "java", repo_name, mut_dir)

    os.makedirs(test_results_dir, exist_ok=True)

    # syntax_report = syntax_analyse(data_file)

    project_dir = os.path.join(cwd, repo_dir)
    # with open(dockerfile_path, "r") as f:
    #     content = f.read()

    # dockerfile_test_path = os.path.join(test_results_dir, "Dockerfile.test")
    # with open(dockerfile_test_path, "w") as f:
    #     f.write(content)

    # 2. 构建镜像
    print("开始构建 Java 项目镜像...")
    try:
        subprocess.run([
            "docker", "build",
            "-t", f"java-repo-{repo_name}",
            "-f", dockerfile_path,
            "."
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"镜像构建失败: {e}")
        sys.exit(1)

    # 3. 运行测试
    # 注意：这里假设项目使用 Maven。如果是 Gradle，请将 mvn 命令改为 ./gradlew
    print("运行 Java 测试 (Maven + JaCoCo)...")
    try:
        # 运行测试的动态命令
        # 使用全限定名调用 jacoco 插件：org.jacoco:jacoco-maven-plugin:0.8.11 (建议指定版本)

        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{test_results_dir}:/results",
            "-v", "./gen_test/gen_tests_files.py:/testbed/gentests_files.py",
            "-v", "./delete_files.py:/testbed/delete_files.py",
            "-v", "./gen_test/delete_java_fail.py:/testbed/delete_fail.py",
            "-v", f"./{data_file}:/testbed/{data_file}",
            # "-v", f"{os.path.expanduser('~/.m2')}:/root/.m2",
            f"java-repo-{repo_name}",
            "bash", "-c", f"""
                # set -e
                cd /testbed
                ROOT_DIR="$(pwd)"
                # 安装 Python3
                if ! command -v python3 &> /dev/null; then
                    apt-get update && apt-get install -y python3
                fi

                echo "生成测试文件..."
                python3 /testbed/gentests_files.py \
                    --project-root /testbed \
                    --data-path /testbed/{data_file}

                
                
                if ! grep -q "<artifactId>junit</artifactId>" pom.xml; then
                    sed -i '/<\/dependencies>/i \
            <dependency>\
                <groupId>junit</groupId>\
                <artifactId>junit</artifactId>\
                <version>4.13.2</version>\
                <scope>test</scope>\
            </dependency>' pom.xml
                fi

                if ! grep -q "<artifactId>junit-vintage-engine</artifactId>" pom.xml; then
                    sed -i '/<\/dependencies>/i \
                    <dependency>\
                        <groupId>org.junit.vintage</groupId>\
                        <artifactId>junit-vintage-engine</artifactId>\
                        <version>5.13.3</version>\
                        <scope>test</scope>\
                    </dependency>' pom.xml
                fi
           
                if ! grep -q "<artifactId>mockito-core</artifactId>" pom.xml; then
                    sed -i '/<\/dependencies>/i \
                    <dependency>\
                        <groupId>org.mockito</groupId>\
                        <artifactId>mockito-core</artifactId>\
                        <version>4.11.0</version>\
                        <scope>test</scope>\
                    </dependency>' pom.xml
                fi

                sed -i 's|<argLine>-javaagent:src/test/resources/agent.jar</argLine>|<argLine>@{{argLine}} -javaagent:src/test/resources/agent.jar</argLine>|' pom.xml

                if ! grep -q "<artifactId>jakarta.xml.bind-api</artifactId>" pom.xml; then
                    sed -i '/<\/dependencies>/i \
                    <dependency>\
                        <groupId>jakarta.xml.bind</groupId>\
                        <artifactId>jakarta.xml.bind-api</artifactId>\
                        <version>4.0.0</version>\
                    </dependency>' pom.xml
                fi

                if ! grep -q "<artifactId>jaxb-runtime</artifactId>" pom.xml; then
                    sed -i '/<\/dependencies>/i \
                    <dependency>\
                        <groupId>org.glassfish.jaxb</groupId>\
                        <artifactId>jaxb-runtime</artifactId>\
                        <version>4.0.3</version>\
                        <scope>runtime</scope>\
                    </dependency>' pom.xml
                fi


                

                MAX_RETRIES=10
                RETRY_COUNT=0
                LOG_FILE="/tmp/compile.log"
                CLEAN_LOG="/tmp/compile.clean.log"

                while true; do
                    echo "===== 编译尝试 $((RETRY_COUNT+1)) ====="
                    # 运行编译，输出到日志文件，并保存退出码
                    mvn test-compile -Drat.skip=true > "$LOG_FILE" 2>&1
                    MVN_EXIT_CODE=$?
                    # 去除 ANSI 颜色码，生成干净日志（不影响后续判断）
                    sed -e 's/\x1b\[[0-9;]*m//g' "$LOG_FILE" > "$CLEAN_LOG"

                    if [ $MVN_EXIT_CODE -eq 0 ]; then
                        echo "✅ 编译成功！"
                        break
                    else
                        echo "❌ 编译失败，正在删除错误文件..."
                        python3 /testbed/delete_files.py "$CLEAN_LOG"

                        RETRY_COUNT=$((RETRY_COUNT+1))
                        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
                            echo "已达到最大重试次数 ($MAX_RETRIES)，退出。"
                            exit 1
                        fi
                        sleep 2
                    fi
                done

                mvn -fae clean org.jacoco:jacoco-maven-plugin:0.8.14:prepare-agent test org.jacoco:jacoco-maven-plugin:0.8.14:report \
                    -DskipTests=false -Dmaven.test.skip=false -DfailIfNoTests=false \
                    -Dmaven.test.failure.ignore=true -Drat.skip=true -B

                mkdir -p /results/reports

                # 5. 收集 JUnit XML 报告（所有子模块的 surefire 报告）
                echo "开始搜集 JUnit XML 报告..."
                find . -name "TEST-*.xml" -path "*/target/surefire-reports/*" -exec cp {{}} /results/reports/ \;

                python3 /testbed/delete_fail.py --reports /results/reports --src src/test/java
               
                mvn test-compile -Drat.skip=true

                echo "执行 PIT 变异测试..."
                # 不按“测试类”过滤，避免一个类中“有通过用例也有失败用例”时整类被排除
                # 只依赖 PIT 的 skipFailingTests，让失败测试不阻断变异分析
                PITEST_BASE_OPTS="-DwithHistory=false -DoutputFormats=XML -DtimestampedReports=true -DfailWhenNoMutations=false -DmutationThreshold=0 -DcoverageThreshold=0 -DskipTests=false -Dmaven.test.failure.ignore=true -DskipFailingTests=true -Drat.skip=true"

                if mvn -fae org.pitest:pitest-maven:1.5.2:mutationCoverage $PITEST_BASE_OPTS -B; then
                    echo "PIT 变异测试执行完成"
                else
                    echo "PIT 变异测试执行失败，继续后续流程" | tee /results/pitest_run.log
                fi


            #     mvn test-compile org.pitest:pitest-maven:1.5.2:mutationCoverage \
            #         -DskipTests=false \
            #         -Dmaven.test.failure.ignore=true \
		    # -DskipFailingTests=true \
            #         -Drat.skip=true -B
                
                find . -name "mutations.xml" -path "*/target/pit-reports/*/*" | while read -r pit_file; do
                    rel_path=$(realpath --relative-to="$ROOT_DIR" "$(dirname "$pit_file")/.." | tr '/' '_')
                    if [ -z "$rel_path" ] || [ "$rel_path" = "." ]; then
                        prefix="root"
                    else
                        prefix="$rel_path"
                    fi
                    cp "$pit_file" "/results/${{prefix}}_pitest_mutations.xml"
                    echo "已拷贝 PIT XML: ${{prefix}}_pitest_mutations.xml"
                done

                
       
            """
        ], check=False, capture_output=True, text=True)
        # 打印输出
        print("=== STDOUT ===")
        print(result.stdout)
        # print("=== STDERR ===")
        # print(result.stderr)
        # print("=== RETURN CODE ===")
        # print(result.returncode)
        
        # 4. 解析结果
        # compiled_count = get_compiled_tests_count(test_results_dir)
        # junit_results = calculate_test_pass_rate(os.path.join(test_results_dir, "reports"))
        # coverage_results = parse_jacoco_xml(os.path.join(test_results_dir, "target_jacoco.xml"), data_file)
        pitest_results = cal_mut(data_file, test_results_dir)

        

        with open(os.path.join(test_results_dir, "mut.json"), 'w', encoding='utf-8') as f:
            json.dump(pitest_results, f, indent=2, ensure_ascii=False)

        print(f"测试完成，报告已生成: {test_results_dir}/mut.json")

    except subprocess.CalledProcessError as e:
        print(f"测试运行失败!")
        print(f"错误标准输出 (stdout): \n{e.stdout}")
        print(f"错误标准错误 (stderr): \n{e.stderr}")
        # 即使失败也尝试生成部分报告
        sys.exit(1)


if __name__ == "__main__":
    # 示例调用
    # for root, dirs, files in os.walk("tests/test_gen/java/fix_jcasbin"):
    #     for file in files:
    #         if "junit5" in file :
    #             continue
    #         full_path = os.path.join(root, file)
    #         print(full_path)
    #         create_and_run_java("output/jcasbin/dockerfile", "projects/jcasbin", full_path)
    #         time.sleep(10)  # 每次测试间隔10秒，避免过快连续运行
    # pass
    create_and_run_java("output/nfe/dockerfile", "projects/nfe", "tests/test_gen/java/fix_nfe/repaired_nfe_lite_junit4_gpt5nano.json")

import subprocess
import os
import sys
import json
import xml.etree.ElementTree as ET
from argparse import ArgumentParser

import csv
import xml.etree.ElementTree as ET

from pathlib import Path
import javalang
from collections import defaultdict
from jacoco_xml import parse_jacoco_xml


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


def create_and_run_java(dockerfile_path, repo_dir, data_file):
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")

    # 1. 准备目录
    repo_name = repo_dir
    if "/" in repo_dir:
        repo_name = repo_dir.split("/")[1]
    test_results_dir = os.path.join(cwd, "test_results", "java", repo_name, "adver_100")

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
        

        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{test_results_dir}:/results",
            # "-v", "./gen_test/gen_tests_files.py:/testbed/gentests_files.py",
            # "-v", "./delete_files.py:/testbed/delete_files.py",
            "-v", f"./AdverBug/adver.py:/testbed/adver.py",
            "-v", f"./AdverBug/test_generation_agent.py:/testbed/test_generation_agent.py",
            "-v", f"./AdverBug/bug_generation_agent.py:/testbed/bug_generation_agent.py",
            "-v", f"./AdverBug/llm_config.py:/testbed/llm_config.py",
            "-v", f"./AdverBug/valid_agent.py:/testbed/valid_agent.py",
            "-v", f"./{data_file}:/testbed/{data_file}",
            f"java-repo-{repo_name}",
            "bash", "-c", f"""
                # set -e
                cd /testbed
                ROOT_DIR="$(pwd)"
                # 安装 Python3
                
               
                
                python3 /testbed/adver.py \
                    --data-path /testbed/{data_file}

                cp /testbed/final_results.json /testbed/results/
                
                
       
            """
        ], check=False, capture_output=True, text=True)
        # 打印输出
        print("=== STDOUT ===")
        print(result.stdout)
        

    

    except subprocess.CalledProcessError as e:
        print(f"测试运行失败!")
        print(f"错误标准输出 (stdout): \n{e.stdout}")
        print(f"错误标准错误 (stderr): \n{e.stderr}")
        # 即使失败也尝试生成部分报告
        sys.exit(1)


if __name__ == "__main__":
    # 示例调用
    create_and_run_java("output/hutool/dockerfile", "projects/hutool", "hutool_100_specification.json")
    # pass
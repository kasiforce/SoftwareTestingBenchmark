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

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fix_data = []
    data1 = data['items']
    for func in data1:
        func1 = func['repair_history']
        raw_code = ""
        if len(func1) > 1: 
            raw_code = func1[1]["test_code"]
        else:
            raw_code = func1[0]["test_code"]
       
        if not raw_code.strip():
            continue

        item = {
            "project_root": func.get("project_root", ""),
            "src_file": func.get("src_file", ""),
            "name": func.get("name", ""),
            "class_name": func.get("class_name", ""),
            "test_file": func.get("test_file", ""),
            "generated_tests": [raw_code]
        }
        fix_data.append(item)
    
    fix_data_path = "fix_data.json"
    with open(fix_data_path, 'w', encoding='utf-8') as f:
        json.dump(fix_data, f, indent=2, ensure_ascii=False)

    syntax_report = syntax_analyse(fix_data_path)

    project_dir = os.path.join(cwd, project_root)

    # 确保 test_results 目录
    test_results_dir = os.path.join(cwd, "test_results", "python")
    repo_name = project_root
    if "/" in project_root:
        repo_name = project_root.split("/")[1]
    test_results_dir = os.path.join(test_results_dir, "fix_"+repo_name)

    data_file1 = data_file.split(".json")[0]
    model_name = data_file1.split("_")[-1]
    framework = data_file1.split("_")[-2]
    json_dir = f"{framework}_{model_name}"
    if "specification" in data_file:
        json_dir = f"specification_{framework}_{model_name}"
    
    test_results_dir = os.path.join(test_results_dir, json_dir)
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
            "-v", "./gen_test/gen_tests_files.py:/testbed/genfixtests_files.py",
            "-v", f"./{fix_data_path}:/testbed/{fix_data_path}",
            "repo-with-test",
            "bash", "-c", f"""
            cd /testbed

            pip install pytest pytest-json-report pytest-timeout coverage pytest-asyncio pytest-mock pycares

            python /testbed/genfixtests_files.py \
                --project-root /testbed \
                --data-path /testbed/{fix_data_path}
            # find {gen_tests_dir} -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true
            # find {gen_tests_dir} -name "*.pyc" -delete 2>/dev/null || true

            # ======================
            # 1. coverage + pytest
            #  --source=markitdown_sample_plugin\
            # ======================
            coverage run --branch \
                --omit="test_*.py,*_test.py,*/tests/*,*/test/*,*/gen_tests/*" \
                -m pytest \
                --import-mode=importlib \
                --continue-on-collection-errors \
                --timeout=2 \
                -q --disable-warnings --tb=no \
                --json-report \
                --json-report-file=/results/report.json

            coverage json -o /results/coverage.json

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


        compile, testcase = calculate_compile_pass_rate(test_results_dir + "/report.json")
        compile["compile_pass_rate"] = compile["compile_pass"] / syntax_report["total"]
        coverage = get_coverage_rate(test_results_dir + "/coverage.json", fix_data_path, project_root)
        summary = syntax_report | compile | testcase | coverage
        # summary = compile | coverage
        with open(test_results_dir + "/summary_filtered.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    except subprocess.CalledProcessError as e:
        print(f"测试运行失败: {e}")
        sys.exit(1)

    print("测试完成")
    print(f"报告位置: {test_results_dir}")

def load_data_file(data_path, project_root):
    """加载 data_file.json，返回文件路径集合和函数标识集合"""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    file_paths = set()
    func_keys = set()
    print(project_root)
    # data1 = data['items']
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
    # root = "tests/test_gen/python/fix_pylint"
    # for root, dirs, files in os.walk(root):
    #     for file in files:
    #         print(file)
    #         file_path = os.path.join(root, file)
    #         create_and_run_py("output/pylint/dockerfile", gen_tests_dir="",
    #                   cover_source="", project_root="projects/pylint", 
    #                   data_file=file_path)


    create_and_run_py("output/pylint/dockerfile", gen_tests_dir="",
                      cover_source="", project_root="projects/pylint", 
                      data_file="tests/test_gen/python/fix_pylint/repaired_pylint_lite_specification_unittest_DSv3.2.json")
    



import re
import os
from pathlib import Path
import json
import subprocess
import sys
# import argparse
from argparse import ArgumentParser
from typing import List, Dict, Tuple

# def delete_test_files_in_test_dirs(project_root):
#     """
#     遍历 JS 项目，只删除 test/tests 目录下的测试文件：
#     - test_*.js
#     - *_test.js
#     - *.test.js
#     - *.tests.js
#     - _spec.js / .spec.js
#     """
#     project_root = Path(project_root)

#     # 忽略目录（仍然保留 node_modules、dist、build 等不进入）
#     skip_dirs = {'.git', 'node_modules', 'dist', 'build', '__tests__'}

#     deleted_files = []

#     for root, dirs, files in os.walk(project_root):
#         root_path = Path(root)

#         # 原地修改 dirs，阻止 os.walk 进入忽略目录
#         dirs[:] = [d for d in dirs if d not in skip_dirs]

#         # 只处理 test 或 tests 目录下的文件
#         # Path.parts 会把路径拆成 ('project', 'test', 'something')
#         if not any(part.lower() in {'test', 'tests'} for part in root_path.parts):
#             continue

#         for file in files:
#             file_path = root_path / file
#             try:
#                 file_path.unlink()
#                 deleted_files.append(file_path)
#             except Exception as e:
#                 print(f"删除失败 {file_path}: {e}")
#             # if not file.endswith('.js'):
#             #     continue

#             # filename = file.lower()

#             # # 匹配 JS 测试文件常见命名规则
#             # if (filename.startswith('test_') or 
#             #     filename.endswith('_test.js') or
#             #     filename.endswith('.test.js') or
#             #     filename.endswith('.tests.js') or
#             #     filename.endswith('_spec.js') or
#             #     filename.endswith('.spec.js')):
                
#             #     file_path = root_path / file
#             #     try:
#             #         file_path.unlink()
#             #         deleted_files.append(file_path)
#             #     except Exception as e:
#             #         print(f"删除失败 {file_path}: {e}")

#     # 输出结果
#     print(f"共删除 {len(deleted_files)} 个测试文件")
#     for f in deleted_files[:10]:
#         print(f"  {f}")

#     if len(deleted_files) > 10:
#         print(f"  ... 还有 {len(deleted_files) - 10} 个文件")

def delete_test_files_in_test_dirs(project_root):
    """
    遍历 JS 项目，删除所有测试文件（无论是否在 test/tests 目录下）：
    - test_*.js
    - *_test.js
    - *.test.js
    - *.tests.js
    - _spec.js / .spec.js
    """
    project_root = Path(project_root)

    # 忽略目录（这些目录通常不包含项目自身的测试文件）
    skip_dirs = {'.git', 'node_modules', 'dist', 'build'}  # 移除了 '__tests__'，因为它是常见的测试目录

    deleted_files = []

    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)

        # 原地修改 dirs，阻止 os.walk 进入忽略目录
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            # 只处理 JavaScript 文件
            if not file.endswith('.js') and not file.endswith('.ts'):
                continue

            file_path = root_path / file
            filename_lower = file.lower()

            # 匹配 JS 测试文件常见命名规则
            # if (filename_lower.startswith('test_') or 
            #     filename_lower.endswith('_test.js') or
            #     filename_lower.endswith('.test.js') or
            #     filename_lower.endswith('.tests.js') or
            #     filename_lower.endswith('_spec.js') or
            #     filename_lower.endswith('.spec.js')):
            if (filename_lower.startswith('test-') or
                filename_lower.startswith('test_') or
                "_test." in filename_lower or 
                ".test." in filename_lower or
                ".test-d." in filename_lower or
                ".tests." in filename_lower or
                "_spec." in filename_lower or
                ".spec." in filename_lower):

                try:
                    file_path.unlink()
                    deleted_files.append(file_path)
                except Exception as e:
                    print(f"删除失败 {file_path}: {e}")

    # 输出结果
    print(f"共删除 {len(deleted_files)} 个测试文件")
    for f in deleted_files[:10]:
        print(f"  {f}")

    if len(deleted_files) > 10:
        print(f"  ... 还有 {len(deleted_files) - 10} 个文件")


# def write_generated_tests(project_root, test_json_path):
#     """生成测试文件（指定 utf-8 编码）"""
#     try:
#         with open(test_json_path, 'r', encoding='utf-8') as f:
#             functions = json.load(f)
#             print(len(functions))

#         total = 0
#         syntax_pass = 0
#         compile_pass = 0

#         for func in functions:
#             # print(func)
#             project = func.get("project_root").split('projects/Proton')[1]
#             test_file = "/testbed"+project + "/" + func.get("test_file")

#             dir_path = os.path.dirname(test_file)
#             if not os.path.exists(dir_path):
#                 os.makedirs(dir_path, exist_ok=True)

#             raw_code = "\n\n".join(func["generated_tests"])
            
#             # 语法检查
#              # 写入文件（UTF-8）
#             with open(test_file, 'w', encoding='utf-8') as f:
#                 f.write("\n\n" + raw_code)
#             print(f"写入 {test_file}")
            
#             total += 1

#             syntax_result = subprocess.run(
#                 ["node", "--check", str(test_file)],
#                 capture_output=True,
#                 text=True
#             )
#             syntax_ok = False
#             if syntax_result.returncode == 0:
#                 syntax_ok = True
#                 syntax_pass += 1
#             else:
#                 os.remove(test_file)
#                 # print(f"[Syntax Error] Test {i}:\n{syntax_result.stderr.strip()}\n")
            
#             if syntax_ok:
#                 result = subprocess.run(
#                     [
#                         "npx", "rollup",
#                         "-c", "rollup.temp.config.mjs",
#                         "--input", str(test_file),
#                     ],
#                     capture_output=True,
#                     text=True
#                 )
#                 success = result.returncode == 0
#                 if success:
#                     compile_pass += 1
#                 else:
#                     os.remove(test_file)
#                     # print(f"[Compile Error] Test :\n{result.stderr.strip()}\n")

#                 # exec_result = subprocess.run(
#                 #     ["node", str(test_file)],
#                 #     capture_output=True,
#                 #     text=True
#                 # )
#                 # if exec_result.returncode == 0:
#                 #     # compile_ok = True
#                 #     compile_pass += 1
#                 # else:
#                 #     os.remove(test_file)
#                 #     print(f"[Compile/Runtime Error] Test :\n{exec_result.stderr.strip()}\n")
        
#         with open("/results/test_results_summary.txt", 'w', encoding='utf-8') as summary_file:
#             summary_file.write(f"Total tests generated: {total}\n")
#             summary_file.write(f"Syntax check passed: {syntax_pass} ({syntax_pass/total*100:.2f}%)\n")
#             summary_file.write(f"Compile/runtime check passed: {compile_pass} ({compile_pass/total*100:.2f}%)\n")

#     except Exception as e:
#         print(f"写入文件失败: {e}")

def write_generated_tests(project_root, test_json_path):
    """生成测试文件（指定 utf-8 编码）"""
    try:
        with open(test_json_path, 'r', encoding='utf-8') as f:
            functions = json.load(f)
            print(len(functions))


        for func in functions:
            # print(func)
            project = func.get("project_root").split('projects/pdf.js')[1]
            test_file = "/testbed"+project + "/" + func.get("test_file")

            dir_path = os.path.dirname(test_file)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            raw_code = "\n\n".join(func["generated_tests"])
            
            # 语法检查
             # 写入文件（UTF-8）
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("\n\n" + raw_code)
            print(f"写入 {test_file}")
            
         

    except Exception as e:
        print(f"写入文件失败: {e}")



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=str,
        help="The root dir of project.",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to data.",
    )
    args = parser.parse_args()

    delete_test_files_in_test_dirs(args.project_root)
    write_generated_tests(args.project_root, args.data_path)

    # delete_test_files_in_test_dirs("projects/markitdown")
    # write_generated_tests("projects/markitdown", "markitdown_lite_specification_unittest_gpt4o.json")
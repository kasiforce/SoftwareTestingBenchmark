import re
import os
from pathlib import Path
import json
import subprocess
import sys
# import argparse
from argparse import ArgumentParser
from typing import List, Dict, Tuple


def delete_test_files_in_test_dirs(project_root):
    """在 test/tests 目录中删除 *test*.py 文件"""
    # 查找 test/tests 目录
    test_dirs = []
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)

        # 跳过某些目录
        skip_dirs = ['.git', 'venv', '.venv', '__pycache__']
        if any(skip in root_path.parts for skip in skip_dirs):
            continue

        # 如果是 test 或 tests 目录
        if root_path.name.lower() in ['test', 'tests', 'gen_tests']:
            test_dirs.append(root_path)

    if not test_dirs:
        print("未找到 test 或 tests 目录")
        return

    # 查找并删除测试文件
    deleted_files = []
    for test_dir in test_dirs:
        for py_file in test_dir.rglob('*.py'):
            if 'test_' in py_file.name.lower() or '_test' in py_file.name.lower():
                try:
                    os.remove(py_file)
                    deleted_files.append(py_file)
                except Exception as e:
                    print(f"删除失败 {py_file}: {e}")

    # 显示结果
    print(f"在 {len(test_dirs)} 个测试目录中删除了 {len(deleted_files)} 个测试文件:")
    for file in deleted_files[:10]:
        print(f"  {file}")

    if len(deleted_files) > 10:
        print(f"  ... 还有 {len(deleted_files) - 10} 个文件")




# def delete_test_files_in_test_dirs(project_root):
#     """在 test/tests 目录中删除 *test*.java 文件"""
#     # 查找 test/tests 目录
#     test_dirs = []
#     for root, dirs, files in os.walk(project_root):
#         root_path = Path(root)

#         # 跳过某些目录
#         skip_dirs = ['.git', 'venv', '.venv', '__pycache__']
#         if any(skip in root_path.parts for skip in skip_dirs):
#             continue

#         # 如果是 test 或 tests 目录
#         if root_path.name.lower() in ['test', 'tests']:
#             test_dirs.append(root_path)

#     if not test_dirs:
#         print("未找到 test 或 tests 目录")
#         return

#     # 查找并删除测试文件
#     deleted_files = []
#     for test_dir in test_dirs:
#         for file in test_dir.rglob('*.java'):
#             if 'Test' in file.name:
#                 try:
#                     os.remove(file)
#                     deleted_files.append(file)
#                 except Exception as e:
#                     print(f"删除失败 {file}: {e}")

#     # 显示结果
#     print(f"在 {len(test_dirs)} 个测试目录中删除了 {len(deleted_files)} 个测试文件:")
#     for file in deleted_files[:10]:
#         print(f"  {file}")

#     if len(deleted_files) > 10:
#         print(f"  ... 还有 {len(deleted_files)-10} 个文件")



# def delete_test_files_in_test_dirs(project_root):
#     """
#     遍历整个项目目录，删除所有匹配：
#     - test_*.py
#     - *_test.py
#     的 Python 文件
#     """
#     project_root = Path(project_root)

#     skip_dirs = {'.git', 'venv', '.venv', '__pycache__'}

#     deleted_files = []

#     for root, dirs, files in os.walk(project_root):
#         root_path = Path(root)

#         # 原地修改 dirs，阻止 os.walk 继续深入这些目录
#         dirs[:] = [d for d in dirs if d not in skip_dirs]

#         for file in files:
#             if not file.endswith('.py'):
#                 continue

#             filename = file.lower()

#             if filename.startswith('test_') or filename.endswith('_test.py'):
#                 file_path = root_path / file
#                 try:
#                     file_path.unlink()
#                     deleted_files.append(file_path)
#                 except Exception as e:
#                     print(f"删除失败 {file_path}: {e}")

#     # 输出结果
#     print(f"共删除 {len(deleted_files)} 个测试文件")
#     for f in deleted_files[:10]:
#         print(f"  {f}")

#     if len(deleted_files) > 10:
#         print(f"  ... 还有 {len(deleted_files) - 10} 个文件")


def write_generated_tests(project_root, test_json_path):
    """生成测试文件（指定 utf-8 编码）"""
    try:
        with open(test_json_path, 'r', encoding='utf-8') as f:
            functions = json.load(f)
            print(len(functions))

        for func in functions:
            # print(func)
            test_file = func.get("test_file", "")
            root = func.get("project_root", "").split('/')
            # print(root)
            if len(root) > 2 and root[-1] != 'src':
                test_file = os.path.join(root[-1], test_file)
            test_file1 = project_root + "/" + test_file
           
            dir_path = os.path.dirname(test_file1)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            raw_code = "\n\n".join(func["generated_tests"])

            # 写入文件（UTF-8）
            with open(test_file1, 'w', encoding='utf-8') as f:
                f.write("\n\n" + raw_code)
            print(f"写入 {test_file1}")

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
    # write_generated_tests("projects/flask", "fix_data.json")


# import json
# import subprocess
# import shutil
# from pathlib import Path
# from argparse import ArgumentParser


# def run_cmd(cmd, cwd):

#     r = subprocess.run(
#         cmd,
#         cwd=cwd,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE
#     )

#     return r.returncode == 0


# def cargo_check(project):

#     return run_cmd(
#         ["cargo", "check", "--quiet"],
#         project
#     )


# def cargo_build(project):

#     return run_cmd(
#         ["cargo", "build", "--quiet"],
#         project
#     )


# def cargo_test(project):

#     return run_cmd(
#         ["cargo", "test", "--quiet"],
#         project
#     )


# def write_test(test_file, code):

#     with open(test_file, "a", encoding="utf8") as f:
#         f.write("\n\n")
#         f.write(code)
#         f.write("\n")


# def remove_test(test_file, code):

#     text = Path(test_file).read_text()

#     text = text.replace(code, "")

#     Path(test_file).write_text(text)


# def rename_test_module(code, name):

#     return code.replace(
#         "mod tests",
#         f"mod tests_{name}"
#     )


# def evaluate(json_file, project_root):

#     data = json.load(open(json_file))

#     project_root = Path(project_root)

#     syntax_pass = 0
#     compile_pass = 0
#     test_pass = 0
#     total = 0

#     results = []

#     print("Pre-build project (compile dependencies)...")

#     cargo_build(project_root)

#     for item in data:

#         if item["test_generation_status"] != "success":
#             continue

#         total += 1

#         name = item["name"]

#         test_file = project_root / item["test_file"]

#         test_codes = item["generated_tests"]

#         if not test_codes:
#             continue

#         code = test_codes[0]

#         code = rename_test_module(code, name)

#         write_test(test_file, code)

#         syntax_ok = cargo_check(project_root)

#         compile_ok = False
#         test_ok = False

#         if syntax_ok:

#             syntax_pass += 1

#             compile_ok = cargo_build(project_root)

#             if compile_ok:

#                 compile_pass += 1

#                 # test_ok = cargo_test(project_root)

#                 # if test_ok:
#                 #     test_pass += 1

#         results.append({
#             "name": name,
#             "syntax_pass": syntax_ok,
#             "compile_pass": compile_ok,
#             # "test_pass": test_ok
#         })

#         remove_test(test_file, code)

#         print(name, syntax_ok, compile_ok)

#     summary = {
#         "total": total,
#         "syntax_pass": syntax_pass,
#         "compile_pass": compile_pass,
#         # "test_pass": test_pass,
#         "syntax_pass_rate": syntax_pass / total if total else 0,
#         "compile_pass_rate": compile_pass / total if total else 0,
#         # "test_pass_rate": test_pass / total if total else 0,
#         "details": results
#     }

#     return summary


# if __name__ == "__main__":
#     parser = ArgumentParser()
#     parser.add_argument(
#         "--project-root",
#         type=str,
#         help="The root dir of project.",
#     )
#     parser.add_argument(
#         "--data-path",
#         type=str,
#         help="Path to data.",
#     )
#     args = parser.parse_args()

#     summary = evaluate(args.data_path, args.project_root)
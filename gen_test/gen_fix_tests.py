



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



def write_generated_tests(project_root, test_json_path):
    """生成测试文件（指定 utf-8 编码）"""
    try:
        with open(test_json_path, 'r', encoding='utf-8') as f:
            functions = json.load(f)
            print(len(functions))
        functions1 = functions['items']
        for func in functions1:
            # print(func)
            func1 = func['repair_history']
            raw_code = ""
            if len(func1) > 1: 
                raw_code = "\n\n".join(func1[1]["test_code"])
            else:
                raw_code = "\n\n".join(func1[0]["test_code"])
            test_file = func.get("test_file", "")
            root = func.get("project_root", "").split('/')
            if len(root) > 2 and root[-1] != 'src':
                test_file = os.path.join(root[-1], test_file)
            test_file1 = project_root + "/" + test_file

            dir_path = os.path.dirname(test_file1)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            
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
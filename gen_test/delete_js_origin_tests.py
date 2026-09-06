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




if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=str,
        help="The root dir of project.",
    )

    args = parser.parse_args()

    delete_test_files_in_test_dirs(args.project_root)
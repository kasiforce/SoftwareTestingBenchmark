# #!/usr/bin/env python3
# """
# 遍历目录下的 test_results_summary.txt 文件，按不同维度聚合测试结果，输出 JSON。
# """

# import os
# import sys
# import re
# import json
# from collections import defaultdict

# def parse_summary_file(filepath):
#     """
#     解析 test_results_summary.txt 文件，返回三个数值的字典。
#     如果解析失败，返回 None。
#     """
#     data = {}
#     try:
#         with open(filepath, 'r', encoding='utf-8') as f:
#             content = f.read()
#     except Exception as e:
#         print(f"警告: 无法读取文件 {filepath}: {e}", file=sys.stderr)
#         return None

#     # 正则提取数字
#     patterns = {
#         'total_tests_generated': r'Total tests generated:\s*(\d+)',
#         'syntax_check_passed': r'Syntax check passed:\s*(\d+)',
#         'compile_runtime_check_passed': r'Compile/runtime check passed:\s*(\d+)',
#     }

#     for key, pattern in patterns.items():
#         match = re.search(pattern, content)
#         if match:
#             data[key] = int(match.group(1))
#         else:
#             # 如果缺少字段，记录警告并跳过该文件
#             print(f"警告: 在 {filepath} 中未找到 {key} 字段", file=sys.stderr)
#             return None
#     return data

# def extract_attributes(dirname):
#     """
#     从目录名中提取模型名、框架名、是否有 specification。
#     目录名格式例如: jest_CodeLlama, specification_jest_gpt4o
#     返回 (model, framework, spec)
#     """
#     parts = dirname.split('_')
#     # 模型名取最后一部分
#     model = parts[-1]
#     # 框架名：如果包含 'jest' 则为 'jest'
#     framework = None
#     if 'jest' in dirname:
#         framework = 'jest'
#     else:
#         # 默认框架名，可根据实际情况调整
#         framework = 'unknown'
#     # 是否有 specification
#     spec = 'with_specification' if 'specification' in dirname else 'without_specification'
#     return model, framework, spec

# def aggregate_data(root_dir):
#     """
#     遍历 root_dir 下的所有 test_results_summary.txt 文件，
#     聚合统计数据并返回三个分组的结果。
#     """
#     # 初始化聚合容器
#     by_model = defaultdict(lambda: defaultdict(int))
#     by_model_framework = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
#     by_model_spec = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

#     # 遍历目录树
#     for dirpath, dirnames, filenames in os.walk(root_dir):
#         if 'test_results_summary.txt' in filenames:
#             filepath = os.path.join(dirpath, 'test_results_summary.txt')
#             parent_dir = os.path.basename(dirpath)  # 子子目录名
#             data = parse_summary_file(filepath)
#             if data is None:
#                 continue

#             model, framework, spec = extract_attributes(parent_dir)

#             # 1. 按模型分组
#             for key, value in data.items():
#                 by_model[model][key] += value

#             # 2. 按模型+框架分组
#             for key, value in data.items():
#                 by_model_framework[model][framework][key] += value

#             # 3. 按模型+specification分组
#             for key, value in data.items():
#                 by_model_spec[model][spec][key] += value

#     return by_model, by_model_framework, by_model_spec

# def convert_to_serializable(obj):
#     """将 defaultdict 转换为普通字典以便 JSON 序列化"""
#     if isinstance(obj, defaultdict):
#         return {k: convert_to_serializable(v) for k, v in obj.items()}
#     elif isinstance(obj, dict):
#         return {k: convert_to_serializable(v) for k, v in obj.items()}
#     else:
#         return obj

# def main():
#     # 获取根目录，默认为当前目录
#     root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
#     if not os.path.isdir(root_dir):
#         print(f"错误: '{root_dir}' 不是一个有效的目录", file=sys.stderr)
#         sys.exit(1)

#     by_model, by_model_framework, by_model_spec = aggregate_data(root_dir)

#     # 转换为普通字典以便 JSON 序列化
#     result = {
#         'by_model': convert_to_serializable(by_model),
#         'by_model_and_framework': convert_to_serializable(by_model_framework),
#         'by_model_and_specification': convert_to_serializable(by_model_spec),
#     }

#     # 输出 JSON
#     print(json.dumps(result, indent=2, ensure_ascii=False))

#     with open(root_dir + '/test_results.json', 'w', encoding='utf-8') as f:
#         json.dump(result, f, indent=2, ensure_ascii=False)

# if __name__ == '__main__':
#     main()



#!/usr/bin/env python3
"""
遍历目录下的 test_results_summary.txt 文件，按不同维度聚合测试结果，输出 JSON。
"""

import os
import sys
import re
import json
from collections import defaultdict

def parse_summary_file(filepath):
    """
    解析 test_results_summary.txt 文件，返回三个数值的字典。
    如果解析失败，返回 None。
    """
    data = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"警告: 无法读取文件 {filepath}: {e}", file=sys.stderr)
        return None

    # 正则提取数字
    patterns = {
        'total_tests_generated': r'Total tests generated:\s*(\d+)',
        'syntax_check_passed': r'Syntax check passed:\s*(\d+)',
        'compile_runtime_check_passed': r'Compile/runtime check passed:\s*(\d+)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            data[key] = int(match.group(1))
        else:
            # 如果缺少字段，记录警告并跳过该文件
            print(f"警告: 在 {filepath} 中未找到 {key} 字段", file=sys.stderr)
            return None
    return data

def extract_attributes(dirname):
    """
    从目录名中提取模型名、框架名、是否有 specification。
    目录名格式例如: jest_CodeLlama, specification_jest_gpt4o
    返回 (model, framework, spec)
    """
    parts = dirname.split('_')
    # 模型名取最后一部分
    model = parts[-1]
    # 框架名：如果包含 'jest' 则为 'jest'
    framework = None
    if 'jest' in dirname:
        framework = 'jest'
    else:
        # 默认框架名，可根据实际情况调整
        framework = 'unknown'
    # 是否有 specification
    spec = 'with_spec' if 'specification' in dirname else 'without_spec'
    return model, framework, spec

def aggregate_data(root_dir):
    """
    遍历 root_dir 下的所有 test_results_summary.txt 文件，
    聚合统计数据并返回三个独立分组的结果。
    """
    # 初始化聚合容器
    by_model = defaultdict(lambda: defaultdict(int))
    by_framework = defaultdict(lambda: defaultdict(int))   # 按框架（不区分模型）
    by_spec = defaultdict(lambda: defaultdict(int))        # 按是否包含 specification（不区分模型）

    # 遍历目录树
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'test_results_summary.txt' in filenames:
            filepath = os.path.join(dirpath, 'test_results_summary.txt')
            parent_dir = os.path.basename(dirpath)  # 子子目录名
            data = parse_summary_file(filepath)
            if data is None:
                continue

            model, framework, spec = extract_attributes(parent_dir)

            # 1. 按模型分组
            for key, value in data.items():
                by_model[model][key] += value

            # 2. 按框架分组（忽略模型）
            for key, value in data.items():
                by_framework[framework][key] += value

            # 3. 按 specification 分组（忽略模型）
            for key, value in data.items():
                by_spec[spec][key] += value

    return by_model, by_framework, by_spec

def convert_to_serializable(obj):
    """将 defaultdict 转换为普通字典以便 JSON 序列化"""
    if isinstance(obj, defaultdict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    else:
        return obj

def main():
    # 获取根目录，默认为当前目录
    # root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    root_dir = 'test_results/javascript'
    if not os.path.isdir(root_dir):
        print(f"错误: '{root_dir}' 不是一个有效的目录", file=sys.stderr)
        sys.exit(1)

    by_model, by_framework, by_spec = aggregate_data(root_dir)

    # 转换为普通字典以便 JSON 序列化
    result = {
        'by_model': convert_to_serializable(by_model),
        'by_framework': convert_to_serializable(by_framework),
        'by_spec': convert_to_serializable(by_spec),
    }

    # 输出 JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))

    with open(root_dir + '/test_results.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
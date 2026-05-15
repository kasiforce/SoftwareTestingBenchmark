# import json
# from pathlib import Path
# from collections import defaultdict

# def parse_dirname(dirname):
#     """
#     从目录名解析出模型、测试框架和是否有 specification 标识。
#     格式: [specification_]框架_模型
#     例如:
#         pytest_CodeLlama      -> model='CodeLlama', framework='pytest', spec=False
#         specification_unittest_gpt4o -> model='gpt4o', framework='unittest', spec=True
#     """
#     parts = dirname.split('_')
#     if parts[0] == 'specification':
#         spec = True
#         framework = parts[1]
#         model = '_'.join(parts[2:])
#     else:
#         spec = False
#         framework = parts[0]
#         model = '_'.join(parts[1:])
#     return model, framework, spec

# def aggregate_json(data, agg):
#     """将单个 JSON 中的数值字段累加到聚合字典中"""
#     # 顶层字段
#     agg['total'] += data.get('total', 0)
#     agg['syntax_correct'] += data.get('syntax_correct', 0)
#     agg['compile_pass'] += data.get('compile_pass', 0)

#     # testcase 子对象
#     tc = data.get('testcase', {})
#     agg['testcase_passed'] += tc.get('passed', 0)
#     agg['testcase_error'] += tc.get('error', 0)
#     agg['testcase_failed'] += tc.get('failed', 0)
#     agg['testcase_total'] += tc.get('total', 0)
#     agg['testcase_collected'] += tc.get('collected', 0)

#     # filtered_stats 子对象
#     fs = data.get('filtered_stats', {})
#     file_stats = fs.get('file', {})
#     agg['filtered_stats_file_total_lines'] += file_stats.get('total_lines', 0)
#     agg['filtered_stats_file_covered_lines'] += file_stats.get('covered_lines', 0)
#     agg['filtered_stats_file_total_branches'] += file_stats.get('total_branches', 0)
#     agg['filtered_stats_file_covered_branches'] += file_stats.get('covered_branches', 0)

#     func_stats = fs.get('function', {})
#     agg['filtered_stats_function_total_lines'] += func_stats.get('total_lines', 0)
#     agg['filtered_stats_function_covered_lines'] += func_stats.get('covered_lines', 0)
#     agg['filtered_stats_function_total_branches'] += func_stats.get('total_branches', 0)
#     agg['filtered_stats_function_covered_branches'] += func_stats.get('covered_branches', 0)

# def compute_ratios(agg):
#     """根据累加的数值重新计算比率字段"""
#     result = agg.copy()

#     # 顶层比率
#     if result['total'] > 0:
#         result['syntax_correct_rate'] = result['syntax_correct'] / result['total']
#         result['compile_pass_rate'] = result['compile_pass'] / result['total']
#     else:
#         result['syntax_correct_rate'] = None
#         result['compile_pass_rate'] = None

#     # testcase 比率
#     if result['testcase_total'] > 0:
#         result['test_pass_rate'] = result['testcase_passed'] / result['testcase_total']
#     else:
#         result['test_pass_rate'] = None

#     if result['testcase_collected'] > 0:
#         # run_pass_rate = (passed + failed) / collected
#         result['run_pass_rate'] = (result['testcase_passed'] + result['testcase_failed']) / result['testcase_collected']
#     else:
#         result['run_pass_rate'] = None

#     # 可选：计算 filtered_stats 中的覆盖率（可自行添加）
#     # result['file_line_coverage'] = result['filtered_stats_file_covered_lines'] / result['filtered_stats_file_total_lines'] if result['filtered_stats_file_total_lines'] else None
#     # ...

#     return result

# def main(root_dir):
#     root = Path(root_dir)

#     # 三个维度的聚合字典，使用 defaultdict 自动初始化数值为 0
#     by_model = defaultdict(lambda: defaultdict(int))
#     by_model_framework = defaultdict(lambda: defaultdict(int))
#     by_model_spec = defaultdict(lambda: defaultdict(int))

#     # 遍历所有 summary_filtered.json 文件
#     for json_file in root.glob('**/summary_filtered.json'):
#         # 从父目录名解析元信息
#         dirname = json_file.parent.name
#         model, framework, spec = parse_dirname(dirname)

#         with open(json_file, 'r', encoding='utf-8') as f:
#             data = json.load(f)

#         # 按模型聚合
#         aggregate_json(data, by_model[model])
#         # 按模型+框架聚合
#         key_mf = f"{model}_{framework}"
#         aggregate_json(data, by_model_framework[key_mf])
#         # 按模型+specification聚合
#         key_ms = f"{model}_{spec}"
#         aggregate_json(data, by_model_spec[key_ms])

#     # 重新计算所有比率
#     by_model_final = {k: compute_ratios(v) for k, v in by_model.items()}
#     by_model_framework_final = {k: compute_ratios(v) for k, v in by_model_framework.items()}
#     by_model_spec_final = {k: compute_ratios(v) for k, v in by_model_spec.items()}

#     # 输出结果
#     print("=== 按模型分组 ===")
#     print(json.dumps(by_model_final, indent=2, ensure_ascii=False))
#     print("\n=== 按模型 + 测试框架分组 ===")
#     print(json.dumps(by_model_framework_final, indent=2, ensure_ascii=False))
#     print("\n=== 按模型 + 是否包含 specification 分组 ===")
#     print(json.dumps(by_model_spec_final, indent=2, ensure_ascii=False))

#     # 可选择性保存到文件
#     with open(root_dir + '/aggregated_results.json', 'w', encoding='utf-8') as f:
#         json.dump({
#             'by_model': by_model_final,
#             'by_model_framework': by_model_framework_final,
#             'by_model_spec': by_model_spec_final
#         }, f, indent=2, ensure_ascii=False)

# if __name__ == '__main__':
#     import sys
#     root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
#     main(root_dir)



import json
from pathlib import Path
from collections import defaultdict

def parse_dirname(dirname):
    """
    从目录名解析出模型、测试框架和是否有 specification 标识。
    格式: [specification_]框架_模型
    例如:
        pytest_CodeLlama      -> model='CodeLlama', framework='pytest', spec=False
        specification_unittest_gpt4o -> model='gpt4o', framework='unittest', spec=True
    """
    parts = dirname.split('_')
    if parts[0] == 'specification':
        spec = True
        framework = parts[1]
        model = '_'.join(parts[2:])
    else:
        spec = False
        framework = parts[0]
        model = '_'.join(parts[1:])
    return model, framework, spec

def aggregate_json(data, agg):
    """将单个 JSON 中的数值字段累加到聚合字典中"""
    # 顶层字段
    agg['total'] += data.get('total', 0)
    agg['syntax_correct'] += data.get('syntax_correct', 0)
    agg['compile_pass'] += data.get('compile_pass', 0)
    agg['excute_pass'] += data.get('excute_pass', 0)
    agg['test_pass'] += data.get('test_pass', 0)
    agg['testcase_passed'] += data.get('testcase_pass_rate', 0)

    # testcase 子对象
    # tc = data.get('testcase', {})
    # agg['testcase_passed'] += tc.get('passed', 0)
    # agg['testcase_error'] += tc.get('error', 0)
    # agg['testcase_failed'] += tc.get('failed', 0)
    # agg['testcase_total'] += tc.get('total', 0)
    # agg['testcase_collected'] += tc.get('collected', 0)

    # filtered_stats 子对象
    fs = data.get('filtered_stats', {})
    file_stats = fs.get('file', {})
    agg['filtered_stats_file_total_lines'] += file_stats.get('total_lines', 0)
    agg['filtered_stats_file_covered_lines'] += file_stats.get('covered_lines', 0)
    agg['filtered_stats_file_total_branches'] += file_stats.get('total_branches', 0)
    agg['filtered_stats_file_covered_branches'] += file_stats.get('covered_branches', 0)

    func_stats = fs.get('function', {})
    agg['filtered_stats_function_total_lines'] += func_stats.get('total_lines', 0)
    agg['filtered_stats_function_covered_lines'] += func_stats.get('covered_lines', 0)
    agg['filtered_stats_function_total_branches'] += func_stats.get('total_branches', 0)
    agg['filtered_stats_function_covered_branches'] += func_stats.get('covered_branches', 0)

def compute_ratios(agg):
    """根据累加的数值重新计算比率字段"""
    result = agg.copy()

    # 顶层比率
    if result['total'] > 0:
        result['syntax_correct_rate'] = result['syntax_correct'] / result['total']
        result['compile_pass_rate'] = result['compile_pass'] / result['total']
        result['excute_pass_rate'] = result['excute_pass'] / result['total']
        result['test_pass_rate'] = result['test_pass'] / result['total']
        result['testcase_passed_rate'] = result['testcase_passed'] / result['total']
    else:
        result['syntax_correct_rate'] = None
        result['compile_pass_rate'] = None
        result['excute_pass_rate'] = None
        result['test_pass_rate'] = None
        result['testcase_passed_rate'] = None

    # testcase 比率
    # if result['testcase_total'] > 0:
    #     result['test_pass_rate'] = result['testcase_passed'] / result['testcase_total']
    # else:
    #     result['test_pass_rate'] = None

    # if result['testcase_collected'] > 0:
    #     # run_pass_rate = (passed + failed) / collected
    #     result['run_pass_rate'] = (result['testcase_passed'] + result['testcase_failed']) / result['testcase_collected']
    # else:
    #     result['run_pass_rate'] = None

    # 可选：计算 filtered_stats 中的覆盖率（可自行添加）
    # result['file_line_coverage'] = result['filtered_stats_file_covered_lines'] / result['filtered_stats_file_total_lines'] if result['filtered_stats_file_total_lines'] else None
    # ...

    return result

def main(root_dir):
    root = Path(root_dir)

    # 三个独立维度的聚合字典
    by_model = defaultdict(lambda: defaultdict(int))      # 按模型
    by_framework = defaultdict(lambda: defaultdict(int))  # 按测试框架（不区分模型）
    by_spec = defaultdict(lambda: defaultdict(int))       # 按是否包含 specification（不区分模型）

    # 遍历所有 summary_filtered.json 文件
    for json_file in root.glob('**/summary_filtered.json'):
        dirname = json_file.parent.name
        model, framework, spec = parse_dirname(dirname)

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 按模型聚合
        aggregate_json(data, by_model[model])
        # 按框架聚合（忽略模型）
        aggregate_json(data, by_framework[framework])
        # 按 specification 聚合（将布尔值转为字符串键，便于阅读）
        spec_key = "with_spec" if spec else "without_spec"
        aggregate_json(data, by_spec[spec_key])

    # 重新计算所有比率
    by_model_final = {k: compute_ratios(v) for k, v in by_model.items()}
    by_framework_final = {k: compute_ratios(v) for k, v in by_framework.items()}
    by_spec_final = {k: compute_ratios(v) for k, v in by_spec.items()}

    # 输出结果
    print("=== 按模型分组 ===")
    print(json.dumps(by_model_final, indent=2, ensure_ascii=False))
    print("\n=== 按测试框架分组 ===")
    print(json.dumps(by_framework_final, indent=2, ensure_ascii=False))
    print("\n=== 按是否包含 specification 分组 ===")
    print(json.dumps(by_spec_final, indent=2, ensure_ascii=False))

    # 保存到文件
    output_path = Path(root_dir) / 'aggregated_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'by_model': by_model_final,
            'by_framework': by_framework_final,
            'by_spec': by_spec_final
        }, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    import sys
    # root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    root_dir = 'test_results/python/fix3' 
    main(root_dir)
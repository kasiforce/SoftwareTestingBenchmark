# import json
# import os
# from typing import Any, Dict

# def is_numeric(value: Any) -> bool:
#     """判断是否为数值类型（int/float），不包括 bool 和 None"""
#     return isinstance(value, (int, float)) and not isinstance(value, bool) and value is not None

# def deep_accumulate(accumulator: Dict, new_data: Dict) -> None:
#     """
#     递归地将 new_data 中的数值累加到 accumulator 中。
#     对于非数值字段，若 accumulator 中不存在则复制，存在则保留 accumulator 的原值（不覆盖）。
#     遇到 None 值时，视为 0 进行累加（如果累加器中有数值）。
#     """
#     for key, value in new_data.items():
#         if isinstance(value, dict):
#             if key not in accumulator:
#                 accumulator[key] = {}
#             deep_accumulate(accumulator[key], value)
#         elif is_numeric(value):
#             old_val = accumulator.get(key)
#             if old_val is None:
#                 old_val = 0
#             accumulator[key] = old_val + value
#         else:
#             # 非数值非字典：如字符串、None等，只在 accumulator 中没有该键时才复制
#             if key not in accumulator:
#                 accumulator[key] = value

# def recalc_pass_rate(stats: Dict) -> None:
#     """重新计算 test_pass_rate"""
#     passed = stats.get("testcase_passed", 0)
#     total = stats.get("testcase_total", 0)
#     stats["test_pass_rate"] = passed / total if total > 0 else None

#     syn = stats.get("syntax_correct", 0)
#     total1 = stats.get("total", 0)
#     stats["syntax_correct_rate"] = syn / total1 if total1 > 0 else None

#     comp = stats.get("compile_pass", 0)
#     stats["compile_pass_rate"] = comp / total1 if total1 > 0 else None

# def add_coverage_metrics(stats: Dict) -> None:
#     """基于累加后的统计字段计算覆盖率并添加到 stats 中"""
#     # 文件级行覆盖率
#     file_total_lines = stats.get("filtered_stats_file_total_lines", 0)
#     file_covered_lines = stats.get("filtered_stats_file_covered_lines", 0)
#     stats["file_line_coverage"] = file_covered_lines / file_total_lines if file_total_lines > 0 else None

#     # 文件级分支覆盖率
#     file_total_branches = stats.get("filtered_stats_file_total_branches", 0)
#     file_covered_branches = stats.get("filtered_stats_file_covered_branches", 0)
#     stats["file_branch_coverage"] = file_covered_branches / file_total_branches if file_total_branches > 0 else None

#     # 函数级行覆盖率
#     func_total_lines = stats.get("filtered_stats_function_total_lines", 0)
#     func_covered_lines = stats.get("filtered_stats_function_covered_lines", 0)
#     stats["function_line_coverage"] = func_covered_lines / func_total_lines if func_total_lines > 0 else None

#     # 函数级分支覆盖率
#     func_total_branches = stats.get("filtered_stats_function_total_branches", 0)
#     func_covered_branches = stats.get("filtered_stats_function_covered_branches", 0)
#     stats["function_branch_coverage"] = func_covered_branches / func_total_branches if func_total_branches > 0 else None

# def merge_aggregated_results(root_dir: str, output_file: str) -> None:
#     """
#     合并 root_dir 下所有子目录中的 aggregated_results.json 文件，
#     并计算覆盖率指标。
#     """
#     total_by_model = {}
#     total_by_model_framework = {}
#     total_by_model_spec = {}

#     file_count = 0
#     for dirpath, _, filenames in os.walk(root_dir):
#         if "aggregated_results.json" in filenames:
#             file_path = os.path.join(dirpath, "aggregated_results.json")
#             try:
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     data = json.load(f)
#             except Exception as e:
#                 print(f"警告: 无法读取文件 {file_path} - {e}")
#                 continue

#             if "by_model" in data:
#                 deep_accumulate(total_by_model, data["by_model"])
#             if "by_model_framework" in data:
#                 deep_accumulate(total_by_model_framework, data["by_model_framework"])
#             if "by_model_spec" in data:
#                 deep_accumulate(total_by_model_spec, data["by_model_spec"])

#             file_count += 1
#             print(f"已处理: {file_path}")

#     if file_count == 0:
#         print("未找到任何 aggregated_results.json 文件。")
#         return

#     # 重新计算 test_pass_rate 并添加覆盖率
#     for model_stats in total_by_model.values():
#         recalc_pass_rate(model_stats)
#         add_coverage_metrics(model_stats)
#     for framework_stats in total_by_model_framework.values():
#         recalc_pass_rate(framework_stats)
#         add_coverage_metrics(framework_stats)
#     for spec_stats in total_by_model_spec.values():
#         recalc_pass_rate(spec_stats)
#         add_coverage_metrics(spec_stats)

#     merged = {
#         "by_model": total_by_model,
#         "by_model_framework": total_by_model_framework,
#         "by_model_spec": total_by_model_spec,
#     }

#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(merged, f, indent=2, ensure_ascii=False)

#     print(f"合并完成！共处理 {file_count} 个文件，结果保存至 {output_file}")

# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description="合并多个 aggregated_results.json，并计算覆盖率")
#     parser.add_argument("--root", default=".", help="要搜索的根目录（默认当前目录）")
#     parser.add_argument("--output", default="merged_aggregated_results.json", help="输出文件路径")
#     args = parser.parse_args()

# # 将不同语言的结果合并
#     merge_aggregated_results("test_results", "test_results/merged_aggregated_results.json")




import json
import os
from typing import Any, Dict

def is_numeric(value: Any) -> bool:
    """判断是否为数值类型（int/float），不包括 bool 和 None"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def deep_accumulate(accumulator: Dict, new_data: Dict) -> None:
    """
    递归地将 new_data 中的数值累加到 accumulator 中。
    对于非数值字段，若 accumulator 中不存在则复制，存在则保留 accumulator 的原值（不覆盖）。
    遇到 None 值时，视为 0 进行累加（如果累加器中有数值）。
    """
    for key, value in new_data.items():
        if isinstance(value, dict):
            if key not in accumulator:
                accumulator[key] = {}
            deep_accumulate(accumulator[key], value)
        elif is_numeric(value):
            old_val = accumulator.get(key)
            if old_val is None:
                old_val = 0
            accumulator[key] = old_val + value
        else:
            # 非数值非字典：如字符串、None等，只在 accumulator 中没有该键时才复制
            if key not in accumulator:
                accumulator[key] = value

def recalc_rates(stats: Dict) -> None:
    """
    根据新格式重新计算各种比率。
    新格式中包含 total, syntax_correct, compile_pass, excute_pass, test_pass 等字段。
    计算:
        syntax_correct_rate = syntax_correct / total
        compile_pass_rate = compile_pass / total
        excute_pass_rate = excute_pass / total
        test_pass_rate = test_pass / total   (注: 原 testcase_passed 字段保留，但不用于比率)
    """
    total = stats.get("total", 0)
    if total > 0:
        stats["syntax_correct_rate"] = stats.get("syntax_correct", 0) / total
        stats["compile_pass_rate"] = stats.get("compile_pass", 0) / total
        stats["excute_pass_rate"] = stats.get("excute_pass", 0) / total
        stats["test_pass_rate"] = stats.get("test_pass", 0) / total
        stats["testcase_passed_rate"] = stats.get("testcase_passed", 0.0) / total
    else:
        stats["syntax_correct_rate"] = None
        stats["compile_pass_rate"] = None
        stats["excute_pass_rate"] = None
        stats["test_pass_rate"] = None
        stats["testcase_passed_rate"] = None

def add_coverage_metrics(stats: Dict) -> None:
    """基于累加后的统计字段计算覆盖率并添加到 stats 中"""
    # 文件级行覆盖率
    file_total_lines = stats.get("filtered_stats_file_total_lines", 0)
    file_covered_lines = stats.get("filtered_stats_file_covered_lines", 0)
    stats["file_line_coverage"] = file_covered_lines / file_total_lines if file_total_lines > 0 else None

    # 文件级分支覆盖率
    file_total_branches = stats.get("filtered_stats_file_total_branches", 0)
    file_covered_branches = stats.get("filtered_stats_file_covered_branches", 0)
    stats["file_branch_coverage"] = file_covered_branches / file_total_branches if file_total_branches > 0 else None

    # 函数级行覆盖率
    func_total_lines = stats.get("filtered_stats_function_total_lines", 0)
    func_covered_lines = stats.get("filtered_stats_function_covered_lines", 0)
    stats["function_line_coverage"] = func_covered_lines / func_total_lines if func_total_lines > 0 else None

    # 函数级分支覆盖率
    func_total_branches = stats.get("filtered_stats_function_total_branches", 0)
    func_covered_branches = stats.get("filtered_stats_function_covered_branches", 0)
    stats["function_branch_coverage"] = func_covered_branches / func_total_branches if func_total_branches > 0 else None

def merge_aggregated_results(root_dir: str, output_file: str) -> None:
    """
    合并 root_dir 下所有子目录中的 aggregated_results.json 文件，
    并重新计算比率及覆盖率指标。
    """
    total_by_model = {}
    total_by_framework = {}
    total_by_spec = {}

    file_count = 0
    for dirpath, _, filenames in os.walk(root_dir):
        if "aggregated_results.json" in filenames:
            file_path = os.path.join(dirpath, "aggregated_results.json")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"警告: 无法读取文件 {file_path} - {e}")
                continue

            # 适配新格式的键名
            if "by_model" in data:
                deep_accumulate(total_by_model, data["by_model"])
            if "by_framework" in data:
                deep_accumulate(total_by_framework, data["by_framework"])
            if "by_spec" in data:
                deep_accumulate(total_by_spec, data["by_spec"])

            file_count += 1
            print(f"已处理: {file_path}")

    if file_count == 0:
        print("未找到任何 aggregated_results.json 文件。")
        return

    # 重新计算各分组下的比率并添加覆盖率
    for stats in total_by_model.values():
        recalc_rates(stats)
        add_coverage_metrics(stats)
    for stats in total_by_framework.values():
        recalc_rates(stats)
        add_coverage_metrics(stats)
    for stats in total_by_spec.values():
        recalc_rates(stats)
        add_coverage_metrics(stats)

    merged = {
        "by_model": total_by_model,
        "by_framework": total_by_framework,
        "by_spec": total_by_spec,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"合并完成！共处理 {file_count} 个文件，结果保存至 {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="合并多个 aggregated_results.json，并计算覆盖率")
    parser.add_argument("--root", default=".", help="要搜索的根目录（默认当前目录）")
    parser.add_argument("--output", default="merged_aggregated_results.json", help="输出文件路径")
    args = parser.parse_args()

    # 将不同语言的结果合并（可根据需要修改根目录）
    merge_aggregated_results("test_results", "test_results/merged_aggregated_results.json")
# import sys
# import json
# import argparse

# def parse_arguments():
#     parser = argparse.ArgumentParser(description="统计覆盖率JSON文件的文件级和函数级数据")
#     parser.add_argument('input_file', nargs='?', default='coverage.json',
#                         help='输入的覆盖率JSON文件路径（默认：coverage.json）')
#     parser.add_argument('-o', '--output', help='输出结果的文件路径（若不指定则打印到控制台）')
#     return parser.parse_args()

# def main():
#     # args = parse_arguments()
#     # input_file = args.input_file
#     # output_file = args.output
#     input_file = "test_results/flask/pytest_CodeLlama-7b/summary.json"
#     output_file = "test_results/flask/pytest_CodeLlama-7b/result.txt"

#     # 读取 JSON 文件
#     try:
#         with open(input_file, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#     except FileNotFoundError:
#         print(f"错误：文件 '{input_file}' 未找到。")
#         sys.exit(1)
#     except json.JSONDecodeError as e:
#         print(f"错误：JSON 解析失败：{e}")
#         sys.exit(1)

#     # 文件级别统计
#     file_totals = {
#         'total_lines': 0,
#         'covered_lines': 0,
#         'total_branches': 0,
#         'covered_branches': 0
#     }

#     file_coverage = data.get('file_coverage', {})
#     for file_path, coverage in file_coverage.items():
#         file_totals['total_lines'] += coverage.get('total_line', 0)
#         file_totals['covered_lines'] += coverage.get('covered_line', 0)
#         file_totals['total_branches'] += coverage.get('total_branch', 0)
#         file_totals['covered_branches'] += coverage.get('covered_branch', 0)

#     # 函数级别统计
#     func_totals = {
#         'total_lines': 0,
#         'covered_lines': 0,
#         'total_branches': 0,
#         'covered_branches': 0
#     }

#     func_coverage = data.get('function_coverage', {})
#     for func_name, coverage in func_coverage.items():
#         func_totals['total_lines'] += coverage.get('total_line', 0)
#         func_totals['covered_lines'] += coverage.get('covered_line', 0)
#         func_totals['total_branches'] += coverage.get('total_branch', 0)
#         func_totals['covered_branches'] += coverage.get('covered_branch', 0)

#     # 准备输出内容
#     output_lines = []
#     output_lines.append("文件级别统计：")
#     output_lines.append(f"  总行数: {file_totals['total_lines']}")
#     output_lines.append(f"  覆盖行数: {file_totals['covered_lines']}")
#     output_lines.append(f"  总分支: {file_totals['total_branches']}")
#     output_lines.append(f"  覆盖分支: {file_totals['covered_branches']}")
#     output_lines.append("")
#     output_lines.append("函数级别统计：")
#     output_lines.append(f"  总行数: {func_totals['total_lines']}")
#     output_lines.append(f"  覆盖行数: {func_totals['covered_lines']}")
#     output_lines.append(f"  总分支: {func_totals['total_branches']}")
#     output_lines.append(f"  覆盖分支: {func_totals['covered_branches']}")

#     output_text = "\n".join(output_lines)

#     # 输出到文件或控制台
#     if output_file:
#         try:
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 f.write(output_text)
#             print(f"统计结果已保存到 {output_file}")
#         except Exception as e:
#             print(f"保存文件失败：{e}")
#             sys.exit(1)
#     else:
#         print(output_text)

# if __name__ == "__main__":
#     main()


# import os
# import sys
# import json
# import csv
# import argparse
# from pathlib import Path

# def parse_arguments():
#     parser = argparse.ArgumentParser(description="批量处理目录下所有 summary.json 的覆盖率统计")
#     parser.add_argument('root_dir', nargs='?', default='.',
#                         help='根目录（默认：当前目录）')
#     parser.add_argument('--summary-csv', '-s', default='coverage_summary.csv',
#                         help='汇总 CSV 文件名（默认：coverage_summary.csv）')
#     parser.add_argument('--no-csv', action='store_true',
#                         help='不生成汇总 CSV 文件')
#     return parser.parse_args()

# def compute_stats(data):
#     """
#     从 JSON 数据中计算文件级和函数级统计
#     返回 (file_stats, func_stats) 两个字典
#     """
#     # 文件级别统计
#     file_totals = {
#         'total_lines': 0,
#         'covered_lines': 0,
#         'total_branches': 0,
#         'covered_branches': 0
#     }
#     file_coverage = data.get('file_coverage', {})
#     for coverage in file_coverage.values():
#         file_totals['total_lines'] += coverage.get('total_line', 0)
#         file_totals['covered_lines'] += coverage.get('covered_line', 0)
#         file_totals['total_branches'] += coverage.get('total_branch', 0)
#         file_totals['covered_branches'] += coverage.get('covered_branch', 0)

#     # 函数级别统计
#     func_totals = {
#         'total_lines': 0,
#         'covered_lines': 0,
#         'total_branches': 0,
#         'covered_branches': 0
#     }
#     func_coverage = data.get('function_coverage', {})
#     for coverage in func_coverage.values():
#         func_totals['total_lines'] += coverage.get('total_line', 0)
#         func_totals['covered_lines'] += coverage.get('covered_line', 0)
#         func_totals['total_branches'] += coverage.get('total_branch', 0)
#         func_totals['covered_branches'] += coverage.get('covered_branch', 0)

#     return file_totals, func_totals

# def format_stats(file_totals, func_totals):
#     """格式化统计结果为字符串"""
#     lines = []
#     lines.append("文件级别统计：")
#     lines.append(f"  总行数: {file_totals['total_lines']}")
#     lines.append(f"  覆盖行数: {file_totals['covered_lines']}")
#     lines.append(f"  总分支: {file_totals['total_branches']}")
#     lines.append(f"  覆盖分支: {file_totals['covered_branches']}")
#     lines.append("")
#     lines.append("函数级别统计：")
#     lines.append(f"  总行数: {func_totals['total_lines']}")
#     lines.append(f"  覆盖行数: {func_totals['covered_lines']}")
#     lines.append(f"  总分支: {func_totals['total_branches']}")
#     lines.append(f"  覆盖分支: {func_totals['covered_branches']}")
#     return "\n".join(lines)

# def process_json_file(json_path, save_dir=None):
#     """处理单个 JSON 文件，返回统计字典，并保存结果到同目录下"""
#     try:
#         with open(json_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#     except Exception as e:
#         print(f"错误：无法读取 {json_path} - {e}")
#         return None

#     # 计算统计
#     file_totals, func_totals = compute_stats(data)

#     # 保存结果到同目录下的 coverage_stats.txt
#     out_path = json_path.parent / 'coverage_stats.txt'
#     try:
#         with open(out_path, 'w', encoding='utf-8') as f:
#             f.write(format_stats(file_totals, func_totals))
#         print(f"已保存结果到 {out_path}")
#     except Exception as e:
#         print(f"错误：无法写入 {out_path} - {e}")

#     # 返回统计字典用于汇总
#     return {
#         'json_file': str(json_path),
#         'file_total_lines': file_totals['total_lines'],
#         'file_covered_lines': file_totals['covered_lines'],
#         'file_total_branches': file_totals['total_branches'],
#         'file_covered_branches': file_totals['covered_branches'],
#         'func_total_lines': func_totals['total_lines'],
#         'func_covered_lines': func_totals['covered_lines'],
#         'func_total_branches': func_totals['total_branches'],
#         'func_covered_branches': func_totals['covered_branches'],
#     }

# def main():
#     # args = parse_arguments()
#     root = Path("test_results/markitdown").resolve()
#     if not root.is_dir():
#         print(f"错误：{root} 不是有效的目录")
#         sys.exit(1)

#     # 查找所有 summary.json
#     json_files = list(root.rglob('summary.json'))
#     if not json_files:
#         print(f"在 {root} 下未找到任何 summary.json 文件")
#         sys.exit(0)

#     print(f"找到 {len(json_files)} 个 summary.json 文件，开始处理...")
#     all_results = []
#     for json_path in json_files:
#         result = process_json_file(json_path)
#         if result:
#             all_results.append(result)

#     # 生成汇总 CSV
#     if all_results:
#         csv_path = root / 'coverage_summary.csv'
#         try:
#             with open(csv_path, 'w', newline='', encoding='utf-8') as f:
#                 fieldnames = [
#                     'json_file',
#                     'file_total_lines', 'file_covered_lines',
#                     'file_total_branches', 'file_covered_branches',
#                     'func_total_lines', 'func_covered_lines',
#                     'func_total_branches', 'func_covered_branches'
#                 ]
#                 writer = csv.DictWriter(f, fieldnames=fieldnames)
#                 writer.writeheader()
#                 writer.writerows(all_results)
#             print(f"汇总 CSV 已保存到 {csv_path}")
#         except Exception as e:
#             print(f"错误：无法写入汇总 CSV - {e}")

#     print("批量处理完成！")

# if __name__ == "__main__":
#     main()



# import csv
# import os
# import argparse
# from collections import defaultdict

# def extract_model_name(file_path):
#     """从文件路径中提取模型名称，假设路径为 .../<model>/summary.json，模型名称为目录名的最后一部分（以下划线分隔）"""
#     dir_path = os.path.dirname(file_path)          # 获取父目录
#     dir_name = os.path.basename(dir_path)          # 获取目录名
#     # 取下划线分割的最后一部分作为模型名称
#     parts = dir_name.split('_')
#     return parts[-1] if parts else dir_name

# def main():
#     parser = argparse.ArgumentParser(description="统计 CSV 中相同模型的各列总和")
#     parser.add_argument('csv_file', help='输入的 CSV 文件路径')
#     parser.add_argument('-o', '--output', help='输出 CSV 文件路径（可选）')
#     args = parser.parse_args()

#     # 需要求和的列名（排除 json_file）
#     sum_columns = [
#         'file_total_lines', 'file_covered_lines',
#         'file_total_branches', 'file_covered_branches',
#         'func_total_lines', 'func_covered_lines',
#         'func_total_branches', 'func_covered_branches'
#     ]

#     # 存储每个模型的累计值：defaultdict(lambda: defaultdict(int))
#     model_sums = defaultdict(lambda: {col: 0 for col in sum_columns})

#     try:
#         with open(args.csv_file, 'r', encoding='utf-8') as f:
#             reader = csv.DictReader(f)
#             # 检查必要列是否存在
#             missing = [col for col in ['json_file'] + sum_columns if col not in reader.fieldnames]
#             if missing:
#                 print(f"错误：CSV 文件中缺少以下列：{missing}")
#                 return

#             for row in reader:
#                 model = extract_model_name(row['json_file'])
#                 for col in sum_columns:
#                     # 转换为整数，如果为空则视为 0
#                     try:
#                         value = int(row[col]) if row[col] else 0
#                     except ValueError:
#                         value = 0
#                     model_sums[model][col] += value
#     except FileNotFoundError:
#         print(f"错误：文件 '{args.csv_file}' 未找到")
#         return
#     except Exception as e:
#         print(f"读取文件时出错：{e}")
#         return

#     if not model_sums:
#         print("没有有效数据")
#         return

#     # 输出结果
#     if args.output:
#         # 保存到 CSV
#         try:
#             with open(args.output, 'w', newline='', encoding='utf-8') as f:
#                 fieldnames = ['model'] + sum_columns
#                 writer = csv.DictWriter(f, fieldnames=fieldnames)
#                 writer.writeheader()
#                 for model, sums in sorted(model_sums.items()):
#                     row = {'model': model, **sums}
#                     writer.writerow(row)
#             print(f"结果已保存到 {args.output}")
#         except Exception as e:
#             print(f"写入输出文件时出错：{e}")
#     else:
#         # 打印到控制台
#         print(f"{'模型':<20} " + " ".join(f"{col:>20}" for col in sum_columns))
#         for model, sums in sorted(model_sums.items()):
#             values = [f"{sums[col]:>20}" for col in sum_columns]
#             print(f"{model:<20} " + " ".join(values))

# if __name__ == "__main__":
#     main()

#     # python cal_py_result.py test_results/tornado/coverage_summary.csv -o test_results/tornado/grouped_results.csv


# import csv
# import argparse
# from collections import defaultdict

# # 需要求和的数值列
# VALUE_COLUMNS = [
#     'file_total_lines', 'file_covered_lines',
#     'file_total_branches', 'file_covered_branches',
#     'func_total_lines', 'func_covered_lines',
#     'func_total_branches', 'func_covered_branches'
# ]

# def parse_arguments():
#     parser = argparse.ArgumentParser(description="合并多个CSV文件，按模型累加数值列")
#     parser.add_argument('csv_files', nargs='+', help='要合并的CSV文件路径（至少一个）')
#     parser.add_argument('-o', '--output', help='输出汇总结果的文件路径（若不指定则打印到控制台）')
#     return parser.parse_args()

# def main():
#     args = parse_arguments()

#     # 存储每个模型的累计值
#     model_sums = defaultdict(lambda: {col: 0 for col in VALUE_COLUMNS})

#     for file_path in args.csv_files:
#         try:
#             with open(file_path, 'r', encoding='utf-8') as f:
#                 reader = csv.DictReader(f)
#                 # 检查必要的列
#                 missing = []
#                 if 'model' not in reader.fieldnames:
#                     missing.append('model')
#                 for col in VALUE_COLUMNS:
#                     if col not in reader.fieldnames:
#                         missing.append(col)
#                 if missing:
#                     print(f"警告：文件 {file_path} 缺少以下列，跳过该文件：{missing}")
#                     continue

#                 for row in reader:
#                     model = row['model'].strip()
#                     for col in VALUE_COLUMNS:
#                         # 转换为整数，处理空值或非法值
#                         try:
#                             val = int(row[col]) if row[col] else 0
#                         except ValueError:
#                             val = 0
#                         model_sums[model][col] += val
#         except FileNotFoundError:
#             print(f"错误：文件 {file_path} 未找到，跳过")
#         except Exception as e:
#             print(f"读取文件 {file_path} 时出错：{e}，跳过")

#     if not model_sums:
#         print("没有有效数据可汇总")
#         return

#     # 准备输出
#     if args.output:
#         try:
#             with open(args.output, 'w', newline='', encoding='utf-8') as f:
#                 fieldnames = ['model'] + VALUE_COLUMNS
#                 writer = csv.DictWriter(f, fieldnames=fieldnames)
#                 writer.writeheader()
#                 for model in sorted(model_sums.keys()):
#                     row = {'model': model, **model_sums[model]}
#                     writer.writerow(row)
#             print(f"汇总结果已保存到 {args.output}")
#         except Exception as e:
#             print(f"写入输出文件时出错：{e}")
#     else:
#         # 打印到控制台（表格形式）
#         # 计算每列宽度以便对齐
#         col_widths = {col: max(len(col), 10) for col in VALUE_COLUMNS}
#         # 打印表头
#         header = f"{'model':<20} " + " ".join(f"{col:>{col_widths[col]}}" for col in VALUE_COLUMNS)
#         print(header)
#         for model in sorted(model_sums.keys()):
#             row_vals = [f"{model_sums[model][col]:>{col_widths[col]}}" for col in VALUE_COLUMNS]
#             print(f"{model:<20} " + " ".join(row_vals))

# if __name__ == "__main__":
#     main()

#     # python cal_py_result.py test_results/tornado/grouped_results.csv test_results/flask/grouped_results.csv test_results/markitdown/grouped_results.csv test_results/pylint/grouped_results.csv


# import os
# import json
# import argparse
# from collections import defaultdict
# import csv

# def extract_model(dirname):
#     """从目录名中提取模型名（取下划线分割的最后一部分）"""
#     parts = dirname.split('_')
#     return parts[-1] if parts else dirname

# def main():
#     parser = argparse.ArgumentParser(description="汇总子目录中summary.json的指标，按模型累加")
#     parser.add_argument('root_dir', help='根目录路径')
#     parser.add_argument('-o', '--output', help='输出CSV文件路径（默认打印到控制台）')
#     args = parser.parse_args()

#     root = args.root_dir
#     if not os.path.isdir(root):
#         print(f"错误：{root} 不是有效目录")
#         return

#     # 存储每个模型的累加值
#     model_totals = defaultdict(lambda: {
#         'total': 0,
#         'syntax_correct': 0,
#         'compile_pass': 0,
#         'test_failed': 0,
#         'test_passed': 0,
#         'test_total': 0,
#         'test_collected': 0
#     })

#     # 遍历根目录下的子目录
#     for entry in os.listdir(root):
#         subdir = os.path.join(root, entry)
#         if not os.path.isdir(subdir):
#             continue
#         json_path = os.path.join(subdir, 'summary.json')
#         if not os.path.isfile(json_path):
#             continue

#         try:
#             with open(json_path, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#         except Exception as e:
#             print(f"警告：无法读取 {json_path} - {e}")
#             continue

#         model = extract_model(entry)
#         # 累加顶层字段
#         model_totals[model]['total'] += data.get('total', 0)
#         model_totals[model]['syntax_correct'] += data.get('syntax_correct', 0)
#         model_totals[model]['compile_pass'] += data.get('compile_pass', 0)

#         # 累加 testcase 子字段
#         testcase = data.get('testcase', {})
#         model_totals[model]['test_failed'] += testcase.get('failed', 0)
#         model_totals[model]['test_passed'] += testcase.get('passed', 0)
#         model_totals[model]['test_total'] += testcase.get('total', 0)
#         model_totals[model]['test_collected'] += testcase.get('collected', 0)

#     if not model_totals:
#         print("未找到任何 summary.json 文件")
#         return

#     # 准备输出行
#     output_rows = []
#     for model, vals in sorted(model_totals.items()):
#         total = vals['total']
#         syntax_correct = vals['syntax_correct']
#         compile_pass = vals['compile_pass']
#         test_failed = vals['test_failed']
#         test_passed = vals['test_passed']
#         test_total = vals['test_total']
#         test_collected = vals['test_collected']

#         # 计算比率（避免除零）
#         syntax_rate = syntax_correct / total if total else 0
#         compile_rate = compile_pass / total if total else 0
#         test_pass_rate = test_passed / test_total if test_total else 0

#         row = {
#             'model': model,
#             'total': total,
#             'syntax_correct': syntax_correct,
#             'syntax_correct_rate': syntax_rate,
#             'compile_pass': compile_pass,
#             'compile_pass_rate': compile_rate,
#             'test_failed': test_failed,
#             'test_passed': test_passed,
#             'test_total': test_total,
#             'test_collected': test_collected,
#             'test_pass_rate': test_pass_rate
#         }
#         output_rows.append(row)

#     if args.output:
#         # 写入CSV
#         fieldnames = ['model', 'total', 'syntax_correct', 'syntax_correct_rate',
#                       'compile_pass', 'compile_pass_rate', 'test_failed',
#                       'test_passed', 'test_total', 'test_collected', 'test_pass_rate']
#         try:
#             with open(args.output, 'w', newline='', encoding='utf-8') as f:
#                 writer = csv.DictWriter(f, fieldnames=fieldnames)
#                 writer.writeheader()
#                 for row in output_rows:
#                     # 将比率格式化为百分比字符串
#                     row['syntax_correct_rate'] = f"{row['syntax_correct_rate']:.2%}"
#                     row['compile_pass_rate'] = f"{row['compile_pass_rate']:.2%}"
#                     row['test_pass_rate'] = f"{row['test_pass_rate']:.2%}"
#                     writer.writerow(row)
#             print(f"汇总结果已保存到 {args.output}")
#         except Exception as e:
#             print(f"写入CSV失败：{e}")
#     else:
#         # 打印表格
#         print(f"{'model':<15} {'total':>6} {'syntax_correct':>15} {'syntax_rate':>11} {'compile_pass':>13} {'compile_rate':>11} {'test_failed':>11} {'test_passed':>11} {'test_total':>10} {'test_pass_rate':>13}")
#         for row in output_rows:
#             print(f"{row['model']:<15} {row['total']:>6} {row['syntax_correct']:>15} {row['syntax_correct_rate']:>10.2%} {row['compile_pass']:>13} {row['compile_pass_rate']:>10.2%} {row['test_failed']:>11} {row['test_passed']:>11} {row['test_total']:>10} {row['test_pass_rate']:>12.2%}")

# if __name__ == "__main__":
#     main()




# 只保留focal file/method 的覆盖率
# import os
# import json
# import argparse
# from collections import defaultdict
# from pathlib import Path

# def load_data_file(data_path):
#     """加载 data_file.json，返回文件路径集合和函数标识集合"""
#     with open(data_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     file_paths = set()
#     func_keys = set()

#     for entry in data:
#         project_root = entry.get('project_root', '').split('projects/pylint')[-1]  # 提取相对路径
#         src_file = entry.get('src_file')
#         if not src_file:
#             continue
#         # src_file = os.path.join(project_root, src_file)
#         file_paths.add(src_file)

#         # 构造函数标识：文件名:类名.方法名 或 文件名:函数名
#         name = entry.get('name', '')
#         class_name = entry.get('class_name')
#         if class_name:
#             func_name = f"{class_name}.{name}"
#         else:
#             func_name = name
#         func_key = f"{src_file}:{func_name}"
#         func_keys.add(func_key)

#     return file_paths, func_keys

# def filter_summary(summary_path, file_paths, func_keys, output_suffix="_filtered"):
#     """处理单个 summary.json，保留匹配的条目，保存到新文件"""
#     try:
#         with open(summary_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#     except Exception as e:
#         print(f"无法读取 {summary_path}：{e}")
#         return

#     # 过滤 file_coverage
#     file_cov = data.get('file_coverage', {})
#     new_file_cov = {k: v for k, v in file_cov.items() if k in file_paths}
#     removed_files = set(file_cov.keys()) - set(new_file_cov.keys())
#     if removed_files:
#         print(f"  文件 {summary_path} 中移除了 {len(removed_files)} 个文件条目")

#     # 过滤 function_coverage
#     func_cov = data.get('function_coverage', {})
#     new_func_cov = {k: v for k, v in func_cov.items() if k in func_keys}
#     removed_funcs = set(func_cov.keys()) - set(new_func_cov.keys())
#     if removed_funcs:
#         print(f"  文件 {summary_path} 中移除了 {len(removed_funcs)} 个函数条目")

#     # 更新数据
#     data['file_coverage'] = new_file_cov
#     data['function_coverage'] = new_func_cov

#     # 生成输出文件名
#     out_path = summary_path.parent / (summary_path.stem + output_suffix + summary_path.suffix)
#     try:
#         with open(out_path, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)
#         print(f"已保存过滤结果到 {out_path}")
#     except Exception as e:
#         print(f"写入 {out_path} 失败：{e}")

# def main():
#     parser = argparse.ArgumentParser(description="过滤summary.json中的覆盖数据，只保留data_file.json中指定的文件和函数")
#     parser.add_argument('root_dir', help='根目录，包含多级子目录，最终目录下应有summary.json')
#     parser.add_argument('data_file', help='data_file.json 路径')
#     parser.add_argument('--output-suffix', default='_filtered',
#                         help='输出文件后缀（默认为 _filtered），例如 summary_filtered.json')
#     args = parser.parse_args()

#     root = Path(args.root_dir)
#     if not root.is_dir():
#         print(f"错误：{root} 不是有效目录")
#         return

#     data_path = Path(args.data_file)
#     if not data_path.is_file():
#         print(f"错误：{data_path} 不存在")
#         return

#     # 加载 data_file.json
#     file_paths, func_keys = load_data_file(data_path)
#     print(f"加载 data_file.json：共 {len(file_paths)} 个文件，{len(func_keys)} 个函数")

#     # 查找所有 summary.json
#     summary_files = list(root.rglob('summary.json'))
#     if not summary_files:
#         print(f"在 {root} 下未找到任何 summary.json 文件")
#         return

#     print(f"找到 {len(summary_files)} 个 summary.json 文件，开始处理...")
#     for sf in summary_files:
#         filter_summary(sf, file_paths, func_keys, args.output_suffix)

#     print("处理完成！")

# if __name__ == "__main__":
#     main()

# # python cal_py_result.py test_results/python/tornado data_file.json


# 过滤focal method的覆盖率
# import os
# import json
# import argparse
# from collections import defaultdict
# from pathlib import Path
# import csv

# def load_data_file(data_path):
#     """加载 data_file.json，返回文件路径集合和函数标识集合"""
#     with open(data_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     file_paths = set()
#     func_keys = set()

#     for entry in data:
#         src_file = entry.get('src_file')
#         if not src_file:
#             continue
#         project_root = entry.get('project_root', '').split('projects/flask/')[-1]  # 提取相对路径
#         src_file = os.path.join(project_root, src_file)
#         file_paths.add(src_file)

#         name = entry.get('name', '')
#         class_name = entry.get('class_name')
#         if class_name:
#             func_name = f"{class_name}.{name}"
#         else:
#             func_name = name
#         func_key = f"{src_file}:{func_name}"
#         func_keys.add(func_key)

#     return file_paths, func_keys

# def compute_stats(coverage_dict):
#     """计算给定覆盖字典的总行/覆盖行/总分枝/覆盖分枝"""
#     total_lines = 0
#     covered_lines = 0
#     total_branches = 0
#     covered_branches = 0
#     for item in coverage_dict.values():
#         total_lines += item.get('total_line', 0)
#         covered_lines += item.get('covered_line', 0)
#         total_branches += item.get('total_branch', 0)
#         covered_branches += item.get('covered_branch', 0)
#     return {
#         'total_lines': total_lines,
#         'covered_lines': covered_lines,
#         'total_branches': total_branches,
#         'covered_branches': covered_branches
#     }

# def filter_summary(summary_path, file_paths, func_keys, output_suffix="_filtered", stats_csv_writer=None, model_name=None):
#     """处理单个 summary.json，保留匹配的条目，计算统计，保存到新文件"""
#     try:
#         with open(summary_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#     except Exception as e:
#         print(f"无法读取 {summary_path}：{e}")
#         return None

#     # 过滤 file_coverage
#     file_cov = data.get('file_coverage', {})
#     new_file_cov = {k: v for k, v in file_cov.items() if k in file_paths}
#     removed_files = set(file_cov.keys()) - set(new_file_cov.keys())
#     if removed_files:
#         print(f"  文件 {summary_path} 中移除了 {len(removed_files)} 个文件条目")

#     # 过滤 function_coverage
#     func_cov = data.get('function_coverage', {})
#     new_func_cov = {k: v for k, v in func_cov.items() if k in func_keys}
#     removed_funcs = set(func_cov.keys()) - set(new_func_cov.keys())
#     if removed_funcs:
#         print(f"  文件 {summary_path} 中移除了 {len(removed_funcs)} 个函数条目")

#     # 计算统计
#     file_stats = compute_stats(new_file_cov)
#     func_stats = compute_stats(new_func_cov)

#     # 更新数据（将统计信息也写入过滤后的JSON）
#     data['file_coverage'] = new_file_cov
#     data['function_coverage'] = new_func_cov
#     data['filtered_stats'] = {
#         'file': file_stats,
#         'function': func_stats
#     }

#     # 生成输出文件名
#     out_path = summary_path.parent / (summary_path.stem + output_suffix + summary_path.suffix)
#     try:
#         with open(out_path, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)
#         print(f"已保存过滤结果到 {out_path}")
#     except Exception as e:
#         print(f"写入 {out_path} 失败：{e}")

#     # 如果需要写入汇总CSV，则写入一行
#     if stats_csv_writer is not None and model_name is not None:
#         stats_csv_writer.writerow({
#             'model': model_name,
#             'summary_file': str(summary_path),
#             'filtered_file': str(out_path),
#             'file_total_lines': file_stats['total_lines'],
#             'file_covered_lines': file_stats['covered_lines'],
#             'file_total_branches': file_stats['total_branches'],
#             'file_covered_branches': file_stats['covered_branches'],
#             'func_total_lines': func_stats['total_lines'],
#             'func_covered_lines': func_stats['covered_lines'],
#             'func_total_branches': func_stats['total_branches'],
#             'func_covered_branches': func_stats['covered_branches']
#         })

#     return file_stats, func_stats

# def extract_model_from_path(path, root_dir, pattern):
#     """根据模式从路径中提取模型名"""
#     rel_path = path.relative_to(root_dir)
#     parts = rel_path.parts
#     if not parts:
#         return "unknown"
#     if pattern == 'first_subdir':
#         return parts[0]
#     else:  # dirname_last_part
#         dir_name = path.parent.name  # summary.json所在目录名
#         parts = dir_name.split('_')
#         return parts[-1] if parts else dir_name

# def main():
#     parser = argparse.ArgumentParser(description="过滤summary.json中的覆盖数据，只保留data_file.json中指定的文件和函数，并统计过滤后的覆盖数据")
#     parser.add_argument('root_dir', help='根目录，包含多级子目录，最终目录下应有summary.json')
#     parser.add_argument('data_file', help='data_file.json 路径')
#     parser.add_argument('--output-suffix', default='_filtered',
#                         help='输出文件后缀（默认为 _filtered），例如 summary_filtered.json')
#     parser.add_argument('--stats-csv', help='输出统计汇总CSV文件路径（可选）')
#     parser.add_argument('--model-pattern', default='first_subdir',
#                         choices=['first_subdir', 'dirname_last_part'],
#                         help='如何从路径中提取模型名：first_subdir（根目录下第一级子目录名），dirname_last_part（取summary.json所在目录名的最后一部分，以下划线分割）')
#     args = parser.parse_args()

#     root = Path(args.root_dir)
#     if not root.is_dir():
#         print(f"错误：{root} 不是有效目录")
#         return

#     data_path = Path(args.data_file)
#     if not data_path.is_file():
#         print(f"错误：{data_path} 不存在")
#         return

#     # 加载 data_file.json
#     file_paths, func_keys = load_data_file(data_path)
#     print(f"加载 data_file.json：共 {len(file_paths)} 个文件，{len(func_keys)} 个函数")

#     # 查找所有 summary.json
#     summary_files = list(root.rglob('summary.json'))
#     if not summary_files:
#         print(f"在 {root} 下未找到任何 summary.json 文件")
#         return

#     print(f"找到 {len(summary_files)} 个 summary.json 文件，开始处理...")

#     # 准备统计CSV
#     stats_rows = []
#     if args.stats_csv:
#         csv_file = open(args.stats_csv, 'w', newline='', encoding='utf-8')
#         fieldnames = ['model', 'summary_file', 'filtered_file',
#                       'file_total_lines', 'file_covered_lines',
#                       'file_total_branches', 'file_covered_branches',
#                       'func_total_lines', 'func_covered_lines',
#                       'func_total_branches', 'func_covered_branches']
#         csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
#         csv_writer.writeheader()
#     else:
#         csv_writer = None

#     for sf in summary_files:
#         # 提取模型名
#         model = extract_model_from_path(sf, root, args.model_pattern)
#         filter_summary(sf, file_paths, func_keys, args.output_suffix,
#                        stats_csv_writer=csv_writer, model_name=model)

#     if csv_writer:
#         csv_file.close()
#         print(f"统计汇总已保存到 {args.stats_csv}")

#     print("处理完成！")

# if __name__ == "__main__":
#     main()


import json
import argparse
from pathlib import Path
from collections import defaultdict
import csv

def parse_dirname(dirname):
    """
    解析目录名，返回 (model, framework, has_specification)
    假设目录名格式如：specification_pytest_gpt4o 或 unittest_DSv3.2 等
    """
    parts = dirname.split('_')
    if not parts:
        return None, None, False
    model = parts[-1]                     # 模型名取最后一部分
    has_spec = parts[0] == 'specification'  # 是否以 specification 开头
    # 查找框架（pytest 或 unittest）
    framework = None
    for p in parts:
        if p in ('pytest', 'unittest'):
            framework = p
            break
    if framework is None:
        framework = 'unknown'              # 若未找到，标记为 unknown
    return model, framework, has_spec

def extract_fields(data):
    """从 JSON 中提取需要统计的字段"""
    fields = {}
    fields['total'] = data.get('total', 0)
    fields['syntax_correct'] = data.get('syntax_correct', 0)
    fields['compile_pass'] = data.get('compile_pass', 0)

    testcase = data.get('testcase', {})
    fields['test_passed'] = testcase.get('passed', 0)
    fields['test_failed'] = testcase.get('failed', 0)
    fields['test_total'] = testcase.get('total', 0)
    fields['test_collected'] = testcase.get('collected', 0)

    filtered_stats = data.get('filtered_stats', {})
    file_stats = filtered_stats.get('file', {})
    fields['file_total_lines'] = file_stats.get('total_lines', 0)
    fields['file_covered_lines'] = file_stats.get('covered_lines', 0)
    fields['file_total_branches'] = file_stats.get('total_branches', 0)
    fields['file_covered_branches'] = file_stats.get('covered_branches', 0)

    func_stats = filtered_stats.get('function', {})
    fields['func_total_lines'] = func_stats.get('total_lines', 0)
    fields['func_covered_lines'] = func_stats.get('covered_lines', 0)
    fields['func_total_branches'] = func_stats.get('total_branches', 0)
    fields['func_covered_branches'] = func_stats.get('covered_branches', 0)

    return fields

def add_rate_columns(row, totals):
    """向行字典中添加比率列（原地修改）"""
    # 语法正确率
    row['syntax_correct_rate'] = (totals['syntax_correct'] / totals['total']) if totals['total'] != 0 else 0.0
    # 编译通过率
    row['compile_pass_rate'] = (totals['compile_pass'] / totals['total']) if totals['total'] != 0 else 0.0
    # 测试通过率
    row['test_pass_rate'] = (totals['test_passed'] / totals['test_total']) if totals['test_total'] != 0 else 0.0
    # 文件行覆盖率
    row['file_line_coverage'] = (totals['file_covered_lines'] / totals['file_total_lines']) if totals['file_total_lines'] != 0 else 0.0
    # 文件分支覆盖率
    row['file_branch_coverage'] = (totals['file_covered_branches'] / totals['file_total_branches']) if totals['file_total_branches'] != 0 else 0.0
    # 函数行覆盖率
    row['func_line_coverage'] = (totals['func_covered_lines'] / totals['func_total_lines']) if totals['func_total_lines'] != 0 else 0.0
    # 函数分支覆盖率
    row['func_branch_coverage'] = (totals['func_covered_branches'] / totals['func_total_branches']) if totals['func_total_branches'] != 0 else 0.0

def main():
    parser = argparse.ArgumentParser(description="分组统计 summary_filtered.json 中的覆盖数据，包含比率列")
    parser.add_argument('root_dir', help='根目录，包含多级子目录，最终目录下应有 summary_filtered.json')
    parser.add_argument('--output-prefix', default='summary_stats',
                        help='输出文件前缀，将生成三个 CSV 文件：{prefix}_by_model.csv, {prefix}_by_framework.csv, {prefix}_by_spec.csv')
    args = parser.parse_args()

    root = Path(args.root_dir)
    if not root.is_dir():
        print(f"错误：{root} 不是有效目录")
        return

    # 查找所有 summary_filtered.json
    summary_files = list(root.rglob('summary_filtered.json'))
    if not summary_files:
        print(f"在 {root} 下未找到任何 summary_filtered.json 文件")
        return

    print(f"找到 {len(summary_files)} 个 summary_filtered.json 文件，开始处理...")

    # 需要累加的字段列表（不包括比率列）
    fields_list = [
        'total', 'syntax_correct', 'compile_pass',
        'test_passed', 'test_failed', 'test_total', 'test_collected',
        'file_total_lines', 'file_covered_lines', 'file_total_branches', 'file_covered_branches',
        'func_total_lines', 'func_covered_lines', 'func_total_branches', 'func_covered_branches'
    ]

    # 比率列列表（用于 fieldnames）
    rate_columns = [
        'syntax_correct_rate', 'compile_pass_rate', 'test_pass_rate',
        'file_line_coverage', 'file_branch_coverage',
        'func_line_coverage', 'func_branch_coverage'
    ]

    # 三个分组累加器
    model_totals = defaultdict(lambda: defaultdict(int))               # key: model
    framework_totals = defaultdict(lambda: defaultdict(int))           # key: (model, framework)
    spec_totals = defaultdict(lambda: defaultdict(int))                # key: (model, has_spec)

    for sf in summary_files:
        dir_name = sf.parent.name          # 子子目录名
        model, framework, has_spec = parse_dirname(dir_name)
        if model is None:
            print(f"警告：无法解析目录名 {dir_name}，跳过文件 {sf}")
            continue

        try:
            with open(sf, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"错误：无法读取 {sf} - {e}")
            continue

        fields = extract_fields(data)

        # 按模型累加
        for field in fields_list:
            model_totals[model][field] += fields[field]

        # 按 (模型, 框架) 累加
        fw_key = (model, framework)
        for field in fields_list:
            framework_totals[fw_key][field] += fields[field]

        # 按 (模型, 是否有spec) 累加
        spec_key = (model, has_spec)
        for field in fields_list:
            spec_totals[spec_key][field] += fields[field]

    # 所有分组共同的 fieldnames：group + 原始数值列 + 比率列
    csv_fieldnames = ['group'] + fields_list + rate_columns

    # 1. 按模型
    with open(f"{args.root_dir}/{args.output_prefix}_by_model.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        for model, totals in sorted(model_totals.items()):
            row = {'group': model}
            row.update(totals)
            add_rate_columns(row, totals)
            writer.writerow(row)
    print(f"已保存按模型分组结果到 {args.output_prefix}_by_model.csv")

    # 2. 按 (模型, 框架)
    with open(f"{args.root_dir}/{args.output_prefix}_by_framework.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        for (model, framework), totals in sorted(framework_totals.items()):
            row = {'group': f"{model}_{framework}"}
            row.update(totals)
            add_rate_columns(row, totals)
            writer.writerow(row)
    print(f"已保存按框架分组结果到 {args.output_prefix}_by_framework.csv")

    # 3. 按 (模型, 是否有spec)
    with open(f"{args.root_dir}/{args.output_prefix}_by_spec.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        for (model, has_spec), totals in sorted(spec_totals.items()):
            spec_label = "spec" if has_spec else "no_spec"
            row = {'group': f"{model}_{spec_label}"}
            row.update(totals)
            add_rate_columns(row, totals)
            writer.writerow(row)
    print(f"已保存按 spec 分组结果到 {args.output_prefix}_by_spec.csv")

    # 可选：打印到控制台（包含比率）
    def print_group(title, data):
        print(f"\n{title}:")
        for key, totals in sorted(data.items()):
            if isinstance(key, tuple):
                if len(key) == 2:
                    k_display = f"{key[0]}_{key[1]}" if isinstance(key[1], str) else f"{key[0]}_{'spec' if key[1] else 'no_spec'}"
                else:
                    k_display = str(key)
            else:
                k_display = key
            row = {'group': k_display}
            row.update(totals)
            add_rate_columns(row, totals)
            # 打印简略信息
            print(f"  {k_display}: total={totals['total']}, syntax_rate={row['syntax_correct_rate']:.2%}, compile_rate={row['compile_pass_rate']:.2%}, test_pass_rate={row['test_pass_rate']:.2%}")

    print_group("按模型分组", model_totals)
    print_group("按 (模型,框架) 分组", {k: v for k, v in framework_totals.items()})
    print_group("按 (模型,spec) 分组", {k: v for k, v in spec_totals.items()})

    print("处理完成！")

if __name__ == "__main__":
    main()
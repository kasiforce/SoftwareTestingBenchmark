# """Plot language-level aggregated benchmark metrics as a grouped bar chart.

# Usage:
#     python test_results/plot_language_bar_matplotlib.py

# Output:
#     test_results/language_metrics_bar.png
# """

# from __future__ import annotations

# import json
# from pathlib import Path


# LANG_FILES = {
#     "Python": Path("test_results/python/aggregated_results.json"),
#     "JavaScript": Path("test_results/javascript/aggregated_results.json"),
#     "Java": Path("test_results/java/aggregated_results.json"),
# }

# METRICS = [
#     "syntax_correct_rate",
#     "compile_pass_rate",
#     "excute_pass_rate",
#     "test_pass_rate",
#     "testcase_passed_rate",
#     "file_line_coverage",
#     "file_branch_coverage",
#     "function_line_coverage",
#     "function_branch_coverage",
# ]

# METRIC_LABELS = [
#     "Syntax",
#     "Compile",
#     "Excute",
#     "Test",
#     "Testcase",
#     "File Line",
#     "File Branch",
#     "Function Line",
#     "Function Branch",
# ]


# def aggregate_language_result(path: Path) -> dict[str, float]:
#     """Aggregate one language's result from by_spec (with_spec + without_spec)."""
#     data = json.loads(path.read_text(encoding="utf-8"))
#     parts = list(data["by_spec"].values())

#     total = sum(item["total"] for item in parts)

#     return {
#         "syntax_correct_rate": sum(item["syntax_correct"] for item in parts) / total,
#         "compile_pass_rate": sum(item["compile_pass"] for item in parts) / total,
#         "excute_pass_rate": sum(item["excute_pass"] for item in parts) / total,
#         "test_pass_rate": sum(item["test_pass"] for item in parts) / total,
#         "testcase_passed_rate": sum(item["testcase_passed"] for item in parts) / total,
#         "file_line_coverage": sum(item["filtered_stats_file_covered_lines"] for item in parts)
#         / sum(item["filtered_stats_file_total_lines"] for item in parts),
#         "file_branch_coverage": sum(item["filtered_stats_file_covered_branches"] for item in parts)
#         / sum(item["filtered_stats_file_total_branches"] for item in parts),
#         "function_line_coverage": sum(item["filtered_stats_function_covered_lines"] for item in parts)
#         / sum(item["filtered_stats_function_total_lines"] for item in parts),
#         "function_branch_coverage": sum(item["filtered_stats_function_covered_branches"] for item in parts)
#         / sum(item["filtered_stats_function_total_branches"] for item in parts),
#     }


# def main() -> None:
#     try:
#         import matplotlib.pyplot as plt
#         import numpy as np
#     except ModuleNotFoundError as exc:
#         raise SystemExit(
#             "matplotlib/numpy not installed. Please install first: pip install matplotlib numpy"
#         ) from exc

#     results = {lang: aggregate_language_result(path) for lang, path in LANG_FILES.items()}

#     x = np.arange(len(METRICS))
#     width = 0.24

#     fig, ax = plt.subplots(figsize=(16, 7))

#     for i, (lang, metric_values) in enumerate(results.items()):
#         y = [metric_values[m] * 100 for m in METRICS]
#         offset = (i - 1) * width
#         bars = ax.bar(x + offset, y, width=width, label=lang)

#         for bar, value in zip(bars, y):
#             ax.text(
#                 bar.get_x() + bar.get_width() / 2,
#                 bar.get_height() + 0.5,
#                 f"{value:.1f}%",
#                 ha="center",
#                 va="bottom",
#                 fontsize=8,
#                 rotation=90,
#             )

#     ax.set_title("Language-level Aggregated Metrics")
#     ax.set_ylabel("Percentage (%)")
#     ax.set_xticks(x)
#     ax.set_xticklabels(METRIC_LABELS, rotation=20, ha="right")
#     ax.set_ylim(0, 105)
#     ax.grid(axis="y", linestyle="--", alpha=0.3)
#     ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.10))

#     out = Path("test_results/language_metrics_bar.png")
#     fig.tight_layout()
#     fig.savefig(out, dpi=220)
#     print(f"Saved: {out}")


# if __name__ == "__main__":
#     main()

# """Plot language-level aggregated benchmark metrics as a line chart.

# Usage:
#     python test_results/plot_language_bar_matplotlib.py

# Output:
#     test_results/language_metrics_line.png
# """

# from __future__ import annotations

# import json
# from pathlib import Path
# import matplotlib.pyplot as plt
# from matplotlib import rcParams

# # 设置中文字体
# rcParams["font.sans-serif"] = ["SimHei"]  # 或者 ["Microsoft YaHei"]
# rcParams["axes.unicode_minus"] = False     # 解决负号显示问题


# LANG_FILES = {
#     "Python": Path("test_results/python/aggregated_results.json"),
#     "JavaScript": Path("test_results/javascript/aggregated_results.json"),
#     "Java": Path("test_results/java/aggregated_results.json"),
# }

# METRICS = [
#     "syntax_correct_rate",
#     "compile_pass_rate",
#     "excute_pass_rate",
#     "test_pass_rate",
#     "testcase_passed_rate",
#     "file_line_coverage",
#     "file_branch_coverage",
#     "function_line_coverage",
#     "function_branch_coverage",
# ]

# METRIC_LABELS = [
#     "Syntax",
#     "Compile",
#     "Excute",
#     "Test",
#     "Testcase",
#     "File Line",
#     "File Branch",
#     "Function Line",
#     "Function Branch",
# ]

# # Use line styles (not colors) to distinguish languages.
# LINE_STYLES = {
#     "Python": "-",      # solid
#     "JavaScript": "--", # dashed
#     "Java": ":",        # dotted
# }

# MARKERS = {
#     "Python": "o",
#     "JavaScript": "s",
#     "Java": "^",
# }


# def aggregate_language_result(path: Path) -> dict[str, float]:
#     data = json.loads(path.read_text(encoding="utf-8"))
#     parts = list(data["by_spec"].values())

#     total = sum(item["total"] for item in parts)

#     return {
#         "syntax_correct_rate": sum(item["syntax_correct"] for item in parts) / total,
#         "compile_pass_rate": sum(item["compile_pass"] for item in parts) / total,
#         "excute_pass_rate": sum(item["excute_pass"] for item in parts) / total,
#         "test_pass_rate": sum(item["test_pass"] for item in parts) / total,
#         "testcase_passed_rate": sum(item["testcase_passed"] for item in parts) / total,
#         "file_line_coverage": sum(item["filtered_stats_file_covered_lines"] for item in parts)
#         / sum(item["filtered_stats_file_total_lines"] for item in parts),
#         "file_branch_coverage": sum(item["filtered_stats_file_covered_branches"] for item in parts)
#         / sum(item["filtered_stats_file_total_branches"] for item in parts),
#         "function_line_coverage": sum(item["filtered_stats_function_covered_lines"] for item in parts)
#         / sum(item["filtered_stats_function_total_lines"] for item in parts),
#         "function_branch_coverage": sum(item["filtered_stats_function_covered_branches"] for item in parts)
#         / sum(item["filtered_stats_function_total_branches"] for item in parts),
#     }


# def main() -> None:
#     try:
#         import matplotlib.pyplot as plt
#         import numpy as np
#     except ModuleNotFoundError as exc:
#         raise SystemExit(
#             "matplotlib/numpy not installed. Please install first: pip install matplotlib numpy"
#         ) from exc

#     results = {lang: aggregate_language_result(path) for lang, path in LANG_FILES.items()}

#     x = np.arange(len(METRICS))
#     fig, ax = plt.subplots(figsize=(16, 7))

#     # 绘制线条
#     for lang, metric_values in results.items():
#         y = [metric_values[m] * 100 for m in METRICS]
#         ax.plot(
#             x,
#             y,
#             linestyle=LINE_STYLES[lang],
#             marker=MARKERS[lang],
#             color="black",
#             linewidth=2,
#             markersize=6,
#             label=lang,  # 每条线都带上 label
#         )

#         # 在每个点上加百分比标注
#         for xi, yi in zip(x, y):
#             ax.text(xi, yi + 0.8, f"{yi:.1f}%", ha="center", va="bottom", fontsize=8)

#     # 设置图例，统一右上角
#     ax.legend(loc="upper right")

#     ax.set_title("模型在不同语言上的平均表现")
#     ax.set_ylabel("Percentage (%)")
#     ax.set_xticks(x)
#     ax.set_xticklabels(METRIC_LABELS, rotation=20, ha="right")
#     ax.set_ylim(0, 105)
#     ax.grid(axis="y", linestyle="--", alpha=0.3)
#     # ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.10))

#     out = Path("test_results/language_metrics_line.png")
#     fig.tight_layout()
#     fig.savefig(out, dpi=220)
#     print(f"Saved: {out}")


# if __name__ == "__main__":
#     main()




# 统计每个函数对应的测试用例数量与覆盖率的关系，输出到 csv 文件中，方便后续分析和绘图。
# import json
# import re
# from pathlib import Path
# import pandas as pd


# GEN_ROOT = Path("tests/test_gen/python")
# RESULT_ROOT = Path("test_results/python")
# OUT_FILE = Path("test_results/python/python_test_count_vs_coverage.csv")


# def count_pytest_cases(test_code: str) -> int:
#     """
#     Count pytest test functions.
#     """
#     pattern = r"def\s+test_[a-zA-Z0-9_]+\s*\("
#     return len(re.findall(pattern, test_code))


# def build_function_key(item: dict) -> str:
#     """
#     Build function key aligned with coverage summary.
#     """
#     src_file = item["src_file"]

#     if not src_file.startswith("src/"):
#         src_file = f"src/{src_file}"

#     class_name = item.get("class_name")
#     func_name = item["name"]

#     if class_name:
#         return f"{src_file}:{class_name}.{func_name}"
#     return f"{src_file}:{func_name}"


# def infer_result_dir(json_name: str) -> str:
#     """
#     flask_lite_pytest_gpt4o.json
#     -> pytest_gpt4o
#     """
#     stem = Path(json_name).stem
#     parts = stem.split("_")

#     # 取 pytest 后面的部分
#     for i, p in enumerate(parts):
#         if p in ("pytest", "unittest"):
#             return "_".join(parts[i:])
#     return "pytest_gpt4o"


# def scan_project(project_dir: Path):
#     rows = []

#     project_name = project_dir.name
#     if "fix" in project_name:
#         print(f"[Skip] Fix project: {project_name}")
#         return rows

#     for gen_file in project_dir.glob("*.json"):
#         result_subdir = infer_result_dir(gen_file.name)
#         result_subdir1 = result_subdir
#         if "glm-4.7" in result_subdir:
#             result_subdir1 = result_subdir.replace("glm-4.7", "glm")
#         elif "gpt5" in result_subdir:
#             result_subdir1 = result_subdir.replace("gpt5nano", "gpt5")
#         cov_file = RESULT_ROOT / project_name / result_subdir1 / "summary_filtered.json"

#         if not cov_file.exists():
#             print(f"[Skip] Coverage not found: {cov_file}")
#             continue

#         with open(gen_file, "r", encoding="utf-8") as f:
#             gen_data = json.load(f)

#         with open(cov_file, "r", encoding="utf-8") as f:
#             cov_data = json.load(f)

#         function_cov = cov_data.get("function_coverage", {})

#         for item in gen_data:
#             function_key = build_function_key(item)

#             generated_tests = item.get("generated_tests", [])
#             total_test_cases = sum(
#                 count_pytest_cases(code)
#                 for code in generated_tests
#             )

#             cov = function_cov.get(function_key)
#             if cov is None:
#                 continue

#             rows.append({
#                 "project": project_name,
#                 "model": result_subdir,
#                 "function": function_key,
#                 "test_case_count": total_test_cases,
#                 "line_coverage": cov["line_coverage"],
#                 "branch_coverage": cov["branch_coverage"],
#                 "covered_line": cov["covered_line"],
#                 "total_line": cov["total_line"],
#                 "covered_branch": cov["covered_branch"],
#                 "total_branch": cov["total_branch"],
#             })

#     return rows


# def main():
#     all_rows = []

#     for project_dir in GEN_ROOT.iterdir():
#         if not project_dir.is_dir():
#             continue

#         print(f"Scanning {project_dir.name}...")
#         rows = scan_project(project_dir)
#         if rows:
#             all_rows.extend(rows)

#     df = pd.DataFrame(all_rows)
#     df.to_csv(OUT_FILE, index=False)

#     print(f"\nSaved to: {OUT_FILE}")
#     print(f"Total matched functions: {len(df)}")
#     print(df.head())


# if __name__ == "__main__":
#     main()




# import json
# import re
# from pathlib import Path
# import pandas as pd


# GEN_ROOT = Path("tests/test_gen/javascript")
# RESULT_ROOT = Path("test_results/javascript")
# OUT_FILE = Path("test_results/javascript/javascript_test_count_vs_coverage.csv")


# def count_jest_cases(test_code: str) -> int:
#     """
#     Count Jest test cases:
#     test(...)
#     it(...)
#     """
#     test_count = len(re.findall(r"\btest\s*\(", test_code))
#     it_count = len(re.findall(r"\bit\s*\(", test_code))
#     return test_count + it_count


# def find_coverage(function_cov: dict, src_file: str, func_name: str):
#     """
#     Fuzzy match:
#     src/plugins/shape/name.js::validatePluginName:1-20
#     """
#     prefix = f"{src_file}::{func_name}"
#     matched = [
#         v for k, v in function_cov.items()
#         if k.startswith(prefix)
#     ]

#     if not matched:
#         return None

#     # merge multiple matched entries
#     total_lines = sum(x["total_lines"] for x in matched)
#     covered_lines = sum(x["covered_lines"] for x in matched)
#     total_branches = sum(x["total_branches"] for x in matched)
#     covered_branches = sum(x["covered_branches"] for x in matched)

#     line_cov = 0 if total_lines == 0 else covered_lines / total_lines * 100
#     branch_cov = 0 if total_branches == 0 else covered_branches / total_branches * 100

#     return {
#         "covered_line": covered_lines,
#         "total_line": total_lines,
#         "line_coverage": line_cov,
#         "covered_branch": covered_branches,
#         "total_branch": total_branches,
#         "branch_coverage": branch_cov,
#     }


# def infer_result_dir(json_name: str) -> str:
#     """
#     modern-error_lite_jest_DSv3.2.json
#     -> jest_DSv3.2
#     """
#     stem = Path(json_name).stem
#     parts = stem.split("_")

#     for i, p in enumerate(parts):
#         if p == "jest":
#             return "_".join(parts[i:])
#     return "jest"


# def scan_project(project_dir: Path):
#     rows = []
#     project_name = project_dir.name

#     for gen_file in project_dir.glob("*.json"):
#         result_subdir = infer_result_dir(gen_file.name)
#         result_subdir1 = result_subdir
#         if "glm-4.7" in result_subdir:
#             result_subdir1 = result_subdir.replace("glm-4.7", "glm")
#         elif "gpt5" in result_subdir:
#             result_subdir1 = result_subdir.replace("gpt5nano", "gpt5")
#         cov_file = RESULT_ROOT / project_name / result_subdir1 / "summary.json"

#         if not cov_file.exists():
#             print(f"[Skip] Coverage not found: {cov_file}")
#             continue

#         with open(gen_file, "r", encoding="utf-8") as f:
#             gen_data = json.load(f)

#         with open(cov_file, "r", encoding="utf-8") as f:
#             cov_data = json.load(f)

#         function_cov = cov_data["coverage"].get("function", {})

#         for item in gen_data:
#             src_file = item["src_file"]
#             func_name = item["name"]

#             generated_tests = item.get("generated_tests", [])
#             total_test_cases = sum(
#                 count_jest_cases(code)
#                 for code in generated_tests
#             )

#             cov = find_coverage(function_cov, src_file, func_name)
#             if cov is None:
#                 continue

#             rows.append({
#                 "project": project_name,
#                 "model": result_subdir,
#                 "function": f"{src_file}::{func_name}",
#                 "test_case_count": total_test_cases,
#                 "line_coverage": cov["line_coverage"],
#                 "branch_coverage": cov["branch_coverage"],
#                 "covered_line": cov["covered_line"],
#                 "total_line": cov["total_line"],
#                 "covered_branch": cov["covered_branch"],
#                 "total_branch": cov["total_branch"],
#             })

#     return rows


# def main():
#     all_rows = []

#     for project_dir in GEN_ROOT.iterdir():
#         if not project_dir.is_dir():
#             continue

#         print(f"Scanning {project_dir.name}...")
#         rows = scan_project(project_dir)
#         all_rows.extend(rows)

#     df = pd.DataFrame(all_rows)
#     df.to_csv(OUT_FILE, index=False)

#     print(f"\nSaved to: {OUT_FILE}")
#     print(f"Total matched functions: {len(df)}")
#     print(df.head())


# if __name__ == "__main__":
#     main()





# import json
# import re
# from pathlib import Path
# import pandas as pd


# GEN_ROOT = Path("tests/test_gen/java")
# RESULT_ROOT = Path("test_results/java")
# OUT_FILE = Path("test_results/java/java_test_count_vs_coverage.csv")


# def count_junit4_cases(test_code: str) -> int:
#     """
#     Count JUnit4 test cases by @Test annotation.
#     """
#     return len(re.findall(r"@Test", test_code))


# def build_function_key(item: dict) -> str:
#     """
#     Java coverage key:
#     src/main/java/.../Options.java:addOptions
#     """
#     src_file = item["src_file"]
#     func_name = item["name"]
#     return f"{src_file}:{func_name}"


# def infer_result_dir(json_name: str) -> str:
#     """
#     commons-cli_lite_specification_junit4_DS6.7b.json
#     -> junit4_DS6.7b
#     """
#     stem = Path(json_name).stem
#     parts = stem.split("_")

#     for i, p in enumerate(parts):
#         if p.startswith("junit"):
#             return "_".join(parts[i:])
#     return "junit4"


# def scan_project(project_dir: Path):
#     rows = []
#     project_name = project_dir.name

#     for gen_file in project_dir.glob("*.json"):
#         result_subdir = infer_result_dir(gen_file.name)
#         result_subdir1 = result_subdir
#         if "glm-4.7" in result_subdir:
#             result_subdir1 = result_subdir.replace("glm-4.7", "glm")
#         elif "gpt5" in result_subdir:
#             result_subdir1 = result_subdir.replace("gpt5nano", "gpt5")
#         cov_file = RESULT_ROOT / project_name / result_subdir1 / "summary.json"

#         if not cov_file.exists():
#             print(f"[Skip] Coverage not found: {cov_file}")
#             continue

#         with open(gen_file, "r", encoding="utf-8") as f:
#             gen_data = json.load(f)

#         with open(cov_file, "r", encoding="utf-8") as f:
#             cov_data = json.load(f)

#         function_cov = cov_data.get("function_coverage", {})

#         for item in gen_data:
#             function_key = build_function_key(item)

#             generated_tests = item.get("generated_tests", [])
#             total_test_cases = sum(
#                 count_junit4_cases(code)
#                 for code in generated_tests
#             )

#             cov = function_cov.get(function_key)
#             if cov is None:
#                 continue

#             rows.append({
#                 "project": project_name,
#                 "model": result_subdir,
#                 "function": function_key,
#                 "test_case_count": total_test_cases,
#                 "line_coverage": cov["line_coverage"],
#                 "branch_coverage": cov["branch_coverage"],
#                 "covered_line": cov["covered_line"],
#                 "total_line": cov["total_line"],
#                 "covered_branch": cov["covered_branch"],
#                 "total_branch": cov["total_branch"],
#             })

#     return rows


# def main():
#     all_rows = []

#     for project_dir in GEN_ROOT.iterdir():
#         if not project_dir.is_dir():
#             continue

#         print(f"Scanning {project_dir.name}...")
#         rows = scan_project(project_dir)
#         all_rows.extend(rows)

#     df = pd.DataFrame(all_rows)
#     df.to_csv(OUT_FILE, index=False)

#     print(f"\nSaved to: {OUT_FILE}")
#     print(f"Total matched functions: {len(df)}")
#     print(df.head())


# if __name__ == "__main__":
#     main()



# import pandas as pd
# import matplotlib.pyplot as plt

# # 读取三语言数据
# df_python = pd.read_csv("test_results/python/python_test_count_vs_coverage.csv")
# df_java = pd.read_csv("test_results/java/java_test_count_vs_coverage.csv")
# df_js = pd.read_csv("test_results/javascript/javascript_test_count_vs_coverage.csv")

# plt.figure(figsize=(8, 6))

# # 绘制散点图，不同形状区分语言
# plt.scatter(df_python["total_line"], df_python["line_coverage"],
#             alpha=0.7, label="Python", marker='o', edgecolor='k')
# plt.scatter(df_java["total_line"], df_java["line_coverage"],
#             alpha=0.7, label="Java", marker='s', edgecolor='k')
# plt.scatter(df_js["total_line"], df_js["line_coverage"],
#             alpha=0.7, label="JavaScript", marker='^', edgecolor='k')

# plt.xlabel("Total Lines in Function")
# plt.ylabel("Line Coverage (%)")
# plt.title("Total Lines vs Line Coverage Across Languages")
# plt.legend(title="Language")
# plt.grid(True)

# # 保存图片
# plt.savefig("test_results/all_languages_total_line_vs_coverage_markers.png", dpi=300, bbox_inches='tight')

# plt.show()


# import pandas as pd
# import matplotlib.pyplot as plt

# # 读取三语言数据（包含 source_lines、covered_line、total_line 列）
# df_python = pd.read_csv("test_results/python/python_test_count_vs_coverage.csv")
# df_java = pd.read_csv("test_results/java/java_test_count_vs_coverage.csv")
# df_js = pd.read_csv("test_results/javascript/javascript_test_count_vs_coverage.csv")

# # 定义统一函数行数等级
# bins = [0, 10, 20, 40, 80, float('inf')]
# labels = [1, 2, 3, 4, 5]

# def compute_weighted_coverage(df, language_name):
#     # 按统一等级分组
#     df['line_level'] = pd.cut(df['total_line'], bins=bins, labels=labels, right=True)
#     # 计算每级覆盖率：覆盖行数总和 / 总行数总和
#     coverage = df.groupby('line_level').apply(
#         lambda x: x['covered_line'].sum() / x['total_line'].sum() * 100
#     ).reset_index(name='line_coverage_percent')
#     coverage['language'] = language_name
#     # 统计每级函数数量
#     coverage['function_count'] = df.groupby('line_level')['total_line'].count().values
#     return coverage

# cov_python = compute_weighted_coverage(df_python, "Python")
# cov_java = compute_weighted_coverage(df_java, "Java")
# cov_js = compute_weighted_coverage(df_js, "JavaScript")

# # 合并三语言数据
# cov_all = pd.concat([cov_python, cov_java, cov_js], axis=0)

# # 绘图
# plt.figure(figsize=(8, 6))
# markers = {'Python': 'o', 'Java': 's', 'JavaScript': '^'}

# for lang in ['Python', 'Java', 'JavaScript']:
#     subset = cov_all[cov_all['language'] == lang]
#     plt.plot(subset['line_level'], subset['line_coverage_percent'],
#              marker=markers[lang], label=lang, linewidth=2)

# plt.xlabel("行数")
# plt.ylabel("函数级行覆盖率 (%)")
# plt.title("不同函数规模下的行覆盖率")
# plt.xticks(labels, ['0-10','11-20','21-40','41-80','>80'])
# plt.grid(True)
# plt.legend(title="Language")

# # 保存图
# plt.savefig("test_results/all_languages_coverage_by_function_size_uniform.png", dpi=300, bbox_inches='tight')
# plt.show()



# import matplotlib.pyplot as plt

# # 数据来源：基于您提供的最终统计表（按异常大类汇总）
# error_data = {
#     "TypeError": 3354,
#     "AttributeError": 3163,
#     "AssertionError": 3003,
#     "UnknownError": 1233,
#     "NameError": 437,
#     "RuntimeError": 410,
#     "NotImplementedError": 290,
#     "FrozenInstanceError": 175,
#     "KeyError": 169,
#     "ValueError": 89,
#     "FileNotFoundError": 75,
#     "UnknownMessageError": 58,
#     "InvalidMessageError": 57,
#     "OSError": 55,
#     "DeprecationWarning": 55,
#     "ImportError": 46,
#     "IndexError": 42,
#     "ModuleNotFoundError": 39,
#     "NoAppException": 35,
#     "NoArgsIsHelpError": 28,
#     "InvalidStateError": 20,
#     "JSONDecodeError": 13,
#     "ChildProcessError": 13,
#     "UnsupportedFormatException": 12,
#     "BadYieldError": 11,
#     "UnboundLocalError": 10,
#     "UserWarning": 10,
#     "SystemExit": 9,
#     "RecursionError": 8,
#     "HTTPClientError": 7,
#     "ReferenceError": 6,
#     "LookupError": 5,
#     "PytestUnraisableExceptionWarning": 3,
#     "NotOleFileError": 3,
#     "UnicodeEncodeError": 3,
#     "PicklingError": 3,
#     "MissingSectionHeaderError": 3,
#     "AstroidSyntaxError": 2,
#     "TokenError": 2,
#     "UnicodeDecodeError": 2,
#     "InvalidSpecError": 1,
#     "CouldntDecodeError": 1,
#     "ExpatError": 1,
#     "FileConversionException": 1,
#     "HTTPError": 1,
#     "InvalidReporterError": 1,
#     "InferenceError": 1,
#     "GitCommandError": 1,
#     "ZeroDivisionError": 1,
#     "CalledProcessError": 1,
#     "PermissionError": 1,
# }

# total = sum(error_data.values())

# # 将占比小于 1% 的类别合并为 "Other"
# threshold = 0.01 * total
# main_data = {}
# other_count = 0

# for name, count in error_data.items():
#     if count >= threshold:
#         main_data[name] = count
#     else:
#         other_count += count

# if other_count > 0:
#     main_data["Other (<1% each)"] = other_count

# # 绘制饼图
# plt.figure(figsize=(14, 10))
# colors = plt.cm.tab20.colors  # 使用 tab20 颜色映射

# # 按数量降序排列，使图例更清晰
# sorted_items = sorted(main_data.items(), key=lambda x: x[1], reverse=True)
# labels = [f"{name}\n({count:,}, {count/total:.1%})" for name, count in sorted_items]
# sizes = [count for _, count in sorted_items]

# wedges, texts, autotexts = plt.pie(
#     sizes,
#     labels=labels,
#     autopct='',
#     startangle=140,
#     colors=colors[:len(sizes)],
#     textprops={'fontsize': 9}
# )

# plt.title(f"测试异常类型分布 (总计 {total:,} 次)", fontsize=16, pad=20)
# plt.axis('equal')  # 保持正圆
# plt.savefig("test_results/error_distribution_python.png", dpi=300, bbox_inches='tight')
# # 调整布局防止标签重叠
# plt.tight_layout()
# plt.show()


# import matplotlib.pyplot as plt
# plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC']
# # plt.rcParams['font.sans-serif'] = ['SimHei']  # 黑体（Windows 常用）
# # plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
# # 数据处理保持不变
# total = sum(error_data.values())
# threshold = 0.01 * total
# main_data = {}
# other_count = 0
# for name, count in error_data.items():
#     if count >= threshold:
#         main_data[name] = count
#     else:
#         other_count += count
# if other_count > 0:
#     main_data["其他 (<1% 每类)"] = other_count  # 中文化

# # 绘图
# plt.figure(figsize=(10, 8))  # 图像稍微小一点
# colors = plt.cm.tab20.colors

# sorted_items = sorted(main_data.items(), key=lambda x: x[1], reverse=True)
# labels = [f"{name}\n({count:,}, {count/total:.1%})" for name, count in sorted_items]
# sizes = [count for _, count in sorted_items]

# wedges, texts, autotexts = plt.pie(
#     sizes,
#     labels=labels,
#     autopct='',
#     startangle=140,
#     colors=colors[:len(sizes)],
#     textprops={'fontsize': 12}  # 字体大一点
# )

# plt.title(f"Python 测试异常类型分布 (总计 {total:,} 次)", fontsize=18, pad=20)  # 中文标题，字号大一点
# plt.axis('equal')
# plt.tight_layout()
# plt.savefig("test_results/error_distribution_python.png", dpi=300, bbox_inches='tight')
# plt.show()




import json
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
import os

# ===== 1. 字体设置 =====
matplotlib.use('Agg')  # 无需 GUI，直接保存 PNG
font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
my_font = fm.FontProperties(fname=font_path)

# ===== 2. 数据准备 =====
base_dir = Path("test_results")
languages = [d.name for d in base_dir.iterdir() if d.is_dir()]

language_avg_compile_rate = {}
model_compile_rates = {}

for lang in languages:
    json_path = base_dir / lang / "aggregated_results.json"
    if not json_path.exists():
        print(f"[Warning] Missing file: {json_path}")
        continue
    print(f"Processing {json_path}...")
    with open(json_path, "r") as f:
        data = json.load(f)

    by_model = data["by_model"]
    total_compile_pass = 0
    total_total = 0

    for model, stats in by_model.items():
        total_compile_pass += stats["filtered_stats_function_covered_lines"]
        total_total += stats["filtered_stats_function_total_lines"]

        if model not in model_compile_rates:
            model_compile_rates[model] = {}
        model_compile_rates[model][lang] = stats["filtered_stats_function_covered_lines"] / stats["filtered_stats_function_total_lines"]

    language_avg_compile_rate[lang] = total_compile_pass / total_total

# ===== 3. 排序横坐标 =====
sorted_langs = sorted(language_avg_compile_rate.items(), key=lambda x: x[1], reverse=True)
langs = [x[0] for x in sorted_langs]
avg_rates = [x[1] for x in sorted_langs]

# ===== 4. 绘图 =====
fig, ax = plt.subplots(figsize=(10, 6))

# 柱状图：语言平均编译通过率
bars = ax.bar(langs, avg_rates, color="lightblue", label="平均行覆盖率")

# 折线图：不同模型在各语言的编译通过率
markers = ['o', 's', '^', 'D', 'v']  # 支持多模型
for i, (model, rates) in enumerate(model_compile_rates.items()):
    y_values = [rates.get(lang, 0) for lang in langs]
    ax.plot(langs, y_values, marker=markers[i % len(markers)], label=model)

# ===== 5. 图表美化 =====
ax.set_ylabel("行覆盖率", fontproperties=my_font)
# ax.set_title("不同语言的平均编译通过率及模型对比", fontproperties=my_font)
ax.set_ylim(0, 1)
ax.legend(prop=my_font)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 显示百分比
ax.set_yticks(np.linspace(0, 1, 11))
ax.set_yticklabels([f"{int(y*100)}%" for y in np.linspace(0, 1, 11)], fontproperties=my_font)

# 保存图像
os.makedirs("test_results", exist_ok=True)
plt.tight_layout()
plt.savefig("test_results/language_func_line_cov.png", dpi=300, bbox_inches='tight')
plt.close(fig)

print("图像已保存：test_results/language_execute_rates.png")
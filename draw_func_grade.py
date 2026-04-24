# import os
# import json
# import csv

# bins = [(0, 10), (11, 20), (21, 40), (41, 80), (81, float("inf"))]
# bin_labels = ["0-10", "11-20", "21-40", "41-80", ">80"]

# # 初始化统计数据结构
# stats = {label: {"covered_lines": 0, "total_lines": 0} for label in bin_labels}

# for root, dirs, files in os.walk("test_results/javascript"):
#     if "fix" in root:
#         continue
#     for file in files:
#         if "summary.json" in file:
#             with open(os.path.join(root, file), "r", encoding="utf-8") as f:
#                 data = json.load(f)
                
#             for func, cov in data.get("coverage", {}).get("function", {}).items():
#                 total = cov.get("total_lines", 0)
#                 covered = cov.get("covered_lines", 0)
#                 # 找到对应等级
#                 for (low, high), label in zip(bins, bin_labels):
#                     if low <= total <= high:
#                         stats[label]["covered_lines"] += covered
#                         stats[label]["total_lines"] += total
#                         break

# output_file = "coverage_by_function_size_js.csv"
# with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerow(["Function_Size", "Covered_Line", "Total_Line", "Coverage(%)"])
#     for label in bin_labels:
#         covered = stats[label]["covered_lines"]
#         total = stats[label]["total_lines"]
#         coverage = (covered / total * 100) if total > 0 else 0
#         writer.writerow([label, covered, total, f"{coverage:.2f}"])



import matplotlib.pyplot as plt
import pandas as pd

# CSV 文件路径
csv_files = {
    "Python": "coverage_by_function_size.csv",
    "Java": "coverage_by_function_size_java.csv",
    "JavaScript": "coverage_by_function_size_js.csv"
}

# 初始化画布
plt.figure(figsize=(8, 5))

for lang, file in csv_files.items():
    df = pd.read_csv(file)
    # 用 Function_Size 作为 x，Coverage(%) 作为 y
    plt.plot(df["Function_Size"], df["Coverage(%)"], marker='o', label=lang)

# 美化图表
# plt.title("Function Coverage by Size Across Languages")
plt.xlabel("Function Size (Lines)")
plt.ylabel("Coverage (%)")
plt.ylim(0, 100)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()

# 保存图片
plt.savefig("coverage_by_size.png", dpi=300, bbox_inches='tight')
plt.show()
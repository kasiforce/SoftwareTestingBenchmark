import json
from collections import Counter
import csv

# JSON 文件路径
file_path = "error_analysis_results.json"

# 读取 JSON
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 提取 semantic_category
categories = []
for item in data:
    # 先把 analysis_result 解析成字典
    analysis_result = json.loads(item["analysis_result"])
    categories.append(analysis_result.get("semantic_category"))

# 统计数量
category_counts = Counter(categories)

# 输出结果
for category, count in category_counts.items():
    print(f"{category}: {count}")

# 保存到 CSV
with open("error_semantic_category_counts.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Semantic_Category", "Count"])
    for category, count in category_counts.items():
        writer.writerow([category, count])

print("统计结果已保存到 semantic_category_counts.csv")
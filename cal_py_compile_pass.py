# import json
# import os
# import sys
# from collections import defaultdict


# def count_compile_pass(directory: str) -> dict:
#     # 第一遍：收集数据，获取每个模型的 items 信息以及全局最大轮次
#     model_items = defaultdict(list)  # {model: [item_info, ...]}
#     overall_max_round = -1

#     for filename in os.listdir(directory):
#         if not filename.endswith(".json"):
#             continue
#         stem = filename[:-5]
#         if "_" not in stem:
#             print(f"跳过无法提取模型名的文件: {filename}")
#             continue
#         model_name = stem.rsplit("_", 1)[-1]

#         filepath = os.path.join(directory, filename)
#         try:
#             with open(filepath, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#         except (json.JSONDecodeError, IOError) as e:
#             print(f"读取或解析文件失败 {filepath}: {e}")
#             continue

#         items = data.get("items", [])
#         if not isinstance(items, list):
#             items = [items]

#         for item in items:
#             repair_history = item.get("repair_history", [])
#             if not repair_history:
#                 continue

#             # 提取每个历史记录条目的 round
#             rounds = []
#             passes = []
#             for entry in repair_history:
#                 r = entry.get("round")
#                 if r is not None:
#                     rounds.append(r)
#                     passes.append(entry.get("stage") in ("run", "done"))
#                 else:
#                     # 无 round 的条目，忽略
#                     pass

#             if not rounds:
#                 continue

#             # 最后一条有 round 的记录，视为该 item 的最终结果
#             final_passed = passes[-1]
#             last_round = rounds[-1]

#             overall_max_round = max(overall_max_round, max(rounds) if rounds else -1)

#             model_items[model_name].append({
#                 "rounds": rounds,
#                 "passes": passes,
#                 "final_passed": final_passed,
#                 "last_round": last_round
#             })

#     if overall_max_round == -1:
#         return {}  # 没有任何有效数据

#     # 第二遍：按轮次统计
#     result = defaultdict(lambda: defaultdict(int))

#     for model, items_info in model_items.items():
#         # 对每个可能的 round 进行统计
#         for r in range(overall_max_round + 1):
#             count = 0
#             for info in items_info:
#                 # 该 item 在这个轮次是否有记录
#                 if r in info["rounds"]:
#                     idx = info["rounds"].index(r)
#                     if info["passes"][idx]:
#                         count += 1
#                 else:
#                     # 没有该轮记录，但最终通过且最后轮次小于当前轮次，视为通过
#                     if info["final_passed"] and info["last_round"] < r:
#                         count += 1
#             # 如果该轮次有通过数据就存储（即使为0也可以保留，但按需可去掉全0轮次）
#             if count > 0:
#                 result[model][f"round {r}"] = count

#     # 转为普通 dict
#     return {model: dict(rounds) for model, rounds in result.items()}


# if __name__ == "__main__":
#     # if len(sys.argv) != 2:
#     #     print("用法: python script.py <目标目录>")
#     #     sys.exit(1)

#     target_dir = "tests/test_gen/python/fix_tornado"
#     if not os.path.isdir(target_dir):
#         print(f"错误: {target_dir} 不是有效的目录")
#         sys.exit(1)

#     stats = count_compile_pass(target_dir)
#     print(json.dumps(stats, indent=2, ensure_ascii=False))



import json
from collections import defaultdict

# 硬编码的四个统计数据块
data1 = {
    "gpt5nano": {"round 0": 127, "round 1": 136, "round 2": 135, "round 3": 136},
    "glm-4.7":  {"round 0": 123, "round 1": 133, "round 2": 134, "round 3": 135},
    "DSv3.2":   {"round 0": 123, "round 1": 133, "round 2": 134, "round 3": 134},
    "gpt4o":    {"round 0": 123, "round 1": 130, "round 2": 134, "round 3": 133},
    "qwen":     {"round 0": 132, "round 1": 135, "round 2": 136, "round 3": 134}
}

data2 = {
    "gpt5nano": {"round 0": 83, "round 1": 91, "round 2": 91, "round 3": 92},
    "qwen":     {"round 0": 52, "round 1": 71, "round 2": 79, "round 3": 78},
    "gpt4o":    {"round 0": 14, "round 1": 73, "round 2": 83, "round 3": 89},
    "glm-4.7":  {"round 0": 29, "round 1": 53, "round 2": 73, "round 3": 80},
    "DSv3.2":   {"round 0": 44, "round 1": 80, "round 2": 88, "round 3": 84}
}

data3 = {
    "glm-4.7":  {"round 0": 312, "round 1": 408, "round 2": 408, "round 3": 415},
    "gpt4o":    {"round 0": 344, "round 1": 400, "round 2": 412, "round 3": 421},
    "DSv3.2":   {"round 0": 358, "round 1": 409, "round 2": 422, "round 3": 419},
    "gpt5nano": {"round 0": 399, "round 1": 425, "round 2": 429, "round 3": 430},
    "qwen":     {"round 0": 374, "round 1": 416, "round 2": 424, "round 3": 424}
}

data4 = {
    "gpt4o":    {"round 0": 89, "round 1": 98, "round 2": 99, "round 3": 99},
    "DSv3.2":   {"round 0": 89, "round 1": 97, "round 2": 102, "round 3": 97},
    "glm-4.7":  {"round 0": 80, "round 1": 95, "round 2": 99, "round 3": 100},
    "gpt5nano": {"round 0": 97, "round 1": 101, "round 2": 102, "round 3": 104},
    "qwen":     {"round 0": 88, "round 1": 102, "round 2": 100, "round 3": 101}
}

# 合并数据
merged = defaultdict(lambda: defaultdict(int))
for data in (data1, data2, data3, data4):
    for model, rounds in data.items():
        for round_key, count in rounds.items():
            merged[model][round_key] += count

# 排序并输出
result = {}
for model, rounds in merged.items():
    sorted_rounds = sorted(rounds.items(), key=lambda x: int(x[0].split()[1]))
    result[model] = {k: v for k, v in sorted_rounds}

print(json.dumps(result, indent=2, ensure_ascii=False))
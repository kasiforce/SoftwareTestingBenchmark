import json
import matplotlib.pyplot as plt
import os

# 合并后的数据
# data = {
#     "gpt5nano": {"round 0": 706, "round 1": 753, "round 2": 757, "round 3": 762},
#     "glm-4.7":  {"round 0": 544, "round 1": 689, "round 2": 714, "round 3": 730},
#     "DSv3.2":   {"round 0": 614, "round 1": 719, "round 2": 746, "round 3": 734},
#     "gpt4o":    {"round 0": 570, "round 1": 701, "round 2": 728, "round 3": 742},
#     "qwen":     {"round 0": 646, "round 1": 724, "round 2": 739, "round 3": 737}
# }
data = {
  "gpt4o": {
    "round 0": 108,
    "round 1": 168,
    "round 2": 197,
    "round 3": 216
  },
  "gpt5nano": {
    "round 0": 174,
    "round 1": 287,
    "round 2": 319,
    "round 3": 333
  },
  "DSv3.2": {
    "round 0": 95,
    "round 1": 176,
    "round 2": 220,
    "round 3": 253
  },
  "glm-4.7": {
    "round 0": 99,
    "round 1": 174,
    "round 2": 215,
    "round 3": 243
  },
  "qwen": {
    "round 0": 119,
    "round 1": 205,
    "round 2": 246,
    "round 3": 278
  }
}

# 总测试数
TOTAL = 384

# 提取轮次标签（假设所有模型轮次相同，排序）
rounds = sorted(data[next(iter(data))].keys(), key=lambda x: int(x.split()[1]))

plt.figure(figsize=(8, 5))

for model, counts in data.items():
    # 按轮次顺序取值，并除以 TOTAL 得到通过率
    rates = [counts[r] / TOTAL for r in rounds]
    plt.plot(rounds, rates, marker='o', label=model)

plt.xlabel('Round')
plt.ylabel('CompR')
# plt.title('Test Pass Rate by Model and Round')
plt.legend()
plt.grid(True)

# 保存图像
os.makedirs("test_results", exist_ok=True)
plt.tight_layout()
plt.savefig("test_results/java_fix_compile.png", dpi=300, bbox_inches='tight')
# plt.close(fig)
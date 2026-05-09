import json
import matplotlib.pyplot as plt
import os

# 合并后的数据
data = {
    "gpt5nano": {"round 0": 706, "round 1": 753, "round 2": 757, "round 3": 762},
    "glm-4.7":  {"round 0": 544, "round 1": 689, "round 2": 714, "round 3": 730},
    "DSv3.2":   {"round 0": 614, "round 1": 719, "round 2": 746, "round 3": 734},
    "gpt4o":    {"round 0": 570, "round 1": 701, "round 2": 728, "round 3": 742},
    "qwen":     {"round 0": 646, "round 1": 724, "round 2": 739, "round 3": 737}
}

# 总测试数
TOTAL = 768

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
plt.savefig("test_results/python_fix_compile.png", dpi=300, bbox_inches='tight')
# plt.close(fig)
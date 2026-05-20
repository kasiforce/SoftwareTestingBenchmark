import xml.etree.ElementTree as ET
from collections import defaultdict

xml_file = "test_results/java/commons-cli/junit4_glm-4.7_mut_fix/tem.xml" 
equivalent_mutants = 0

# -------- 临时包装根元素 --------
with open(xml_file, 'r', encoding='utf-8') as f:
    xml_content = "<mutations>\n" + f.read() + "\n</mutations>"

root = ET.fromstring(xml_content)

total_mutants = 0
test_kill_count = defaultdict(int)

for mutation in root.findall('mutation'):
    total_mutants += 1
    status = mutation.get('status')
    if status == 'KILLED':
        killing_test = mutation.find('killingTest')
        if killing_test is not None and killing_test.text:
            test_name = killing_test.text.strip()
            test_kill_count[test_name] += 1

N = len(test_kill_count)

denominator = N * (total_mutants - equivalent_mutants)
ms_per_test = sum(test_kill_count.values()) / denominator if denominator > 0 else 0

print(f"Sum of killed mutants: {sum(test_kill_count.values())}")

print(f"Total mutants: {total_mutants}")
print(f"Equivalent mutants: {equivalent_mutants}")
print(f"Effective tests (killed at least one mutant): {N}")
print(f"MS per-test: {ms_per_test:.4f}")

print("\nEach test kills:")
for test, count in test_kill_count.items():
    print(f"{test}: {count}")
# import xml.etree.ElementTree as ET
# from collections import defaultdict

# # -------- 配置 --------
# xml_file = "test_results/java/commons-cli/junit4_glm-4.7_mut_fix/tem.xml"       # 替换为你的 PIT 输出路径
# equivalent_mutants = 0           # 如果知道等价变异体数量可以填入，否则保持 0

# # -------- 解析 XML --------
# tree = ET.parse(xml_file)
# root = tree.getroot()

# total_mutants = 0
# test_kill_count = defaultdict(int)  # 每条测试杀死的变异体数量

# for mutation in root.findall('mutation'):
#     total_mutants += 1
#     status = mutation.get('status')
#     # 只统计被杀死的变异体
#     if status == 'KILLED':
#         killing_test = mutation.find('killingTest')
#         if killing_test is not None and killing_test.text:
#             test_name = killing_test.text.strip()
#             test_kill_count[test_name] += 1

# # 有效测试用例数量 N（至少杀死一个变异体的测试）
# N = len(test_kill_count)

# # 避免除零
# denominator = N * (total_mutants - equivalent_mutants)
# if denominator <= 0:
#     ms_per_test = 0
# else:
#     ms_per_test = sum(test_kill_count.values()) / denominator

# # -------- 输出 --------
# print(f"Total mutants: {total_mutants}")
# print(f"Equivalent mutants: {equivalent_mutants}")
# print(f"Effective tests (killed at least one mutant): {N}")
# print(f"MS per-test: {ms_per_test:.4f}")

# print("\nEach test kills:")
# for test, count in test_kill_count.items():
#     print(f"{test}: {count}")
import json
import xml.etree.ElementTree as ET
import os

# def cal_mut(data_path, mut_path):
#     mut_path1 = None
#     for filename in os.listdir(mut_path):
#         if filename.endswith("_pitest_mutations.xml"):
#             mut_path1 = os.path.join(mut_path, filename)
#     if mut_path1 is None:
#         print(f"未找到突变测试结果 XML 文件，路径: {mut_path}")
#         return
#     # ----------------- 解析 JSON -----------------
#     with open(data_path, 'r', encoding='utf-8') as f:
#         json_data = json.load(f)
#     data = json_data['items']
#     json_src_files = [item['src_file'] for item in data]

#     # ----------------- 解析 XML -----------------
#     tree = ET.parse(mut_path1)
#     root = tree.getroot()

#     total_matched = 0        # 匹配上的突变体总数
#     total_detected = 0       # 被杀死的数量
#     matched_source_files = set()  # 匹配到哪些源文件（文件名）

#     for mutation in root.findall('mutation'):
#         mutated_class = mutation.findtext('mutatedClass')
#         # 将类名转为路径，比如 org.a.b.C -> org/a/b/C.java
#         class_path = mutated_class.replace('.', '/') + '.java'

#         # 检查是否在 JSON 的任意 src_file 中出现（以该路径结尾）
#         if any(json_path.endswith(class_path) for json_path in json_src_files):
#             total_matched += 1
#             matched_source_files.add(mutation.findtext('sourceFile'))

#             # 判断是否被杀死
#             if mutation.get('detected') == 'true':
#                 total_detected += 1

#     # ----------------- 输出统计 -----------------
#     print(f"JSON 中包含的源文件数量: {len(json_src_files)}")
#     print(f"匹配上的突变体总数: {total_matched}")
#     print(f"被杀死的突变体数量: {total_detected}")
#     print(f"匹配上的源文件（去重）: {matched_source_files}")

#     if total_matched > 0:
#         print(f"杀死率: {total_detected / total_matched * 100:.1f}%")
#     else:
#         print("未匹配到任何突变体")

#     return {"total_mut": total_matched,
#             "killed": total_detected}




def cal_mut(data_path, mut_path):
    mut_path1 = None
    for filename in os.listdir(mut_path):
        if filename.endswith("_pitest_mutations.xml"):
            mut_path1 = os.path.join(mut_path, filename)
    if mut_path1 is None:
        print(f"未找到突变测试结果 XML 文件，路径: {mut_path}")
        return

    # ----------------- 解析 JSON -----------------
    with open(data_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    data = json_data['items']
    # data = json_data

    # 构建目标方法集合
    target_methods = set()
    for item in data:
        method_name = item['name']
        src_file = item['src_file']

        if src_file.startswith("src/main/java/"):
            class_path = src_file[len("src/main/java/"):]
        elif src_file.startswith("src/"):
            class_path = src_file[4:]
        else:
            class_path = src_file

        if class_path.endswith(".java"):
            class_path = class_path[:-5]
        class_full_name = class_path.replace('/', '.')

        target_methods.add((class_full_name, method_name))

    # ----------------- 解析 XML -----------------
    tree = ET.parse(mut_path1)
    root = tree.getroot()

    total_matched = 0
    total_detected = 0
    matched_source_files = set()

    # 新增：状态统计字典
    status_counts = {
        'KILLED': 0,
        'SURVIVED': 0,
        'NO_COVERAGE': 0
    }

    method_stats = {}

    for mutation in root.findall('mutation'):
        mutated_class = mutation.findtext('mutatedClass')
        mutated_method = mutation.findtext('mutatedMethod')

        if (mutated_class, mutated_method) in target_methods:
            total_matched += 1
            source_file = mutation.findtext('sourceFile')
            matched_source_files.add(source_file)

            # 获取 status 属性并统计
            status = mutation.get('status')          # 例如 "KILLED", "SURVIVED", "NO_COVERAGE"
            if status in status_counts:
                status_counts[status] += 1
            else:
                # 若出现其他未知状态，可自行扩展
                status_counts[status] = status_counts.get(status, 0) + 1

            # 判断被杀死（依然用 detected 或 status）
            if mutation.get('detected') == 'true':
                total_detected += 1

            # 记录每个方法统计（可选）
            key = (mutated_class, mutated_method)
            if key not in method_stats:
                method_stats[key] = {'total': 0, 'killed': 0}
            method_stats[key]['total'] += 1
            if mutation.get('detected') == 'true':
                method_stats[key]['killed'] += 1

    # ----------------- 输出统计 -----------------
    print(f"JSON 中包含的目标方法数量: {len(target_methods)}")
    print(f"匹配上的突变体总数（仅目标方法）: {total_matched}")
    print(f"被杀死的突变体数量: {total_detected}")
    print(f"涉及到的源文件（去重）: {matched_source_files}")

    # 新增：输出状态分布
    print("\n突变体状态分布：")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

    print("\n每个目标方法的变异分数：")
    for (cls, method), stats in method_stats.items():
        kill_rate = (stats['killed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {cls}.{method}: 突变体 {stats['total']}, 杀死 {stats['killed']}, 杀死率 {kill_rate:.1f}%")

    if total_matched > 0:
        overall_rate = total_detected / total_matched * 100
        print(f"\n总体杀死率（目标方法）: {overall_rate:.1f}%")
    else:
        print("未匹配到任何目标方法的突变体")

    # 返回值也可以带上状态分布
    return {
        "total_mut": total_matched,
        "killed": total_detected,
        "status_counts": status_counts
    }


# cal_mut("tests/test_gen/java/commons-cli/commons-cli_lite_junit4_CodeLlama-7b.json","test_results/java/commons-cli/junit4_gpt4o_mut_fix")
# import json
# import xml.etree.ElementTree as ET
# import os

# # ----------------- 解析 JSON -----------------
# with open('tests/test_gen/java/commons-jxpath/commons-jxpath_lite_junit4_CodeLlama-7b.json', 'r', encoding='utf-8') as f:
#     json_data = json.load(f)

# # 收集所有出现在 JSON 中的源文件（相对路径，带前缀 src/main/java/）
# json_src_files = [item['src_file'] for item in json_data]

# # ----------------- 解析 XML -----------------
# tree = ET.parse('test_results/java/commons-jxpath/junit4_CodeLlama-7b_mut/target_pit-reports_pitest_mutations.xml')
# root = tree.getroot()

# matching_mutations = []      # 存放匹配的 mutation 元素
# matching_source_files = set()  # 统计匹配到的源文件（去重）

# for mutation in root.findall('mutation'):
#     source_file = mutation.findtext('sourceFile')  # 文件名
#     mutated_class = mutation.findtext('mutatedClass')  # 全限定类名

#     # 将类名转换为相对路径字符串，例如：
#     # org.apache.commons.jxpath.ri.parser.XPathParserTokenManager
#     # -> org/apache/commons/jxpath/ri/parser/XPathParserTokenManager.java
#     class_path = mutated_class.replace('.', '/') + '.java'

#     # 检查是否与 JSON 中任意一个 src_file 匹配（以该路径结尾）
#     matched = any(json_path.endswith(class_path) for json_path in json_src_files)

#     # 或者更简单的按文件名匹配（可能不准确，慎用）：
#     # matched = any(os.path.basename(json_path) == source_file for json_path in json_src_files)

#     if matched:
#         matching_mutations.append(mutation)
#         matching_source_files.add(source_file)

# # ----------------- 输出结果 -----------------
# print(f"JSON 中的源码文件数: {len(json_src_files)}")
# print(f"匹配上的 mutation 记录数: {len(matching_mutations)}")
# print(f"匹配上的源文件（去重）: {matching_source_files}")
# for m in matching_mutations:
#     print(f"  - {m.findtext('mutatedClass')} ({m.findtext('sourceFile')}:{m.findtext('lineNumber')})")
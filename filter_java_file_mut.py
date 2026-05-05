import json
import xml.etree.ElementTree as ET
import os

def cal_mut(data_path, mut_path):
    for filename in os.listdir(mut_path):
        if filename.endswith("_pitest_mutations.xml"):
            mut_path = os.path.join(mut_path, filename)
    # ----------------- 解析 JSON -----------------
    with open(data_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    json_src_files = [item['src_file'] for item in json_data]

    # ----------------- 解析 XML -----------------
    tree = ET.parse(mut_path)
    root = tree.getroot()

    total_matched = 0        # 匹配上的突变体总数
    total_detected = 0       # 被杀死的数量
    matched_source_files = set()  # 匹配到哪些源文件（文件名）

    for mutation in root.findall('mutation'):
        mutated_class = mutation.findtext('mutatedClass')
        # 将类名转为路径，比如 org.a.b.C -> org/a/b/C.java
        class_path = mutated_class.replace('.', '/') + '.java'

        # 检查是否在 JSON 的任意 src_file 中出现（以该路径结尾）
        if any(json_path.endswith(class_path) for json_path in json_src_files):
            total_matched += 1
            matched_source_files.add(mutation.findtext('sourceFile'))

            # 判断是否被杀死
            if mutation.get('detected') == 'true':
                total_detected += 1

    # ----------------- 输出统计 -----------------
    print(f"JSON 中包含的源文件数量: {len(json_src_files)}")
    print(f"匹配上的突变体总数: {total_matched}")
    print(f"被杀死的突变体数量: {total_detected}")
    print(f"匹配上的源文件（去重）: {matched_source_files}")

    if total_matched > 0:
        print(f"杀死率: {total_detected / total_matched * 100:.1f}%")
    else:
        print("未匹配到任何突变体")

    return {"total_mut": total_matched,
            "killed": total_detected}


cal_mut("tests/test_gen/java/commons-cli/commons-cli_lite_junit4_CodeLlama-7b.json","test_results/java/commons-cli/junit4_CodeLlama-7b_mut")
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
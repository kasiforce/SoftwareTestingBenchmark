import os
import json
import xml.etree.ElementTree as ET

def calculate_test_pass_rate(report_dir):
    """
    解析 report_dir 下的所有 JUnit XML 文件，统计 errors 总和为 0 的 XML 文件个数。
    """

    if not os.path.exists(report_dir):
        return 0, 0, 0

    pass_rate = 0 # sum(pass case/total case)/task number
    pass_rate1 = 0 # 只要有一个测试用例成功就算成功
    excute_pass = 0

    for filename in os.listdir(report_dir):
        if filename.endswith(".xml"):
            try:
                
                total = 0
                passed = 0
                failures = 0
                errors = 0
                skipped = 0
                errors_total = 0

                tree = ET.parse(os.path.join(report_dir, filename))
                root = tree.getroot()
                # 有些报告根节点是 testsuite，有些是 testsuites
                suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
                
                for suite in suites:
                    errors_total += int(suite.attrib.get('errors', 0))
                    total += int(suite.attrib.get('tests', 0))
                    failures += int(suite.attrib.get('failures', 0))
                    errors += int(suite.attrib.get('errors', 0))
                    skipped += int(suite.attrib.get('skipped', 0))
                passed = total - failures - errors - skipped
                if passed > 0:
                    pass_rate1 += 1
                pass_rate += (passed / total) if total > 0 else 0
                if errors_total == 0:
                    excute_pass += 1

            except Exception as e:
                print(f"解析 {os.path.join(report_dir, filename)} 失败: {e}")

    return excute_pass, pass_rate, pass_rate1

def update_summary_json(report_dir, excute_pass, pass_rate, pass_rate1):
    """
    在 reports 的父目录下写入或更新 summary.json 文件。
    """
    parent_dir = os.path.dirname(report_dir)  # reports 的父目录
    summary_file = os.path.join(parent_dir, "summary.json")

    data = {}
    if os.path.exists(summary_file):
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取 {summary_file} 失败，将创建新文件: {e}")

    data["excute_pass"] = excute_pass
    data["pass_rate"] = pass_rate
    data["pass_rate1"] = pass_rate1

    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"已更新 {summary_file}")
    except IOError as e:
        print(f"写入 {summary_file} 失败: {e}")

def main(root_dir):
    """
    遍历 root_dir，找到所有名为 reports 的目录，对每个目录处理并更新 summary.json。
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if os.path.basename(dirpath) == "reports":
            print(f"处理目录: {dirpath}")
            excute_pass, pass_rate, pass_rate1 = calculate_test_pass_rate(dirpath)
            update_summary_json(dirpath, excute_pass, pass_rate, pass_rate1)

if __name__ == "__main__":
    # 请将此处替换为实际根目录路径
    root_directory = "test_results/java"
    main(root_directory)
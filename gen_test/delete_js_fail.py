import json
import re
import sys
from pathlib import Path


def escape_regex(text):
    return re.escape(text)


def skip_test_in_file(test_file, test_title):
    """在测试文件内将匹配的 test/it 改成 test.skip/it.skip（保留原有功能）"""
    path = Path(test_file)
    if not path.exists():
        print(f"[WARN] 文件不存在: {test_file}")
        return False

    content = path.read_text(encoding="utf-8")
    patterns = [
        rf'test\s*\(\s*[\'"]{escape_regex(test_title)}[\'"]',
        rf'it\s*\(\s*[\'"]{escape_regex(test_title)}[\'"]',
    ]

    replaced = False
    for pattern in patterns:
        new_content = re.sub(
            pattern,
            lambda m: m.group(0).replace("test(", "test.skip(").replace("it(", "it.skip("),
            content,
            count=1,
        )
        if new_content != content:
            content = new_content
            replaced = True
            break

    if replaced:
        path.write_text(content, encoding="utf-8")
        print(f"[SKIPPED] {test_title}")
    else:
        print(f"[NOT FOUND] {test_title}")
    return replaced


def delete_test_file(test_file):
    """直接删除整个测试文件"""
    path = Path(test_file)
    if path.exists():
        path.unlink()
        print(f"[DELETED] {test_file}")
        return True
    else:
        print(f"[WARN] 文件不存在，无需删除: {test_file}")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("python delete_failed.py result.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_failed_cases = 0
    total_skipped_cases = 0
    total_deleted_files = 0

    for suite in data["testResults"]:
        test_file = suite["name"]

        # 情况1：整个套件编译失败（assertionResults 为空）
        if suite["status"] == "failed" and len(suite.get("assertionResults", [])) == 0:
            print(f"[FAILED SUITE] {test_file} (编译失败，将直接删除文件)")
            if delete_test_file(test_file):
                total_deleted_files += 1
            continue  # 不用再遍历用例了

        # 情况2：单个用例失败（可选用 skip 或删除，这里保留 skip 行为）
        for case in suite.get("assertionResults", []):
            if case["status"] != "failed":
                continue
            total_failed_cases += 1
            title = case["title"]
            ok = skip_test_in_file(test_file, title)
            if ok:
                total_skipped_cases += 1

    print()
    print("===================================")
    print(f"失败用例数: {total_failed_cases}")
    print(f"skip 用例数: {total_skipped_cases}")
    print(f"删除文件数: {total_deleted_files}")
    print("===================================")


if __name__ == "__main__":
    main()
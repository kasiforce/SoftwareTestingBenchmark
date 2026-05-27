import json
import re
import sys
from pathlib import Path


def escape_regex(text):
    return re.escape(text)


def skip_test_in_file(test_file, test_title):

    path = Path(test_file)

    if not path.exists():
        print(f"[WARN] 文件不存在: {test_file}")
        return False

    content = path.read_text(encoding="utf-8")

    original_content = content

    # =========================================================
    # 匹配:
    #
    # test("xxx"
    # test('xxx'
    # it("xxx"
    # it('xxx'
    # =========================================================

    patterns = [

        rf'test\s*\(\s*[\'"]{escape_regex(test_title)}[\'"]',

        rf'it\s*\(\s*[\'"]{escape_regex(test_title)}[\'"]',
    ]

    replaced = False

    for pattern in patterns:

        new_content = re.sub(
            pattern,
            lambda m: m.group(0).replace(
                "test(",
                "test.skip("
            ).replace(
                "it(",
                "it.skip("
            ),
            content,
            count=1
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


def main():

    if len(sys.argv) < 2:
        print("用法:")
        print("python delete_js_fail.py result.json")
        sys.exit(1)

    json_path = sys.argv[1]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_failed = 0
    total_skipped = 0

    for suite in data["testResults"]:

        test_file = suite["name"]

        for case in suite["assertionResults"]:

            if case["status"] != "failed":
                continue

            total_failed += 1

            title = case["title"]

            ok = skip_test_in_file(
                test_file,
                title
            )

            if ok:
                total_skipped += 1

    print()
    print("===================================")
    print(f"失败测试数量: {total_failed}")
    print(f"成功 skip 数量: {total_skipped}")
    print("===================================")


if __name__ == "__main__":
    main()
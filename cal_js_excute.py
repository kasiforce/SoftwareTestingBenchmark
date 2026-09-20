# #!/usr/bin/env python3
# """
# 处理 Jest 生成的 JSON 报告（格式如示例），统计：
# - excute_pass: 包含非断言错误（运行时错误）的测试文件数
# - test_pass:   至少有一个通过用例的测试文件数
# - testcase_pass_rate: 每个文件的通过率（%）之和（累加）
# 结果写入同目录下的 summary_filtered.json
# """

# import json
# import os
# import sys
# from pathlib import Path


# def is_assertion_failure(failure_messages):
#     """判断失败消息是否为断言失败（Jest 断言通常以 'expect(' 开头）"""
#     if not failure_messages:
#         return False
#     msg = failure_messages[0] if failure_messages else ""
#     return msg.strip().startswith("Error: expect(")


# def process_jest_report(report_path):
#     """处理单个 Jest 报告文件，返回统计结果（按文件累加通过率）"""
#     try:
#         with open(report_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#     except (json.JSONDecodeError, IOError) as e:
#         print(f"  警告：无法读取或解析 {report_path} - {e}")
#         return None

#     test_results = data.get("testResults", [])
#     if not test_results:
#         print(f"  警告：{report_path} 中没有 testResults")
#         return {"excute_pass": 0, "test_pass": 0, "testcase_pass_rate": 0.0}

#     file_stats = []
#     for tr in test_results:
#         assertions = tr.get("assertionResults", [])
#         total = len(assertions)
#         passed = sum(1 for a in assertions if a.get("status") == "passed")
#         has_passed = passed > 0
#         has_runtime_error = False

#         for a in assertions:
#             if a.get("status") == "failed":
#                 failure_messages = a.get("failureMessages", [])
#                 if not is_assertion_failure(failure_messages):
#                     has_runtime_error = True
#                     break

#         file_stats.append({
#             "total": total,
#             "passed": passed,
#             "has_runtime_error": has_runtime_error,
#             "has_passed": has_passed
#         })

#     excute_pass = sum(1 for fs in file_stats if not fs["has_runtime_error"])
#     test_pass = sum(1 for fs in file_stats if fs["has_passed"])

#     # 计算每个文件的通过率（百分比）并累加
#     pass_rate_sum = 0.0
#     for fs in file_stats:
#         if fs["total"] > 0:
#             file_pass_rate = fs["passed"] / fs["total"]
#             pass_rate_sum += file_pass_rate

#     return {
#         "excute_pass": excute_pass,
#         "test_pass": test_pass,
#         "testcase_pass_rate": pass_rate_sum
#     }


# def update_summary(summary_path, new_stats):
#     """更新 summary_filtered.json，保留原有其他字段"""
#     existing = {}
#     if os.path.exists(summary_path):
#         try:
#             with open(summary_path, "r", encoding="utf-8") as f:
#                 existing = json.load(f)
#         except (json.JSONDecodeError, IOError):
#             pass
#     existing.update(new_stats)
#     with open(summary_path, "w", encoding="utf-8") as f:
#         json.dump(existing, f, indent=2, ensure_ascii=False)


# def main():
#     # root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
#     root_dir = "test_results/javascript"
#     root_path = Path(root_dir).resolve()
#     if not root_path.is_dir():
#         print(f"错误：{root_path} 不是有效目录")
#         sys.exit(1)

#     report_files = list(root_path.rglob("report.json"))
#     if not report_files:
#         print(f"在 {root_path} 下未找到任何 report.json 文件")
#         return

#     print(f"找到 {len(report_files)} 个 report.json 文件，开始处理...")
#     for report_path in report_files:
#         parent_dir = report_path.parent
#         summary_path = parent_dir / "summary.json"
#         print(f"处理: {report_path}")

#         stats = process_jest_report(report_path)
#         if stats is not None:
#             update_summary(summary_path, stats)
#             print(f"  已更新 {summary_path}")
#             print(f"    excute_pass = {stats['excute_pass']}")
#             print(f"    test_pass = {stats['test_pass']}")
#             print(f"    testcase_pass_rate (累加和) = {stats['testcase_pass_rate']}")
#         else:
#             print(f"  跳过 {report_path}")

#     print("全部处理完成。")


# if __name__ == "__main__":
#     main()










#!/usr/bin/env python3
"""
遍历两层目录：root/level1/level2/report.json
- 如果存在 report.json，基于它计算统计并更新同级的 summary_filtered.json。
- 如果不存在 report.json，则将 summary_filtered.json 中的三个字段设为 0。
"""

import json
import os
import sys
from pathlib import Path


def is_assertion_failure(failure_messages):
    """判断失败消息是否为断言失败（Jest 断言通常以 'expect(' 开头）"""
    if not failure_messages:
        return False
    msg = failure_messages[0] if failure_messages else ""
    return msg.strip().startswith("Error: expect(")


def process_jest_report(report_path):
    """处理 Jest 报告文件，返回统计结果（文件通过率累加）"""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  警告：无法读取或解析 {report_path} - {e}")
        return None

    test_results = data.get("testResults", [])
    if not test_results:
        return {"excute_pass": 0, "test_pass": 0, "testcase_pass_rate": 0.0}

    file_stats = []
    for tr in test_results:
        assertions = tr.get("assertionResults", [])
        total = len(assertions)
        passed = sum(1 for a in assertions if a.get("status") == "passed")
        has_passed = passed > 0
        has_runtime_error = False

        for a in assertions:
            if a.get("status") == "failed":
                failure_messages = a.get("failureMessages", [])
                if not is_assertion_failure(failure_messages):
                    has_runtime_error = True
                    break

        file_stats.append({
            "total": total,
            "passed": passed,
            "has_runtime_error": has_runtime_error,
            "has_passed": has_passed
        })

    excute_pass = sum(1 for fs in file_stats if not fs["has_runtime_error"])
    test_pass = sum(1 for fs in file_stats if fs["has_passed"])
    # 计算每个文件的通过率（百分比）并累加
    pass_rate_sum = 0.0
    for fs in file_stats:
        if fs["total"] > 0:
            file_pass_rate = fs["passed"] / fs["total"]
            pass_rate_sum += file_pass_rate

    return {
        "excute_pass": excute_pass,
        "test_pass": test_pass,
        "testcase_pass_rate": pass_rate_sum
    }


def update_summary(summary_path, new_stats):
    """更新 summary_filtered.json，保留原有其他字段"""
    existing = {}
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    existing.update(new_stats)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def main():
    # root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    root_dir = "test_results/javascript"
    root_path = Path(root_dir).resolve()
    if not root_path.is_dir():
        print(f"错误：{root_path} 不是有效目录")
        sys.exit(1)

    # 遍历第一级子目录
    for level1_dir in root_path.iterdir():
        if not level1_dir.is_dir():
            continue
        # 遍历第二级子目录
        for level2_dir in level1_dir.iterdir():
            if not level2_dir.is_dir():
                continue

            report_path = level2_dir / "report.json"
            summary_path = level2_dir / "summary.json"

            if report_path.exists():
                print(f"处理有报告的目录: {level2_dir}")
                stats = process_jest_report(report_path)
                if stats is not None:
                    update_summary(summary_path, stats)
                    print(f"  已更新 {summary_path}")
                    print(f"    excute_pass = {stats['excute_pass']}")
                    print(f"    test_pass = {stats['test_pass']}")
                    print(f"    testcase_pass_rate = {stats['testcase_pass_rate']}")
            else:
                # 没有 report.json，写入零值
                zero_stats = {"excute_pass": 0, "test_pass": 0, "testcase_pass_rate": 0.0}
                update_summary(summary_path, zero_stats)
                print(f"处理无报告的目录: {level2_dir} -> 写入零值到 {summary_path}")

    print("全部处理完成。")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
遍历指定目录（默认为当前目录），寻找所有 report.json 文件，
对每个文件统计：
- excute_pass: 包含非 AssertionError 错误的测试文件数
- test_pass:   至少有一个通过用例的测试文件数
- testcase_pass_rate: 所有用例的通过率（%）
然后将结果写入同级的 summary_filtered.json 中（保留原有其他字段）。
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict


def is_runtime_error(test):
    """
    判断一个测试是否属于运行时错误（非断言失败）。
    规则：
      - outcome 为 "error" -> 运行时错误
      - outcome 为 "failed" 且 crash.message 不以 "AssertionError" 开头 -> 运行时错误
    """
    outcome = test.get("outcome")
    if outcome == "error":
        return True
    if outcome == "failed":
        crash = test.get("setup", {}).get("crash") or test.get("call", {}).get("crash") or test.get("teardown", {}).get("crash")
        if crash:
            msg = crash.get("message", "")
            # 处理 msg 为 None 的情况
            if msg is None:
                return True
            # 检查是否以 AssertionError 开头（常见格式）
            if not msg.startswith("AssertionError"):
                return True
    return False


def process_report(report_path):
    """处理单个 report.json 文件，返回统计结果字典"""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  警告：无法读取或解析 {report_path} - {e}")
        return None

    tests = data.get("tests", [])
    if not tests:
        print(f"  警告：{report_path} 中没有测试用例")
        return {"excute_pass": 0, "test_pass": 0, "testcase_pass_rate": 0.0}

    # 按测试文件分组（nodeid 中 "::" 之前的部分）
    file_stats = defaultdict(lambda: {
        "has_runtime_error": False,
        "has_passed": False,
        "total_cases": 0,
        "passed_cases": 0
    })

    for test in tests:
        nodeid = test.get("nodeid", "")
        if "::" in nodeid:
            file_path = nodeid.split("::")[0]
        else:
            file_path = nodeid  # 降级处理

        stats = file_stats[file_path]
        stats["total_cases"] += 1

        # 统计通过用例
        if test.get("outcome") == "passed":
            stats["has_passed"] = True
            stats["passed_cases"] += 1

        # 统计运行时错误
        if is_runtime_error(test):
            stats["has_runtime_error"] = True

    # 计算最终指标
    excute_pass = sum(1 for s in file_stats.values() if not s["has_runtime_error"])
    test_pass = sum(1 for s in file_stats.values() if s["has_passed"])

    # 计算每个文件的通过率并累加
    total_pass_rate_sum = 0.0
    for stats in file_stats.values():
        if stats["total_cases"] > 0:
            file_pass_rate = stats["passed_cases"] / stats["total_cases"]
            total_pass_rate_sum += file_pass_rate

    return {
        "excute_pass": excute_pass,
        "test_pass": test_pass,
        "testcase_pass_rate": total_pass_rate_sum  
    }


def update_summary(summary_path, new_stats):
    """将统计结果更新到 summary_filtered.json 中，保留原有其他字段"""
    existing = {}
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  警告：无法读取 {summary_path}，将创建新文件 - {e}")

    # 更新指定字段
    existing.update(new_stats)

    # 写回文件
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def main():
    # 获取根目录（命令行参数或当前目录）
    # root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    # root_path = Path(root_dir).resolve()
    root_path = Path("test_results/python").resolve()
    if not root_path.is_dir():
        print(f"错误：{root_path} 不是有效目录")
        sys.exit(1)

    # 递归查找所有 report.json
    report_files = list(root_path.rglob("report.json"))
    if not report_files:
        print(f"在 {root_path} 下未找到任何 report.json 文件")
        return

    print(f"找到 {len(report_files)} 个 report.json 文件，开始处理...")
    for report_path in report_files:
        parent_dir = report_path.parent
        summary_path = parent_dir / "summary_filtered.json"
        print(f"处理: {report_path}")

        stats = process_report(report_path)
        if stats is not None:
            update_summary(summary_path, stats)
            print(f"  已更新 {summary_path}")
            print(f"    excute_pass = {stats['excute_pass']}")
            print(f"    test_pass = {stats['test_pass']}")
            print(f"    testcase_pass_rate = {stats['testcase_pass_rate']}%")
        else:
            print(f"  跳过 {report_path}")

    print("全部处理完成。")


if __name__ == "__main__":
    main()
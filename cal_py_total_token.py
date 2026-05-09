#!/usr/bin/env python3
"""
aggregate_model_usage.py
遍历目录下所有 *.json 文件，文件名格式为 *_[模型名].json。
读取 total_tokens、cost、_elapsed_seconds，按模型分组累加。
"""

import os
import json
import argparse
from collections import defaultdict


def extract_model_name(filename: str) -> str:
    """
    从文件名提取模型名称。
    假设格式: [前缀]_[模型名].json
    提取规则: 去掉 .json 后缀，再以最后一个 '_' 分割，取最后一部分。
    若无下划线，则返回整个名称（不含后缀）。
    """
    base, _ = os.path.splitext(filename)  # 去掉 .json
    if "_" in base:
        model = base.rsplit("_", 1)[1]
    else:
        model = base
    return model


def main():
    # parser = argparse.ArgumentParser(
    #     description="按模型分组汇总 token 用量、花费和耗时（文件名格式：*_模型名.json）"
    # )
    # parser.add_argument(
    #     "directory",
    #     nargs="?",
    #     default=".",
    #     help="要扫描的目录，默认为当前目录",
    # )
    # args = parser.parse_args()
    target_dir = "tests/test_gen/python/fix_tornado"

    if not os.path.isdir(target_dir):
        print(f"错误: {target_dir} 不是有效目录")
        return

    model_stats = defaultdict(lambda: {
        "total_tokens": 0,
        "cost": 0.0,
        "_elapsed_seconds": 0.0,
        "file_count": 0
    })

    for filename in os.listdir(target_dir):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(target_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: 无法读取或解析 {filepath}: {e}")
            continue

        usage = data.get("_usage_summary", {})
        elapsed = data.get("_elapsed_seconds")
        if not isinstance(usage, dict):
            print(f"警告: {filepath} 中 _usage_summary 格式有误，跳过")
            continue

        total_tokens = usage.get("total_tokens")
        cost = usage.get("cost")
        if total_tokens is None or cost is None or elapsed is None:
            print(f"警告: {filepath} 缺少 total_tokens/cost/_elapsed_seconds，跳过")
            continue

        model = extract_model_name(filename)
        model_stats[model]["total_tokens"] += total_tokens
        model_stats[model]["cost"] += cost
        model_stats[model]["_elapsed_seconds"] += elapsed
        model_stats[model]["file_count"] += 1

    if not model_stats:
        print("未找到任何含有有效数据的 JSON 文件。")
        return

    print(f"{'模型':<20} {'文件数':<8} {'total_tokens':<16} {'cost':<12} {'elapsed_seconds':<18}")
    print("-" * 74)
    total_files = 0
    grand_tokens = 0
    grand_cost = 0.0
    grand_elapsed = 0.0
    for model, stats in sorted(model_stats.items()):
        print(
            f"{model:<20} "
            f"{stats['file_count']:<8} "
            f"{stats['total_tokens']:<16} "
            f"{stats['cost']:<12.6f} "
            f"{stats['_elapsed_seconds']:<18.2f}"
        )
        total_files += stats["file_count"]
        grand_tokens += stats["total_tokens"]
        grand_cost += stats["cost"]
        grand_elapsed += stats["_elapsed_seconds"]

    print("-" * 74)
    print(
        f"{'总计':<20} "
        f"{total_files:<8} "
        f"{grand_tokens:<16} "
        f"{grand_cost:<12.6f} "
        f"{grand_elapsed:<18.2f}"
    )


if __name__ == "__main__":
    main()
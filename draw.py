# """Plot language-level aggregated benchmark metrics as a grouped bar chart.

# Usage:
#     python test_results/plot_language_bar_matplotlib.py

# Output:
#     test_results/language_metrics_bar.png
# """

# from __future__ import annotations

# import json
# from pathlib import Path


# LANG_FILES = {
#     "Python": Path("test_results/python/aggregated_results.json"),
#     "JavaScript": Path("test_results/javascript/aggregated_results.json"),
#     "Java": Path("test_results/java/aggregated_results.json"),
# }

# METRICS = [
#     "syntax_correct_rate",
#     "compile_pass_rate",
#     "excute_pass_rate",
#     "test_pass_rate",
#     "testcase_passed_rate",
#     "file_line_coverage",
#     "file_branch_coverage",
#     "function_line_coverage",
#     "function_branch_coverage",
# ]

# METRIC_LABELS = [
#     "Syntax",
#     "Compile",
#     "Excute",
#     "Test",
#     "Testcase",
#     "File Line",
#     "File Branch",
#     "Function Line",
#     "Function Branch",
# ]


# def aggregate_language_result(path: Path) -> dict[str, float]:
#     """Aggregate one language's result from by_spec (with_spec + without_spec)."""
#     data = json.loads(path.read_text(encoding="utf-8"))
#     parts = list(data["by_spec"].values())

#     total = sum(item["total"] for item in parts)

#     return {
#         "syntax_correct_rate": sum(item["syntax_correct"] for item in parts) / total,
#         "compile_pass_rate": sum(item["compile_pass"] for item in parts) / total,
#         "excute_pass_rate": sum(item["excute_pass"] for item in parts) / total,
#         "test_pass_rate": sum(item["test_pass"] for item in parts) / total,
#         "testcase_passed_rate": sum(item["testcase_passed"] for item in parts) / total,
#         "file_line_coverage": sum(item["filtered_stats_file_covered_lines"] for item in parts)
#         / sum(item["filtered_stats_file_total_lines"] for item in parts),
#         "file_branch_coverage": sum(item["filtered_stats_file_covered_branches"] for item in parts)
#         / sum(item["filtered_stats_file_total_branches"] for item in parts),
#         "function_line_coverage": sum(item["filtered_stats_function_covered_lines"] for item in parts)
#         / sum(item["filtered_stats_function_total_lines"] for item in parts),
#         "function_branch_coverage": sum(item["filtered_stats_function_covered_branches"] for item in parts)
#         / sum(item["filtered_stats_function_total_branches"] for item in parts),
#     }


# def main() -> None:
#     try:
#         import matplotlib.pyplot as plt
#         import numpy as np
#     except ModuleNotFoundError as exc:
#         raise SystemExit(
#             "matplotlib/numpy not installed. Please install first: pip install matplotlib numpy"
#         ) from exc

#     results = {lang: aggregate_language_result(path) for lang, path in LANG_FILES.items()}

#     x = np.arange(len(METRICS))
#     width = 0.24

#     fig, ax = plt.subplots(figsize=(16, 7))

#     for i, (lang, metric_values) in enumerate(results.items()):
#         y = [metric_values[m] * 100 for m in METRICS]
#         offset = (i - 1) * width
#         bars = ax.bar(x + offset, y, width=width, label=lang)

#         for bar, value in zip(bars, y):
#             ax.text(
#                 bar.get_x() + bar.get_width() / 2,
#                 bar.get_height() + 0.5,
#                 f"{value:.1f}%",
#                 ha="center",
#                 va="bottom",
#                 fontsize=8,
#                 rotation=90,
#             )

#     ax.set_title("Language-level Aggregated Metrics")
#     ax.set_ylabel("Percentage (%)")
#     ax.set_xticks(x)
#     ax.set_xticklabels(METRIC_LABELS, rotation=20, ha="right")
#     ax.set_ylim(0, 105)
#     ax.grid(axis="y", linestyle="--", alpha=0.3)
#     ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.10))

#     out = Path("test_results/language_metrics_bar.png")
#     fig.tight_layout()
#     fig.savefig(out, dpi=220)
#     print(f"Saved: {out}")


# if __name__ == "__main__":
#     main()

"""Plot language-level aggregated benchmark metrics as a line chart.

Usage:
    python test_results/plot_language_bar_matplotlib.py

Output:
    test_results/language_metrics_line.png
"""

from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体
rcParams["font.sans-serif"] = ["SimHei"]  # 或者 ["Microsoft YaHei"]
rcParams["axes.unicode_minus"] = False     # 解决负号显示问题


LANG_FILES = {
    "Python": Path("test_results/python/aggregated_results.json"),
    "JavaScript": Path("test_results/javascript/aggregated_results.json"),
    "Java": Path("test_results/java/aggregated_results.json"),
}

METRICS = [
    "syntax_correct_rate",
    "compile_pass_rate",
    "excute_pass_rate",
    "test_pass_rate",
    "testcase_passed_rate",
    "file_line_coverage",
    "file_branch_coverage",
    "function_line_coverage",
    "function_branch_coverage",
]

METRIC_LABELS = [
    "Syntax",
    "Compile",
    "Excute",
    "Test",
    "Testcase",
    "File Line",
    "File Branch",
    "Function Line",
    "Function Branch",
]

# Use line styles (not colors) to distinguish languages.
LINE_STYLES = {
    "Python": "-",      # solid
    "JavaScript": "--", # dashed
    "Java": ":",        # dotted
}

MARKERS = {
    "Python": "o",
    "JavaScript": "s",
    "Java": "^",
}


def aggregate_language_result(path: Path) -> dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = list(data["by_spec"].values())

    total = sum(item["total"] for item in parts)

    return {
        "syntax_correct_rate": sum(item["syntax_correct"] for item in parts) / total,
        "compile_pass_rate": sum(item["compile_pass"] for item in parts) / total,
        "excute_pass_rate": sum(item["excute_pass"] for item in parts) / total,
        "test_pass_rate": sum(item["test_pass"] for item in parts) / total,
        "testcase_passed_rate": sum(item["testcase_passed"] for item in parts) / total,
        "file_line_coverage": sum(item["filtered_stats_file_covered_lines"] for item in parts)
        / sum(item["filtered_stats_file_total_lines"] for item in parts),
        "file_branch_coverage": sum(item["filtered_stats_file_covered_branches"] for item in parts)
        / sum(item["filtered_stats_file_total_branches"] for item in parts),
        "function_line_coverage": sum(item["filtered_stats_function_covered_lines"] for item in parts)
        / sum(item["filtered_stats_function_total_lines"] for item in parts),
        "function_branch_coverage": sum(item["filtered_stats_function_covered_branches"] for item in parts)
        / sum(item["filtered_stats_function_total_branches"] for item in parts),
    }


def main() -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "matplotlib/numpy not installed. Please install first: pip install matplotlib numpy"
        ) from exc

    results = {lang: aggregate_language_result(path) for lang, path in LANG_FILES.items()}

    x = np.arange(len(METRICS))
    fig, ax = plt.subplots(figsize=(16, 7))

    # 绘制线条
    for lang, metric_values in results.items():
        y = [metric_values[m] * 100 for m in METRICS]
        ax.plot(
            x,
            y,
            linestyle=LINE_STYLES[lang],
            marker=MARKERS[lang],
            color="black",
            linewidth=2,
            markersize=6,
            label=lang,  # 每条线都带上 label
        )

        # 在每个点上加百分比标注
        for xi, yi in zip(x, y):
            ax.text(xi, yi + 0.8, f"{yi:.1f}%", ha="center", va="bottom", fontsize=8)

    # 设置图例，统一右上角
    ax.legend(loc="upper right")

    ax.set_title("模型在不同语言上的平均表现")
    ax.set_ylabel("Percentage (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(METRIC_LABELS, rotation=20, ha="right")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    # ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.10))

    out = Path("test_results/language_metrics_line.png")
    fig.tight_layout()
    fig.savefig(out, dpi=220)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
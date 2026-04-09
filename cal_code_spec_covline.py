from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


PROJECTS = {
    "commons-cli": "commons-cli_lite_junit4_CodeLlama-7b.json",
    "commons-jxpath": "commons-jxpath_lite_junit4_CodeLlama-7b.json",
    "jcasbin": "jcasbin_lite_junit4_CodeLlama-7b.json",
    "nfe": "nfe_lite_junit4_CodeLlama-7b.json",
}


def resolve_src_json(filename: str) -> Path:
    candidates = [
        Path("tests/test_gen/java") / filename,
        Path("tests/test_gen") / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"Could not find source json: {filename}")


def load_target_files(src_json: Path) -> set[str]:
    data = json.loads(src_json.read_text(encoding="utf-8"))
    return {item["src_file"] for item in data if item.get("src_file")}


def covered_lines_from_xml(xml_path: Path, allowed_src_files: set[str]) -> set[tuple[str, int]]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    covered: set[tuple[str, int]] = set()
    for package in root.findall("package"):
        package_name = package.attrib.get("name", "")
        for sourcefile in package.findall("sourcefile"):
            source_name = sourcefile.attrib.get("name")
            if not source_name:
                continue

            rel_src = f"src/main/java/{package_name}/{source_name}" if package_name else source_name
            if rel_src not in allowed_src_files:
                continue

            for line in sourcefile.findall("line"):
                if int(line.attrib.get("ci", "0")) != 0:
                    covered.add((rel_src, int(line.attrib["nr"])))

    return covered


def analyze_project(project: str, src_json: Path) -> dict[str, object]:
    results_root = Path("test_results/java") / project
    if not results_root.exists():
        raise FileNotFoundError(f"Results root not found: {results_root}")

    allowed_src_files = load_target_files(src_json)
    group_covered: dict[str, set[tuple[str, int]]] = defaultdict(set)
    group_dirs: dict[str, list[str]] = defaultdict(list)

    for child in sorted(results_root.iterdir()):
        if not child.is_dir():
            continue
        jacoco = child / "target_jacoco.xml"
        if not jacoco.exists():
            continue

        group = "with_specification" if "specification" in child.name else "without_specification"
        group_dirs[group].append(child.name)
        group_covered[group] |= covered_lines_from_xml(jacoco, allowed_src_files)

    spec = group_covered.get("with_specification", set())
    nonspec = group_covered.get("without_specification", set())

    # ---- 计算汇总统计数据 ----
    summary = {
        "total_with_specification": len(spec),
        "total_without_specification": len(nonspec),
        "common_intersection": len(spec & nonspec),
        "only_with_specification": len(spec - nonspec),
        "only_without_specification": len(nonspec - spec),
    }

    def by_file(lines: set[tuple[str, int]]) -> dict[str, int]:
        grouped: dict[str, set[int]] = defaultdict(set)
        for file_path, line_no in lines:
            grouped[file_path].add(line_no)
        return {k: len(v) for k, v in sorted(grouped.items())}

    # 按文件的汇总也加一份（可选）
    per_file_summary = {}
    all_files = sorted(set(by_file(spec).keys()) | set(by_file(nonspec).keys()))
    for f in all_files:
        spec_lines = {line for (file, line) in spec if file == f}
        nonspec_lines = {line for (file, line) in nonspec if file == f}
        per_file_summary[f] = {
            "with_specification": len(spec_lines),
            "without_specification": len(nonspec_lines),
            "common": len(spec_lines & nonspec_lines),
            "only_with_spec": len(spec_lines - nonspec_lines),
            "only_without_spec": len(nonspec_lines - spec_lines),
        }

    return {
        "project": project,
        "src_json": str(src_json),
        "allowed_src_files": sorted(allowed_src_files),
        "group_dirs": {k: v for k, v in group_dirs.items()},
        "summary": summary,                               # 新增：总体统计
        "per_file_summary": per_file_summary,             # 新增：按文件统计
        "with_spec": spec,
        "without_spec": nonspec,
        "per_file_with_spec": by_file(spec),
        "per_file_without_spec": by_file(nonspec),
    }


def print_report(report: dict[str, object]) -> None:
    project = report["project"]
    spec: set[tuple[str, int]] = report["with_spec"]  # type: ignore[assignment]
    nonspec: set[tuple[str, int]] = report["without_spec"]  # type: ignore[assignment]
    group_dirs: dict[str, list[str]] = report["group_dirs"]  # type: ignore[assignment]
    per_spec: dict[str, int] = report["per_file_with_spec"]  # type: ignore[assignment]
    per_nonspec: dict[str, int] = report["per_file_without_spec"]  # type: ignore[assignment]
    summary: dict[str, int] = report.get("summary", {})  # type: ignore[assignment]

    print(f"\n=== {project} ===")
    print(f"src_json: {report['src_json']}")
    print("Allowed src_file list:")
    for f in report["allowed_src_files"]:  # type: ignore[index]
        print(f"  - {f}")

    print("Group directories:")
    for group in ("with_specification", "without_specification"):
        dirs = group_dirs.get(group, [])
        print(f"  {group}: {len(dirs)} dirs")

    print("Covered line counts (union within each group):")
    # 优先使用 summary 中的值，若没有则重新计算（向后兼容）
    if summary:
        print(f"  with_specification: {summary['total_with_specification']}")
        print(f"  without_specification: {summary['total_without_specification']}")
        print(f"  common(intersection): {summary['common_intersection']}")
        print(f"  only_with_specification: {summary['only_with_specification']}")
        print(f"  only_without_specification: {summary['only_without_specification']}")
    else:
        print(f"  with_specification: {len(spec)}")
        print(f"  without_specification: {len(nonspec)}")
        print(f"  common(intersection): {len(spec & nonspec)}")
        print(f"  only_with_specification: {len(spec - nonspec)}")
        print(f"  only_without_specification: {len(nonspec - spec)}")

    print("Per-file covered line counts:")
    files = sorted(set(per_spec) | set(per_nonspec))
    for f in files:
        common = len({x for x in spec & nonspec if x[0] == f})
        print(
            f"  - {f}: with_specification={per_spec.get(f, 0)}, "
            f"without_specification={per_nonspec.get(f, 0)}, common={common}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="Only analyze selected project(s). Can be passed multiple times.",
    )
    return parser.parse_args()


def make_serializable(obj):
    """递归地将集合和元组转换为列表，以便 JSON 序列化。"""
    if isinstance(obj, set):
        return sorted([make_serializable(item) for item in obj])
    elif isinstance(obj, tuple):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    else:
        return obj


def save_report(report: dict[str, object], output_dir: Path) -> None:
    """将报告保存为 JSON 文件。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    project = report["project"]
    output_file = output_dir / f"{project}_coverage_report.json"

    serializable_report = make_serializable(report)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(serializable_report, f, indent=2, ensure_ascii=False)
    print(f"Report saved to {output_file}")


def main() -> None:
    args = parse_args()
    selected = args.projects if args.projects else list(PROJECTS)

    for project in selected:
        if project not in PROJECTS:
            raise ValueError(f"Unsupported project: {project}. Supported: {', '.join(PROJECTS)}")

        src_json = resolve_src_json(PROJECTS[project])
        report = analyze_project(project, src_json)
        print_report(report)

        output_dir = Path("test_results/java") / project
        save_report(report, output_dir)


if __name__ == "__main__":
    main()
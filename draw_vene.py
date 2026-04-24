# # #!/usr/bin/env python3
# # """Analyze spec vs non-spec coverage for configured Java/JavaScript/Python projects."""

# # from __future__ import annotations

# # import argparse
# # import json
# # import struct
# # import zlib
# # from collections import defaultdict
# # from pathlib import Path
# # import xml.etree.ElementTree as ET


# # JAVA_PROJECTS = {
# #     "commons-cli": "commons-cli_lite_junit4_CodeLlama-7b.json",
# #     "commons-jxpath": "commons-jxpath_lite_junit4_CodeLlama-7b.json",
# #     "jcasbin": "jcasbin_lite_junit4_CodeLlama-7b.json",
# #     "nfe": "nfe_lite_junit4_CodeLlama-7b.json",
# # }

# # JS_PROJECTS = {
# #     "modern-error": "modern-error_jest_glm-4.7.json",
# #     "pdf": "pdf_jest_glm-4.7.json",
# #     "proton": "proton_specification_jest_glm-4.7.json",
# #     "simple-statistics": "simple-statistics_jest_glm-4.7.json",
# # }

# # PY_PROJECTS = {
# #     "flask": "flask_lite_unittest_CodeLlama-7b.json",
# #     "markitdown": "markitdown_lite_unittest_CodeLlama-7b.json",
# #     "pylint": "pylint_lite_unittest_CodeLlama-7b.json",
# #     "tornado": "tornado_lite_unittest_CodeLlama-7b.json",
# # }


# # def resolve_src_json(filename: str) -> Path:
# #     candidates = [
# #         Path("tests/test_gen/java") / filename,
# #         Path("tests/test_gen/javascript") / filename,
# #         Path("tests/test_gen/python") / filename,
# #         Path("tests/test_gen") / filename,
# #     ]
# #     for path in candidates:
# #         if path.exists():
# #             return path
# #     raise FileNotFoundError(f"Could not find source json: {filename}")


# # def load_target_files(src_json: Path) -> set[str]:
# #     data = json.loads(src_json.read_text(encoding="utf-8"))
# #     return {item["src_file"] for item in data if item.get("src_file")}


# # def find_src_match(raw_path: str, allowed_src_files: set[str]) -> str | None:
# #     normalized = raw_path.replace("\\", "/")
# #     if normalized in allowed_src_files:
# #         return normalized
# #     normalized = normalized.lstrip("/")
# #     if normalized in allowed_src_files:
# #         return normalized

# #     for candidate in allowed_src_files:
# #         if normalized.endswith("/" + candidate) or normalized.endswith(candidate):
# #             return candidate
# #     return None


# # def covered_lines_from_jacoco(xml_path: Path, allowed_src_files: set[str]) -> set[tuple[str, int]]:
# #     tree = ET.parse(xml_path)
# #     root = tree.getroot()

# #     covered: set[tuple[str, int]] = set()
# #     for package in root.findall("package"):
# #         package_name = package.attrib.get("name", "")
# #         for sourcefile in package.findall("sourcefile"):
# #             source_name = sourcefile.attrib.get("name")
# #             if not source_name:
# #                 continue

# #             rel_src = f"src/main/java/{package_name}/{source_name}" if package_name else source_name
# #             if rel_src not in allowed_src_files:
# #                 continue

# #             for line in sourcefile.findall("line"):
# #                 if int(line.attrib.get("ci", "0")) != 0:
# #                     covered.add((rel_src, int(line.attrib["nr"])))

# #     return covered


# # def covered_lines_from_istanbul(json_path: Path, allowed_src_files: set[str]) -> set[tuple[str, int]]:
# #     data = json.loads(json_path.read_text(encoding="utf-8"))
# #     covered: set[tuple[str, int]] = set()

# #     for file_path, payload in data.items():
# #         matched_src = find_src_match(file_path, allowed_src_files)
# #         if matched_src is None:
# #             continue

# #         statement_map = payload.get("statementMap", {})
# #         statement_hits = payload.get("s", {})

# #         for statement_id, stmt in statement_map.items():
# #             if int(statement_hits.get(statement_id, 0)) == 0:
# #                 continue
# #             line = stmt.get("start", {}).get("line")
# #             if isinstance(line, int):
# #                 covered.add((matched_src, line))

# #     return covered


# # def covered_lines_from_py_coverage(json_path: Path, allowed_src_files: set[str]) -> set[tuple[str, int]]:
# #     data = json.loads(json_path.read_text(encoding="utf-8"))
# #     covered: set[tuple[str, int]] = set()

# #     for file_path, payload in data.get("files", {}).items():
# #         matched_src = find_src_match(file_path, allowed_src_files)
# #         if matched_src is None:
# #             continue

# #         for line in payload.get("executed_lines", []):
# #             if isinstance(line, int):
# #                 covered.add((matched_src, line))

# #     return covered


# # def analyze_java_project(project: str, src_json: Path) -> dict[str, object]:
# #     results_root = Path("test_results/java") / project
# #     if not results_root.exists():
# #         raise FileNotFoundError(f"Results root not found: {results_root}")

# #     allowed_src_files = load_target_files(src_json)
# #     group_covered: dict[str, set[tuple[str, int]]] = defaultdict(set)
# #     group_dirs: dict[str, list[str]] = defaultdict(list)

# #     for child in sorted(results_root.iterdir()):
# #         jacoco = child / "target_jacoco.xml"
# #         if child.is_dir() and jacoco.exists():
# #             group = "with_specification" if "specification" in child.name else "without_specification"
# #             group_dirs[group].append(child.name)
# #             group_covered[group] |= covered_lines_from_jacoco(jacoco, allowed_src_files)

# #     return build_report("java", project, src_json, allowed_src_files, group_dirs, group_covered)


# # def analyze_js_project(project: str, src_json: Path) -> dict[str, object]:
# #     results_root = Path("test_results/javascript") / project
# #     if not results_root.exists():
# #         raise FileNotFoundError(f"Results root not found: {results_root}")

# #     allowed_src_files = load_target_files(src_json)
# #     group_covered: dict[str, set[tuple[str, int]]] = defaultdict(set)
# #     group_dirs: dict[str, list[str]] = defaultdict(list)

# #     for child in sorted(results_root.iterdir()):
# #         coverage_json = child / "coverage" / "coverage-final.json"
# #         if child.is_dir() and coverage_json.exists():
# #             group = "with_specification" if "specification" in child.name else "without_specification"
# #             group_dirs[group].append(child.name)
# #             group_covered[group] |= covered_lines_from_istanbul(coverage_json, allowed_src_files)

# #     return build_report("javascript", project, src_json, allowed_src_files, group_dirs, group_covered)


# # def analyze_py_project(project: str, src_json: Path) -> dict[str, object]:
# #     results_root = Path("test_results/python") / project
# #     if not results_root.exists():
# #         raise FileNotFoundError(f"Results root not found: {results_root}")

# #     allowed_src_files = load_target_files(src_json)
# #     group_covered: dict[str, set[tuple[str, int]]] = defaultdict(set)
# #     group_dirs: dict[str, list[str]] = defaultdict(list)

# #     for child in sorted(results_root.iterdir()):
# #         coverage_json = child / "coverage.json"
# #         if child.is_dir() and coverage_json.exists():
# #             group = "with_specification" if "specification" in child.name else "without_specification"
# #             group_dirs[group].append(child.name)
# #             group_covered[group] |= covered_lines_from_py_coverage(coverage_json, allowed_src_files)

# #     return build_report("python", project, src_json, allowed_src_files, group_dirs, group_covered)


# # def build_report(
# #     language: str,
# #     project: str,
# #     src_json: Path,
# #     allowed_src_files: set[str],
# #     group_dirs: dict[str, list[str]],
# #     group_covered: dict[str, set[tuple[str, int]]],
# # ) -> dict[str, object]:
# #     spec = group_covered.get("with_specification", set())
# #     nonspec = group_covered.get("without_specification", set())

# #     def by_file(lines: set[tuple[str, int]]) -> dict[str, int]:
# #         grouped: dict[str, set[int]] = defaultdict(set)
# #         for file_path, line_no in lines:
# #             grouped[file_path].add(line_no)
# #         return {k: len(v) for k, v in sorted(grouped.items())}

# #     return {
# #         "language": language,
# #         "project": project,
# #         "src_json": str(src_json),
# #         "allowed_src_files": sorted(allowed_src_files),
# #         "group_dirs": {k: sorted(v) for k, v in group_dirs.items()},
# #         "with_spec": spec,
# #         "without_spec": nonspec,
# #         "per_file_with_spec": by_file(spec),
# #         "per_file_without_spec": by_file(nonspec),
# #     }


# # def write_venn_svg(report: dict[str, object], output_dir: Path) -> Path:
# #     language = str(report["language"])
# #     project = str(report["project"])
# #     spec: set[tuple[str, int]] = report["with_spec"]  # type: ignore[assignment]
# #     nonspec: set[tuple[str, int]] = report["without_spec"]  # type: ignore[assignment]

# #     only_spec = len(spec - nonspec)
# #     only_without = len(nonspec - spec)
# #     both = len(spec & nonspec)

# #     output_dir.mkdir(parents=True, exist_ok=True)
# #     out_path = output_dir / f"venn_{language}_{project}.svg"

# #     svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="520" viewBox="0 0 860 520">
# #   <rect width="100%" height="100%" fill="white"/>
# #   <text x="430" y="45" text-anchor="middle" font-size="26" font-family="Arial">{language}/{project} Coverage Venn</text>

# #   <circle cx="330" cy="250" r="150" fill="#66b3ff" fill-opacity="0.45" stroke="#2f6fab" stroke-width="2"/>
# #   <circle cx="530" cy="250" r="150" fill="#ff9999" fill-opacity="0.45" stroke="#b85b5b" stroke-width="2"/>

# #   <text x="250" y="105" text-anchor="middle" font-size="18" font-family="Arial">Spec-only + overlap</text>
# #   <text x="610" y="105" text-anchor="middle" font-size="18" font-family="Arial">Without-only + overlap</text>

# #   <text x="255" y="255" text-anchor="middle" font-size="42" font-family="Arial" font-weight="bold">{only_spec}</text>
# #   <text x="605" y="255" text-anchor="middle" font-size="42" font-family="Arial" font-weight="bold">{only_without}</text>
# #   <text x="430" y="255" text-anchor="middle" font-size="42" font-family="Arial" font-weight="bold">{both}</text>

# #   <text x="255" y="290" text-anchor="middle" font-size="16" font-family="Arial">only spec covered lines</text>
# #   <text x="605" y="290" text-anchor="middle" font-size="16" font-family="Arial">only without covered lines</text>
# #   <text x="430" y="290" text-anchor="middle" font-size="16" font-family="Arial">covered by both</text>

# #   <text x="430" y="430" text-anchor="middle" font-size="17" font-family="Arial">with_specification total: {len(spec)} | without_specification total: {len(nonspec)}</text>
# # </svg>
# # '''
# #     out_path.write_text(svg, encoding="utf-8")
# #     return out_path


# # def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
# #     return struct.pack("!I", len(data)) + chunk_type + data + struct.pack(
# #         "!I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF
# #     )


# # def _draw_circle_alpha(
# #     canvas: list[list[tuple[int, int, int]]],
# #     cx: int,
# #     cy: int,
# #     radius: int,
# #     color: tuple[int, int, int],
# #     alpha: float,
# # ) -> None:
# #     height = len(canvas)
# #     width = len(canvas[0]) if height else 0
# #     r2 = radius * radius
# #     for y in range(max(0, cy - radius), min(height, cy + radius + 1)):
# #         dy2 = (y - cy) * (y - cy)
# #         for x in range(max(0, cx - radius), min(width, cx + radius + 1)):
# #             dx2 = (x - cx) * (x - cx)
# #             if dx2 + dy2 <= r2:
# #                 bg = canvas[y][x]
# #                 canvas[y][x] = (
# #                     int(bg[0] * (1 - alpha) + color[0] * alpha),
# #                     int(bg[1] * (1 - alpha) + color[1] * alpha),
# #                     int(bg[2] * (1 - alpha) + color[2] * alpha),
# #                 )


# # _DIGITS_5X7 = {
# #     "0": ["11111", "10001", "10001", "10001", "10001", "10001", "11111"],
# #     "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
# #     "2": ["11111", "00001", "00001", "11111", "10000", "10000", "11111"],
# #     "3": ["11111", "00001", "00001", "01111", "00001", "00001", "11111"],
# #     "4": ["10001", "10001", "10001", "11111", "00001", "00001", "00001"],
# #     "5": ["11111", "10000", "10000", "11111", "00001", "00001", "11111"],
# #     "6": ["11111", "10000", "10000", "11111", "10001", "10001", "11111"],
# #     "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
# #     "8": ["11111", "10001", "10001", "11111", "10001", "10001", "11111"],
# #     "9": ["11111", "10001", "10001", "11111", "00001", "00001", "11111"],
# # }


# # def _draw_number(canvas: list[list[tuple[int, int, int]]], text: str, x: int, y: int) -> None:
# #     color = (20, 20, 20)
# #     cursor_x = x
# #     for ch in text:
# #         bitmap = _DIGITS_5X7.get(ch)
# #         if bitmap is None:
# #             cursor_x += 8
# #             continue
# #         for row_i, row_bits in enumerate(bitmap):
# #             for col_i, bit in enumerate(row_bits):
# #                 if bit == "1":
# #                     px = cursor_x + col_i
# #                     py = y + row_i
# #                     if 0 <= py < len(canvas) and 0 <= px < len(canvas[0]):
# #                         canvas[py][px] = color
# #         cursor_x += 8


# # def write_venn_png(report: dict[str, object], output_dir: Path) -> Path:
# #     language = str(report["language"])
# #     project = str(report["project"])
# #     spec: set[tuple[str, int]] = report["with_spec"]  # type: ignore[assignment]
# #     nonspec: set[tuple[str, int]] = report["without_spec"]  # type: ignore[assignment]

# #     only_spec = len(spec - nonspec)
# #     only_without = len(nonspec - spec)
# #     both = len(spec & nonspec)

# #     width, height = 860, 520
# #     canvas = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]

# #     _draw_circle_alpha(canvas, 330, 250, 150, (102, 179, 255), 0.45)
# #     _draw_circle_alpha(canvas, 530, 250, 150, (255, 153, 153), 0.45)

# #     _draw_number(canvas, str(only_spec), 230, 245)
# #     _draw_number(canvas, str(only_without), 580, 245)
# #     _draw_number(canvas, str(both), 405, 245)

# #     raw = bytearray()
# #     for row in canvas:
# #         raw.append(0)
# #         for r, g, b in row:
# #             raw.extend((r, g, b))

# #     output_dir.mkdir(parents=True, exist_ok=True)
# #     out_path = output_dir / f"venn_{language}_{project}.png"

# #     png = bytearray(b"\x89PNG\r\n\x1a\n")
# #     ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
# #     png.extend(_png_chunk(b"IHDR", ihdr))
# #     png.extend(_png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9)))
# #     png.extend(_png_chunk(b"IEND", b""))
# #     out_path.write_bytes(bytes(png))
# #     return out_path


# # def print_report(report: dict[str, object]) -> None:
# #     language = report["language"]
# #     project = report["project"]
# #     spec: set[tuple[str, int]] = report["with_spec"]  # type: ignore[assignment]
# #     nonspec: set[tuple[str, int]] = report["without_spec"]  # type: ignore[assignment]
# #     group_dirs: dict[str, list[str]] = report["group_dirs"]  # type: ignore[assignment]
# #     per_spec: dict[str, int] = report["per_file_with_spec"]  # type: ignore[assignment]
# #     per_nonspec: dict[str, int] = report["per_file_without_spec"]  # type: ignore[assignment]

# #     print(f"\n=== {language}/{project} ===")
# #     print(f"src_json: {report['src_json']}")
# #     print("Group directories:")
# #     for group in ("with_specification", "without_specification"):
# #         print(f"  {group}: {len(group_dirs.get(group, []))} dirs")

# #     print("Covered line counts (union within each group):")
# #     print(f"  with_specification: {len(spec)}")
# #     print(f"  without_specification: {len(nonspec)}")
# #     print(f"  common(intersection): {len(spec & nonspec)}")
# #     print(f"  only_with_specification: {len(spec - nonspec)}")
# #     print(f"  only_without_specification: {len(nonspec - spec)}")

# #     print("Per-file covered line counts:")
# #     for file_path in sorted(set(per_spec) | set(per_nonspec)):
# #         common = len({x for x in spec & nonspec if x[0] == file_path})
# #         print(
# #             f"  - {file_path}: with_specification={per_spec.get(file_path, 0)}, "
# #             f"without_specification={per_nonspec.get(file_path, 0)}, common={common}"
# #         )


# # def parse_args() -> argparse.Namespace:
# #     parser = argparse.ArgumentParser(description=__doc__)
# #     parser.add_argument("--language", choices=["java", "javascript", "python", "all"], default="all")
# #     parser.add_argument("--project", action="append", dest="projects")
# #     parser.add_argument(
# #         "--venn-dir",
# #         help="If set, write a simple Venn-like SVG per analyzed project into this directory.",
# #     )
# #     parser.add_argument(
# #         "--png-dir",
# #         help="If set, write a simple Venn-like PNG per analyzed project into this directory.",
# #     )
# #     return parser.parse_args()


# # def main() -> None:
# #     args = parse_args()

# #     selected_java = list(JAVA_PROJECTS)
# #     selected_js = list(JS_PROJECTS)
# #     selected_py = list(PY_PROJECTS)
# #     if args.projects:
# #         selected_java = [p for p in args.projects if p in JAVA_PROJECTS]
# #         selected_js = [p for p in args.projects if p in JS_PROJECTS]
# #         selected_py = [p for p in args.projects if p in PY_PROJECTS]

# #     all_reports: list[dict[str, object]] = []

# #     if args.language in ("java", "all"):
# #         for project in selected_java:
# #             report = analyze_java_project(project, resolve_src_json(JAVA_PROJECTS[project]))
# #             print_report(report)
# #             all_reports.append(report)

# #     if args.language in ("javascript", "all"):
# #         for project in selected_js:
# #             report = analyze_js_project(project, resolve_src_json(JS_PROJECTS[project]))
# #             print_report(report)
# #             all_reports.append(report)

# #     if args.language in ("python", "all"):
# #         for project in selected_py:
# #             report = analyze_py_project(project, resolve_src_json(PY_PROJECTS[project]))
# #             print_report(report)
# #             all_reports.append(report)

# #     if args.venn_dir:
# #         out_dir = Path(args.venn_dir)
# #         print(f"\nWriting Venn-like SVG files to: {out_dir}")
# #         for report in all_reports:
# #             svg_path = write_venn_svg(report, out_dir)
# #             print(f"  - {svg_path}")

# #     if args.png_dir:
# #         out_dir = Path(args.png_dir)
# #         print(f"\nWriting Venn-like PNG files to: {out_dir}")
# #         for report in all_reports:
# #             png_path = write_venn_png(report, out_dir)
# #             print(f"  - {png_path}")


# # if __name__ == "__main__":
# #     main()


# from matplotlib import pyplot as plt
# from matplotlib_venn import venn2

# # 中文显示
# plt.rcParams["font.sans-serif"] = ["SimHei"]
# plt.rcParams["axes.unicode_minus"] = False

# plt.figure(figsize=(6, 6), dpi=300)

# venn2(
#     subsets=(1467, 4894, 16780),  # 仅左，仅右，交集
#     set_labels=("With Spec", "Without Spec")
# )

# plt.title("Spec 与 Without Spec 的覆盖交集")
# plt.tight_layout()
# plt.savefig("spec_without_overlap.png", dpi=300)
# plt.show()

from matplotlib import pyplot as plt
from matplotlib_venn import venn2

# 中文显示
# plt.rcParams["font.sans-serif"] = ["SimHei"]
# plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC"]
plt.rcParams["axes.unicode_minus"] = False

plt.figure(figsize=(6, 6), dpi=300)

venn2(
    subsets=(1467, 4894, 16780),  # 仅左，仅右，交集
    set_labels=("Specification", "Code")
)

# plt.title("The coverage intersection between Specification and Code")
plt.tight_layout()
plt.savefig("spec_without_overlap.png", dpi=300)
plt.show()
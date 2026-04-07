# import os
# import json
# import csv
# from typing import Dict, Any, Set


# # =============================
# # 工具函数
# # =============================

# def norm_path(p: str) -> str:
#     return p.replace("\\", "/").lstrip("./")


# def safe_int(x):
#     try:
#         return int(float(x))
#     except:
#         return 0


# def path_to_class(src_file: str) -> str:
#     src_file = norm_path(src_file)
#     if "src/main/java/" in src_file:
#         src_file = src_file.split("src/main/java/")[1]
#     return src_file.replace("/", ".").replace(".java", "")


# # =============================
# # 读取 data_file.json
# # =============================

# def load_data_file(data_file_json):
#     with open(data_file_json, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     file_set: Set[str] = set()
#     function_set: Set[str] = set()

#     for item in data:
#         src_file = norm_path(item.get("src_file", ""))
#         name = item.get("name", "")

#         if src_file:
#             file_set.add(src_file)

#         if src_file and name:
#             cls = path_to_class(src_file)
#             function_set.add(f"{cls}.{name}")

#     return file_set, function_set


# # =============================
# # file 覆盖率
# # =============================

# def match_file(csv_file: str, allowed_files: Set[str]):
#     for f in allowed_files:
#         if f.endswith(csv_file):
#             return f
#     return None


# def read_file_coverage(csv_path, allowed_files):
#     result = {}

#     if not os.path.exists(csv_path):
#         return result

#     with open(csv_path, "r", encoding="utf-8-sig") as f:
#         sample = f.read(1024)
#         f.seek(0)

#         dialect = csv.Sniffer().sniff(sample)
#         reader = csv.DictReader(f, dialect=dialect)

#         reader.fieldnames = [n.strip() for n in reader.fieldnames]

#         for row in reader:
#             row = {k.strip(): v for k, v in row.items()}

#             raw_file = norm_path(row.get("File", ""))

#             matched = match_file(raw_file, allowed_files)
#             if not matched:
#                 continue

#             line_missed = safe_int(row.get("Line_Missed"))
#             line_covered = safe_int(row.get("Line_Covered"))
#             total_lines = safe_int(row.get("Total_Lines"))

#             branch_missed = safe_int(row.get("Branch_Missed"))
#             branch_covered = safe_int(row.get("Branch_Covered"))
#             total_branches = safe_int(row.get("Total_Branches"))

#             result[matched] = {
#                 "covered_line": line_covered,
#                 "total_line": total_lines,
#                 "line_coverage": round(line_covered / total_lines * 100, 2) if total_lines else 0.0,
#                 "covered_branch": branch_covered,
#                 "total_branch": total_branches,
#                 "branch_coverage": round(branch_covered / total_branches * 100, 2) if total_branches else 0.0,
#             }

#     return result


# # =============================
# # function 覆盖率（class.method）
# # =============================

# def read_function_coverage(csv_path, function_set, allowed_files):
#     result = {}

#     if not os.path.exists(csv_path):
#         return result

#     # with open(csv_path, "r", encoding="utf-8-sig") as f:
#     #     sample = f.read(1024)
#     #     f.seek(0)

#     #     dialect = csv.Sniffer().sniff(sample)
#     #     reader = csv.DictReader(f, dialect=dialect)

#     #     # 清洗表头
#     #     reader.fieldnames = [n.strip() for n in reader.fieldnames]
#     with open(csv_path, "r", encoding="utf-8-sig") as f:
#         reader = csv.DictReader(f)

#         for row in reader:
#             # 🔥 过滤 None key + 清洗
#             row = {
#                 k.strip(): v.strip() if isinstance(v, str) else v
#                 for k, v in row.items()
#                 if k is not None
#             }
#             print(row)
#             cls = row.get("Class", "")
#             method = row.get("Method", "")

#             if not cls or not method:
#                 continue

#             full_name = f"{cls}.{method}"

#             # 🔥 debug可打开
#             # print("CSV:", full_name)

#             if full_name not in function_set:
#                 continue

#             # 找 src_file
#             matched_file = None
#             for fpath in allowed_files:
#                 if path_to_class(fpath) == cls:
#                     matched_file = fpath
#                     break

#             if not matched_file:
#                 continue

#             key = f"{matched_file}:{method}"

#             line_missed = safe_int(row.get("Line_Missed"))
#             line_covered = safe_int(row.get("Line_Covered"))
#             branch_missed = safe_int(row.get("Branch_Missed"))
#             branch_covered = safe_int(row.get("Branch_Covered"))

#             total_lines = line_missed + line_covered
#             total_branches = branch_missed + branch_covered

#             result[key] = {
#                 "covered_line": line_covered,
#                 "total_line": total_lines,
#                 "line_coverage": round(line_covered / total_lines * 100, 2) if total_lines else 0.0,
#                 "covered_branch": branch_covered,
#                 "total_branch": total_branches,
#                 "branch_coverage": round(branch_covered / total_branches * 100, 2) if total_branches else 0.0,
#             }

#     return result


# # =============================
# # 补全未覆盖函数（推荐开启）
# # =============================

# def fill_missing_functions(func_cov, function_set, allowed_files):
#     existing = set(func_cov.keys())

#     for f in function_set:
#         cls, method = f.rsplit(".", 1)

#         for fpath in allowed_files:
#             if path_to_class(fpath) == cls:
#                 key = f"{fpath}:{method}"
#                 if key not in existing:
#                     func_cov[key] = {
#                         "covered_line": 0,
#                         "total_line": 0,
#                         "line_coverage": 0.0,
#                         "covered_branch": 0,
#                         "total_branch": 0,
#                         "branch_coverage": 0.0,
#                     }


# # =============================
# # 汇总
# # =============================

# def summarize(data):
#     return {
#         "total_lines": sum(v["total_line"] for v in data.values()),
#         "covered_lines": sum(v["covered_line"] for v in data.values()),
#         "total_branches": sum(v["total_branch"] for v in data.values()),
#         "covered_branches": sum(v["covered_branch"] for v in data.values()),
#     }


# # =============================
# # 主流程
# # =============================

# def process_dir(root_dir, data_file_json):
#     allowed_files, function_set = load_data_file(data_file_json)

#     for cur_dir, _, _ in os.walk(root_dir):

#         file_csv = os.path.join(cur_dir, "file_coverage.csv")
#         func_csv = os.path.join(cur_dir, "function_coverage.csv")

#         if not (os.path.exists(file_csv) or os.path.exists(func_csv)):
#             continue

#         file_cov = read_file_coverage(file_csv, allowed_files)
#         func_cov = read_function_coverage(func_csv, function_set, allowed_files)

#         # 🔥 是否补零（推荐打开）
#         fill_missing_functions(func_cov, function_set, allowed_files)

#         output = {
#             "file_coverage": file_cov,
#             "function_coverage": func_cov,
#             "summary": {
#                 "file": summarize(file_cov),
#                 "function": summarize(func_cov),
#             }
#         }

#         out_path = os.path.join(cur_dir, "coverage_filtered.json")
#         with open(out_path, "w", encoding="utf-8") as f:
#             json.dump(output, f, indent=2, ensure_ascii=False)

#         # print(f"✔ Generated: {out_path}")


# # =============================
# # 入口
# # =============================

# if __name__ == "__main__":
#     ROOT_DIR = "test_results/java/commons-jxpath"
#     DATA_FILE = "data_file.json"

#     process_dir(ROOT_DIR, DATA_FILE)


import os
import json
import csv
from pathlib import Path
from typing import Dict, Any, Set, Tuple, List, Optional


def norm_path(p: str) -> str:
    """统一路径分隔符，便于比较。"""
    return p.replace("\\", "/").lstrip("./")


def load_data_file(data_file_json: str):
    with open(data_file_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_set: Set[str] = set()
    function_keys: Set[str] = set()

    # 用于更宽松匹配
    function_name_set: Set[Tuple[str, str]] = set()        # (src_file, method_name)
    function_class_set: Set[Tuple[str, str, str]] = set()   # (src_file, class_name, method_name)

    for item in data:
        src_file = norm_path(item.get("src_file", ""))
        if src_file:
            file_set.add(src_file)

        item_type = item.get("type", "")
        name = item.get("name", "")
        class_name = item.get("class_name", "")
        full_class_name = item.get("full_class_name", "")

        if item_type in ("function", "method"):
            # 常见几种可匹配方式
            if src_file and name:
                function_name_set.add((src_file, name))

            if src_file and class_name and name:
                function_class_set.add((src_file, class_name, name))
                function_keys.add(f"{src_file}:{class_name}.{name}")

            if src_file and full_class_name and name:
                function_class_set.add((src_file, full_class_name, name))
                function_keys.add(f"{src_file}:{full_class_name}.{name}")

            # 纯函数场景
            if src_file and name and not class_name and not full_class_name:
                function_keys.add(f"{src_file}:{name}")

    return file_set, function_keys, function_name_set, function_class_set


def safe_float(x: str) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def safe_int(x: str) -> int:
    try:
        return int(float(x))
    except Exception:
        return 0


def read_file_coverage(csv_path: str, allowed_files: Set[str]) -> Dict[str, Dict[str, Any]]:
    result = {}
    if not os.path.exists(csv_path):
        return result

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_name = norm_path(row.get("File", ""))
            if file_name not in allowed_files:
                continue

            line_missed = safe_int(row.get("Line_Missed", 0))
            line_covered = safe_int(row.get("Line_Covered", 0))
            total_lines = safe_int(row.get("Total_Lines", 0))

            branch_missed = safe_int(row.get("Branch_Missed", 0))
            branch_covered = safe_int(row.get("Branch_Covered", 0))
            total_branches = safe_int(row.get("Total_Branches", 0))

            line_cov = round((line_covered / total_lines * 100) if total_lines else 0.0, 2)
            branch_cov = round((branch_covered / total_branches * 100) if total_branches else 0.0, 2)

            result[file_name] = {
                "covered_line": line_covered,
                "total_line": total_lines,
                "line_coverage": line_cov,
                "covered_branch": branch_covered,
                "total_branch": total_branches,
                "branch_coverage": branch_cov,
            }

    return result


def build_function_key_from_row(row: Dict[str, str]) -> List[str]:
    """
    返回若干个候选 key，用于匹配 data_file.json。
    优先使用更精确的形式，再退化到更宽松的形式。
    """
    pkg = (row.get("Package") or "").strip()
    cls = (row.get("Class") or "").strip()
    method = (row.get("Method") or "").strip()

    candidates = []

    # 常见形式：Class.Method
    if cls and method:
        candidates.append(f"{cls}.{method}")

    # 更完整形式：Package.Class.Method
    if pkg and cls and method:
        candidates.append(f"{pkg}.{cls}.{method}")

    # 仅方法名
    if method:
        candidates.append(method)

    return candidates


def read_function_coverage(
    csv_path: str,
    allowed_files: Set[str],
    function_keys: Set[str],
    function_name_set: Set[Tuple[str, str]],
    function_class_set: Set[Tuple[str, str, str]],
    current_dir: str,
) -> Dict[str, Dict[str, Any]]:
    result = {}
    if not os.path.exists(csv_path):
        return result

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candidates = build_function_key_from_row(row)
            method = (row.get("Method") or "").strip()

            matched_key = None

            # 1) 先尝试用当前子目录中的 src_file 直接匹配
            #    这里无法从 function_coverage.csv 直接得到 src_file，所以先靠 data_file.json 的已知组合去判断。
            #    如果你的 data_file.json 中 function 记录很多，这一层通常够用。
            for cand in candidates:
                for file_path in allowed_files:
                    possible_key = f"{file_path}:{cand}"
                    if possible_key in function_keys:
                        matched_key = possible_key
                        break
                if matched_key:
                    break

            # 2) 更宽松匹配：只按 (src_file, method) / (src_file, class, method) 匹配
            #    由于 function_coverage.csv 没有 src_file，这里依然只能靠 data_file.json 的记录集合判断。
            if matched_key is None and method:
                for file_path in allowed_files:
                    if (file_path, method) in function_name_set:
                        matched_key = f"{file_path}:{method}"
                        break

            if matched_key is None:
                continue

            line_missed = safe_int(row.get("Line_Missed", 0))
            line_covered = safe_int(row.get("Line_Covered", 0))
            branch_missed = safe_int(row.get("Branch_Missed", 0))
            branch_covered = safe_int(row.get("Branch_Covered", 0))

            total_lines = line_missed + line_covered
            total_branches = branch_missed + branch_covered

            line_cov = round((line_covered / total_lines * 100) if total_lines else 0.0, 2)
            branch_cov = round((branch_covered / total_branches * 100) if total_branches else 0.0, 2)

            result[matched_key] = {
                "covered_line": line_covered,
                "total_line": total_lines,
                "line_coverage": line_cov,
                "covered_branch": branch_covered,
                "total_branch": total_branches,
                "branch_coverage": branch_cov,
            }

    return result


def summarize(entries: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    total_lines = sum(v["total_line"] for v in entries.values())
    covered_lines = sum(v["covered_line"] for v in entries.values())
    total_branches = sum(v["total_branch"] for v in entries.values())
    covered_branches = sum(v["covered_branch"] for v in entries.values())
    return {
        "total_lines": total_lines,
        "covered_lines": covered_lines,
        "total_branches": total_branches,
        "covered_branches": covered_branches,
    }


def process_one_dir(dir_path: str, allowed_files: Set[str],
                    function_keys: Set[str],
                    function_name_set: Set[Tuple[str, str]],
                    function_class_set: Set[Tuple[str, str, str]]) -> bool:
    file_csv = os.path.join(dir_path, "file_coverage.csv")
    func_csv = os.path.join(dir_path, "function_coverage.csv")

    has_any = os.path.exists(file_csv) or os.path.exists(func_csv)
    if not has_any:
        return False

    file_cov = read_file_coverage(file_csv, allowed_files)
    func_cov = read_function_coverage(
        func_csv,
        allowed_files,
        function_keys,
        function_name_set,
        function_class_set,
        dir_path,
    )

    out = {
        "file_coverage": file_cov,
        "function_coverage": func_cov,
        "summary": {
            "file": summarize(file_cov),
            "function": summarize(func_cov),
        },
    }

    out_path = os.path.join(dir_path, "coverage_filtered.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return True


def main(root_dir: str, data_file_json: str):
    allowed_files, function_keys, function_name_set, function_class_set = load_data_file(data_file_json)

    for cur_dir, _, _ in os.walk(root_dir):
        process_one_dir(cur_dir, allowed_files, function_keys, function_name_set, function_class_set)


if __name__ == "__main__":
    # 修改成你的实际路径
    ROOT_DIR = "test_results/java/commons-jxpath"
    DATA_FILE_JSON = "data_file.json"
    main(ROOT_DIR, DATA_FILE_JSON)
#!/usr/bin/env python3
"""
为 Surefire 报告中失败的测试方法自动添加 @Ignore / @Disabled 注解。
用法：
    python add_ignore_to_failures.py [--reports reports] [--src src/test/java]
"""

import sys
import os
import re
import glob
import xml.etree.ElementTree as ET
from collections import defaultdict


def find_java_file(classname: str, src_root: str = "src/test/java") -> str:
    """
    根据全限定类名推测对应的 Java 源文件路径。
    支持内部类（类名中包含 $）：返回外部类的文件。
    """
    # 内部类取外部类名
    outer = classname.split("$")[0]
    parts = outer.split(".")
    # 最后一个部分是文件名，前面是包路径
    if len(parts) < 1:
        raise ValueError(f"Invalid classname: {classname}")
    simple_name = parts[-1]
    package_path = os.path.join(*parts[:-1]) if len(parts) > 1 else ""
    return os.path.join(src_root, package_path, f"{simple_name}.java")


def find_method_range(
    lines: list, classname: str, method_name: str
) -> tuple | None:
    """
    在文件行列表中查找指定类中的方法声明位置。
    返回 (start_line_idx, end_line_idx) 或 None。
    优先在内部类体范围内查找，找不到时回退到整个文件查找。
    """
    # 如果类名包含 $，说明是内部类，需要先定位内部类体范围
    inner_class = None
    if "$" in classname:
        inner_class = classname.split("$")[-1]

    def _search_in(lines_subset, base_index):
        """在 lines_subset 中搜索方法声明，返回绝对行号"""
        method_pat = re.compile(r"\b" + re.escape(method_name) + r"\s*\(")
        for i, line in enumerate(lines_subset):
            if method_pat.search(line):
                return base_index + i
        return None

    # 如果存在内部类，先找出该内部类的范围
    if inner_class:
        # 简单匹配 "class InnerName" 或 "static class InnerName"
        class_pat = re.compile(
            r"(?:static\s+)?class\s+" + re.escape(inner_class) + r"\b"
        )
        class_start = None
        for i, line in enumerate(lines):
            if class_pat.search(line):
                class_start = i
                break
        if class_start is not None:
            # 大括号配对找到类体结束
            brace = 0
            in_class = False
            class_end = class_start
            for j in range(class_start, len(lines)):
                brace += lines[j].count("{")
                if "{" in lines[j]:
                    in_class = True
                brace -= lines[j].count("}")
                if in_class and brace <= 0:
                    class_end = j
                    break
            # 在该范围内搜索方法
            meth_idx = _search_in(
                lines[class_start : class_end + 1], class_start
            )
            if meth_idx is not None:
                return meth_idx

    # 回退：在整个文件中搜索（可能会错误匹配外部类的同名方法，但测试类通常只有一套）
    return _search_in(lines, 0)


def add_annotation(filepath: str, classname: str, method_name: str) -> bool:
    """
    在指定 Java 文件中为指定方法添加 @Ignore / @Disabled，
    自动检测 JUnit 版本并补充 import。
    返回是否成功。
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines(keepends=True)
    except Exception as e:
        print(f"  ! 读取文件失败 {filepath}: {e}")
        return False

    method_idx = find_method_range(lines, classname, method_name)
    if method_idx is None:
        print(f"  ? 在文件中未找到方法 {method_name}，可能为纯内部类或源码不一致")
        return False

    # 检测 JUnit 版本
    if "org.junit.jupiter.api" in content:
        junit_ver = 5
        annotation = "@Disabled"
        import_line = "import org.junit.jupiter.api.Disabled;\n"
    elif "org.junit.Test" in content or "junit.framework" in content:
        junit_ver = 4
        annotation = "@Ignore"
        import_line = "import org.junit.Ignore;\n"
    else:
        # 默认按 JUnit 4 处理
        junit_ver = 4
        annotation = "@Ignore"
        import_line = "import org.junit.Ignore;\n"

    # 检查是否已有该注解
    check_lines = lines[max(0, method_idx - 3) : method_idx]
    if any(annotation in l for l in check_lines):
        print(f"  ✓ 注解已存在，跳过")
        return True

    # 补充 import 语句（如果需要）
    if import_line.strip() not in content:
        # 寻找最后一个 import 之后的位置
        last_import = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("import "):
                last_import = i
        if last_import >= 0:
            lines.insert(last_import + 1, import_line)
            method_idx += 1  # 方法行号后移
        else:
            # 没有 import，插入到 package 之后
            pkg_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("package "):
                    pkg_idx = i
                    break
            insert_at = pkg_idx + 1 if pkg_idx >= 0 else 0
            lines.insert(insert_at, import_line)
            method_idx += 1

    # 确定缩进
    method_line = lines[method_idx]
    indent = method_line[: len(method_line) - len(method_line.lstrip())]
    annotation_line = indent + annotation + "\n"

    # 检查方法上是否已有其他注解（如 @Test），将 @Ignore 放在它们之前
    # 简单处理：直接插入在当前方法声明前一行（即 method_idx 之前）
    lines.insert(method_idx, annotation_line)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"  ✓ 已添加 {annotation} 到 {method_name}")
        return True
    except Exception as e:
        print(f"  ! 写入文件失败 {filepath}: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="自动为失败测试添加 @Ignore/@Disabled")
    parser.add_argument("--reports", default="reports", help="Surefire 报告目录")
    parser.add_argument("--src", default="src/test/java", help="测试源码根目录")
    args = parser.parse_args()

    reports_dir = args.reports
    src_dir = args.src

    # 收集所有 XML 报告
    xml_files = glob.glob(os.path.join(reports_dir, "**/*.xml"), recursive=True)
    if not xml_files:
        print("未找到任何 Surefire XML 报告。")
        sys.exit(1)

    # 解析失败用例
    failures = defaultdict(set)  # classname -> set of method_names
    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except Exception:
            print(f"警告：无法解析 {xml_file}，跳过")
            continue
        for tc in root.findall("testcase"):
            if tc.find("failure") is not None or tc.find("error") is not None:
                classname = tc.get("classname", "").strip()
                name = tc.get("name", "").strip()
                if classname and name:
                    failures[classname].add(name)

    if not failures:
        print("未发现任何失败的测试用例。")
        return

    total_methods = sum(len(v) for v in failures.values())
    print(f"发现 {len(failures)} 个类中的 {total_methods} 个失败测试方法\n")

    success = 0
    for classname, methods in failures.items():
        filepath = find_java_file(classname, src_dir)
        if not os.path.isfile(filepath):
            print(f"[跳过] 找不到源文件: {classname} ({filepath})")
            continue
        print(f"处理 {classname}")
        for method in methods:
            if add_annotation(filepath, classname, method):
                success += 1
            else:
                print(f"  ✗ 未能为 {method} 添加注解")

    print(f"\n完成：成功注解 {success}/{total_methods} 个失败测试方法。")
    if success < total_methods:
        print("部分测试可能因内部类定位失败或文件缺失需手动处理。")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
使用 tree-sitter 删除 JSON 文件中 code 字段的注释（及可选 docstring）

支持语言：
    - python
    - java
    - javascript

功能：
    - 删除普通注释
    - Python 可选删除 docstring
    - 保留字符串内容
    - 保留代码结构
    - 支持 JSON 数组 / 单对象
"""

import sys
import json
import re
import argparse

from tree_sitter import Parser
from tree_sitter_languages import get_language


# ============================================================================
# 语言映射
# ============================================================================

LANG_MAP = {
    "python": "python",
    "py": "python",
    "java": "java",
    "javascript": "javascript",
    "js": "javascript",
}


# ============================================================================
# Tree-sitter Language
# ============================================================================

def get_lang(name):
    """
    根据字符串获取 tree-sitter Language 对象
    """

    name = name.lower()

    if name not in LANG_MAP:
        raise ValueError(f"Unsupported language: {name}")

    return get_language(LANG_MAP[name])


# ============================================================================
# Parser
# ============================================================================

def create_parser(lang):
    """
    兼容不同版本 py-tree-sitter 的 Parser 创建方式
    """

    parser = Parser()

    try:
        # 老版本
        parser.set_language(lang)
    except AttributeError:
        # 新版本
        parser.language = lang

    return parser


# ============================================================================
# Comment Collection
# ============================================================================

def collect_comment_nodes(node, comments):
    """
    递归收集 comment 节点

    JavaScript / Java 可能包含：
        - comment
        - line_comment
        - block_comment
    """

    if "comment" in node.type:
        comments.append((node.start_byte, node.end_byte))

    for child in node.children:
        collect_comment_nodes(child, comments)


# ============================================================================
# Python Docstring Collection
# ============================================================================

def collect_python_docstrings(node, docstrings):
    """
    收集 Python docstring

    docstring 本质：

        module/class/function 的第一条 statement
            expression_statement
                string

    注意：
        普通字符串不能删除
    """

    target_parents = {
        "module",
        "class_definition",
        "function_definition",
    }

    if node.type in target_parents:

        body = None

        # module 没有 block
        if node.type == "module":
            body = node
        else:
            for child in node.children:
                if child.type == "block":
                    body = child
                    break

        if body is not None:

            first_stmt = None

            for child in body.children:

                # 只考虑 named node
                if child.is_named and "comment" not in child.type:
                    first_stmt = child
                    break

            if (
                first_stmt is not None
                and first_stmt.type == "expression_statement"
                and first_stmt.child_count > 0
            ):

                first_child = first_stmt.children[0]

                # string / concatenated_string
                if "string" in first_child.type:

                    docstrings.append(
                        (
                            first_stmt.start_byte,
                            first_stmt.end_byte,
                        )
                    )

    for child in node.children:
        collect_python_docstrings(child, docstrings)


# ============================================================================
# Main Remove Logic
# ============================================================================

def remove_comments_and_docstrings(
    code: str,
    language_name: str,
    keep_docstring: bool = False,
    compress_blank_lines: bool = True,
):
    """
    删除注释和 docstring

    Args:
        code:
            源代码字符串

        language_name:
            语言名称

        keep_docstring:
            是否保留 Python docstring

        compress_blank_lines:
            是否压缩连续空行

    Returns:
        清洗后的代码
    """

    lang = get_lang(language_name)

    parser = create_parser(lang)

    source_bytes = code.encode("utf8")

    tree = parser.parse(source_bytes)

    root = tree.root_node

    # parse error warning
    if root.has_error:
        print(
            f"[WARN] Tree-sitter parse error in {language_name}",
            file=sys.stderr,
        )

    remove_ranges = []

    # ----------------------------------------------------------------------
    # 1. 收集普通注释
    # ----------------------------------------------------------------------

    collect_comment_nodes(root, remove_ranges)

    # ----------------------------------------------------------------------
    # 2. Python docstring
    # ----------------------------------------------------------------------

    normalized_lang = LANG_MAP[language_name.lower()]

    if normalized_lang == "python" and not keep_docstring:

        collect_python_docstrings(
            root,
            remove_ranges,
        )

    # ----------------------------------------------------------------------
    # 3. 倒序删除
    # ----------------------------------------------------------------------

    result = bytearray(source_bytes)

    remove_ranges.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    for start, end in remove_ranges:
        del result[start:end]

    cleaned_code = result.decode(
        "utf8",
        errors="replace",
    )

    # ----------------------------------------------------------------------
    # 4. 压缩连续空行
    # ----------------------------------------------------------------------

    if compress_blank_lines:

        cleaned_code = re.sub(
            r"\n\s*\n\s*\n+",
            "\n\n",
            cleaned_code,
        )

    return cleaned_code


# ============================================================================
# JSON Processing
# ============================================================================

def process_json(
    input_file,
    output_file,
    default_lang=None,
    keep_docstring=False,
    compress_blank_lines=True,
):
    """
    处理 JSON 文件
    """

    with open(input_file, "r", encoding="utf8") as f:
        data = json.load(f)

    # 兼容单对象
    if isinstance(data, dict):
        data = [data]

    for idx, item in enumerate(data):

        code = item.get("code")

        if not code:
            continue

        lang_name = item.get("language") or default_lang

        if not lang_name:
            raise ValueError(
                f"Item {idx} missing language field"
            )

        try:

            cleaned_code = remove_comments_and_docstrings(
                code=code,
                language_name=lang_name,
                keep_docstring=keep_docstring,
                compress_blank_lines=compress_blank_lines,
            )

            item["code"] = cleaned_code

        except Exception as e:

            print(
                f"[ERROR] Failed processing item {idx}: {e}",
                file=sys.stderr,
            )

    with open(output_file, "w", encoding="utf8") as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"✅ Saved cleaned JSON to: {output_file}")


# ============================================================================
# CLI
# ============================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Remove comments/docstrings from JSON code fields "
            "using tree-sitter"
        )
    )

    parser.add_argument(
        "input",
        help="Input JSON file",
    )

    parser.add_argument(
        "output",
        help="Output JSON file",
    )

    parser.add_argument(
        "--lang",
        help=(
            "Default language when "
            "'language' field is missing"
        ),
    )

    parser.add_argument(
        "--keep-docstring",
        action="store_true",
        help="Keep Python docstrings",
    )

    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Disable blank line compression",
    )

    args = parser.parse_args()

    try:

        process_json(
            input_file=args.input,
            output_file=args.output,
            default_lang=args.lang,
            keep_docstring=args.keep_docstring,
            compress_blank_lines=not args.no_compress,
        )

    except Exception as e:

        print(f"❌ ERROR: {e}", file=sys.stderr)

        sys.exit(1)


# ============================================================================
# Entry
# ============================================================================

if __name__ == "__main__":
    main()
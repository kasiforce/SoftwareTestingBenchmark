# import tree_sitter_python as tspython
# import tree_sitter_java as tsjava
# import tree_sitter_rust as tsrust
# import tree_sitter_javascript as tsjavascript
# from tree_sitter import Language, Parser

# # 创建各语言的 Language 对象
# PY_LANGUAGE = Language(tspython.language())
# JAVA_LANGUAGE = Language(tsjava.language())
# RUST_LANGUAGE = Language(tsrust.language())
# JS_LANGUAGE = Language(tsjavascript.language())

# # 创建解析器
# python_parser = Parser(PY_LANGUAGE)
# java_parser = Parser(JAVA_LANGUAGE)
# js_parser = Parser(JS_LANGUAGE)


# multi_parser.py
import tree_sitter_languages
from tree_sitter import Parser

# 使用 tree_sitter_languages 获取语言
# PY_LANGUAGE = tree_sitter_languages.get_language('python')
# JAVA_LANGUAGE = tree_sitter_languages.get_language('java')
# RUST_LANGUAGE = tree_sitter_languages.get_language('rust')
# JS_LANGUAGE = tree_sitter_languages.get_language('javascript')


def create_parser(language_name):
    parser = Parser()
    parser.set_language(tree_sitter_languages.get_language(language_name))
    return parser

python_parser = create_parser('python')
java_parser = create_parser('java')
rust_parser = create_parser('rust')
js_parser = create_parser('javascript')

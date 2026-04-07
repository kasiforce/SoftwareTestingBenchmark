import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from multi_parser import rust_parser
from func_select import StratifiedFunctionSelector
from file_select import *


# class RustFocalExtractor:
#     def __init__(self, project_root: str, output_file: str):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file

#         # 初始化 tree-sitter Rust parser
#         self.parser = rust_parser

#         # 忽略的目录和文件模式
#         self.ignore_patterns = self._get_ignore_patterns()

#         # 存储函数信息
#         self.functions = []

#     def _get_ignore_patterns(self) -> Dict[str, Set[str]]:
#         """获取忽略模式"""
#         return {
#             'dirs': {
#                 'target', '.git', '.cargo', 'node_modules',
#                 '__pycache__', '.pytest_cache', '.mypy_cache',
#                 '.idea', '.vscode', 'build', 'dist', '.direnv'
#             },
#             'files': {
#                 'Cargo.lock', '.DS_Store'
#             },
#             'patterns': [
#                 r'^test_', r'_test\.rs$', r'^tests?/', r'^benches/',
#                 r'^examples/', r'\.d$', r'\.so$', r'\.dylib$', r'\.dll$', r'\.rlib$'
#             ]
#         }

#     def extract_project_focal_functions(self) -> List[Dict]:
#         """提取项目中所有 Rust 文件的公有函数"""
#         print(f"开始提取 Rust 项目: {self.project_root}")

#         # 遍历项目目录
#         for root, dirs, files in os.walk(self.project_root):
#             # 过滤忽略的目录
#             dirs[:] = [d for d in dirs if not self._should_ignore_dir(d, root)]

#             for file in files:
#                 if not file.endswith('.rs'):
#                     continue

#                 file_path = os.path.join(root, file)

#                 # 检查是否应该忽略该文件
#                 if self._should_ignore_file(file, file_path):
#                     continue

#                 try:
#                     # 提取文件中的函数
#                     functions_in_file = self._extract_functions_from_file(file_path)
#                     if functions_in_file:
#                         self.functions.extend(functions_in_file)
#                         print(f"  在 {self._get_relative_path(file_path)} 中找到 {len(functions_in_file)} 个公有函数")

#                 except Exception as e:
#                     print(f"处理文件 {file_path} 时出错: {e}")
#                     continue

#         # 保存结果
#         self._save_to_json()
#         print(f"\n提取完成，共找到 {len(self.functions)} 个公有函数")
#         print(f"结果已保存到: {self.output_file}")

#         return self.functions

#     def _should_ignore_dir(self, dir_name: str, root_path: str) -> bool:
#         """检查是否应该忽略目录"""
#         # 检查目录名是否在忽略列表中
#         if dir_name in self.ignore_patterns['dirs']:
#             return True

#         # 检查是否为隐藏目录
#         if dir_name.startswith('.'):
#             return True

#         # 检查路径是否匹配忽略模式
#         relative_path = os.path.relpath(os.path.join(root_path, dir_name), self.project_root)
#         for pattern in self.ignore_patterns['patterns']:
#             if re.search(pattern, relative_path):
#                 return True

#         return False

#     def _should_ignore_file(self, file_name: str, file_path: str) -> bool:
#         """检查是否应该忽略文件"""
#         # 检查文件名是否在忽略列表中
#         if file_name in self.ignore_patterns['files']:
#             return True

#         # 检查是否为测试文件
#         if file_name.startswith('test_') or file_name.endswith('_test.rs'):
#             return True

#         # 检查路径是否匹配忽略模式
#         relative_path = self._get_relative_path(file_path)
#         for pattern in self.ignore_patterns['patterns']:
#             if re.search(pattern, relative_path):
#                 return True

#         return False

#     def _get_relative_path(self, file_path: str) -> str:
#         """获取相对于项目根目录的路径"""
#         return os.path.relpath(file_path, self.project_root)

#     def _extract_functions_from_file(self, file_path: str) -> List[Dict]:
#         """从文件中提取所有公有函数"""
#         with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
#             content = f.read()

#         # 解析 Rust 代码
#         tree = self.parser.parse(bytes(content, 'utf-8'))
#         root_node = tree.root_node

#         # 首先提取文件中所有的结构体定义
#         struct_definitions = self._extract_all_struct_definitions(root_node, content)

#         # 提取文件中所有的impl块中的new函数
#         impl_new_functions = self._extract_impl_new_functions(root_node, content)

#         # 提取函数
#         functions = []
#         self._traverse_and_extract(
#             root_node,
#             content,
#             file_path,
#             [],  # 当前模块路径
#             [],  # 当前结构体上下文
#             [],  # 当前 trait 上下文
#             [],  # 当前 impl 上下文
#             functions,
#             struct_definitions,
#             impl_new_functions
#         )

#         return functions

#     def _extract_all_struct_definitions(self, root_node, content: str) -> Dict[str, str]:
#         """提取文件中所有的结构体定义，只保留完整代码"""
#         struct_definitions = {}

#         def extract_struct(node):
#             if node.type == 'struct_item':
#                 struct_name = None

#                 # 提取结构体名
#                 for child in node.children:
#                     if child.type == 'type_identifier':
#                         struct_name = self._get_node_text(child, content)
#                         break

#                 if struct_name:
#                     # 获取完整的结构体定义代码
#                     struct_code = content[node.start_byte:node.end_byte]
#                     struct_definitions[struct_name] = struct_code

#             for child in node.children:
#                 extract_struct(child)

#         extract_struct(root_node)
#         return struct_definitions

#     def _extract_impl_new_functions(self, root_node, content: str) -> Dict[str, str]:
#         """提取文件中所有impl块中的new函数，只保留完整代码"""
#         new_functions = {}

#         def extract_impl_new(node):
#             if node.type == 'impl_item':
#                 impl_type = None

#                 # 提取impl的类型
#                 for child in node.children:
#                     if child.type == 'type_identifier':
#                         impl_type = self._get_node_text(child, content)
#                         break

#                 if impl_type:
#                     # 查找impl块中的new函数
#                     for child in node.children:
#                         if child.type == 'declaration_list':
#                             for func_child in child.children:
#                                 if func_child.type == 'function_item':
#                                     func_name = None

#                                     # 提取函数名
#                                     for subchild in func_child.children:
#                                         if subchild.type == 'identifier':
#                                             func_name = self._get_node_text(subchild, content)
#                                             break

#                                     if func_name == 'new':
#                                         # 检查是否为关联函数（没有self参数）
#                                         if self._is_associated_function(func_child, content):
#                                             # 提取函数代码
#                                             func_code = content[func_child.start_byte:func_child.end_byte]
#                                             new_functions[impl_type] = func_code

#             for child in node.children:
#                 extract_impl_new(child)

#         extract_impl_new(root_node)
#         return new_functions

#     def _traverse_and_extract(
#         self,
#         node,
#         content: str,
#         file_path: str,
#         module_path: List[str],
#         struct_stack: List[str],  # 只存储结构体名
#         trait_stack: List[str],   # 只存储trait名
#         impl_stack: List[str],    # 只存储impl类型
#         functions: List[Dict],
#         struct_definitions: Dict[str, str],
#         impl_new_functions: Dict[str, str]
#     ):
#         """遍历语法树并提取函数"""

#         # 处理模块声明
#         if node.type == 'mod_item':
#             module_name = self._get_node_text(node.child_by_field_name('name'), content)
#             if module_name:
#                 module_path.append(module_name)
#                 # 继续遍历模块体
#                 for child in node.children:
#                     self._traverse_and_extract(
#                         child, content, file_path, module_path.copy(),
#                         struct_stack, trait_stack, impl_stack, functions,
#                         struct_definitions, impl_new_functions
#                     )
#                 return

#         # 处理结构体定义
#         elif node.type == 'struct_item':
#             struct_name = None
#             for child in node.children:
#                 if child.type == 'type_identifier':
#                     struct_name = self._get_node_text(child, content)
#                     break

#             if struct_name:
#                 struct_stack.append(struct_name)
#                 # 继续遍历结构体体
#                 for child in node.children:
#                     self._traverse_and_extract(
#                         child, content, file_path, module_path,
#                         struct_stack.copy(), trait_stack, impl_stack, functions,
#                         struct_definitions, impl_new_functions
#                     )
#                 return

#         # 处理 trait 定义
#         elif node.type == 'trait_item':
#             trait_name = None
#             for child in node.children:
#                 if child.type == 'type_identifier':
#                     trait_name = self._get_node_text(child, content)
#                     break

#             if trait_name:
#                 trait_stack.append(trait_name)
#                 # 继续遍历 trait 体
#                 for child in node.children:
#                     self._traverse_and_extract(
#                         child, content, file_path, module_path,
#                         struct_stack, trait_stack.copy(), impl_stack, functions,
#                         struct_definitions, impl_new_functions
#                     )
#                 return

#         # 处理 impl 块
#         elif node.type == 'impl_item':
#             impl_type = None

#             for child in node.children:
#                 if child.type == 'type_identifier':
#                     impl_type = self._get_node_text(child, content)
#                     break

#             if impl_type:
#                 impl_stack.append(impl_type)
#                 # 继续遍历 impl 体
#                 for child in node.children:
#                     self._traverse_and_extract(
#                         child, content, file_path, module_path,
#                         struct_stack, trait_stack, impl_stack.copy(), functions,
#                         struct_definitions, impl_new_functions
#                     )
#                 return

#         # 处理函数定义
#         elif node.type == 'function_item':
#             function_info = self._extract_function_info(
#                 node, content, file_path, module_path,
#                 struct_stack, trait_stack, impl_stack,
#                 struct_definitions, impl_new_functions
#             )
#             if function_info:
#                 functions.append(function_info)

#         # 递归遍历子节点
#         for child in node.children:
#             self._traverse_and_extract(
#                 child, content, file_path, module_path,
#                 struct_stack, trait_stack, impl_stack, functions,
#                 struct_definitions, impl_new_functions
#             )

#     def _extract_function_info(
#         self,
#         node,
#         content: str,
#         file_path: str,
#         module_path: List[str],
#         struct_stack: List[str],
#         trait_stack: List[str],
#         impl_stack: List[str],
#         struct_definitions: Dict[str, str],
#         impl_new_functions: Dict[str, str]
#     ) -> Optional[Dict]:
#         """提取函数信息"""
#         # 获取函数名 - 查找 identifier 节点
#         function_name = None
#         for child in node.children:
#             if child.type == 'identifier':
#                 function_name = self._get_node_text(child, content)
#                 break

#         if not function_name:
#             return None

#         # 检查是否为公有函数（包括 pub, pub(crate) 等）
#         if not self._is_public(node, content):
#             return None

#         # 跳过测试函数（带有 #[test] 属性）
#         if self._is_test_function(node, content):
#             return None

#         # 跳过 main 函数
#         if function_name == 'main':
#             return None

#         # 跳过构造函数（new 函数）不作为被测函数
#         if function_name == 'new' and struct_stack:
#             return None

#         # 检查是否为异步函数
#         is_async = self._is_async_function(node, content)

#         # 检查是否为不安全函数
#         is_unsafe = self._is_unsafe_function(node, content)

#         src_file = self._get_relative_path(file_path)

#         # 构建函数信息
#         function_info = {
#             'name': function_name,
#             'src_file': src_file,
#             'test_file': src_file,  # Rust 测试通常写在源文件中
#             'code': content[node.start_byte:node.end_byte],
#             'is_async': is_async,
#             'is_unsafe': is_unsafe,
#             'module_path': module_path.copy(),
#         }

#         # 添加上下文信息 - 简化版本
#         if struct_stack:
#             struct_name = struct_stack[-1]
#             context = {}

#             # 如果有该结构体的定义，添加结构体代码
#             if struct_name in struct_definitions:
#                 context['struct_definition'] = struct_definitions[struct_name]

#             # 如果有该结构体的new函数，添加new函数代码
#             if struct_name in impl_new_functions:
#                 context['new_function'] = impl_new_functions[struct_name]

#             # 只有有上下文信息时才添加
#             if context:
#                 function_info['context'] = context

#         return function_info

#     def _is_public(self, node, content: str) -> bool:
#         """检查节点是否为公有（包括 pub, pub(crate), pub(super) 等）"""
#         for child in node.children:
#             if child.type == 'visibility_modifier':
#                 # 检查 visibility_modifier 的内容是否以 'pub' 开头
#                 text = self._get_node_text(child, content)
#                 if text and text.startswith('pub'):
#                     return True
#         return False

#     def _is_async_function(self, node, content: str) -> bool:
#         """检查是否为异步函数"""
#         # 检查 function_modifiers 节点
#         for child in node.children:
#             if child.type == 'function_modifiers':
#                 text = self._get_node_text(child, content)
#                 if text and 'async' in text:
#                     return True
#         return False

#     def _is_unsafe_function(self, node, content: str) -> bool:
#         """检查是否为不安全函数"""
#         # 检查 function_modifiers 节点
#         for child in node.children:
#             if child.type == 'function_modifiers':
#                 text = self._get_node_text(child, content)
#                 if text and 'unsafe' in text:
#                     return True
#         return False

#     def _is_associated_function(self, node, content: str) -> bool:
#         """检查是否为关联函数（没有 self 参数）"""
#         # 查找参数列表，检查是否有 self_parameter 节点
#         for child in node.children:
#             if child.type == 'parameters':
#                 # 检查参数中是否有 self_parameter
#                 for param_child in child.children:
#                     if param_child.type == 'self_parameter':
#                         return False
#         return True

#     def _is_test_function(self, node, content: str) -> bool:
#         """检查是否为测试函数"""
#         # 检查节点前面是否有 attribute_item 且包含 #[test]
#         current_node = node
#         # 向前查找兄弟节点
#         while current_node:
#             # 检查当前节点的前一个兄弟节点
#             prev_sibling = current_node.prev_sibling
#             if prev_sibling and prev_sibling.type == 'attribute_item':
#                 attr_text = self._get_node_text(prev_sibling, content)
#                 if attr_text and ('#[test]' in attr_text or '#[cfg(test)]' in attr_text):
#                     return True

#             # 如果前一个节点是注释，继续向前查找
#             if prev_sibling and prev_sibling.type in ('line_comment', 'block_comment'):
#                 current_node = prev_sibling
#                 continue
#             else:
#                 break

#         return False

#     def _get_node_text(self, node, content: str) -> Optional[str]:
#         """获取节点的文本内容"""
#         if node:
#             text = content[node.start_byte:node.end_byte]
#             return text.decode('utf-8') if isinstance(text, bytes) else text
#         return None

#     def _save_to_json(self):
#         """保存提取结果到 JSON 文件"""
#         # 转换为可序列化的格式
#         serializable_functions = []
#         for func in self.functions:
#             # 复制函数信息
#             func_copy = func.copy()

#             # 确保所有字段都是可序列化的
#             for key, value in func_copy.items():
#                 if isinstance(value, bytes):
#                     func_copy[key] = value.decode('utf-8', errors='ignore')

#             serializable_functions.append(func_copy)

#         # 写入 JSON 文件
#         with open(self.output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable_functions, f, indent=2, ensure_ascii=False)


class RustProjectTestScopeExtractor:
    def __init__(self, project_root: str, file_list, output_file: str = None,
                 min_loc_threshold: int = 5, random_seed: int = 42):
        """
        初始化增强版提取器

        Args:
            project_root: 项目根目录
            file_list: 文件列表
            output_file: 输出文件路径（可选）
            min_loc_threshold: 最小行数阈值
            random_seed: 随机种子
        """
        self.project_root = project_root
        self.files = file_list
        self.output_file = output_file
        self.min_loc_threshold = min_loc_threshold
        self.random_seed = random_seed

        # 初始化 tree-sitter Rust parser
        from multi_parser import rust_parser
        self.parser = rust_parser

        # 存储函数信息
        self.functions = []

        # getter/setter模式的正则表达式 (Rust版本)
        self.getter_setter_patterns = [
            r'^get_',  # get_
            r'^set_',  # set_
            r'^is_',  # is_
            r'^has_',  # has_
            r'^create_',  # create_
            r'^build_',  # build_
            r'^to_',  # to_
            r'^from_',  # from_
            r'^as_',  # as_
            r'^into_',  # into_
        ]

        # 初始化选择器
        self.selector = StratifiedFunctionSelector(random_seed=random_seed)

        # 存储统计信息
        self.stats = defaultdict(lambda: defaultdict(int))
        self.selection_results = []

    def _compute_complexity_and_loc(self, code):
        """使用lizard计算圈复杂度、代码行数和参数数量"""
        complexity = 0
        loc = 0
        param_count = 0
        try:
            report = lizard.analyze_file.analyze_source_code("temp.rs", code)

            if report.function_list:
                complexity = report.function_list[0].__dict__['cyclomatic_complexity']
                loc = report.function_list[0].__dict__['nloc']
                param_count = len(report.function_list[0].__dict__['full_parameters'])

        except Exception as e:
            # 如果分析失败，使用默认值
            complexity = 1
            loc = len([line for line in code.split('\n') if line.strip()])
            # 尝试从代码中提取参数数量
            try:
                # 匹配Rust函数参数部分
                param_match = re.search(r'\((.*?)\)', code.split('\n')[0])
                if param_match:
                    param_text = param_match.group(1)
                    # 过滤掉类型注解，只保留参数名
                    params = [p.split(':')[0].strip() for p in param_text.split(',') if p.strip()]
                    param_count = len([p for p in params if p and p != 'self'])
            except:
                param_count = 0

        return complexity, loc, param_count

    def _get_relative_path(self, file_path: str) -> str:
        """获取相对于项目根目录的路径"""
        return os.path.relpath(file_path, self.project_root)

    def _extract_functions_from_file(self, file_path: str) -> List[Dict]:
        """从文件中提取所有公有函数"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 解析 Rust 代码
        tree = self.parser.parse(bytes(content, 'utf-8'))
        root_node = tree.root_node

        # 首先提取文件中所有的结构体定义
        struct_definitions = self._extract_all_struct_definitions(root_node, content)

        # 提取文件中所有的impl块中的new函数
        impl_new_functions = self._extract_impl_new_functions(root_node, content)

        # 提取函数
        functions = []
        self._traverse_and_extract(
            root_node,
            content,
            file_path,
            [],  # 当前模块路径
            [],  # 当前结构体上下文
            [],  # 当前 trait 上下文
            [],  # 当前 impl 上下文
            functions,
            struct_definitions,
            impl_new_functions
        )

        return functions

    def _extract_all_struct_definitions(self, root_node, content: str) -> Dict[str, str]:
        """提取文件中所有的结构体定义，只保留完整代码"""
        struct_definitions = {}

        def extract_struct(node):
            if node.type == 'struct_item':
                struct_name = None

                # 提取结构体名
                for child in node.children:
                    if child.type == 'type_identifier':
                        struct_name = self._get_node_text(child, content)
                        break

                if struct_name:
                    # 获取完整的结构体定义代码
                    struct_code = content[node.start_byte:node.end_byte]
                    struct_definitions[struct_name] = struct_code

            for child in node.children:
                extract_struct(child)

        extract_struct(root_node)
        return struct_definitions

    def _extract_impl_new_functions(self, root_node, content: str) -> Dict[str, str]:
        """提取文件中所有impl块中的new函数，只保留完整代码"""
        new_functions = {}

        def extract_impl_new(node):
            if node.type == 'impl_item':
                impl_type = None

                # 提取impl的类型
                for child in node.children:
                    if child.type == 'type_identifier':
                        impl_type = self._get_node_text(child, content)
                        break

                if impl_type:
                    # 查找impl块中的new函数
                    for child in node.children:
                        if child.type == 'declaration_list':
                            for func_child in child.children:
                                if func_child.type == 'function_item':
                                    func_name = None

                                    # 提取函数名
                                    for subchild in func_child.children:
                                        if subchild.type == 'identifier':
                                            func_name = self._get_node_text(subchild, content)
                                            break

                                    if func_name == 'new':
                                        # 检查是否为关联函数（没有self参数）
                                        if self._is_associated_function(func_child, content):
                                            # 提取函数代码
                                            func_code = content[func_child.start_byte:func_child.end_byte]
                                            new_functions[impl_type] = func_code

            for child in node.children:
                extract_impl_new(child)

        extract_impl_new(root_node)
        return new_functions

    def _traverse_and_extract(
            self,
            node,
            content: str,
            file_path: str,
            module_path: List[str],
            struct_stack: List[str],  # 只存储结构体名
            trait_stack: List[str],  # 只存储trait名
            impl_stack: List[str],  # 只存储impl类型
            functions: List[Dict],
            struct_definitions: Dict[str, str],
            impl_new_functions: Dict[str, str]
    ):
        """遍历语法树并提取函数"""

        # 处理模块声明
        if node.type == 'mod_item':
            module_name = self._get_node_text(node.child_by_field_name('name'), content)
            if module_name:
                module_path.append(module_name)
                # 继续遍历模块体
                for child in node.children:
                    self._traverse_and_extract(
                        child, content, file_path, module_path.copy(),
                        struct_stack, trait_stack, impl_stack, functions,
                        struct_definitions, impl_new_functions
                    )
                return

        # 处理结构体定义
        elif node.type == 'struct_item':
            struct_name = None
            for child in node.children:
                if child.type == 'type_identifier':
                    struct_name = self._get_node_text(child, content)
                    break

            if struct_name:
                struct_stack.append(struct_name)
                # 继续遍历结构体体
                for child in node.children:
                    self._traverse_and_extract(
                        child, content, file_path, module_path,
                        struct_stack.copy(), trait_stack, impl_stack, functions,
                        struct_definitions, impl_new_functions
                    )
                return

        # 处理 trait 定义
        elif node.type == 'trait_item':
            trait_name = None
            for child in node.children:
                if child.type == 'type_identifier':
                    trait_name = self._get_node_text(child, content)
                    break

            if trait_name:
                trait_stack.append(trait_name)
                # 继续遍历 trait 体
                for child in node.children:
                    self._traverse_and_extract(
                        child, content, file_path, module_path,
                        struct_stack, trait_stack.copy(), impl_stack, functions,
                        struct_definitions, impl_new_functions
                    )
                return

        # 处理 impl 块
        elif node.type == 'impl_item':
            impl_type = None

            for child in node.children:
                if child.type == 'type_identifier':
                    impl_type = self._get_node_text(child, content)
                    break

            if impl_type:
                impl_stack.append(impl_type)
                # 继续遍历 impl 体
                for child in node.children:
                    self._traverse_and_extract(
                        child, content, file_path, module_path,
                        struct_stack, trait_stack, impl_stack.copy(), functions,
                        struct_definitions, impl_new_functions
                    )
                return

        # 处理函数定义
        elif node.type == 'function_item':
            function_info = self._extract_function_info(
                node, content, file_path, module_path,
                struct_stack, trait_stack, impl_stack,
                struct_definitions, impl_new_functions
            )
            if function_info:
                functions.append(function_info)

        # 递归遍历子节点
        for child in node.children:
            self._traverse_and_extract(
                child, content, file_path, module_path,
                struct_stack, trait_stack, impl_stack, functions,
                struct_definitions, impl_new_functions
            )

    def _extract_function_info(
            self,
            node,
            content: str,
            file_path: str,
            module_path: List[str],
            struct_stack: List[str],
            trait_stack: List[str],
            impl_stack: List[str],
            struct_definitions: Dict[str, str],
            impl_new_functions: Dict[str, str]
    ) -> Optional[Dict]:
        """提取函数信息"""
        # 获取函数名 - 查找 identifier 节点
        function_name = None
        for child in node.children:
            if child.type == 'identifier':
                function_name = self._get_node_text(child, content)
                break

        if not function_name:
            return None

        # 检查是否为公有函数（包括 pub, pub(crate) 等）
        if not self._is_public(node, content):
            return None

        # 跳过测试函数（带有 #[test] 属性）
        if self._is_test_function(node, content):
            return None

        # 跳过 main 函数
        if function_name == 'main':
            return None

        # 跳过构造函数（new 函数）不作为被测函数
        if function_name == 'new' and struct_stack:
            return None

        # 检查是否为异步函数
        is_async = self._is_async_function(node, content)

        # 检查是否为不安全函数
        is_unsafe = self._is_unsafe_function(node, content)

        # 获取函数代码
        func_code = content[node.start_byte:node.end_byte]

        # 使用lizard计算复杂度指标
        complexity, loc, param_count = self._compute_complexity_and_loc(func_code)

        src_file = self._get_relative_path(file_path)

        # 构建函数信息
        function_info = {
            'name': function_name,
            'src_file': src_file,
            'test_file': src_file,  # Rust 测试通常写在源文件中
            'code': func_code,
            'is_async': is_async,
            'is_unsafe': is_unsafe,
            'module_path': module_path.copy(),
            'complexity': complexity,
            'loc': loc,
            'param_count': param_count
        }

        # 添加上下文信息
        if struct_stack:
            struct_name = struct_stack[-1]
            function_info['struct_name'] = struct_name

            context = {}

            # 如果有该结构体的定义，添加结构体代码
            if struct_name in struct_definitions:
                context['struct_definition'] = struct_definitions[struct_name]

            # 如果有该结构体的new函数，添加new函数代码
            if struct_name in impl_new_functions:
                context['new_function'] = impl_new_functions[struct_name]

            # 只有有上下文信息时才添加
            if context:
                function_info['context'] = context

        return function_info

    def _is_public(self, node, content: str) -> bool:
        """检查节点是否为公有（包括 pub, pub(crate), pub(super) 等）"""
        for child in node.children:
            if child.type == 'visibility_modifier':
                # 检查 visibility_modifier 的内容是否以 'pub' 开头
                text = self._get_node_text(child, content)
                if text and text.startswith('pub'):
                    return True
        return False

    def _is_async_function(self, node, content: str) -> bool:
        """检查是否为异步函数"""
        # 检查 function_modifiers 节点
        for child in node.children:
            if child.type == 'function_modifiers':
                text = self._get_node_text(child, content)
                if text and 'async' in text:
                    return True
        return False

    def _is_unsafe_function(self, node, content: str) -> bool:
        """检查是否为不安全函数"""
        # 检查 function_modifiers 节点
        for child in node.children:
            if child.type == 'function_modifiers':
                text = self._get_node_text(child, content)
                if text and 'unsafe' in text:
                    return True
        return False

    def _is_associated_function(self, node, content: str) -> bool:
        """检查是否为关联函数（没有 self 参数）"""
        # 查找参数列表，检查是否有 self_parameter 节点
        for child in node.children:
            if child.type == 'parameters':
                # 检查参数中是否有 self_parameter
                for param_child in child.children:
                    if param_child.type == 'self_parameter':
                        return False
        return True

    def _is_test_function(self, node, content: str) -> bool:
        """检查是否为测试函数"""
        # 检查节点前面是否有 attribute_item 且包含 #[test]
        current_node = node
        # 向前查找兄弟节点
        while current_node:
            # 检查当前节点的前一个兄弟节点
            prev_sibling = current_node.prev_sibling
            if prev_sibling and prev_sibling.type == 'attribute_item':
                attr_text = self._get_node_text(prev_sibling, content)
                if attr_text and ('#[test]' in attr_text or '#[cfg(test)]' in attr_text):
                    return True

            # 如果前一个节点是注释，继续向前查找
            if prev_sibling and prev_sibling.type in ('line_comment', 'block_comment'):
                current_node = prev_sibling
                continue
            else:
                break

        return False

    def _get_node_text(self, node, content: str) -> Optional[str]:
        """获取节点的文本内容"""
        if node:
            text = content[node.start_byte:node.end_byte]
            return text.decode('utf-8') if isinstance(text, bytes) else text
        return None

    # 3.1 文件内候选函数过滤（硬规则）
    def _should_filter_method(self, method_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断是否应该过滤该方法

        Returns:
            tuple: (是否过滤, 过滤原因)
        """
        method_code = method_info.get('code', '')
        method_name = method_info.get('name', '')
        loc = method_info.get('loc', 0)
        cc = method_info.get('complexity', 1)

        # 规则1: trivial functions（LOC < N & CC = 1）
        if loc < self.min_loc_threshold and cc == 1:
            return True, f"trivial (LOC={loc}<{self.min_loc_threshold} & CC={cc}=1)"

        # 规则2: getter / setter（模式匹配）
        if self._is_getter_setter(method_name):
            return True, "getter/setter"

        # 规则3: 无返回值且无状态修改
        if self._no_return_no_state_change(method_code, method_name):
            return True, "无返回值无状态修改"

        # 规则4: auto-generated / inline wrappers
        if self._is_trivial_wrapper(method_code, method_name, loc):
            return True, "简单包装器"

        return False, ""

    def _is_getter_setter(self, method_name: str) -> bool:
        """判断是否是getter/setter方法"""
        for pattern in self.getter_setter_patterns:
            if re.match(pattern, method_name):
                return True
        return False

    def _no_return_no_state_change(self, method_code: str, method_name: str) -> bool:
        """判断是否无返回值且无状态修改"""
        # 检查是否有return语句
        has_return = re.search(r'\breturn\b', method_code) is not None

        # 检查是否有字段赋值（Rust中的赋值）
        has_field_assignment = False
        lines = method_code.split('\n')
        for line in lines:
            if '=' in line and ('self.' in line or 'mut ' in line):
                has_field_assignment = True
                break

        # 如果既没有return也没有字段赋值，则可能是unit函数
        if not has_return and not has_field_assignment:
            # 排除一些特殊情况
            excluded_names = ['init', 'setup', 'start', 'run', 'execute', 'process', 'handle', 'drop']
            if method_name.lower() not in excluded_names:
                return True

        return False

    def _is_trivial_wrapper(self, method_code: str, method_name: str, loc: int) -> bool:
        """判断是否是简单包装器"""
        if loc <= 3:  # 非常短的方法
            lines = [l.strip() for l in method_code.split('\n') if l.strip()]
            effective_lines = [l for l in lines if not l.startswith('//') and not l.startswith('/*')]

            if len(effective_lines) <= 2:
                # 排除一些重要方法
                important_methods = ['run', 'execute', 'process', 'handle', 'main']
                if method_name not in important_methods:
                    return True

        return False

    # 主提取和选择流程
    def extract_and_select_functions(self) -> List[Dict[str, Any]]:
        """
        完整的提取和选择流程：
        1. 解析项目提取所有方法
        2. 应用过滤规则
        3. 对每个文件进行分层抽样
        """
        # 1. 提取所有函数
        print(f"开始提取项目函数，文件数量: {len(self.files)}")

        all_functions = []

        for file_path in self.files:
            try:
                print(f"处理文件: {os.path.basename(file_path)}")
                functions_in_file = self._extract_functions_from_file(file_path)
                if functions_in_file:
                    all_functions.extend(functions_in_file)
                    print(f"  找到 {len(functions_in_file)} 个公有函数")

            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
                continue

        # 按文件分组方法
        methods_by_file = defaultdict(list)
        for func in all_functions:
            # 将相对路径转换回绝对路径以便分组
            rel_path = func['src_file']
            abs_path = os.path.join(self.project_root, rel_path)
            methods_by_file[abs_path].append(func)

        all_selected_methods = []

        # 处理每个文件
        for file_path, file_methods in methods_by_file.items():
            try:
                file_name = os.path.basename(file_path)
                print(f"\n处理文件: {file_name}")

                # 步骤2: 应用硬规则过滤
                candidate_methods = []
                filtered_methods = []

                for method in file_methods:
                    should_filter, filter_reason = self._should_filter_method(method)

                    if should_filter:
                        filtered_methods.append({
                            **method,
                            'filter_reason': filter_reason
                        })
                        self.stats[file_name]['filtered'] += 1
                    else:
                        candidate_methods.append(method)
                        self.stats[file_name]['candidates'] += 1

                print(f"  原始方法数: {len(file_methods)}")
                print(f"  过滤后方法数: {len(candidate_methods)}")
                print(f"  过滤掉的方法数: {len(filtered_methods)}")

                # 步骤3: 分层抽样选择
                if candidate_methods:
                    selection_result = self.selector.select_functions_from_file(
                        file_path, candidate_methods
                    )

                    if selection_result['selected_functions']:
                        # 添加到最终结果
                        for func in selection_result['selected_functions']:
                            # 构建完整方法信息
                            method_info = {
                                "project_root": self.project_root,
                                "name": func['name'],
                                "src_file": func['src_file'],
                                "test_file": func['test_file'],
                                "code": func['code'],
                                "is_async": func.get('is_async', False),
                                "is_unsafe": func.get('is_unsafe', False),
                                "type": "function",
                                # "loc": func.get('loc', 0),
                                # "complexity": func.get('complexity', 1),
                                # "param_count": func.get('param_count', 0),
                                # "func_score": func.get('func_score', 0),
                                # "raw_metrics": func.get('raw_metrics', {}),
                                "module_path": func.get('module_path', [])
                            }

                            # 添加结构体相关信息
                            if func.get('struct_name'):
                                method_info.update({
                                    'struct_name': func.get('struct_name'),
                                    'context': func.get('context', {})
                                })

                            all_selected_methods.append(method_info)

                        # 保存选择结果
                        self.selection_results.append(selection_result)

                        print(f"  选择完成: {len(selection_result['selected_functions'])} 个函数")

                        # 打印分层统计
                        strata_info = selection_result['stratification']
                        if strata_info:
                            print(f"  分层情况:")
                            for tier_name, tier_info in strata_info.items():
                                if tier_info['count'] > 0:
                                    print(f"    {tier_name}: {tier_info['count']} 个函数")
                    else:
                        print(f"    没有选择任何函数")

                # 记录统计
                self.stats[file_name]['total'] = len(file_methods)

            except Exception as e:
                print(f"处理 {file_path} 时出错: {e}")
                continue

        # 保存结果
        if self.output_file:
            self._save_to_json(all_selected_methods)

        # 打印统计报告
        self._print_statistics_report()

        print(f"\n提取完成，共找到 {len(all_functions)} 个公有函数")
        print(f"经过过滤和选择，最终选择了 {len(all_selected_methods)} 个函数")

        return all_selected_methods

    def _print_statistics_report(self):
        """打印统计报告"""
        print("\n" + "=" * 60)
        print("统计报告")
        print("=" * 60)

        total_methods = sum(self.stats[file]['total'] for file in self.stats)
        total_candidates = sum(self.stats[file]['candidates'] for file in self.stats)
        total_filtered = sum(self.stats[file]['filtered'] for file in self.stats)
        total_selected = sum(len(result.get('selected_functions', [])) for result in self.selection_results)

        print(f"总方法数: {total_methods}")
        print(f"候选方法数: {total_candidates}")
        print(f"过滤方法数: {total_filtered}")
        print(f"选择方法数: {total_selected}")
        print(f"涉及文件数: {len(self.selection_results)}")

        # 打印每个文件的选择情况
        for file, stats in self.stats.items():
            if stats.get('total', 0) > 0:
                print(f"\n{file}:")
                print(f"  总方法: {stats.get('total', 0)}")
                print(f"  候选方法: {stats.get('candidates', 0)}")
                print(f"  过滤方法: {stats.get('filtered', 0)}")

    def _save_to_json(self, data: List[Dict[str, Any]]):
        """保存结果到JSON文件"""
        if not self.output_file:
            return

        try:
            # 确保输出目录存在
            # os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n结果已保存到: {self.output_file}")
        except Exception as e:
            print(f"保存JSON文件时出错: {e}")

    def save_to_json(self, output_file: str = None):
        """兼容旧接口"""
        if output_file:
            self.output_file = output_file
        return self.extract_and_select_functions()

    def print_detailed_selection_report(self):
        """打印详细的选择报告"""
        for result in self.selection_results:
            if result['selected_functions']:
                self.selector.print_selection_report(result)
                print()


if __name__ == "__main__":
    project_root = "projects/ndarray"
    output_file = "ndarray_lite.json"

    # 创建分析器实例
    analyzer = FileQualityAnalyzer(
        language="rust",
        random_seed=42,  # 固定随机种子，确保结果可重复
        sampling_k=2  # 每个层级抽取2个文件
    )

    # 完整分析项目
    sample_files = analyzer.analyze_project(
        project_path=project_root,
        group_by_module=True  # 按模块分组
    )

    # 创建提取器并执行
    extractor = RustProjectTestScopeExtractor(
        project_root=project_root,
        file_list=sample_files,
        output_file=output_file,
        min_loc_threshold=5,
        random_seed=42
    )

    selected_methods = extractor.extract_and_select_functions()

# import os
# import json
# import re
# import sys
# import time
# from pathlib import Path
# from typing import List, Dict, Optional, Set
# from multi_parser import rust_parser

# class RustFocalExtractor:
#     def __init__(self, project_root: str, output_file: str):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file

#         # 初始化 tree-sitter Rust parser
#         self.parser = rust_parser

#         # 忽略的目录和文件模式
#         self.ignore_patterns = self._get_ignore_patterns()

#         # 存储函数信息
#         self.functions = []

#         # 统计信息
#         self.stats = {
#             'files_processed': 0,
#             'files_skipped': 0,
#             'functions_found': 0,
#             'start_time': time.time()
#         }

#     def _get_ignore_patterns(self) -> Dict[str, Set[str]]:
#         """获取忽略模式"""
#         return {
#             'dirs': {
#                 'target', '.git', '.cargo', 'node_modules',
#                 '__pycache__', '.pytest_cache', '.mypy_cache',
#                 '.idea', '.vscode', 'build', 'dist', '.direnv'
#             },
#             'files': {
#                 'Cargo.lock', '.DS_Store'
#             },
#             'patterns': [
#                 r'^test_', r'_test\.rs$', r'^tests?/', r'^benches/',
#                 r'^examples/', r'\.d$', r'\.so$', r'\.dylib$', r'\.dll$', r'\.rlib$'
#             ]
#         }

#     def extract_project_focal_functions(self) -> List[Dict]:
#         """提取项目中所有 Rust 文件的公有函数"""
#         print(f"开始提取 Rust 项目: {self.project_root}")
#         print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

#         # 首先统计总文件数
#         total_files = self._count_rust_files()
#         print(f"总 Rust 文件数: {total_files}")

#         processed = 0
#         last_print_time = time.time()

#         # 遍历项目目录
#         for root, dirs, files in os.walk(self.project_root):
#             # 过滤忽略的目录
#             dirs[:] = [d for d in dirs if not self._should_ignore_dir(d, root)]

#             for file in files:
#                 if not file.endswith('.rs'):
#                     continue

#                 file_path = os.path.join(root, file)

#                 # 检查是否应该忽略该文件
#                 if self._should_ignore_file(file, file_path):
#                     self.stats['files_skipped'] += 1
#                     continue

#                 # 进度显示
#                 processed += 1
#                 current_time = time.time()
#                 if current_time - last_print_time > 2.0:  # 每2秒打印一次进度
#                     elapsed = current_time - self.stats['start_time']
#                     print(f"进度: {processed}/{total_files} 文件 ({processed/total_files*100:.1f}%), "
#                           f"已用时: {elapsed:.1f}秒, "
#                           f"找到函数: {len(self.functions)}")
#                     last_print_time = current_time

#                 try:
#                     # 检查文件大小，跳过过大的文件
#                     file_size = os.path.getsize(file_path)
#                     if file_size > 1024 * 1024:  # 跳过大于1MB的文件
#                         print(f"  跳过大文件: {self._get_relative_path(file_path)} ({file_size/1024:.1f}KB)")
#                         self.stats['files_skipped'] += 1
#                         continue

#                     # 提取文件中的函数
#                     functions_in_file = self._extract_functions_from_file(file_path)
#                     if functions_in_file:
#                         self.functions.extend(functions_in_file)
#                         self.stats['functions_found'] += len(functions_in_file)
#                         print(f"  [{processed}/{total_files}] 在 {self._get_relative_path(file_path)} "
#                               f"中找到 {len(functions_in_file)} 个公有函数")

#                     self.stats['files_processed'] += 1

#                 except Exception as e:
#                     print(f"处理文件 {file_path} 时出错: {e}")
#                     self.stats['files_skipped'] += 1
#                     continue

#         # 保存结果
#         self._save_to_json()

#         # 打印统计信息
#         total_time = time.time() - self.stats['start_time']
#         print(f"\n{'='*60}")
#         print(f"提取完成!")
#         print(f"总用时: {total_time:.1f}秒")
#         print(f"处理文件: {self.stats['files_processed']}")
#         print(f"跳过文件: {self.stats['files_skipped']}")
#         print(f"找到函数: {self.stats['functions_found']}")
#         print(f"结果已保存到: {self.output_file}")

#         return self.functions

#     def _count_rust_files(self) -> int:
#         """统计项目中的 Rust 文件总数"""
#         count = 0
#         for root, dirs, files in os.walk(self.project_root):
#             dirs[:] = [d for d in dirs if not self._should_ignore_dir(d, root)]
#             for file in files:
#                 if file.endswith('.rs'):
#                     file_path = os.path.join(root, file)
#                     if not self._should_ignore_file(file, file_path):
#                         count += 1
#         return count

#     def _should_ignore_dir(self, dir_name: str, root_path: str) -> bool:
#         """检查是否应该忽略目录"""
#         # 检查目录名是否在忽略列表中
#         if dir_name in self.ignore_patterns['dirs']:
#             return True

#         # 检查是否为隐藏目录
#         if dir_name.startswith('.'):
#             return True

#         # 检查路径是否匹配忽略模式
#         relative_path = os.path.relpath(os.path.join(root_path, dir_name), self.project_root)
#         for pattern in self.ignore_patterns['patterns']:
#             if re.search(pattern, relative_path):
#                 return True

#         return False

#     def _should_ignore_file(self, file_name: str, file_path: str) -> bool:
#         """检查是否应该忽略文件"""
#         # 检查文件名是否在忽略列表中
#         if file_name in self.ignore_patterns['files']:
#             return True

#         # 检查是否为测试文件
#         if file_name.startswith('test_') or file_name.endswith('_test.rs'):
#             return True

#         # 检查路径是否匹配忽略模式
#         relative_path = self._get_relative_path(file_path)
#         for pattern in self.ignore_patterns['patterns']:
#             if re.search(pattern, relative_path):
#                 return True

#         return False

#     def _get_relative_path(self, file_path: str) -> str:
#         """获取相对于项目根目录的路径"""
#         return os.path.relpath(file_path, self.project_root)

#     def _extract_functions_from_file(self, file_path: str) -> List[Dict]:
#         """从文件中提取所有公有函数"""
#         try:
#             with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
#                 content = f.read()

#             # 解析 Rust 代码
#             tree = self.parser.parse(bytes(content, 'utf-8'))
#             root_node = tree.root_node

#             # 简化：只提取顶层函数，不处理复杂的嵌套结构
#             functions = []
#             self._simple_traverse(root_node, content, file_path, functions)

#             return functions

#         except Exception as e:
#             print(f"  解析文件 {file_path} 失败: {e}")
#             return []

#     def _simple_traverse(self, node, content: str, file_path: str, functions: List[Dict]):
#         """简化的遍历方法，只提取顶级函数"""
#         # 处理函数定义
#         if node.type == 'function_item':
#             function_info = self._extract_simple_function_info(node, content, file_path)
#             if function_info:
#                 functions.append(function_info)

#         # 递归遍历子节点，但限制深度
#         if node.child_count > 0:
#             for child in node.children:
#                 self._simple_traverse(child, content, file_path, functions)

#     def _extract_simple_function_info(self, node, content: str, file_path: str) -> Optional[Dict]:
#         """简化的函数信息提取"""
#         # 获取函数名
#         function_name = None
#         for child in node.children:
#             if child.type == 'identifier':
#                 function_name = self._get_node_text(child, content)
#                 break

#         if not function_name:
#             return None

#         # 检查是否为公有函数
#         if not self._is_public_or_crate_simple(node, content):
#             return None

#         # 跳过测试函数
#         if self._is_test_function_simple(node, content):
#             return None

#         # 跳过 main 函数
#         if function_name == 'main':
#             return None

#         # 跳过构造函数
#         if function_name == 'new':
#             return None

#         src_file = self._get_relative_path(file_path)

#         # 构建函数信息
#         function_info = {
#             'name': function_name,
#             'src_file': src_file,
#             'test_file': src_file,
#             'code': content[node.start_byte:node.end_byte],
#             'is_async': self._is_async_function_simple(node, content),
#             'is_unsafe': self._is_unsafe_function_simple(node, content),
#             'module_path': [],
#         }

#         return function_info

#     def _is_public_or_crate_simple(self, node, content: str) -> bool:
#         """简化的公有性检查"""
#         for child in node.children:
#             if child.type == 'visibility_modifier':
#                 text = self._get_node_text(child, content)
#                 if text and text.startswith('pub'):
#                     return True
#         return False

#     def _is_async_function_simple(self, node, content: str) -> bool:
#         """简化的异步函数检查"""
#         for child in node.children:
#             if child.type == 'function_modifiers':
#                 text = self._get_node_text(child, content)
#                 if text and 'async' in text:
#                     return True
#         return False

#     def _is_unsafe_function_simple(self, node, content: str) -> bool:
#         """简化的不安全函数检查"""
#         for child in node.children:
#             if child.type == 'function_modifiers':
#                 text = self._get_node_text(child, content)
#                 if text and 'unsafe' in text:
#                     return True
#         return False

#     def _is_test_function_simple(self, node, content: str) -> bool:
#         """简化的测试函数检查"""
#         # 检查前面的属性
#         current_node = node
#         while current_node:
#             prev_sibling = current_node.prev_sibling
#             if prev_sibling and prev_sibling.type == 'attribute_item':
#                 attr_text = self._get_node_text(prev_sibling, content)
#                 if attr_text and ('#[test]' in attr_text or '#[cfg(test)]' in attr_text):
#                     return True
#             elif prev_sibling and prev_sibling.type in ('line_comment', 'block_comment'):
#                 current_node = prev_sibling
#                 continue
#             else:
#                 break
#         return False

#     def _get_node_text(self, node, content: str) -> Optional[str]:
#         """获取节点的文本内容"""
#         if node:
#             text = content[node.start_byte:node.end_byte]
#             return text.decode('utf-8') if isinstance(text, bytes) else text
#         return None

#     def _save_to_json(self):
#         """保存提取结果到 JSON 文件"""
#         # 转换为可序列化的格式
#         serializable_functions = []
#         for func in self.functions:
#             # 复制函数信息
#             func_copy = func.copy()

#             # 确保所有字段都是可序列化的
#             for key, value in func_copy.items():
#                 if isinstance(value, bytes):
#                     func_copy[key] = value.decode('utf-8', errors='ignore')

#             serializable_functions.append(func_copy)

#         # 写入 JSON 文件
#         with open(self.output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable_functions, f, indent=2, ensure_ascii=False)


# # 解决方案2：使用正则表达式的快速版本
# class FastRustFocalExtractor:
#     def __init__(self, project_root: str, output_file: str):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file

#         # 忽略模式
#         self.ignore_dirs = {
#             'target', '.git', '.cargo', 'node_modules',
#             '__pycache__', '.pytest_cache', '.mypy_cache',
#             '.idea', '.vscode', 'build', 'dist', '.direnv',
#             'test', 'tests', 'benches', 'examples'
#         }

#         self.functions = []
#         self.stats = {
#             'files_processed': 0,
#             'files_skipped': 0,
#             'functions_found': 0,
#             'start_time': time.time()
#         }

#     def extract_project_focal_functions(self) -> List[Dict]:
#         """使用正则表达式快速提取公有函数"""
#         print(f"开始快速提取 Rust 项目: {self.project_root}")
#         print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

#         # 统计文件数
#         total_files = self._count_rust_files()
#         print(f"总 Rust 文件数: {total_files}")

#         processed = 0
#         last_print_time = time.time()

#         for root, dirs, files in os.walk(self.project_root):
#             # 过滤目录
#             dirs[:] = [d for d in dirs if d not in self.ignore_dirs and not d.startswith('.')]

#             for file in files:
#                 if not file.endswith('.rs'):
#                     continue

#                 # 跳过测试文件
#                 if file.startswith('test_') or file.endswith('_test.rs'):
#                     continue

#                 file_path = os.path.join(root, file)

#                 # 进度显示
#                 processed += 1
#                 current_time = time.time()
#                 if current_time - last_print_time > 2.0:
#                     elapsed = current_time - self.stats['start_time']
#                     print(f"进度: {processed}/{total_files} 文件 ({processed/total_files*100:.1f}%), "
#                           f"已用时: {elapsed:.1f}秒, "
#                           f"找到函数: {len(self.functions)}")
#                     last_print_time = current_time

#                 try:
#                     # 检查文件大小
#                     file_size = os.path.getsize(file_path)
#                     if file_size > 1024 * 1024:  # 大于1MB跳过
#                         print(f"  跳过大文件: {os.path.relpath(file_path, self.project_root)} ({file_size/1024:.1f}KB)")
#                         self.stats['files_skipped'] += 1
#                         continue

#                     with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
#                         content = f.read()

#                     functions_in_file = self._extract_functions_regex(file_path, content)
#                     if functions_in_file:
#                         self.functions.extend(functions_in_file)
#                         self.stats['functions_found'] += len(functions_in_file)
#                         print(f"  [{processed}/{total_files}] 在 {os.path.relpath(file_path, self.project_root)} "
#                               f"中找到 {len(functions_in_file)} 个公有函数")

#                     self.stats['files_processed'] += 1

#                 except Exception as e:
#                     print(f"处理文件 {file_path} 时出错: {e}")
#                     self.stats['files_skipped'] += 1
#                     continue

#         # 保存结果
#         self._save_to_json()

#         # 打印统计信息
#         total_time = time.time() - self.stats['start_time']
#         print(f"\n{'='*60}")
#         print(f"快速提取完成!")
#         print(f"总用时: {total_time:.1f}秒")
#         print(f"处理文件: {self.stats['files_processed']}")
#         print(f"跳过文件: {self.stats['files_skipped']}")
#         print(f"找到函数: {self.stats['functions_found']}")
#         print(f"结果已保存到: {self.output_file}")

#         return self.functions

#     def _count_rust_files(self) -> int:
#         """统计文件数"""
#         count = 0
#         for root, dirs, files in os.walk(self.project_root):
#             dirs[:] = [d for d in dirs if d not in self.ignore_dirs and not d.startswith('.')]
#             for file in files:
#                 if file.endswith('.rs'):
#                     if not (file.startswith('test_') or file.endswith('_test.rs')):
#                         count += 1
#         return count

#     def _extract_functions_regex(self, file_path: str, content: str) -> List[Dict]:
#         """使用正则表达式提取函数"""
#         functions = []
#         relative_path = os.path.relpath(file_path, self.project_root)

#         # 改进的正则表达式，匹配公有函数
#         # 匹配: pub fn 函数名 或 pub(crate) fn 函数名 或 pub async fn 函数名 等
#         pattern = r'(?:(?://.*?\n|/\*.*?\*/|\s)*)?(?:#\[[^\]]*\])?\s*(pub\s*(?:\([^)]*\))?\s*(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)\s*\([^)]*\)\s*(?:->[^{]+)?\s*\{)'

#         for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
#             function_name = match.group(2)

#             # 跳过测试函数和main函数
#             if function_name == 'main' or function_name == 'new':
#                 continue

#             # 检查是否为测试函数（查找前面的#[test]）
#             start_pos = match.start()
#             prev_text = content[max(0, start_pos-200):start_pos]
#             if '#[test]' in prev_text or '#[cfg(test)]' in prev_text:
#                 continue

#             # 提取函数代码
#             func_start = match.start(1)
#             func_end = self._find_function_end(content, func_start)

#             if func_end > func_start:
#                 full_match = match.group(0)
#                 function_info = {
#                     'name': function_name,
#                     'src_file': relative_path,
#                     'test_file': relative_path,
#                     'code': content[func_start:func_end],
#                     'is_async': 'async' in full_match,
#                     'is_unsafe': 'unsafe' in full_match,
#                     'is_associated': 'self' not in match.group(1),
#                     'module_path': [],
#                     'function_type': 'unknown'
#                 }

#                 functions.append(function_info)

#         return functions

#     def _find_function_end(self, content: str, start_pos: int) -> int:
#         """查找函数结束位置"""
#         brace_count = 0
#         in_string = False
#         string_char = None
#         escape = False

#         i = start_pos
#         while i < len(content):
#             char = content[i]

#             if escape:
#                 escape = False
#             elif char == '\\':
#                 escape = True
#             elif not in_string:
#                 if char == '{':
#                     brace_count += 1
#                 elif char == '}':
#                     brace_count -= 1
#                     if brace_count == 0:
#                         return i + 1
#                 elif char in ('"', "'"):
#                     in_string = True
#                     string_char = char
#             elif char == string_char:
#                 in_string = False

#             i += 1

#         return len(content)

#     def _save_to_json(self):
#         """保存到 JSON 文件"""
#         with open(self.output_file, 'w', encoding='utf-8') as f:
#             json.dump(self.functions, f, indent=2, ensure_ascii=False)


# def main():
#     """主函数，提供选择"""
#     import sys

#     print("请选择提取模式:")
#     print("1. 完整模式 (使用tree-sitter，准确但可能慢)")
#     print("2. 快速模式 (使用正则表达式，快速但可能不准确)")
#     print("3. 测试模式 (处理单个小文件)")

#     choice = input("请选择 (默认为3): ").strip() or "3"

#     if len(sys.argv) > 1:
#         project_root = sys.argv[1]
#         output_file = sys.argv[2] if len(sys.argv) > 2 else "rust_focal_functions.json"
#     else:
#         project_root = input("请输入 Rust 项目路径 (默认为当前目录): ").strip() or "."
#         output_file = input("请输入输出文件名 (默认为 rust_focal_functions.json): ").strip() or "rust_focal_functions.json"

#     if choice == "3":
#         # 测试模式：创建一个简单的测试文件
#         test_dir = "test_project"
#         os.makedirs(test_dir, exist_ok=True)

#         test_code = """
#         pub fn public_function() -> i32 {
#             42
#         }

#         fn private_function() -> i32 {
#             24
#         }

#         pub async fn async_function() -> i32 {
#             100
#         }

#         pub(crate) fn crate_public_function() -> i32 {
#             200
#         }

#         struct TestStruct {
#             value: i32,
#         }

#         impl TestStruct {
#             pub fn new(value: i32) -> Self {
#                 TestStruct { value }
#             }

#             pub fn get_value(&self) -> i32 {
#                 self.value
#             }
#         }
#         #[cfg(test)]
#         mod tests {
#             use super::*;

#             const SHERLOCK: &'static str = "\
#         For the Doctor Watsons of this world, as opposed to the Sherlock
#         Holmeses, success in the province of detective work must always
#         be, to a very large extent, the result of luck. Sherlock Holmes
#         can extract a clew from a wisp of straw or a flake of cigar ash;
#         but Doctor Watson has to have it taken out for him and dusted,
#         and exhibited clearly, with a label attached.\
#         ";

#             fn m(start: usize, end: usize) -> Match {
#                 Match::new(start, end)
#             }

#             fn lines(text: &str) -> Vec<&str> {
#                 let mut results = vec![];
#                 let mut it = LineStep::new(b'\n', 0, text.len());
#                 while let Some(m) = it.next_match(text.as_bytes()) {
#                     results.push(&text[m]);
#                 }
#                 results
#             }

#             fn line_ranges(text: &str) -> Vec<std::ops::Range<usize>> {
#                 let mut results = vec![];
#                 let mut it = LineStep::new(b'\n', 0, text.len());
#                 while let Some(m) = it.next_match(text.as_bytes()) {
#                     results.push(m.start()..m.end());
#                 }
#                 results
#             }

#             fn prev(text: &str, pos: usize, count: usize) -> usize {
#                 preceding_by_pos(text.as_bytes(), pos, b'\n', count)
#             }

#             fn loc(text: &str, start: usize, end: usize) -> Match {
#                 locate(text.as_bytes(), b'\n', Match::new(start, end))
#             }

#             #[test]
#             fn line_count() {
#                 assert_eq!(0, count(b"", b'\n'));
#                 assert_eq!(1, count(b"\n", b'\n'));
#                 assert_eq!(2, count(b"\n\n", b'\n'));
#                 assert_eq!(2, count(b"a\nb\nc", b'\n'));
#             }
#         }
#         """

#         test_file = os.path.join(test_dir, "test.rs")
#         with open(test_file, 'w', encoding='utf-8') as f:
#             f.write(test_code)

#         project_root = test_dir
#         output_file = "test_output.json"

#     extractor = RustFocalExtractor(project_root, output_file)


#     try:
#         functions = extractor.extract_project_focal_functions()

#         if functions:
#             print(f"\n=== 提取结果示例 ===")
#             for i, func in enumerate(functions[:5]):  # 显示前5个函数
#                 print(f"\n{i+1}. {func['name']}")
#                 print(f"   文件: {func['src_file']}")
#                 print(f"   异步: {func.get('is_async', False)}, 不安全: {func.get('is_unsafe', False)}")
#                 if 'code' in func and len(func['code']) < 200:
#                     print(f"   代码预览: {func['code'][:100]}...")

#     except KeyboardInterrupt:
#         print("\n\n用户中断，正在保存已提取的结果...")
#         extractor._save_to_json()
#         print(f"已保存 {len(extractor.functions)} 个函数到 {extractor.output_file}")
#     except Exception as e:
#         print(f"提取过程中出错: {e}")
#         import traceback
#         traceback.print_exc()

#     if choice == "3":
#         # 清理测试文件
#         import shutil
#         if os.path.exists(test_dir):
#             shutil.rmtree(test_dir)
#         # if os.path.exists("test_output.json"):
#         #     os.remove("test_output.json")


# if __name__ == "__main__":
#     main()
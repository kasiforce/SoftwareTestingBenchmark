# from multi_parser import python_parser
# import os
# import json
# import re


# class PythonFocalExtractor:
#     def __init__(self, project_root, output_file):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file

#     def extract_project_focal_methods(self):
#         """提取项目中所有Python文件的公有函数"""
#         all_methods = []

#         # 定义要忽略的目录模式
#         IGNORE_DIRS = {
#             'test', 'tests', '__pycache__', '.git', '.svn', '.hg',
#             'venv', 'env', '.env', 'virtualenv', 'envs',
#             '.vscode', '.idea', '.pytest_cache', '.mypy_cache',
#             'build', 'dist', '*.egg-info', 'node_modules'
#         }

#         for root, dirs, files in os.walk(self.project_root):
#             # 过滤掉需要忽略的目录（仅按完整目录名）
#             dirs[:] = [
#                 d for d in dirs
#                 if d not in IGNORE_DIRS
#                 and not d.startswith('.')
#             ]

#             # 若当前根目录本身是需要忽略的目录，直接跳过
#             if any(part in IGNORE_DIRS for part in root.split(os.sep)):
#                 continue

#             for file in files:
#                 # 检查文件扩展名
#                 if not file.endswith('.py'):
#                     continue

#                 # 检查是否为测试文件或应忽略的文件
#                 if self._should_skip_file(file):
#                     continue

#                 # 检查文件路径是否包含忽略目录
#                 if self._is_in_ignored_path(root, IGNORE_DIRS):
#                     continue

#                 file_path = os.path.join(root, file)

#                 try:
#                     # 添加调试信息
#                     print(f"处理文件: {file_path}")

#                     methods = self._extract_focal_method(file_path)
#                     if methods:
#                         # 过滤公有方法（不以单下划线开头）
#                         public_methods = [
#                             method for method in methods
#                             if not method.get('name', '').startswith('_')
#                         ]
#                         all_methods.extend(public_methods)

#                 except SyntaxError as e:
#                     print(f"语法错误，跳过文件 {file_path}: {e}")
#                     continue
#                 except UnicodeDecodeError as e:
#                     print(f"编码错误，跳过文件 {file_path}: {e}")
#                     continue
#                 except Exception as e:
#                     print(f"处理 {file_path} 时出错: {e}")
#                     continue

#         self._save_to_json(all_methods)
#         print(f"提取完成，共找到 {len(all_methods)} 个公有方法")
#         return all_methods

#     def _should_skip_file(self, filename: str) -> bool:
#         """判断是否应该跳过该文件"""
#         # 基本忽略规则
#         if filename in ['conftest.py', 'setup.py', '__about__.py', '__version__.py']:
#             return True

#         # 测试文件模式
#         if filename.startswith('test_') or filename.endswith('_test.py'):
#             return True

#         # 私有模块（以单下划线开头）
#         # if filename.startswith('_'):
#         #     return True

#         return False

#     def _is_in_ignored_path(self, root_path: str, ignore_dirs: set) -> bool:
#         parts = root_path.split(os.sep)
#         for part in parts:
#             if part in ignore_dirs:
#                 return True
#         return False

#     def _extract_focal_method(self, file_path):
#         """提取文件中所有公有函数，包括嵌套类中的方法，同时提取类构造函数、字段、import语句"""
#         with open(file_path, 'r', encoding='utf-8') as f:
#             code = f.read()
#             tree = python_parser.parse(bytes(code, 'utf-8'))
#             root_node = tree.root_node

#             # 首先提取文件的import语句
#             imports = self._extract_imports(root_node, code)

#             focal_methods = []
#             stack = [(root_node, [])]  # (节点, 路径上的类)

#             while stack:
#                 node, current_classes = stack.pop()

#                 # 处理类定义
#                 if node.type == 'class_definition':
#                     class_name = self._get_name(node)
#                     if class_name:
#                         # 提取类构造函数、字段
#                         init_info = self._extract_init_method(node, code)
#                         fields_info = self._extract_class_fields(node, code)

#                         # 创建新的类上下文
#                         class_context = {
#                             'class_name': class_name,
#                             'init': init_info,
#                             'fields': fields_info,
#                             'node': node
#                         }

#                         new_classes = current_classes + [class_context]

#                         # 将子节点与新类上下文一起压栈
#                         for child in reversed(node.children):
#                             stack.append((child, new_classes))
#                         continue

#                 # 处理函数定义
#                 elif node.type == 'function_definition':
#                     function_name = self._get_name(node)

#                     # 只提取公有函数（不以单下划线开头）
#                     if function_name and not function_name.startswith('_'):
#                         proj_root = str(self.project_root) + '/'
#                         src_file = str(file_path).split(proj_root)[1]
#                         method_info = {
#                             'name': function_name,
#                             'src_file': src_file,
#                             'test_file': self._gen_test_file_path(file_path, function_name),
#                             'code': code[node.start_byte:node.end_byte],
#                             'is_async': self._is_async_function(node),
#                             'imports': imports
#                         }

#                         # 如果有类上下文，记录所属类
#                         if current_classes:
#                             method_info['class_hierarchy'] = [cls['class_name'] for cls in current_classes]
#                             method_info['class_name'] = current_classes[-1]['class_name']
#                             method_info['full_class_name'] = '.'.join([cls['class_name'] for cls in current_classes])
#                             method_info['class_init'] = current_classes[-1]['init']
#                             method_info['class_fields'] = current_classes[-1]['fields']
#                             method_info['type'] = 'method'

#                         else:
#                             method_info['type'] = 'function'

#                         focal_methods.append(method_info)

#                 # 继续遍历子节点
#                 for child in reversed(node.children):
#                     stack.append((child, current_classes))

#             return focal_methods

#     # def _extract_focal_method(self, file_path):
#     #     """提取文件中所有公有函数，包括嵌套类中的方法，同时提取import语句"""
#     #     with open(file_path, 'r', encoding='utf-8') as f:
#     #         code = f.read()
#     #         tree = python_parser.parse(bytes(code, 'utf-8'))
#     #         root_node = tree.root_node

#     #         # 首先提取文件的import语句
#     #         imports = self._extract_imports(root_node, code)

#     #         focal_methods = []

#     #         # 使用迭代方式遍历，更好地控制类边界的检测
#     #         stack = [(root_node, [])]  # (节点, 路径上的类)

#     #         while stack:
#     #             node, current_classes = stack.pop()

#     #             # 处理类定义
#     #             if node.type == 'class_definition':
#     #                 class_name = self._get_name(node)
#     #                 if class_name:
#     #                     # 创建新的类上下文
#     #                     new_classes = current_classes + [{
#     #                         'name': class_name,
#     #                         'node': node
#     #                     }]

#     #                     # 将子节点与新类上下文一起压栈
#     #                     for child in reversed(node.children):
#     #                         stack.append((child, new_classes))
#     #                     continue

#     #             # 处理函数定义
#     #             elif node.type == 'function_definition':
#     #                 function_name = self._get_name(node)

#     #                 # 只提取公有函数（不以单下划线开头）
#     #                 if function_name and not function_name.startswith('_'):
#     #                     proj_root = str(self.project_root) + '/'
#     #                     src_file = str(file_path).split(proj_root)[1]
#     #                     method_info = {
#     #                         'name': function_name,
#     #                         'src_file': src_file,
#     #                         'test_file': self._gen_test_file_path(file_path, function_name),
#     #                         'code': code[node.start_byte:node.end_byte],
#     #                         'is_async': self._is_async_function(node),
#     #                         'imports': imports  # 添加import上下文
#     #                     }

#     #                     # 如果有类上下文，记录所属类
#     #                     if current_classes:
#     #                         # 记录所有嵌套的类
#     #                         method_info['class_hierarchy'] = [cls['name'] for cls in current_classes]
#     #                         method_info['class_name'] = current_classes[-1]['name']  # 直接所属类
#     #                         method_info['full_class_name'] = '.'.join([cls['name'] for cls in current_classes])
#     #                         method_info['type'] = 'method'
#     #                     else:
#     #                         method_info['type'] = 'function'

#     #                     focal_methods.append(method_info)

#     #             # 继续遍历子节点
#     #             for child in reversed(node.children):
#     #                 stack.append((child, current_classes))

#     #         return focal_methods

#     def _extract_init_method(self, class_node, code):
#         for child in class_node.children:
#             if child.type == 'function_definition':
#                 func_name = self._get_name(child)
#                 if func_name == '__init__':
#                     params = []
#                     for param_node in child.children:
#                         if param_node.type == 'parameters':
#                             for p in param_node.children:
#                                 if p.type == 'identifier':
#                                     params.append(p.text.decode('utf-8'))
#                     params = [p for p in params if p != 'self']
#                     return {
#                         'name': '__init__',
#                         'params': params,
#                         'code': code[child.start_byte:child.end_byte],
#                         'is_async': self._is_async_function(child)
#                     }
#         return None

#     def _extract_class_fields(self, class_node, code):
#         """
#         提取类的字段信息，返回的是字段的完整代码片段（字符串）。
#         兼容：
#         - 带类型注解的字段：mimetype: Optional[str] = None
#         - 纯赋值字段：x = 1
#         """
#         fields = []

#         for child in class_node.children:
#             # 普通赋值（x = 1）
#             if child.type == 'assignment':
#                 # 直接截取整个 assignment 节点的源码
#                 field_code = code[child.start_byte:child.end_byte].strip()
#                 fields.append(field_code)
#                 continue

#             # 类型注解（mimetype: Optional[str] = None）
#             if child.type == 'annotation':
#                 # annotation 节点的源码已经包含了完整声明
#                 field_code = code[child.start_byte:child.end_byte].strip()
#                 fields.append(field_code)
#                 continue

#         return fields

#     def _gen_test_file_path(self, file_path, function_name):
#         temp_path = file_path.split(str(self.project_root))[1]
#         temp_path2 = temp_path.split(".py")[0]
#         file_name = temp_path2.split('/')[-1]
#         temp_path3 = temp_path2.split(file_name)[0]
#         return "gen_tests" + str(temp_path3) + "Test" + file_name + '/' + "test_" + function_name + ".py"


#     def _extract_imports(self, root_node, code):
#         """提取文件中的所有import语句"""
#         imports = {
#             'imports': [],  # 简单import语句
#             'from_imports': [],  # from ... import 语句
#             'imports_with_aliases': []  # 带别名的import
#         }

#         def traverse_imports(node):
#             """递归遍历节点提取import语句"""
#             if node.type == 'import_statement':
#                 # 处理 import xxx, import xxx as yyy
#                 import_text = code[node.start_byte:node.end_byte].strip()
#                 if ' as ' in import_text:
#                     imports['imports_with_aliases'].append(import_text)
#                 else:
#                     imports['imports'].append(import_text)

#             elif node.type == 'import_from_statement':
#                 # 处理 from xxx import yyy
#                 import_text = code[node.start_byte:node.end_byte].strip()
#                 imports['from_imports'].append(import_text)

#             # 继续遍历子节点
#             for child in node.children:
#                 traverse_imports(child)

#         # 从根节点开始遍历
#         traverse_imports(root_node)
#         return imports

#     def _get_name(self, node):
#         """从函数/类定义节点中提取函数/类名"""
#         for child in node.children:
#             if child.type == 'identifier':
#                 return child.text.decode('utf-8')
#         return None

#     def _is_async_function(self, function_node):
#         """检查是否为异步函数"""
#         for child in function_node.children:
#             if child.type == 'async':
#                 return True
#         return False

#     def _save_to_json(self, methods):
#         """将提取结果保存为JSON文件"""

#         # 转换为可序列化的格式
#         serializable_methods = []
#         for method in methods:
#             serializable_method = method.copy()
#             # 确保所有字符串都是可序列化的
#             for key, value in serializable_method.items():
#                 if isinstance(value, bytes):
#                     serializable_method[key] = value.decode('utf-8')
#             serializable_methods.append(serializable_method)

#         with open(self.output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable_methods, f, indent=2, ensure_ascii=False)


# if __name__ == "__main__":
#     extractor = PythonFocalExtractor("testbed/markitdown", "markitdown_focal_class_context.json")
#     extractor.extract_project_focal_methods()


# import os
# import json
# from multi_parser import python_parser

# class PythonFocalExtractor:
#     def __init__(self, project_root, output_file):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file
#         self.class_info_dict = {}  # 存储类信息的字典，键为类的全名

#     def extract_project_focal_methods(self):
#         """提取项目中所有Python文件的公有函数"""
#         all_methods = []

#         # 定义要忽略的目录模式
#         IGNORE_DIRS = {
#             'test', 'tests', '__pycache__', '.git', '.svn', '.hg',
#             'venv', 'env', '.env', 'virtualenv', 'envs',
#             '.vscode', '.idea', '.pytest_cache', '.mypy_cache',
#             'build', 'dist', '*.egg-info', 'node_modules'
#         }

#         for root, dirs, files in os.walk(self.project_root):
#             # 过滤掉需要忽略的目录（仅按完整目录名）
#             dirs[:] = [
#                 d for d in dirs
#                 if d not in IGNORE_DIRS
#                 and not d.startswith('.')
#             ]

#             # 若当前根目录本身是需要忽略的目录，直接跳过
#             if any(part in IGNORE_DIRS for part in root.split(os.sep)):
#                 continue

#             for file in files:
#                 # 检查文件扩展名
#                 if not file.endswith('.py'):
#                     continue

#                 # 检查是否为测试文件或应忽略的文件
#                 if self._should_skip_file(file):
#                     continue

#                 # 检查文件路径是否包含忽略目录
#                 if self._is_in_ignored_path(root, IGNORE_DIRS):
#                     continue

#                 file_path = os.path.join(root, file)

#                 try:
#                     # 添加调试信息
#                     # print(f"处理文件: {file_path}")

#                     methods = self._extract_focal_method(file_path)
#                     if methods:
#                         # 过滤公有方法（不以单下划线开头）
#                         public_methods = [
#                             method for method in methods
#                             if not method.get('name', '').startswith('_')
#                         ]
#                         all_methods.extend(public_methods)

#                 except SyntaxError as e:
#                     print(f"语法错误，跳过文件 {file_path}: {e}")
#                     continue
#                 except UnicodeDecodeError as e:
#                     print(f"编码错误，跳过文件 {file_path}: {e}")
#                     continue
#                 except Exception as e:
#                     print(f"处理 {file_path} 时出错: {e}")
#                     continue

#         self._save_to_json(all_methods)
#         print(f"提取完成，共找到 {len(all_methods)} 个公有方法")
#         return all_methods

#     def _should_skip_file(self, filename: str) -> bool:
#         """判断是否应该跳过该文件"""
#         # 基本忽略规则
#         if filename in ['conftest.py', 'setup.py', '__about__.py', '__version__.py']:
#             return True

#         # 测试文件模式
#         if filename.startswith('test_') or filename.endswith('_test.py'):
#             return True

#         return False

#     def _is_in_ignored_path(self, root_path: str, ignore_dirs: set) -> bool:
#         parts = root_path.split(os.sep)
#         for part in parts:
#             if part in ignore_dirs:
#                 return True
#         return False

#     def _extract_focal_method(self, file_path):
#         """提取文件中所有公有函数，包括嵌套类中的方法，同时提取import语句和类上下文"""
#         with open(file_path, 'r', encoding='utf-8') as f:
#             code = f.read()
#             tree = python_parser.parse(bytes(code, 'utf-8'))
#             root_node = tree.root_node

#             # 首先提取文件的import语句
#             imports = self._extract_imports(root_node, code)

#             # 提取文件中所有的类信息（包括嵌套类）
#             class_info_dict = self._extract_all_classes(root_node, code)
#             self.class_info_dict = class_info_dict

#             focal_methods = []

#             # 使用迭代方式遍历，更好地控制类边界的检测
#             stack = [(root_node, [])]  # (节点, 路径上的类)

#             while stack:
#                 node, current_classes = stack.pop()

#                 # 处理类定义
#                 if node.type == 'class_definition':
#                     class_name = self._get_name(node)
#                     if class_name:
#                         # 创建新的类上下文
#                         new_classes = current_classes + [{
#                             'name': class_name,
#                             'node': node
#                         }]

#                         # 将子节点与新类上下文一起压栈
#                         for child in reversed(node.children):
#                             stack.append((child, new_classes))
#                         continue

#                 # 处理函数定义
#                 elif node.type == 'function_definition':
#                     function_name = self._get_name(node)

#                     # 只提取公有函数（不以单下划线开头）
#                     if function_name and not function_name.startswith('_'):
#                         proj_root = str(self.project_root) + '/'
#                         src_file = str(file_path).split(proj_root)[1]

#                         # 构建方法信息
#                         method_info = {
#                             'name': function_name,
#                             'src_file': src_file,
#                             'test_file': self._gen_test_file_path(file_path, function_name),
#                             'code': code[node.start_byte:node.end_byte],
#                             'is_async': self._is_async_function(node),
#                             'imports': imports  # 添加import上下文
#                         }

#                         # 如果有类上下文，添加类信息和构造函数
#                         if current_classes:
#                             # 获取类的全名
#                             class_hierarchy = [cls['name'] for cls in current_classes]
#                             full_class_name = '.'.join(class_hierarchy)

#                             # 添加类信息
#                             method_info['class_hierarchy'] = class_hierarchy
#                             method_info['class_name'] = current_classes[-1]['name']  # 直接所属类
#                             method_info['full_class_name'] = full_class_name
#                             method_info['type'] = 'method'

#                             # 获取类的构造函数和字段信息
#                             class_info = class_info_dict.get(full_class_name)
#                             if class_info:
#                                 # 只添加构造函数（如果存在的话）
#                                 if 'constructor' in class_info:
#                                     method_info['class_constructor'] = class_info['constructor']
#                                 # 添加字段信息
#                                 if 'fields' in class_info:
#                                     method_info['class_fields'] = class_info['fields']
#                                 # 添加类变量
#                                 if 'class_variables' in class_info:
#                                     method_info['class_variables'] = class_info['class_variables']
#                         else:
#                             method_info['type'] = 'function'

#                         focal_methods.append(method_info)

#                 # 继续遍历子节点
#                 for child in reversed(node.children):
#                     stack.append((child, current_classes))

#             return focal_methods

#     def _extract_all_classes(self, root_node, code):
#         """提取文件中所有的类信息，包括构造函数和字段"""
#         class_info_dict = {}

#         def extract_class_details(class_node, parent_classes=[]):
#             """递归提取类信息"""
#             class_name = self._get_name(class_node)
#             if not class_name:
#                 return

#             # 构建类的全名
#             full_class_name = '.'.join(parent_classes + [class_name]) if parent_classes else class_name

#             # 初始化类信息
#             class_info = {
#                 'name': class_name,
#                 'full_name': full_class_name,
#                 'constructor': None,
#                 'fields': [],  # 实例字段
#                 'class_variables': [],  # 类变量
#                 'nested_classes': []
#             }

#             # 查找类的body
#             class_body = None
#             for child in class_node.children:
#                 if child.type == 'block':
#                     class_body = child
#                     break

#             if class_body:
#                 # 遍历类体中的节点
#                 for child in class_body.children:
#                     # 提取构造函数 (__init__)
#                     if child.type == 'function_definition':
#                         func_name = self._get_name(child)
#                         if func_name == '__init__':
#                             # 提取构造函数代码和参数
#                             class_info['constructor'] = code[child.start_byte:child.end_byte]

#                     # 提取类变量（类级别的赋值）
#                     elif child.type == 'expression_statement':
#                         # 检查是否包含赋值
#                         assignment = self._find_assignment(child)
#                         if assignment:
#                             # 检查是否是类变量（不是self.xxx）
#                             if not self._is_instance_assignment(assignment, code):
#                                 var_info = self._extract_variable_info(assignment, code)
#                                 # print("var: "+var_info)
#                                 if var_info:
#                                     class_info['class_variables'].append(var_info)

#                     # 提取字段（实例变量赋值，通常在__init__中提取，但也可能在类方法中）
#                     elif child.type == 'assignment':
#                         # 检查是否是实例字段
#                         if self._is_instance_assignment(child, code):
#                             field_info = self._extract_field_info(child, code)
#                             print("field: "+field_info)
#                             if field_info:
#                                 class_info['fields'].append(field_info)

#                     # 递归处理嵌套类
#                     elif child.type == 'class_definition':
#                         nested_class_name = self._get_name(child)
#                         if nested_class_name:
#                             nested_info = extract_class_details(child, parent_classes + [class_name])
#                             if nested_info:
#                                 class_info['nested_classes'].append(nested_info)

#             return class_info

#         # 遍历所有顶级类
#         def traverse_nodes(node):
#             if node.type == 'class_definition':
#                 class_info = extract_class_details(node)
#                 if class_info:
#                     class_info_dict[class_info['full_name']] = class_info
#             for child in node.children:
#                 traverse_nodes(child)

#         traverse_nodes(root_node)
#         return class_info_dict

#     def _find_assignment(self, node):
#         """在节点中查找赋值语句"""
#         stack = [node]
#         while stack:
#             current = stack.pop()
#             if current.type == 'assignment':
#                 return current
#             for child in current.children:
#                 stack.append(child)
#         return None

#     def _is_instance_assignment(self, assignment_node, code):
#         """检查是否是实例字段赋值"""
#         for child in assignment_node.children:
#             if child.type == 'attribute':
#                 attr_text = code[child.start_byte:child.end_byte]
#                 if attr_text.startswith('self.'):
#                     return True
#         return False

#     def _extract_variable_info(self, assignment_node, code):
#         """提取变量信息（不提取私有字段）"""
#         try:
#             left_side = None
#             right_side = None
#             left_node = None

#             # 查找赋值操作符
#             for i, child in enumerate(assignment_node.children):
#                 if child.type == 'identifier' or child.type == 'attribute':
#                     left_side = code[child.start_byte:child.end_byte]
#                     left_node = child  # 记录左侧节点

#                 elif child.type == '=':
#                     if i + 1 < len(assignment_node.children):
#                         right_side = code[assignment_node.children[i+1].start_byte:assignment_node.children[i+1].end_byte]
#                     break

#             if left_side:
#                 # 将字节串转换为字符串（如果需要）
#                 if isinstance(left_side, bytes):
#                     left_side_str = left_side.decode('utf-8')
#                 else:
#                     left_side_str = str(left_side)

#                 # 检查是否为私有字段（以_开头）
#                 if left_side_str.startswith('_'):
#                     return None

#                 # 对于属性访问，检查属性名部分
#                 if left_node and left_node.type == 'attribute':
#                     # 拆分属性访问路径
#                     attr_parts = left_side_str.split('.')
#                     if attr_parts and attr_parts[-1].startswith('_'):
#                         return None

#                 return code[assignment_node.start_byte:assignment_node.end_byte]

#         except Exception as e:
#             # 打印错误信息以便调试
#             print(f"Error extracting variable info: {e}")
#             pass
#         return None

#     def _extract_field_info(self, assignment_node, code):
#         """提取字段信息"""
#         return self._extract_variable_info(assignment_node, code)

#     def _gen_test_file_path(self, file_path, function_name):
#         temp_path = file_path.split(str(self.project_root))[1]
#         temp_path2 = temp_path.split(".py")[0]
#         file_name = temp_path2.split('/')[-1]
#         temp_path3 = temp_path2.split(file_name)[0]
#         return "gen_tests" + str(temp_path3) + "Test" + file_name + '/' + "test_" + function_name + ".py"

#     def _extract_imports(self, root_node, code):
#         """提取文件中的所有import语句"""
#         imports = {
#             'imports': [],  # 简单import语句
#             'from_imports': [],  # from ... import 语句
#             'imports_with_aliases': []  # 带别名的import
#         }

#         def traverse_imports(node):
#             """递归遍历节点提取import语句"""
#             if node.type == 'import_statement':
#                 # 处理 import xxx, import xxx as yyy
#                 import_text = code[node.start_byte:node.end_byte].strip()
#                 if ' as ' in import_text:
#                     imports['imports_with_aliases'].append(import_text)
#                 else:
#                     imports['imports'].append(import_text)

#             elif node.type == 'import_from_statement':
#                 # 处理 from xxx import yyy
#                 import_text = code[node.start_byte:node.end_byte].strip()
#                 imports['from_imports'].append(import_text)

#             # 继续遍历子节点
#             for child in node.children:
#                 traverse_imports(child)

#         # 从根节点开始遍历
#         traverse_imports(root_node)
#         return imports

#     def _get_name(self, node):
#         """从函数/类定义节点中提取函数/类名"""
#         for child in node.children:
#             if child.type == 'identifier':
#                 return child.text.decode('utf-8')
#         return None

#     def _is_async_function(self, function_node):
#         """检查是否为异步函数"""
#         for child in function_node.children:
#             if child.type == 'async':
#                 return True
#         return False

#     def _save_to_json(self, methods):
#         """将提取结果保存为JSON文件"""
#         # 转换为可序列化的格式
#         serializable_methods = []
#         for method in methods:
#             serializable_method = method.copy()
#             # 确保所有字符串都是可序列化的
#             for key, value in serializable_method.items():
#                 if isinstance(value, bytes):
#                     serializable_method[key] = value.decode('utf-8')
#             serializable_methods.append(serializable_method)

#         with open(self.output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable_methods, f, indent=2, ensure_ascii=False)


# import os
# import json
# import re
# from multi_parser import python_parser

# class PythonFocalExtractor:
#     def __init__(self, project_root, output_file):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file
#         self.class_info_dict = {}  # 存储类信息的字典，键为类的全名

#     def extract_project_focal_methods(self):
#         """提取项目中所有Python文件的公有函数"""
#         all_methods = []

#         # 定义要忽略的目录模式
#         IGNORE_DIRS = {
#             'test', 'tests', '__pycache__', '.git', '.svn', '.hg',
#             'venv', 'env', '.env', 'virtualenv', 'envs',
#             '.vscode', '.idea', '.pytest_cache', '.mypy_cache',
#             'build', 'dist', '*.egg-info', 'node_modules'
#         }

#         for root, dirs, files in os.walk(self.project_root):
#             # 过滤掉需要忽略的目录（仅按完整目录名）
#             dirs[:] = [
#                 d for d in dirs
#                 if d not in IGNORE_DIRS
#                 and not d.startswith('.')
#             ]

#             # 若当前根目录本身是需要忽略的目录，直接跳过
#             if any(part in IGNORE_DIRS for part in root.split(os.sep)):
#                 continue

#             for file in files:
#                 # 检查文件扩展名
#                 if not file.endswith('.py'):
#                     continue

#                 # 检查是否为测试文件或应忽略的文件
#                 if self._should_skip_file(file):
#                     continue

#                 # 检查文件路径是否包含忽略目录
#                 if self._is_in_ignored_path(root, IGNORE_DIRS):
#                     continue

#                 file_path = os.path.join(root, file)

#                 try:
#                     # 添加调试信息
#                     # print(f"处理文件: {file_path}")

#                     methods = self._extract_focal_method(file_path)
#                     if methods:
#                         # 过滤公有方法（不以单下划线开头）
#                         public_methods = [
#                             method for method in methods
#                             if not method.get('name', '').startswith('_')
#                         ]
#                         all_methods.extend(public_methods)

#                 except SyntaxError as e:
#                     print(f"语法错误，跳过文件 {file_path}: {e}")
#                     continue
#                 except UnicodeDecodeError as e:
#                     print(f"编码错误，跳过文件 {file_path}: {e}")
#                     continue
#                 except Exception as e:
#                     print(f"处理 {file_path} 时出错: {e}")
#                     continue

#         self._save_to_json(all_methods)
#         print(f"提取完成，共找到 {len(all_methods)} 个公有方法")
#         return all_methods

#     def _should_skip_file(self, filename: str) -> bool:
#         """判断是否应该跳过该文件"""
#         # 基本忽略规则
#         if filename in ['conftest.py', 'setup.py', '__about__.py', '__version__.py']:
#             return True

#         # 测试文件模式
#         if filename.startswith('test_') or filename.endswith('_test.py'):
#             return True

#         return False

#     def _is_in_ignored_path(self, root_path: str, ignore_dirs: set) -> bool:
#         parts = root_path.split(os.sep)
#         for part in parts:
#             if part in ignore_dirs:
#                 return True
#         return False

#     def _extract_focal_method(self, file_path):
#         """提取文件中所有公有函数，包括嵌套类中的方法，同时提取import语句和类上下文"""
#         with open(file_path, 'r', encoding='utf-8') as f:
#             code = f.read()
#             tree = python_parser.parse(bytes(code, 'utf-8'))
#             root_node = tree.root_node

#             # 首先提取文件的import语句
#             imports = self._extract_imports(root_node, code)

#             # 提取文件中所有的类信息（包括嵌套类）
#             class_info_dict = self._extract_all_classes(root_node, code)
#             self.class_info_dict = class_info_dict

#             focal_methods = []

#             # 使用迭代方式遍历，更好地控制类边界的检测
#             stack = [(root_node, [])]  # (节点, 路径上的类)

#             while stack:
#                 node, current_classes = stack.pop()

#                 # 如果是带装饰的定义（decorated_definition），优先处理装饰器
#                 if node.type == 'decorated_definition':
#                     # 查找内部的 function_definition 或 class_definition
#                     inner_def = None
#                     for child in node.children:
#                         if child.type in ('function_definition', 'class_definition'):
#                             inner_def = child
#                             break

#                     # 如果是函数定义，并且被 @deprecated 标注，则跳过提取
#                     if inner_def and inner_def.type == 'function_definition':
#                         if self._decorated_definition_has_deprecated(node, code):
#                             # 跳过已弃用的函数/方法
#                             continue
#                         # 否则，按常规提取该函数（把 inner_def 当作 function_definition 处理）
#                         node = inner_def  # fall through to function logic below

#                 # 处理类定义
#                 if node.type == 'class_definition':
#                     class_name = self._get_name(node)
#                     if class_name:
#                         # 创建新的类上下文
#                         new_classes = current_classes + [{
#                             'name': class_name,
#                             'node': node
#                         }]

#                         # 将子节点与新类上下文一起压栈
#                         for child in reversed(node.children):
#                             stack.append((child, new_classes))
#                         continue

#                 # 处理函数定义
#                 if node.type == 'function_definition':
#                     function_name = self._get_name(node)

#                     # 只提取公有函数（不以单下划线开头）
#                     if function_name and not function_name.startswith('_'):
#                         proj_root = str(self.project_root) + '/'
#                         src_file = str(file_path).split(proj_root)[1]

#                         # 构建方法信息
#                         method_info = {
#                             'name': function_name,
#                             'src_file': src_file,
#                             'test_file': self._gen_test_file_path(file_path, function_name),
#                             'code': code[node.start_byte:node.end_byte],
#                             'is_async': self._is_async_function(node),
#                             'imports': imports  # 添加import上下文
#                         }

#                         # 如果有类上下文，添加类信息和构造函数
#                         if current_classes:
#                             # 获取类的全名
#                             class_hierarchy = [cls['name'] for cls in current_classes]
#                             full_class_name = '.'.join(class_hierarchy)

#                             # 添加类信息
#                             method_info['class_hierarchy'] = class_hierarchy
#                             method_info['class_name'] = current_classes[-1]['name']  # 直接所属类
#                             method_info['full_class_name'] = full_class_name
#                             method_info['type'] = 'method'

#                             # 获取类的构造函数和字段信息
#                             class_info = class_info_dict.get(full_class_name)
#                             if class_info:
#                                 # 只添加构造函数（如果存在的话）
#                                 if 'constructor' in class_info:
#                                     method_info['class_constructor'] = class_info['constructor']
#                                 # 添加字段信息
#                                 if 'fields' in class_info:
#                                     method_info['class_fields'] = class_info['fields']
#                                 # 添加类变量
#                                 if 'class_variables' in class_info:
#                                     method_info['class_variables'] = class_info['class_variables']
#                         else:
#                             method_info['type'] = 'function'

#                         focal_methods.append(method_info)

#                 # 继续遍历子节点
#                 for child in reversed(node.children):
#                     stack.append((child, current_classes))

#             return focal_methods

#     def _extract_all_classes(self, root_node, code):
#         """提取文件中所有的类信息，包括构造函数和字段"""
#         class_info_dict = {}

#         def extract_class_details(class_node, parent_classes=[]):
#             """递归提取类信息"""
#             class_name = self._get_name(class_node)
#             if not class_name:
#                 return

#             # 构建类的全名
#             full_class_name = '.'.join(parent_classes + [class_name]) if parent_classes else class_name

#             # 初始化类信息
#             class_info = {
#                 'name': class_name,
#                 'full_name': full_class_name,
#                 'constructor': None,
#                 'fields': [],  # 实例字段
#                 'class_variables': [],  # 类变量
#                 'nested_classes': []
#             }

#             # 查找类的body
#             class_body = None
#             for child in class_node.children:
#                 if child.type == 'block':
#                     class_body = child
#                     break

#             if class_body:
#                 # 遍历类体中的节点
#                 for child in class_body.children:
#                     # 处理被装饰的函数（decorated_definition），可能包含 __init__
#                     if child.type == 'decorated_definition':
#                         # 查找内部的 function_definition
#                         inner = None
#                         for gc in child.children:
#                             if gc.type == 'function_definition':
#                                 inner = gc
#                                 break
#                         if inner:
#                             func_name = self._get_name(inner)
#                             # 如果是 __init__ 并且没有被 @deprecated 标注，则提取
#                             if func_name == '__init__':
#                                 if not self._decorated_definition_has_deprecated(child, code):
#                                     class_info['constructor'] = code[inner.start_byte:inner.end_byte]
#                                 # 否则跳过（认为构造函数已弃用）

#                         continue

#                     # 提取构造函数 (__init__)
#                     if child.type == 'function_definition':
#                         func_name = self._get_name(child)
#                         if func_name == '__init__':
#                             class_info['constructor'] = code[child.start_byte:child.end_byte]

#                     # 提取类变量（类级别的赋值）
#                     elif child.type == 'expression_statement':
#                         # 检查是否包含赋值
#                         assignment = self._find_assignment(child)
#                         if assignment:
#                             # 检查是否是类变量（不是self.xxx）
#                             if not self._is_instance_assignment(assignment, code):
#                                 var_info = self._extract_variable_info(assignment, code)
#                                 if var_info:
#                                     class_info['class_variables'].append(var_info)

#                     # 提取字段（实例变量赋值，通常在__init__中提取，但也可能在类方法中）
#                     elif child.type == 'assignment':
#                         # 检查是否是实例字段
#                         if self._is_instance_assignment(child, code):
#                             field_info = self._extract_field_info(child, code)
#                             if field_info:
#                                 class_info['fields'].append(field_info)

#                     # 递归处理嵌套类
#                     elif child.type == 'class_definition':
#                         nested_class_name = self._get_name(child)
#                         if nested_class_name:
#                             nested_info = extract_class_details(child, parent_classes + [class_name])
#                             if nested_info:
#                                 class_info['nested_classes'].append(nested_info)

#             return class_info

#         # 遍历所有顶级类
#         def traverse_nodes(node):
#             if node.type == 'class_definition':
#                 class_info = extract_class_details(node)
#                 if class_info:
#                     class_info_dict[class_info['full_name']] = class_info
#             for child in node.children:
#                 traverse_nodes(child)

#         traverse_nodes(root_node)
#         return class_info_dict

#     def _find_assignment(self, node):
#         """在节点中查找赋值语句"""
#         stack = [node]
#         while stack:
#             current = stack.pop()
#             if current.type == 'assignment':
#                 return current
#             for child in current.children:
#                 stack.append(child)
#         return None

#     def _is_instance_assignment(self, assignment_node, code):
#         """检查是否是实例字段赋值"""
#         for child in assignment_node.children:
#             if child.type == 'attribute':
#                 attr_text = code[child.start_byte:child.end_byte]
#                 if attr_text.startswith('self.'):
#                     return True
#         return False

#     def _extract_variable_info(self, assignment_node, code):
#         """提取变量信息（不提取私有字段）"""
#         try:
#             left_side = None
#             right_side = None
#             left_node = None

#             # 查找赋值操作符
#             for i, child in enumerate(assignment_node.children):
#                 if child.type == 'identifier' or child.type == 'attribute':
#                     left_side = code[child.start_byte:child.end_byte]
#                     left_node = child  # 记录左侧节点

#                 elif child.type == '=':
#                     if i + 1 < len(assignment_node.children):
#                         right_side = code[assignment_node.children[i+1].start_byte:assignment_node.children[i+1].end_byte]
#                     break

#             if left_side:
#                 # 将字节串转换为字符串（如果需要）
#                 if isinstance(left_side, bytes):
#                     left_side_str = left_side.decode('utf-8')
#                 else:
#                     left_side_str = str(left_side)

#                 # 检查是否为私有字段（以_开头）
#                 if left_side_str.startswith('_'):
#                     return None

#                 # 对于属性访问，检查属性名部分
#                 if left_node and left_node.type == 'attribute':
#                     # 拆分属性访问路径
#                     attr_parts = left_side_str.split('.')
#                     if attr_parts and attr_parts[-1].startswith('_'):
#                         return None

#                 return code[assignment_node.start_byte:assignment_node.end_byte]

#         except Exception as e:
#             # 打印错误信息以便调试
#             print(f"Error extracting variable info: {e}")
#             pass
#         return None

#     def _extract_field_info(self, assignment_node, code):
#         """提取字段信息"""
#         return self._extract_variable_info(assignment_node, code)

#     def _gen_test_file_path(self, file_path, function_name):
#         temp_path = file_path.split(str(self.project_root))[1]
#         temp_path2 = temp_path.split(".py")[0]
#         file_name = temp_path2.split('/')[-1]
#         temp_path3 = temp_path2.split(file_name)[0]
#         return "gen_tests" + str(temp_path3) + "Test" + file_name + '/' + "test_" + function_name + ".py"

#     def _extract_imports(self, root_node, code):
#         """提取文件中的所有import语句"""
#         imports = {
#             'imports': [],  # 简单import语句
#             'from_imports': [],  # from ... import 语句
#             'imports_with_aliases': []  # 带别名的import
#         }

#         def traverse_imports(node):
#             """递归遍历节点提取import语句"""
#             if node.type == 'import_statement':
#                 # 处理 import xxx, import xxx as yyy
#                 import_text = code[node.start_byte:node.end_byte].strip()
#                 if ' as ' in import_text:
#                     imports['imports_with_aliases'].append(import_text)
#                 else:
#                     imports['imports'].append(import_text)

#             elif node.type == 'import_from_statement':
#                 # 处理 from xxx import yyy
#                 import_text = code[node.start_byte:node.end_byte].strip()
#                 imports['from_imports'].append(import_text)

#             # 继续遍历子节点
#             for child in node.children:
#                 traverse_imports(child)

#         # 从根节点开始遍历
#         traverse_imports(root_node)
#         return imports

#     def _get_name(self, node):
#         """从函数/类定义节点中提取函数/类名"""
#         for child in node.children:
#             if child.type == 'identifier':
#                 return child.text.decode('utf-8')
#         return None

#     def _is_async_function(self, function_node):
#         """检查是否为异步函数"""
#         for child in function_node.children:
#             if child.type == 'async':
#                 return True
#         return False

#     def _decorated_definition_has_deprecated(self, decorated_node, code) -> bool:
#         """
#         检查 decorated_definition 节点的装饰器中是否包含 deprecated 关键字。
#         通过在装饰器源码文本中查找独立单词 'deprecated'（忽略大小写）来判断。
#         """
#         try:
#             for child in decorated_node.children:
#                 # 装饰器文本通常以 '@' 开头，直接取对应源码片段做检查
#                 text = code[child.start_byte:child.end_byte].strip()
#                 if text.startswith('@'):
#                     # 小写并使用边界匹配，避免比如 'notdeprecated' 的误判
#                     if re.search(r'\bdeprecated\b', text.lower()):
#                         return True
#             return False
#         except Exception:
#             return False

#     def _save_to_json(self, methods):
#         """将提取结果保存为JSON文件"""
#         # 转换为可序列化的格式
#         serializable_methods = []
#         for method in methods:
#             serializable_method = method.copy()
#             # 确保所有字符串都是可序列化的
#             for key, value in serializable_method.items():
#                 if isinstance(value, bytes):
#                     serializable_method[key] = value.decode('utf-8')
#             serializable_methods.append(serializable_method)

#         with open(self.output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable_methods, f, indent=2, ensure_ascii=False)


# if __name__ == "__main__":
#     extractor = PythonFocalExtractor("projects/tornado/tornado", "tornado_focal_class_context1.json")
#     extractor.extract_project_focal_methods()


import os
import json
import re
import ast
import radon
import numpy as np
import random
# from radon.complexity import cc_visit
# from radon.raw import analyze
from collections import defaultdict
from multi_parser import python_parser
from file_select import *
from func_select import StratifiedFunctionSelector


class EnhancedPythonFocalExtractor:
    """
    增强版Python焦点方法提取器：包含过滤和分层选择功能
    """

    def __init__(self, project_root, file_list, output_file, min_loc_threshold=5, random_seed=42):
        """
        初始化提取器

        Args:
            project_root: 项目根目录
            file_list: 文件列表
            output_file: 输出文件
            min_loc_threshold: 最小行数阈值
            random_seed: 随机种子
        """
        self.project_root = project_root
        self.files = file_list
        self.output_file = output_file
        self.min_loc_threshold = min_loc_threshold
        self.random_seed = random_seed

        # 初始化组件
        self.selector = StratifiedFunctionSelector(random_seed=random_seed)

        # getter/setter模式的正则表达式
        self.getter_setter_patterns = [
            r'^get_', r'^set_', r'^is_', r'^has_',  # 前缀
            r'_get$', r'_set$',  # 后缀
            r'^[gs]et[A-Z]',  # Java风格的getter/setter
        ]

        # 存储统计信息
        self.stats = defaultdict(lambda: defaultdict(int))
        self.selection_results = []

    def extract_and_select_functions(self):
        """
        完整的提取和选择流程：
        1. 提取项目中的方法
        2. 应用过滤规则
        3. 对每个文件进行分层抽样
        """
        all_selected_methods = []

        for file_path in self.files:
            try:
                print(f"\n处理文件: {os.path.basename(file_path)}")

                # 步骤1: 提取文件中的所有方法
                all_methods = self._extract_focal_method(file_path)
                if not all_methods:
                    print(f"    文件中没有提取到方法")
                    continue

                # 步骤2: 过滤公有方法
                public_methods = [
                    method for method in all_methods
                    if not method.get('name', '').startswith('_')
                ]

                # 步骤3: 应用硬规则过滤
                candidate_methods = []
                filtered_methods = []

                for method in public_methods:
                    should_filter, filter_reason = self._should_filter_method(method)

                    if should_filter:
                        filtered_methods.append({
                            **method,
                            'filter_reason': filter_reason
                        })
                        self.stats[os.path.basename(file_path)]['filtered'] += 1
                    else:
                        candidate_methods.append(method)
                        self.stats[os.path.basename(file_path)]['candidates'] += 1

                # 步骤4: 分层抽样选择
                if candidate_methods:
                    selection_result = self.selector.select_functions_from_file(
                        file_path, candidate_methods
                    )

                    if selection_result['selected_functions']:
                        # 添加到最终结果
                        for func in selection_result['selected_functions']:
                            # 添加文件信息
                            # func['source_file'] = file_path
                            function = {
                                "project_root": func['project_root'],
                                "name": func['name'],
                                "src_file": func['src_file'],
                                "test_file": func['test_file'],
                                "code": func['code'],
                                "is_async": func['is_async'],
                                "type": func['type']
                            }
                            if func['type'] == "method":
                                function['class_hierarchy'] = func['class_hierarchy']
                                function['class_name'] = func['class_name']
                                function['full_class_name'] = func['full_class_name']
                                function['class_constructor'] = func['class_constructor']
                                function['class_fields'] = func['class_fields']
                                function['class_variables'] = func['class_variables']
                                function['class_hierarchy'] = func['class_hierarchy']

                            all_selected_methods.append(function)

                        # 保存选择结果
                        self.selection_results.append(selection_result)

                        print(f"   选择完成: {len(selection_result['selected_functions'])} 个函数")
                    else:
                        print(f"    没有选择任何函数")

                # 记录统计
                self.stats[os.path.basename(file_path)]['total'] = len(all_methods)
                self.stats[os.path.basename(file_path)]['public'] = len(public_methods)

            except SyntaxError as e:
                print(f"语法错误，跳过文件 {file_path}: {e}")
                continue
            except UnicodeDecodeError as e:
                print(f"编码错误，跳过文件 {file_path}: {e}")
                continue
            except Exception as e:
                print(f"处理 {file_path} 时出错: {e}")
                continue

        # 保存结果
        self._save_to_json(all_selected_methods)

        # 打印统计报告
        # self._print_statistics_report()

        return all_selected_methods

    def _should_filter_method(self, method_info):
        """
        判断是否应该过滤该方法

        Returns:
            tuple: (是否过滤, 过滤原因)
        """
        # 获取方法代码
        method_code = method_info.get('code', '')

        # 规则1: trivial functions (LOC < N & CC = 1)
        if self._is_trivial_function(method_code, method_info):
            return True, "trivial (LOC<阈值 & CC=1)"

        # 规则2: getter / setter（模式匹配）
        method_name = method_info.get('name', '')
        if self._is_getter_setter(method_name, method_info):
            return True, "getter/setter"

        # 规则3: 无返回值且无状态修改
        if self._no_return_no_state_change(method_code, method_info):
            return True, "无返回值无状态修改"

        # 规则4: auto-generated / inline wrappers
        if self._is_trivial_wrapper(method_code, method_info):
            return True, "简单包装器"

        return False, ""

    def _is_trivial_function(self, method_code, method_info):
        """规则1: trivial functions（LOC < N & CC = 1）"""
        try:
            loc = method_info.get('loc', 0)
            complexity = method_info.get('complexity', 1)

            if loc < self.min_loc_threshold and complexity == 1:
                return True
        except Exception:
            pass

        return False

    def _is_getter_setter(self, method_name, method_info):
        """规则2: getter / setter（模式匹配）"""
        for pattern in self.getter_setter_patterns:
            if re.match(pattern, method_name):
                complexity = method_info.get('complexity', 1)
                if complexity <= 1:
                    return True
        return False

    def _no_return_no_state_change(self, method_code, method_info):
        """规则3: 无返回值且无状态修改"""
        try:
            # 检查是否有return语句
            has_return = 'return ' in method_code

            # 检查是否有对self属性的赋值
            has_self_assignment = False
            lines = method_code.split('\n')
            for line in lines:
                stripped = line.strip()
                if 'self.' in stripped and '=' in stripped:
                    if stripped.find('self.') < stripped.find('='):
                        has_self_assignment = True
                        break

            # 如果既没有return也没有对self的赋值，则过滤
            if not has_return and not has_self_assignment:
                method_name = method_info.get('name', '')
                if method_name not in ['__init__', '__new__', 'setup', 'initialize']:
                    return True
        except Exception:
            pass

        return False

    def _is_trivial_wrapper(self, method_code, method_info):
        """规则4: auto-generated / inline wrappers"""
        try:
            lines = method_code.split('\n')
            effective_lines = [line.strip() for line in lines
                               if line.strip() and not line.strip().startswith('#')]

            if len(effective_lines) <= 2:
                method_name = method_info.get('name', '')
                if method_name not in ['run', 'execute', 'process', 'handle', 'main']:
                    return True
        except Exception:
            pass

        return False

    # 以下是您原有的方法，我根据需要进行修改
    # 主要修改：添加参数计数功能

    def _extract_focal_method(self, file_path):
        """提取文件中所有公有函数，包括参数计数"""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            tree = python_parser.parse(bytes(code, 'utf-8'))
            root_node = tree.root_node

            # imports = self._extract_imports(root_node, code)
            class_info_dict = self._extract_all_classes(root_node, code)

            focal_methods = []
            stack = [(root_node, [])]  # (节点, 路径上的类)

            while stack:
                node, current_classes = stack.pop()

                # 处理装饰器定义
                if node.type == 'decorated_definition':
                    inner_def = None
                    for child in node.children:
                        if child.type in ('function_definition', 'class_definition'):
                            inner_def = child
                            break

                    if inner_def and inner_def.type == 'function_definition':
                        if self._decorated_definition_has_deprecated(node, code):
                            continue
                        node = inner_def

                # 处理类定义
                if node.type == 'class_definition':
                    class_name = self._get_name(node)
                    if class_name:
                        new_classes = current_classes + [{
                            'name': class_name,
                            'node': node
                        }]

                        for child in reversed(node.children):
                            stack.append((child, new_classes))
                        continue

                # 处理函数定义
                if node.type == 'function_definition':
                    function_name = self._get_name(node)

                    if function_name and not function_name.startswith('_'):

                        # 计算代码行数、复杂度、参数个数
                        method_code = code[node.start_byte:node.end_byte]

                        complexity, loc, param_count = self._compute_complexity_and_loc(method_code)

                        proj_root = str(self.project_root) + '/'
                        src_file = str(file_path).split(proj_root)[1]

                        # 构建方法信息
                        method_info = {
                            'project_root': self.project_root,
                            'name': function_name,
                            'src_file': src_file,
                            'test_file': self._gen_test_file_path(file_path, function_name),
                            'code': method_code,
                            'is_async': self._is_async_function(node),
                            # 'imports': imports,
                            'loc': loc,
                            'complexity': complexity,
                            'param_count': param_count
                        }

                        # 添加类信息
                        if current_classes:
                            class_hierarchy = [cls['name'] for cls in current_classes]
                            full_class_name = '.'.join(class_hierarchy)

                            method_info['class_hierarchy'] = class_hierarchy
                            method_info['class_name'] = current_classes[-1]['name']
                            method_info['full_class_name'] = full_class_name
                            method_info['type'] = 'method'

                            class_info = class_info_dict.get(full_class_name)
                            if class_info:
                                if 'constructor' in class_info:
                                    method_info['class_constructor'] = class_info['constructor']
                                if 'fields' in class_info:
                                    method_info['class_fields'] = class_info['fields']
                                if 'class_variables' in class_info:
                                    method_info['class_variables'] = class_info['class_variables']
                        else:
                            method_info['type'] = 'function'

                        focal_methods.append(method_info)

                # 继续遍历子节点
                for child in reversed(node.children):
                    stack.append((child, current_classes))

            return focal_methods

    def _compute_complexity_and_loc(self, code):
        """计算代码的圈复杂度、代码行数、参数个数"""
        complexity = 0
        loc = 0
        param_count = 0
        try:
            report = lizard.analyze_file.analyze_source_code("temp.py", code)

            complexity = report.function_list[0].__dict__['cyclomatic_complexity']
            loc = report.function_list[0].__dict__['nloc']
            param_count = len(report.function_list[0].__dict__['full_parameters'])

        except Exception:
            pass

        return complexity, loc, param_count

    def _gen_test_file_path(self, file_path, function_name):
        temp_path = file_path.split(str(self.project_root))[1]
        temp_path2 = temp_path.split(".py")[0]
        file_name = temp_path2.split('/')[-1]
        temp_path3 = temp_path2.split(file_name)[0]
        test_path = str(temp_path3) + "Test" + file_name + '/' + "test_" + function_name + ".py"
        if "src/" in test_path:
            test_path = test_path[1:]
            return test_path.replace('src/', 'test/')
        return "tests" + test_path

    def _extract_imports(self, root_node, code):
        """提取文件中的所有import语句"""
        imports = {
            'imports': [],
            'from_imports': [],
            'imports_with_aliases': []
        }

        def traverse_imports(node):
            if node.type == 'import_statement':
                import_text = code[node.start_byte:node.end_byte].strip()
                if ' as ' in import_text:
                    imports['imports_with_aliases'].append(import_text)
                else:
                    imports['imports'].append(import_text)

            elif node.type == 'import_from_statement':
                import_text = code[node.start_byte:node.end_byte].strip()
                imports['from_imports'].append(import_text)

            for child in node.children:
                traverse_imports(child)

        traverse_imports(root_node)
        return imports

    def _extract_all_classes(self, root_node, code):
        """提取文件中所有的类信息，包括构造函数和字段"""
        class_info_dict = {}

        def extract_class_details(class_node, parent_classes=[]):
            class_name = self._get_name(class_node)
            if not class_name:
                return

            full_class_name = '.'.join(parent_classes + [class_name]) if parent_classes else class_name

            class_info = {
                'name': class_name,
                'full_name': full_class_name,
                'constructor': None,
                'fields': [],
                'class_variables': [],
                'nested_classes': []
            }

            class_body = None
            for child in class_node.children:
                if child.type == 'block':
                    class_body = child
                    break

            if class_body:
                for child in class_body.children:
                    if child.type == 'decorated_definition':
                        inner = None
                        for gc in child.children:
                            if gc.type == 'function_definition':
                                inner = gc
                                break
                        if inner:
                            func_name = self._get_name(inner)
                            if func_name == '__init__':
                                if not self._decorated_definition_has_deprecated(child, code):
                                    class_info['constructor'] = code[inner.start_byte:inner.end_byte]
                        continue

                    if child.type == 'function_definition':
                        func_name = self._get_name(child)
                        if func_name == '__init__':
                            class_info['constructor'] = code[child.start_byte:child.end_byte]

                    elif child.type == 'expression_statement':
                        assignment = self._find_assignment(child)
                        if assignment:
                            if not self._is_instance_assignment(assignment, code):
                                var_info = self._extract_variable_info(assignment, code)
                                if var_info:
                                    class_info['class_variables'].append(var_info)

                    elif child.type == 'assignment':
                        if self._is_instance_assignment(child, code):
                            field_info = self._extract_field_info(child, code)
                            if field_info:
                                class_info['fields'].append(field_info)

                    elif child.type == 'class_definition':
                        nested_class_name = self._get_name(child)
                        if nested_class_name:
                            nested_info = extract_class_details(child, parent_classes + [class_name])
                            if nested_info:
                                class_info['nested_classes'].append(nested_info)

            return class_info

        def traverse_nodes(node):
            if node.type == 'class_definition':
                class_info = extract_class_details(node)
                if class_info:
                    class_info_dict[class_info['full_name']] = class_info
            for child in node.children:
                traverse_nodes(child)

        traverse_nodes(root_node)
        return class_info_dict

    def _get_name(self, node):
        """从函数/类定义节点中提取函数/类名"""
        for child in node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return None

    def _is_async_function(self, function_node):
        """检查是否为异步函数"""
        for child in function_node.children:
            if child.type == 'async':
                return True
        return False

    def _decorated_definition_has_deprecated(self, decorated_node, code) -> bool:
        """检查装饰器中是否包含deprecated关键字"""
        try:
            for child in decorated_node.children:
                text = code[child.start_byte:child.end_byte].strip()
                if text.startswith('@'):
                    if re.search(r'\bdeprecated\b', text.lower()):
                        return True
            return False
        except Exception:
            return False

    def _find_assignment(self, node):
        """在节点中查找赋值语句"""
        stack = [node]
        while stack:
            current = stack.pop()
            if current.type == 'assignment':
                return current
            for child in current.children:
                stack.append(child)
        return None

    def _is_instance_assignment(self, assignment_node, code):
        """检查是否是实例字段赋值"""
        for child in assignment_node.children:
            if child.type == 'attribute':
                attr_text = code[child.start_byte:child.end_byte]
                if attr_text.startswith('self.'):
                    return True
        return False

    def _extract_variable_info(self, assignment_node, code):
        """提取变量信息"""
        try:
            left_side = None
            right_side = None
            left_node = None

            for i, child in enumerate(assignment_node.children):
                if child.type == 'identifier' or child.type == 'attribute':
                    left_side = code[child.start_byte:child.end_byte]
                    left_node = child

                elif child.type == '=':
                    if i + 1 < len(assignment_node.children):
                        right_side = code[assignment_node.children[i + 1].start_byte:assignment_node.children[
                            i + 1].end_byte]
                    break

            if left_side:
                if isinstance(left_side, bytes):
                    left_side_str = left_side.decode('utf-8')
                else:
                    left_side_str = str(left_side)

                if left_side_str.startswith('_'):
                    return None

                if left_node and left_node.type == 'attribute':
                    attr_parts = left_side_str.split('.')
                    if attr_parts and attr_parts[-1].startswith('_'):
                        return None

                return code[assignment_node.start_byte:assignment_node.end_byte]

        except Exception as e:
            pass
        return None

    def _extract_field_info(self, assignment_node, code):
        """提取字段信息"""
        return self._extract_variable_info(assignment_node, code)

    def _save_to_json(self, methods):
        """将提取结果保存为JSON文件"""
        serializable_methods = []
        for method in methods:
            serializable_method = method.copy()
            for key, value in serializable_method.items():
                if isinstance(value, bytes):
                    serializable_method[key] = value.decode('utf-8')
            serializable_methods.append(serializable_method)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_methods, f, indent=2, ensure_ascii=False)

    def _print_statistics_report(self):
        """打印统计报告"""
        print("\n" + "=" * 80)
        print("完整提取与选择统计报告")
        print("=" * 80)

        total_files = len(self.stats)
        total_methods = sum(stats.get('total', 0) for stats in self.stats.values())
        total_public = sum(stats.get('public', 0) for stats in self.stats.values())
        total_candidates = sum(stats.get('candidates', 0) for stats in self.stats.values())
        total_filtered = sum(stats.get('filtered', 0) for stats in self.stats.values())
        total_selected = len([result for result in self.selection_results
                              if result['selected_functions']])

        print(f"\n 总体统计:")
        print(f"  处理文件数: {total_files}")
        print(f"  提取方法总数: {total_methods}")
        print(f"  公有方法数: {total_public}")
        print(f"  候选方法数: {total_candidates}")
        print(f"  过滤方法数: {total_filtered}")
        print(f"  选择文件数: {total_selected}")

        if total_candidates > 0:
            filter_rate = total_filtered / total_public * 100 if total_public > 0 else 0
            selection_rate = total_selected / total_files * 100 if total_files > 0 else 0
            print(f"  过滤率: {filter_rate:.1f}%")
            print(f"  选择率: {selection_rate:.1f}%")

        # 打印每个文件的选择详情
        if self.selection_results:
            print(f"\n 文件选择详情:")
            for result in self.selection_results:
                if result['selected_functions']:
                    print(f"\n  {result['file_name']}:")
                    print(f"    候选函数: {result['total_candidates']}")
                    print(f"    选择函数: {len(result['selected_functions'])}")
                    for tier_name, tier_info in result['stratification'].items():
                        print(f"    {tier_name}: {tier_info['count']}个函数")

                    print(f"    选择的函数:")
                    for i, func in enumerate(result['selected_functions'], 1):
                        tier = self.selector._get_tier_for_func(func, result)
                        print(f"      {i}. {func.get('full_class_name', '')}.{func.get('name', '')} "
                              f"(层: {tier}, 得分: {func.get('func_score', 0):.4f})")


# 使用示例
if __name__ == "__main__":
    project_root = "projects/pylint"

    # 创建分析器实例
    analyzer = FileQualityAnalyzer(
        language="python",
        random_seed=42,  # 固定随机种子，确保结果可重复
        sampling_k=2  # 每个层级抽取2个文件
    )

    # 完整分析项目
    sample_files = analyzer.analyze_project(
        project_path=project_root,
        group_by_module=True  # 按模块分组
    )

    print(len(sample_files))

    # 创建提取器
    extractor = EnhancedPythonFocalExtractor(
        project_root=project_root,
        file_list=sample_files,
        output_file="pylint_lite.json",
        min_loc_threshold=5,
        random_seed=42
    )

    # 执行完整的提取和选择流程
    selected_functions = extractor.extract_and_select_functions()

    # 打印详细的选择报告
    # if extractor.selection_results:
    #     print("\n" + "="*80)
    #     print("详细选择报告")
    #     print("="*80)

    #     for result in extractor.selection_results:
    #         extractor.selector.print_selection_report(result)
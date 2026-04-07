# import os
# import json
# from multi_parser import js_parser


# class JSFocalExtractor:
#     """提取 JavaScript 项目中的公有函数"""

#     def __init__(self, project_root, output_file):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file

#     def extract_project_public_functions(self):
#         """遍历项目目录，提取所有公有函数"""
#         public_functions = []

#         for root, dirs, files in os.walk(self.project_root):
#             # 忽略测试文件、node_modules、git 等
#             if any(ignore in root for ignore in ['test', 'node_modules', '.git', '.vscode', '.idea']):
#                 continue

#             for file in files:
#                 if file.endswith('.js') and not file.startswith('test_'):
#                     file_path = os.path.join(root, file)
#                     try:
#                         funcs = self._extract_public_functions_from_file(file_path)
#                         public_functions.extend(funcs)
#                     except Exception as exc:
#                         print(f"Error processing {file_path}: {exc}")

#         return public_functions

#     def _extract_public_functions_from_file(self, file_path):
#         """从单个 .js 文件中提取公有函数"""

#         with open(file_path, 'rb') as f:
#             code = f.read()          # bytes
#         tree = js_parser.parse(code)
#         root_node = tree.root_node

#         public_funcs = []

#         # 采用深度优先的显式栈（node, current_class_stack）
#         stack = [(root_node, [])]

#         while stack:
#             node, current_classes = stack.pop()

#             # 处理类声明 / 类表达式
#             if node.type in ('class_declaration', 'class_expression'):
#                 class_name = self._get_name(node, code)
#                 if class_name:
#                     new_classes = current_classes + [{'name': class_name, 'node': node}]
#                     # 将子节点压入栈，携带新的类上下文
#                     for child in reversed(node.children):
#                         stack.append((child, new_classes))
#                     continue

#             # 处理函数声明 / 方法定义
#             if node.type in ('function_declaration', 'method_definition'):
#                 func_name = self._get_name(node, code)
#                 if func_name and not func_name.startswith('_') and not func_name.startswith('#'):
#                     func_info = {
#                         'name': func_name,
#                         'file': file_path,
#                         'code': code[node.start_byte:node.end_byte].decode('utf-8'),  # 解码为 str
#                         'is_async': self._is_async_function(node),
#                     }

#                     # 记录所属类信息（如果有）
#                     if current_classes:
#                         func_info['class_hierarchy'] = [cls['name'] for cls in current_classes]
#                         func_info['class_name'] = current_classes[-1]['name']
#                         func_info['full_class_name'] = '.'.join(
#                             [cls['name'] for cls in current_classes]
#                         )
#                         func_info['type'] = 'method'
#                     else:
#                         func_info['type'] = 'function'

#                     public_funcs.append(func_info)

#             # 处理箭头函数（可在全局或对象属性中出现）
#             elif node.type == 'arrow_function':
#                 # 只保留那些有显式名称的箭头函数（如 const foo = () => {}）
#                 func_name = self._get_ancestor_assignment_name(node, code)
#                 if func_name and not func_name.startswith('_') and not func_name.startswith('#'):
#                     func_info = {
#                         'name': func_name,
#                         'file': file_path,
#                         'code': code[node.start_byte:node.end_byte].decode('utf-8'),
#                         'is_async': self._is_async_function(node),
#                         'type': 'function',
#                     }
#                     public_funcs.append(func_info)

#             # 继续遍历子节点
#             for child in reversed(node.children):
#                 stack.append((child, current_classes))

#         return public_funcs

#     def _get_name(self, node, code):
#         """提取类/函数的名称"""
#         for child in node.children:
#             if child.type == 'identifier':
#                 return code[child.start_byte:child.end_byte].decode('utf-8')
#         return None

#     def _get_ancestor_assignment_name(self, node, code):
#         """
#         对于 arrow_function，尝试向上寻找最近的 AssignmentExpression
#         例如 const foo = () => { … }，返回 'foo'
#         """
#         parent = node.parent
#         while parent:
#             if parent.type == 'assignment_expression':
#                 for child in parent.children:
#                     if child.type == 'identifier':
#                         return code[child.start_byte:child.end_byte].decode('utf-8')
#             parent = parent.parent
#         return None

#     def _is_async_function(self, func_node):
#         """判断函数是否使用 async 关键字"""
#         for child in func_node.children:
#             if child.type == 'async':
#                 return True
#         return False

#     def save_to_json(self, output_file):
#         """将提取的函数信息保存为 JSON"""
#         functions = self.extract_project_public_functions()

#         # 确保所有 bytes 都被解码为 str
#         serializable = []
#         for fn in functions:
#             fn_copy = fn.copy()
#             for k, v in fn_copy.items():
#                 if isinstance(v, bytes):
#                     fn_copy[k] = v.decode('utf-8')
#             serializable.append(fn_copy)

#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable, f, indent=2, ensure_ascii=False)


# if __name__ == '__main__':
#     project_root = './three.js'
#     output_path = 'three_focal.json'

#     extractor = JSFocalExtractor(project_root, output_path)
#     extractor.extract_project_public_functions()


import os
import json
from multi_parser import js_parser

# class JSFocalExtractor:
#     """提取 JavaScript 项目中的公有函数和类上下文信息"""

#     def __init__(self, project_root, output_file):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file
#         self.test_files_cache = {}  # 缓存测试文件查找结果

#     def extract_project_functions(self):
#         """提取项目中的所有公有函数（包含类上下文）"""
#         all_functions = []

#         # 定义要忽略的目录模式
#         IGNORE_DIRS = ['node_modules', 'dist', 'build', '.git', '.vscode', 'docs', 'examples', 'test', 'tests', '__tests__', 'coverage']

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
#                 if file.endswith('.js') and not file.endswith('.test.js') and not file.endswith('.tests.js'):
#                     file_path = os.path.join(root, file)
#                     try:
#                         print(f"处理文件: {file_path}")
#                         file_funcs = self._extract_functions_from_file(file_path)
#                         all_functions.extend(file_funcs)
#                     except Exception as exc:
#                         print(f"Error processing {file_path}: {exc}")

#         return all_functions

#     def _get_declarator_name_and_init(self, declarator_node, code):
#         """从variable_declarator节点提取变量名和初始化表达式（简化版）"""
#         var_name = None
#         init_node = None

#         # 方法1：直接遍历查找 function 或 arrow_function 节点
#         for child in declarator_node.children:
#             if child.type == 'identifier':
#                 var_name = code[child.start_byte:child.end_byte].decode('utf-8')
#             elif child.type in ['function', 'arrow_function']:
#                 init_node = child

#         # 方法2：如果没找到，检查是否有等号，等号后面的节点就是初始化表达式
#         if not init_node:
#             for i, child in enumerate(declarator_node.children):
#                 if child.type == '=' and i + 1 < len(declarator_node.children):
#                     next_node = declarator_node.children[i + 1]
#                     if next_node.type in ['function', 'arrow_function']:
#                         init_node = next_node
#                     break

#         return var_name, init_node

#     def _is_private_name(self, name):
#         """判断名称是否为私有（以下划线或井号开头）"""
#         # 确保name是字符串
#         if not isinstance(name, str):
#             return False
#         return name.startswith('_') or name.startswith('#')

#     def _extract_functions_from_file(self, file_path):
#         """从单个文件中提取函数信息（完整版）"""
#         with open(file_path, 'rb') as f:
#             code = f.read()

#         tree = js_parser.parse(code)
#         root_node = tree.root_node

#         functions = []
#         # 第一遍：提取类信息
#         class_contexts = self._extract_all_class_info(root_node, code, file_path)

#         # 第二遍：提取函数信息
#         stack = [(root_node, [], False)]  # (节点, 类栈, 是否在函数体内)

#         while stack:
#             node, current_classes, in_function_body = stack.pop()

#             # 1. 处理类声明
#             if node.type == 'class_declaration':
#                 class_name = self._get_class_name(node, code)
#                 if class_name:
#                     new_class_stack = current_classes + [class_name]
#                     # 找到类体
#                     for child in node.children:
#                         if child.type == 'class_body':
#                             for grandchild in reversed(child.children):
#                                 stack.append((grandchild, new_class_stack, in_function_body))
#                             break
#                 continue

#             # 2. 处理函数声明
#             if node.type == 'function_declaration':
#                 if in_function_body:
#                     # 嵌套函数，只传递状态不提取
#                     self._push_function_body_children(node, stack, current_classes, True)
#                     continue

#                 func_name = self._get_name(node, code)
#                 if func_name and not self._is_private_name(func_name):
#                     func_info = self._create_function_info(
#                         node, code, file_path, func_name, 'function', current_classes
#                     )
#                     if func_info:
#                         functions.append(func_info)

#                 self._push_function_body_children(node, stack, current_classes, True)
#                 continue

#             # 3. 处理变量声明 - 使用 lexical_declaration（const/let声明）
#             if node.type == 'lexical_declaration' and not in_function_body:
#                 # 遍历所有声明器
#                 for child in node.children:
#                     if child.type == 'variable_declarator':
#                         var_name, init_node = self._get_declarator_name_and_init(child, code)

#                         if var_name and init_node and not self._is_private_name(var_name):
#                             # 处理函数表达式
#                             if init_node.type == 'function':
#                                 # 提取整个 lexical_declaration 的完整代码
#                                 full_code = code[node.start_byte:node.end_byte].decode('utf-8')

#                                 func_info = {
#                                     'name': var_name,
#                                     'src_file': os.path.relpath(file_path, self.project_root),
#                                     'test_file': self._find_test_file(file_path, var_name),
#                                     'code': full_code,  # 完整代码，包括 const ... =
#                                     'is_async': self._is_async_function(init_node),
#                                     'type': 'function',
#                                 }

#                                 # 如果是类方法，添加类上下文
#                                 if current_classes:
#                                     class_name = current_classes[-1]
#                                     func_info.update({
#                                         'class_hierarchy': current_classes,
#                                         'class_name': class_name,
#                                         'full_class_name': '.'.join(current_classes)
#                                     })

#                                     # 获取类信息
#                                     if class_name in class_contexts:
#                                         class_context = class_contexts[class_name]
#                                         func_info['constructor'] = class_context.get('constructor', [])
#                                         func_info['fields'] = class_context.get('fields', [])
#                                     else:
#                                         func_info['constructor'] = []
#                                         func_info['fields'] = []

#                                 functions.append(func_info)

#                                 # 标记函数体内部
#                                 self._push_function_body_children(init_node, stack, current_classes, True)

#                             # 处理箭头函数表达式
#                             elif init_node.type == 'arrow_function':
#                                 # 提取整个 lexical_declaration 的完整代码
#                                 full_code = code[node.start_byte:node.end_byte].decode('utf-8')

#                                 func_info = {
#                                     'name': var_name,
#                                     'src_file': os.path.relpath(file_path, self.project_root),
#                                     'test_file': self._find_test_file(file_path, var_name),
#                                     'code': full_code,  # 完整代码，包括 const ... =
#                                     'is_async': self._is_async_arrow_function(init_node, code),
#                                     'type': 'function',
#                                 }

#                                 # 如果是类方法，添加类上下文
#                                 if current_classes:
#                                     class_name = current_classes[-1]
#                                     func_info.update({
#                                         'class_hierarchy': current_classes,
#                                         'class_name': class_name,
#                                         'full_class_name': '.'.join(current_classes)
#                                     })

#                                     # 获取类信息
#                                     if class_name in class_contexts:
#                                         class_context = class_contexts[class_name]
#                                         func_info['constructor'] = class_context.get('constructor', [])
#                                         func_info['fields'] = class_context.get('fields', [])
#                                     else:
#                                         func_info['constructor'] = []
#                                         func_info['fields'] = []

#                                 functions.append(func_info)

#                                 # 标记箭头函数内部
#                                 for grandchild in reversed(init_node.children):
#                                     stack.append((grandchild, current_classes, True))

#                 # 重要：处理完变量声明后，跳过默认的子节点遍历
#                 continue

#             # 4. 处理方法定义
#             if node.type == 'method_definition' and current_classes:
#                 method_name = self._get_name(node, code)
#                 if method_name and method_name != 'constructor' and not self._is_private_name(method_name):
#                     func_info = self._create_function_info(
#                         node, code, file_path, method_name, 'method', current_classes
#                     )
#                     if func_info:
#                         functions.append(func_info)

#                 self._push_function_body_children(node, stack, current_classes, True)
#                 continue

#             # 5. 处理类字段箭头函数
#             if node.type == 'field_definition' and current_classes and not in_function_body:
#                 field_name = self._get_field_name(node, code)
#                 if field_name and not self._is_private_name(field_name):
#                     # 检查是否是箭头函数
#                     for child in node.children:
#                         if child.type == 'arrow_function':
#                             func_info = self._create_function_info(
#                                 node, code, file_path, field_name, 'method', current_classes,
#                                 is_arrow_method=True
#                             )
#                             if func_info:
#                                 functions.append(func_info)

#                             # 标记箭头函数内部
#                             for grandchild in reversed(child.children):
#                                 stack.append((grandchild, current_classes, True))
#                             break

#             # 6. 处理顶层箭头函数赋值（非声明形式，较少见）
#             if node.type == 'arrow_function' and not current_classes and not in_function_body:
#                 func_name = self._get_ancestor_assignment_name(node, code)
#                 if func_name and not self._is_private_name(func_name):
#                     # 尝试向上查找赋值表达式，提取完整代码
#                     assignment_node = self._find_assignment_expression(node)
#                     if assignment_node:
#                         full_code = code[assignment_node.start_byte:assignment_node.end_byte].decode('utf-8')
#                     else:
#                         full_code = code[node.start_byte:node.end_byte].decode('utf-8')

#                     func_info = {
#                         'name': func_name,
#                         'src_file': os.path.relpath(file_path, self.project_root),
#                         'test_file': self._find_test_file(file_path, func_name),
#                         'code': full_code,
#                         'is_async': self._is_async_arrow_function(node, code),
#                         'type': 'function',
#                     }

#                     functions.append(func_info)

#                     for child in reversed(node.children):
#                         stack.append((child, current_classes, True))

#             # 7. 默认情况：继续遍历子节点
#             for child in reversed(node.children):
#                 stack.append((child, current_classes, in_function_body))

#         return functions

#     def _find_assignment_expression(self, node):
#         """向上查找赋值表达式节点"""
#         current = node.parent
#         while current:
#             if current.type == 'assignment_expression':
#                 return current
#             current = current.parent
#         return None


#     def _extract_all_class_info(self, root_node, code, file_path):
#         """提取文件中所有类的信息"""
#         class_contexts = {}
#         stack = [root_node]
#         while stack:
#             node = stack.pop()
#             if node.type in ('class_declaration', 'class_expression'):
#                 class_info = self._extract_class_info(node, code, file_path)
#                 if class_info and class_info['name']:
#                     class_contexts[class_info['name']] = class_info
#             for child in node.children:
#                 stack.append(child)
#         return class_contexts

#     def _push_function_body_children(self, func_node, stack, current_classes, in_body_status):
#         """将一个函数节点的函数体子节点压栈"""
#         for child in func_node.children:
#             if child.type == 'statement_block':
#                 for grandchild in reversed(child.children):
#                     stack.append((grandchild, current_classes, in_body_status))
#                 return

#         # 如果没有statement_block（如箭头函数表达式体）
#         for child in reversed(func_node.children):
#             if child.type not in ('formal_parameters', 'async', 'function', 'identifier'):
#                 stack.append((child, current_classes, in_body_status))


#     def _extract_class_info(self, class_node, code, file_path):
#         """提取类的信息（构造函数和字段）"""
#         class_info = {
#             'name': '',
#             'constructor': [],
#             'fields': []
#         }

#         # 提取类名
#         class_name = self._get_class_name(class_node, code)
#         if not class_name:
#             return None

#         class_info['name'] = class_name

#         # 查找类体
#         class_body = None
#         for child in class_node.children:
#             if child.type == 'class_body':
#                 class_body = child
#                 break

#         if not class_body:
#             return class_info

#         # 遍历类体提取构造函数和字段
#         for child in class_body.children:
#             if child.type == 'method_definition':
#                 method_name = self._get_name(child, code)
#                 if method_name == 'constructor':
#                     # 提取构造函数代码
#                     constructor_code = code[child.start_byte:child.end_byte].decode('utf-8')
#                     class_info['constructor'].append(constructor_code)

#             elif child.type in ('field_definition', 'public_field_definition'):
#                 # 提取字段代码
#                 field_code = code[child.start_byte:child.end_byte].decode('utf-8')
#                 field_name = self._extract_field_name(child, code)

#                 # 提取字段
#                 if field_name:
#                     class_info['fields'].append(field_code)

#         return class_info

#     def _create_function_info(self, func_node, code, file_path, func_name, func_type, class_stack, is_arrow_method=False):
#         """创建函数信息记录（用于函数声明、方法定义等）"""
#         # 查找测试文件
#         test_file = self._find_test_file(file_path, func_name)

#         # 处理不同类型的函数节点
#         if func_node.type in ('function_declaration', 'method_definition', 'function'):
#             # 这些都有标准结构
#             func_code = code[func_node.start_byte:func_node.end_byte].decode('utf-8')
#             is_async = self._is_async_function(func_node)
#         elif func_node.type == 'arrow_function' or is_arrow_method:
#             # 箭头函数
#             func_code = code[func_node.start_byte:func_node.end_byte].decode('utf-8')
#             is_async = self._is_async_arrow_function(func_node, code)
#         else:
#             # 其他类型（如field_definition）
#             func_code = code[func_node.start_byte:func_node.end_byte].decode('utf-8')
#             is_async = False

#         # 构建基本信息
#         func_info = {
#             'name': func_name,
#             'src_file': os.path.relpath(file_path, self.project_root),
#             'test_file': test_file,
#             'code': func_code,
#             'is_async': is_async,
#             'type': func_type,
#         }

#         # 如果是类方法，添加类上下文
#         if class_stack:
#             class_name = class_stack[-1]
#             func_info.update({
#                 'class_hierarchy': class_stack,
#                 'class_name': class_name,
#                 'full_class_name': '.'.join(class_stack)
#             })

#             # 获取类信息
#             class_contexts = self._get_class_contexts_for_file(file_path)
#             if class_name in class_contexts:
#                 class_context = class_contexts[class_name]
#                 func_info['class_constructor'] = class_context.get('constructor', [])
#                 func_info['class_fields'] = class_context.get('fields', [])
#             else:
#                 func_info['class_constructor'] = []
#                 func_info['class_fields'] = []

#         return func_info

#     def _get_class_contexts_for_file(self, file_path):
#         """获取文件的类上下文缓存"""
#         # 简单实现：每次重新解析文件获取类信息
#         with open(file_path, 'rb') as f:
#             code = f.read()

#         tree = js_parser.parse(code)
#         root_node = tree.root_node

#         class_contexts = {}
#         stack = [root_node]

#         while stack:
#             node = stack.pop()

#             if node.type in ('class_declaration', 'class_expression'):
#                 class_info = self._extract_class_info(node, code, file_path)
#                 if class_info and class_info['name']:
#                     class_contexts[class_info['name']] = class_info

#             for child in node.children:
#                 stack.append(child)

#         return class_contexts

#     def _extract_class_info_from_stack(self, node, code, class_name):
#         """从当前节点向上查找类信息"""
#         # 向上查找最近的类节点
#         current = node.parent
#         while current:
#             if current.type in ('class_declaration', 'class_expression'):
#                 # 检查是否是目标类
#                 name = self._get_class_name(current, code)
#                 if name == class_name:
#                     return self._extract_class_info(current, code, '')
#             current = current.parent

#         return None

#     def _find_test_file(self, file_path, func_name):
#         temp_path = file_path.split(str(self.project_root))[1]
#         temp_path2 = temp_path.split(".js")[0]
#         file_name = temp_path2.split('/')[-1]
#         temp_path3 = temp_path2.split(file_name)[0]
#         return "gen_tests" + str(temp_path3) + "Test" + file_name + '/' + func_name + ".test.js"

#     def _get_class_name(self, class_node, code):
#         """获取类名"""
#         for child in class_node.children:
#             if child.type == 'identifier':
#                 return code[child.start_byte:child.end_byte].decode('utf-8')
#         return None

#     def _get_name(self, node, code):
#         """获取节点名称"""
#         for child in node.children:
#             if child.type in ('identifier', 'property_identifier'):
#                 return code[child.start_byte:child.end_byte].decode('utf-8')
#         return None

#     def _get_field_name(self, field_node, code):
#         """获取字段名"""
#         for child in field_node.children:
#             if child.type in ('property_identifier'):
#                 field_name = code[child.start_byte:child.end_byte].decode('utf-8')
#                 if field_name and not field_name.startswith("_") and not field_name.startswith("#"):
#                     return field_name
#         return None

#     def _extract_field_name(self, field_node, code):
#         """提取字段名"""
#         return self._get_field_name(field_node, code)

#     def _get_ancestor_assignment_name(self, node, code):
#         """对于箭头函数，尝试向上寻找最近的赋值表达式"""
#         parent = node.parent
#         while parent:
#             if parent.type == 'assignment_expression':
#                 for child in parent.children:
#                     if child.type == 'identifier':
#                         return code[child.start_byte:child.end_byte].decode('utf-8')
#             parent = parent.parent
#         return None

#     def _is_async_function(self, func_node):
#         """判断函数是否使用 async 关键字"""
#         for child in func_node.children:
#             if child.type == 'async':
#                 return True
#         return False

#     def _is_async_arrow_function(self, node, code):
#         """判断箭头函数是否使用 async 关键字"""
#         # 对于箭头函数，检查是否有 async 修饰符
#         if node.type == 'arrow_function':
#             for child in node.children:
#                 if child.type == 'async':
#                     return True

#         # 对于字段定义，需要检查其箭头函数子节点
#         elif node.type in ('field_definition', 'public_field_definition'):
#             for child in node.children:
#                 if child.type == 'arrow_function':
#                     return self._is_async_arrow_function(child, code)

#         return False

#     def save_to_json(self, output_file=None):
#         """将提取的函数信息保存为 JSON"""
#         output_file = output_file or self.output_file
#         functions = self.extract_project_functions()

#         # 序列化数据
#         serializable = []
#         for fn in functions:
#             fn_copy = fn.copy()
#             # 确保所有字符串都是 unicode
#             for k, v in fn_copy.items():
#                 if isinstance(v, bytes):
#                     fn_copy[k] = v.decode('utf-8')
#                 elif isinstance(v, list):
#                     fn_copy[k] = [
#                         item.decode('utf-8') if isinstance(item, bytes) else item
#                         for item in v
#                     ]
#             serializable.append(fn_copy)

#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable, f, indent=2, ensure_ascii=False)

#         print(f"Extracted {len(serializable)} functions")

#         # 统计信息
#         method_count = sum(1 for f in serializable if f['type'] == 'method')
#         function_count = sum(1 for f in serializable if f['type'] == 'function')
#         arrow_method_count = sum(1 for f in serializable if f.get('code', '').count('=>') > 0)

#         print(f"Methods: {method_count}, Global functions: {function_count}")
#         print(f"Arrow function methods: {arrow_method_count}")

#         return serializable

import re
import lizard
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict
from func_select import StratifiedFunctionSelector
from file_select import *


class JSProjectTestScopeExtractor:
    """提取 JavaScript 项目中的公有函数和类上下文信息，并进行函数级选择"""

    def __init__(self, project_root, file_list, output_file=None,
                 min_loc_threshold=5, random_seed=42):
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
        self.test_files_cache = {}  # 缓存测试文件查找结果

        # getter/setter模式的正则表达式 (JavaScript版本)
        self.getter_setter_patterns = [
            r'^get[A-Z]',  # getXxx
            r'^set[A-Z]',  # setXxx
            r'^is[A-Z]',  # isXxx
            r'^has[A-Z]',  # hasXxx
            r'^create[A-Z]',  # createXxx
            r'^build[A-Z]',  # buildXxx
            r'^to[A-Z]',  # toXxx
            r'^toString$',  # toString
            r'^toJSON$',  # toJSON
            r'^valueOf$',  # valueOf
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
            report = lizard.analyze_file.analyze_source_code("temp.js", code)

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
                # 匹配方法参数部分（JavaScript）
                param_match = re.search(r'\((.*?)\)', code.split('\n')[0])
                if param_match:
                    param_text = param_match.group(1)
                    param_count = len([p for p in param_text.split(',') if p.strip()])
            except:
                param_count = 0

        return complexity, loc, param_count

    def _extract_project_functions(self):
        """提取项目中的所有公有函数（包含类上下文）"""
        all_functions = []

        for file_path in self.files:
            try:
                file_funcs = self._extract_functions_from_file(file_path)
                all_functions.extend(file_funcs)
            except Exception as exc:
                print(f"Error processing {file_path}: {exc}")

        return all_functions

    def _get_declarator_name_and_init(self, declarator_node, code):
        """从variable_declarator节点提取变量名和初始化表达式（简化版）"""
        var_name = None
        init_node = None

        # 方法1：直接遍历查找 function 或 arrow_function 节点
        for child in declarator_node.children:
            if child.type == 'identifier':
                var_name = code[child.start_byte:child.end_byte].decode('utf-8')
            elif child.type in ['function', 'arrow_function']:
                init_node = child

        # 方法2：如果没找到，检查是否有等号，等号后面的节点就是初始化表达式
        if not init_node:
            for i, child in enumerate(declarator_node.children):
                if child.type == '=' and i + 1 < len(declarator_node.children):
                    next_node = declarator_node.children[i + 1]
                    if next_node.type in ['function', 'arrow_function']:
                        init_node = next_node
                    break

        return var_name, init_node

    def _is_private_name(self, name):
        """判断名称是否为私有（以下划线或井号开头）"""
        # 确保name是字符串
        if not isinstance(name, str):
            return False
        return name.startswith('_') or name.startswith('#')

    def _extract_functions_from_file(self, file_path):
        """从单个文件中提取函数信息（完整版）"""
        # 这里假设js_parser已经导入
        from multi_parser import js_parser

        with open(file_path, 'rb') as f:
            code = f.read()

        tree = js_parser.parse(code)
        root_node = tree.root_node

        functions = []
        # 第一遍：提取类信息
        class_contexts = self._extract_all_class_info(root_node, code, file_path)

        # 第二遍：提取函数信息
        stack = [(root_node, [], False)]  # (节点, 类栈, 是否在函数体内)

        while stack:
            node, current_classes, in_function_body = stack.pop()

            # 1. 处理类声明
            if node.type == 'class_declaration':
                class_name = self._get_class_name(node, code)
                if class_name:
                    new_class_stack = current_classes + [class_name]
                    # 找到类体
                    for child in node.children:
                        if child.type == 'class_body':
                            for grandchild in reversed(child.children):
                                stack.append((grandchild, new_class_stack, in_function_body))
                            break
                continue

            # 2. 处理函数声明
            if node.type == 'function_declaration':
                if in_function_body:
                    # 嵌套函数，只传递状态不提取
                    self._push_function_body_children(node, stack, current_classes, True)
                    continue

                func_name = self._get_name(node, code)
                if func_name and not self._is_private_name(func_name):
                    # 使用lizard计算复杂度指标
                    func_code = code[node.start_byte:node.end_byte].decode('utf-8')
                    complexity, loc, param_count = self._compute_complexity_and_loc(func_code)

                    func_info = self._create_function_info(
                        node, code, file_path, func_name, 'function', current_classes,
                        complexity=complexity, loc=loc, param_count=param_count
                    )
                    if func_info:
                        functions.append(func_info)

                self._push_function_body_children(node, stack, current_classes, True)
                continue

            # 3. 处理变量声明 - 使用 lexical_declaration（const/let声明）
            if node.type == 'lexical_declaration' and not in_function_body:
                # 遍历所有声明器
                for child in node.children:
                    if child.type == 'variable_declarator':
                        var_name, init_node = self._get_declarator_name_and_init(child, code)

                        if var_name and init_node and not self._is_private_name(var_name):
                            # 处理函数表达式
                            if init_node.type == 'function':
                                # 提取整个 lexical_declaration 的完整代码
                                full_code = code[node.start_byte:node.end_byte].decode('utf-8')

                                # 使用lizard计算复杂度指标
                                complexity, loc, param_count = self._compute_complexity_and_loc(full_code)

                                func_info = {
                                    'name': var_name,
                                    'src_file': os.path.relpath(file_path, self.project_root),
                                    'test_file': self._find_test_file(file_path, var_name),
                                    'code': full_code,  # 完整代码，包括 const ... =
                                    'is_async': self._is_async_function(init_node),
                                    'type': 'function',
                                    'complexity': complexity,
                                    'loc': loc,
                                    'param_count': param_count,
                                    'start_line': node.start_point[0] + 1,
                                    'end_line': node.end_point[0] + 1
                                }

                                # 如果是类方法，添加类上下文
                                if current_classes:
                                    class_name = current_classes[-1]
                                    func_info.update({
                                        'class_hierarchy': current_classes,
                                        'class_name': class_name,
                                        'full_class_name': '.'.join(current_classes)
                                    })

                                    # 获取类信息
                                    if class_name in class_contexts:
                                        class_context = class_contexts[class_name]
                                        func_info['class_constructor'] = class_context.get('constructor', [])
                                        func_info['class_fields'] = class_context.get('fields', [])
                                    else:
                                        func_info['class_constructor'] = []
                                        func_info['class_fields'] = []

                                functions.append(func_info)

                                # 标记函数体内部
                                self._push_function_body_children(init_node, stack, current_classes, True)

                            # 处理箭头函数表达式
                            elif init_node.type == 'arrow_function':
                                # 提取整个 lexical_declaration 的完整代码
                                full_code = code[node.start_byte:node.end_byte].decode('utf-8')

                                # 使用lizard计算复杂度指标
                                complexity, loc, param_count = self._compute_complexity_and_loc(full_code)

                                func_info = {
                                    'name': var_name,
                                    'src_file': os.path.relpath(file_path, self.project_root),
                                    'test_file': self._find_test_file(file_path, var_name),
                                    'code': full_code,  # 完整代码，包括 const ... =
                                    'is_async': self._is_async_arrow_function(init_node, code),
                                    'type': 'function',
                                    'complexity': complexity,
                                    'loc': loc,
                                    'param_count': param_count,
                                    'start_line': node.start_point[0] + 1,
                                    'end_line': node.end_point[0] + 1
                                }

                                # 如果是类方法，添加类上下文
                                if current_classes:
                                    class_name = current_classes[-1]
                                    func_info.update({
                                        'class_hierarchy': current_classes,
                                        'class_name': class_name,
                                        'full_class_name': '.'.join(current_classes)
                                    })

                                    # 获取类信息
                                    if class_name in class_contexts:
                                        class_context = class_contexts[class_name]
                                        func_info['class_constructor'] = class_context.get('constructor', [])
                                        func_info['class_fields'] = class_context.get('fields', [])
                                    else:
                                        func_info['class_constructor'] = []
                                        func_info['class_fields'] = []

                                functions.append(func_info)

                                # 标记箭头函数内部
                                for grandchild in reversed(init_node.children):
                                    stack.append((grandchild, current_classes, True))

                # 重要：处理完变量声明后，跳过默认的子节点遍历
                continue

            # 4. 处理方法定义
            if node.type == 'method_definition' and current_classes:
                method_name = self._get_name(node, code)
                if method_name and method_name != 'constructor' and not self._is_private_name(method_name):
                    # 使用lizard计算复杂度指标
                    method_code = code[node.start_byte:node.end_byte].decode('utf-8')
                    complexity, loc, param_count = self._compute_complexity_and_loc(method_code)

                    func_info = self._create_function_info(
                        node, code, file_path, method_name, 'method', current_classes,
                        complexity=complexity, loc=loc, param_count=param_count
                    )
                    if func_info:
                        functions.append(func_info)

                self._push_function_body_children(node, stack, current_classes, True)
                continue

            # 5. 处理类字段箭头函数
            if node.type == 'field_definition' and current_classes and not in_function_body:
                field_name = self._get_field_name(node, code)
                if field_name and not self._is_private_name(field_name):
                    # 检查是否是箭头函数
                    for child in node.children:
                        if child.type == 'arrow_function':
                            # 使用lizard计算复杂度指标
                            field_code = code[node.start_byte:node.end_byte].decode('utf-8')
                            complexity, loc, param_count = self._compute_complexity_and_loc(field_code)

                            func_info = self._create_function_info(
                                node, code, file_path, field_name, 'method', current_classes,
                                is_arrow_method=True, complexity=complexity, loc=loc, param_count=param_count
                            )
                            if func_info:
                                functions.append(func_info)

                            # 标记箭头函数内部
                            for grandchild in reversed(child.children):
                                stack.append((grandchild, current_classes, True))
                            break

            # 6. 处理顶层箭头函数赋值（非声明形式，较少见）
            if node.type == 'arrow_function' and not current_classes and not in_function_body:
                func_name = self._get_ancestor_assignment_name(node, code)
                if func_name and not self._is_private_name(func_name):
                    # 尝试向上查找赋值表达式，提取完整代码
                    assignment_node = self._find_assignment_expression(node)
                    if assignment_node:
                        full_code = code[assignment_node.start_byte:assignment_node.end_byte].decode('utf-8')
                        start_line = assignment_node.start_point[0] + 1
                        end_line = assignment_node.end_point[0] + 1
                    else:
                        full_code = code[node.start_byte:node.end_byte].decode('utf-8')
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1

                    # 使用lizard计算复杂度指标
                    complexity, loc, param_count = self._compute_complexity_and_loc(full_code)

                    func_info = {
                        'name': func_name,
                        'src_file': os.path.relpath(file_path, self.project_root),
                        'test_file': self._find_test_file(file_path, func_name),
                        'code': full_code,
                        'is_async': self._is_async_arrow_function(node, code),
                        'type': 'function',
                        'complexity': complexity,
                        'loc': loc,
                        'param_count': param_count,
                        'start_line': start_line,
                        'end_line': end_line
                    }

                    functions.append(func_info)

                    for child in reversed(node.children):
                        stack.append((child, current_classes, True))

            # 7. 默认情况：继续遍历子节点
            for child in reversed(node.children):
                stack.append((child, current_classes, in_function_body))

        return functions

    def _find_assignment_expression(self, node):
        """向上查找赋值表达式节点"""
        current = node.parent
        while current:
            if current.type == 'assignment_expression':
                return current
            current = current.parent
        return None

    def _extract_all_class_info(self, root_node, code, file_path):
        """提取文件中所有类的信息"""
        class_contexts = {}
        stack = [root_node]
        while stack:
            node = stack.pop()
            if node.type in ('class_declaration', 'class_expression'):
                class_info = self._extract_class_info(node, code, file_path)
                if class_info and class_info['name']:
                    class_contexts[class_info['name']] = class_info
            for child in node.children:
                stack.append(child)
        return class_contexts

    def _push_function_body_children(self, func_node, stack, current_classes, in_body_status):
        """将一个函数节点的函数体子节点压栈"""
        for child in func_node.children:
            if child.type == 'statement_block':
                for grandchild in reversed(child.children):
                    stack.append((grandchild, current_classes, in_body_status))
                return

        # 如果没有statement_block（如箭头函数表达式体）
        for child in reversed(func_node.children):
            if child.type not in ('formal_parameters', 'async', 'function', 'identifier'):
                stack.append((child, current_classes, in_body_status))

    def _extract_class_info(self, class_node, code, file_path):
        """提取类的信息（构造函数和字段）"""
        class_info = {
            'name': '',
            'constructor': [],
            'fields': []
        }

        # 提取类名
        class_name = self._get_class_name(class_node, code)
        if not class_name:
            return None

        class_info['name'] = class_name

        # 查找类体
        class_body = None
        for child in class_node.children:
            if child.type == 'class_body':
                class_body = child
                break

        if not class_body:
            return class_info

        # 遍历类体提取构造函数和字段
        for child in class_body.children:
            if child.type == 'method_definition':
                method_name = self._get_name(child, code)
                if method_name == 'constructor':
                    # 提取构造函数代码
                    constructor_code = code[child.start_byte:child.end_byte].decode('utf-8')
                    class_info['constructor'].append(constructor_code)

            elif child.type in ('field_definition', 'public_field_definition'):
                # 提取字段代码
                field_code = code[child.start_byte:child.end_byte].decode('utf-8')
                field_name = self._extract_field_name(child, code)

                # 提取字段
                if field_name:
                    class_info['fields'].append(field_code)

        return class_info

    def _create_function_info(self, func_node, code, file_path, func_name, func_type,
                              class_stack, is_arrow_method=False, **kwargs):
        """创建函数信息记录（用于函数声明、方法定义等）"""
        # 查找测试文件
        test_file = self._find_test_file(file_path, func_name)

        # 从kwargs中获取复杂度指标
        complexity = kwargs.get('complexity', 1)
        loc = kwargs.get('loc', 0)
        param_count = kwargs.get('param_count', 0)

        # 处理不同类型的函数节点
        if func_node.type in ('function_declaration', 'method_definition', 'function'):
            # 这些都有标准结构
            func_code = code[func_node.start_byte:func_node.end_byte].decode('utf-8')
            is_async = self._is_async_function(func_node)
        elif func_node.type == 'arrow_function' or is_arrow_method:
            # 箭头函数
            func_code = code[func_node.start_byte:func_node.end_byte].decode('utf-8')
            is_async = self._is_async_arrow_function(func_node, code)
        else:
            # 其他类型（如field_definition）
            func_code = code[func_node.start_byte:func_node.end_byte].decode('utf-8')
            is_async = False

        start_line = func_node.start_point[0] + 1
        end_line = func_node.end_point[0] + 1
        # 构建基本信息
        func_info = {
            'name': func_name,
            'src_file': os.path.relpath(file_path, self.project_root),
            'test_file': test_file,
            'code': func_code,
            'is_async': is_async,
            'type': func_type,
            'complexity': complexity,
            'loc': loc,
            'param_count': param_count,
            'start_line': start_line,
            'end_line': end_line
        }

        # 如果是类方法，添加类上下文
        if class_stack:
            class_name = class_stack[-1]
            func_info.update({
                'class_hierarchy': class_stack,
                'class_name': class_name,
                'full_class_name': '.'.join(class_stack)
            })

            # 获取类信息
            class_contexts = self._get_class_contexts_for_file(file_path)
            if class_name in class_contexts:
                class_context = class_contexts[class_name]
                func_info['class_constructor'] = class_context.get('constructor', [])
                func_info['class_fields'] = class_context.get('fields', [])
            else:
                func_info['class_constructor'] = []
                func_info['class_fields'] = []

        return func_info

    def _get_class_contexts_for_file(self, file_path):
        """获取文件的类上下文缓存"""
        # 简单实现：每次重新解析文件获取类信息
        from multi_parser import js_parser

        with open(file_path, 'rb') as f:
            code = f.read()

        tree = js_parser.parse(code)
        root_node = tree.root_node

        class_contexts = {}
        stack = [root_node]

        while stack:
            node = stack.pop()

            if node.type in ('class_declaration', 'class_expression'):
                class_info = self._extract_class_info(node, code, file_path)
                if class_info and class_info['name']:
                    class_contexts[class_info['name']] = class_info

            for child in node.children:
                stack.append(child)

        return class_contexts

    def _extract_class_info_from_stack(self, node, code, class_name):
        """从当前节点向上查找类信息"""
        # 向上查找最近的类节点
        current = node.parent
        while current:
            if current.type in ('class_declaration', 'class_expression'):
                # 检查是否是目标类
                name = self._get_class_name(current, code)
                if name == class_name:
                    return self._extract_class_info(current, code, '')
            current = current.parent

        return None

    def _find_test_file(self, file_path, func_name):
        """生成测试文件路径"""
        # 提取相对路径
        if file_path.startswith(self.project_root):
            rel_path = file_path[len(self.project_root):].lstrip(os.sep)
        else:
            rel_path = file_path

        # 移除.js扩展名
        rel_path_no_ext = os.path.splitext(rel_path)[0]

        # 将src替换为test
        if "src/" in rel_path_no_ext:
            rel_path_no_ext = rel_path_no_ext.replace('src/', 'test/')
        else:
            rel_path_no_ext = rel_path_no_ext.split('/')[1]
            rel_path_no_ext = "test/" + rel_path_no_ext

        # 生成测试文件名
        test_file = f"{rel_path_no_ext}/{func_name}.test.js"

        return test_file

    def _get_class_name(self, class_node, code):
        """获取类名"""
        for child in class_node.children:
            if child.type == 'identifier':
                return code[child.start_byte:child.end_byte].decode('utf-8')
        return None

    def _get_name(self, node, code):
        """获取节点名称"""
        for child in node.children:
            if child.type in ('identifier', 'property_identifier'):
                return code[child.start_byte:child.end_byte].decode('utf-8')
        return None

    def _get_field_name(self, field_node, code):
        """获取字段名"""
        for child in field_node.children:
            if child.type in ('property_identifier'):
                field_name = code[child.start_byte:child.end_byte].decode('utf-8')
                if field_name and not field_name.startswith("_") and not field_name.startswith("#"):
                    return field_name
        return None

    def _extract_field_name(self, field_node, code):
        """提取字段名"""
        return self._get_field_name(field_node, code)

    def _get_ancestor_assignment_name(self, node, code):
        """对于箭头函数，尝试向上寻找最近的赋值表达式"""
        parent = node.parent
        while parent:
            if parent.type == 'assignment_expression':
                for child in parent.children:
                    if child.type == 'identifier':
                        return code[child.start_byte:child.end_byte].decode('utf-8')
            parent = parent.parent
        return None

    def _is_async_function(self, func_node):
        """判断函数是否使用 async 关键字"""
        for child in func_node.children:
            if child.type == 'async':
                return True
        return False

    def _is_async_arrow_function(self, node, code):
        """判断箭头函数是否使用 async 关键字"""
        # 对于箭头函数，检查是否有 async 修饰符
        if node.type == 'arrow_function':
            for child in node.children:
                if child.type == 'async':
                    return True

        # 对于字段定义，需要检查其箭头函数子节点
        elif node.type in ('field_definition', 'public_field_definition'):
            for child in node.children:
                if child.type == 'arrow_function':
                    return self._is_async_arrow_function(child, code)

        return False

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
        if self._is_getter_setter(method_name, method_code):
            return True, "getter/setter"

        # 规则3: 无返回值且无状态修改
        if self._no_return_no_state_change(method_code, method_name):
            return True, "无返回值无状态修改"

        # 规则4: auto-generated / inline wrappers
        if self._is_trivial_wrapper(method_code, method_name, loc):
            return True, "简单包装器"

        return False, ""

    def _is_getter_setter(self, method_name: str, method_code: str) -> bool:
        """判断是否是getter/setter方法"""
        for pattern in self.getter_setter_patterns:
            if re.match(pattern, method_name):
                return True
        if "get " in method_code or "set " in method_code:
            return True
        return False

    def _no_return_no_state_change(self, method_code: str, method_name: str) -> bool:
        """判断是否无返回值且无状态修改"""
        # 检查是否有return语句
        has_return = re.search(r'\breturn\b', method_code) is not None

        # 检查是否有字段赋值（JavaScript中的this赋值）
        has_field_assignment = False
        lines = method_code.split('\n')
        for line in lines:
            if '=' in line and ('this.' in line or 'this[' in line):
                has_field_assignment = True
                break

        # 如果既没有return也没有字段赋值，则可能是void方法
        if not has_return and not has_field_assignment:
            # 排除一些特殊情况
            excluded_names = ['init', 'setup', 'start', 'run', 'execute', 'process', 'handle']
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
                important_methods = ['run', 'execute', 'process', 'handle']
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
        all_functions = self._extract_project_functions()

        # 按文件分组方法
        methods_by_file = defaultdict(list)
        for func in all_functions:
            methods_by_file[func['src_file']].append(func)

        all_selected_methods = []

        # 处理每个文件
        for rel_file_path, file_methods in methods_by_file.items():
            try:
                file_path = os.path.join(self.project_root, rel_file_path)
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
                                "type": func.get('type', 'function'),
                                'start_line': func.get('start_line', 0),
                                'end_line': func.get('end_line', 0)
                                # "loc": func.get('loc', 0),
                                # "complexity": func.get('complexity', 1),
                                # "param_count": func.get('param_count', 0),
                                # "func_score": func.get('func_score', 0),
                                # "raw_metrics": func.get('raw_metrics', {})
                            }

                            # 添加类相关信息
                            if func.get('class_name'):
                                method_info.update({
                                    'class_name': func.get('class_name'),
                                    'full_class_name': func.get('full_class_name', ''),
                                    'class_constructor': func.get('class_constructor', []),
                                    'class_fields': func.get('class_fields', []),
                                    'class_hierarchy': func.get('class_hierarchy', [])
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
                print(f"处理 {rel_file_path} 时出错: {e}")
                continue

        # 保存结果
        if self.output_file:
            self._save_to_json(all_selected_methods)

        # 打印统计报告
        self._print_statistics_report()

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


if __name__ == '__main__':
    project_root = "projects/Proton"

    # 创建分析器实例
    analyzer = FileQualityAnalyzer(
        language="javascript",
        random_seed=42,  # 固定随机种子，确保结果可重复
        sampling_k=2  # 每个层级抽取2个文件
    )

    # 完整分析项目
    sample_files = analyzer.analyze_project(
        project_path=project_root,
        group_by_module=True  # 按模块分组
    )

    # 创建提取器并执行
    extractor = JSProjectTestScopeExtractor(
        project_root=project_root,
        file_list=sample_files,
        output_file="proton_lite.json",
        min_loc_threshold=5,
        random_seed=42
    )

    selected_methods = extractor.extract_and_select_functions()

# import os
# import json
# from multi_parser import js_parser


# class JSFocalExtractor:
#     """提取 JavaScript 项目中的公有函数和类上下文信息"""

#     def __init__(self, project_root, output_file):
#         self.project_root = os.path.abspath(project_root)
#         self.output_file = output_file
#         self.test_files_cache = {}  # 缓存测试文件查找结果

#     def extract_project_functions(self):
#         """提取项目中的所有公有函数（包含类上下文）"""
#         all_functions = []

#         for root, dirs, files in os.walk(self.project_root):
#             # 忽略测试文件、node_modules、git 等
#             if any(ignore in root for ignore in ['test', 'node_modules', '.git', '.vscode', '.idea']):
#                 continue

#             for file in files:
#                 if file.endswith('.js') and not file.endswith('.test.js') and not file.endswith('.tests.js'):
#                     file_path = os.path.join(root, file)
#                     try:
#                         file_funcs = self._extract_functions_from_file(file_path)
#                         all_functions.extend(file_funcs)
#                     except Exception as exc:
#                         print(f"Error processing {file_path}: {exc}")

#         return all_functions

#     def _extract_functions_from_file(self, file_path):
#         """从单个文件中提取函数信息"""
#         with open(file_path, 'rb') as f:
#             code = f.read()  # bytes

#         tree = js_parser.parse(code)
#         root_node = tree.root_node

#         functions = []
#         class_contexts = {}  # 存储类名 -> 类信息

#         # 第一遍：提取类信息
#         stack = [root_node]
#         while stack:
#             node = stack.pop()

#             # 处理类声明
#             if node.type in ('class_declaration', 'class_expression'):
#                 class_info = self._extract_class_info(node, code, file_path)
#                 if class_info and class_info['name']:
#                     class_contexts[class_info['name']] = class_info
#                     # 不继续遍历类内部，稍后单独处理
#                     continue

#             # 继续遍历子节点
#             for child in reversed(node.children):
#                 stack.append(child)

#         # 第二遍：提取函数信息
#         stack = [(root_node, [])]  # (node, class_stack)
#         while stack:
#             node, current_classes = stack.pop()

#             # 处理类声明
#             if node.type in ('class_declaration', 'class_expression'):
#                 class_name = self._get_class_name(node, code)
#                 if class_name:
#                     new_class_stack = current_classes + [class_name]
#                     # 遍历类体
#                     class_body = None
#                     for child in node.children:
#                         if child.type == 'class_body':
#                             class_body = child
#                             break

#                     if class_body:
#                         for child in reversed(class_body.children):
#                             stack.append((child, new_class_stack))
#                     continue

#             # 处理函数声明（全局）
#             if node.type == 'function_declaration' and not current_classes:
#                 func_name = self._get_name(node, code)
#                 if func_name and not func_name.startswith('_') and not func_name.startswith('#'):
#                     func_info = self._create_function_info(
#                         node, code, file_path, func_name, 'function', current_classes
#                     )
#                     if func_info:
#                         functions.append(func_info)

#             # 处理方法定义
#             elif node.type == 'method_definition' and current_classes:
#                 method_name = self._get_name(node, code)
#                 if method_name and method_name != 'constructor' and not method_name.startswith('_') and not method_name.startswith('#'):
#                     func_info = self._create_function_info(
#                         node, code, file_path, method_name, 'method', current_classes
#                     )
#                     if func_info:
#                         functions.append(func_info)

#             # 处理箭头函数（全局）
#             elif node.type == 'arrow_function' and not current_classes:
#                 func_name = self._get_ancestor_assignment_name(node, code)
#                 if func_name and not func_name.startswith('_') and not func_name.startswith('#'):
#                     func_info = self._create_function_info(
#                         node, code, file_path, func_name, 'function', current_classes
#                     )
#                     if func_info:
#                         functions.append(func_info)

#             # 继续遍历子节点
#             for child in reversed(node.children):
#                 stack.append((child, current_classes))

#         return functions

#     def _extract_class_info(self, class_node, code, file_path):
#         """提取类的信息（构造函数和字段）"""
#         class_info = {
#             'name': '',
#             'constructor': [],
#             'fields': []
#         }

#         # 提取类名
#         class_name = self._get_class_name(class_node, code)
#         if not class_name:
#             return None

#         class_info['name'] = class_name

#         # 查找类体
#         class_body = None
#         for child in class_node.children:
#             if child.type == 'class_body':
#                 class_body = child
#                 break

#         if not class_body:
#             return class_info

#         # 遍历类体提取构造函数和字段
#         for child in class_body.children:
#             if child.type == 'method_definition':
#                 method_name = self._get_name(child, code)
#                 if method_name == 'constructor':
#                     # 提取构造函数代码
#                     constructor_code = code[child.start_byte:child.end_byte].decode('utf-8')
#                     class_info['constructor'].append(constructor_code)

#             elif child.type in ('field_definition', 'public_field_definition'):
#                 # 提取字段代码
#                 field_code = code[child.start_byte:child.end_byte].decode('utf-8')
#                 field_name = self._extract_field_name(child, code)

#                 # 只提取公有字段（不以_开头）
#                 if field_name and not field_name.startswith('_') and not field_name.startswith('#'):
#                     class_info['fields'].append(field_code)

#         return class_info

#     def _create_function_info(self, func_node, code, file_path, func_name, func_type, class_stack):
#         """创建函数信息记录"""
#         # 查找对应的测试文件
#         test_file = self._find_test_file(file_path, func_name)

#         # 构建函数信息
#         func_info = {
#             'name': func_name,
#             'src_file': os.path.relpath(file_path, self.project_root),
#             'test_file': test_file,
#             'code': code[func_node.start_byte:func_node.end_byte].decode('utf-8'),
#             'is_async': self._is_async_function(func_node),
#             'type': func_type,
#         }

#         # 如果是类方法，添加类上下文信息
#         if class_stack:
#             class_name = class_stack[-1]
#             func_info.update({
#                 'class_hierarchy': class_stack,
#                 'class_name': class_name,
#                 'full_class_name': '.'.join(class_stack)
#             })

#             # 获取类的构造函数和字段
#             if class_name in self._get_class_contexts_for_file(file_path):
#                 class_context = self._get_class_contexts_for_file(file_path)[class_name]
#                 func_info['constructor'] = class_context.get('constructor', [])
#                 func_info['fields'] = class_context.get('fields', [])
#             else:
#                 # 如果类信息未缓存，临时提取
#                 class_info = self._extract_class_info_from_stack(func_node, code, class_name)
#                 if class_info:
#                     func_info['constructor'] = class_info.get('constructor', [])
#                     func_info['fields'] = class_info.get('fields', [])
#                 else:
#                     func_info['constructor'] = []
#                     func_info['fields'] = []

#         return func_info

#     def _get_class_contexts_for_file(self, file_path):
#         """获取文件的类上下文缓存"""
#         # 简单实现：每次重新解析文件获取类信息
#         with open(file_path, 'rb') as f:
#             code = f.read()

#         tree = js_parser.parse(code)
#         root_node = tree.root_node

#         class_contexts = {}
#         stack = [root_node]

#         while stack:
#             node = stack.pop()

#             if node.type in ('class_declaration', 'class_expression'):
#                 class_info = self._extract_class_info(node, code, file_path)
#                 if class_info and class_info['name']:
#                     class_contexts[class_info['name']] = class_info

#             for child in node.children:
#                 stack.append(child)

#         return class_contexts

#     def _extract_class_info_from_stack(self, node, code, class_name):
#         """从当前节点向上查找类信息"""
#         # 向上查找最近的类节点
#         current = node.parent
#         while current:
#             if current.type in ('class_declaration', 'class_expression'):
#                 # 检查是否是目标类
#                 name = self._get_class_name(current, code)
#                 if name == class_name:
#                     return self._extract_class_info(current, code, '')
#             current = current.parent

#         return None

#     def _find_test_file(self, src_file_path, func_name):
#         """查找对应的测试文件"""
#         src_rel_path = os.path.relpath(src_file_path, self.project_root)

#         # 尝试几种常见的测试文件命名约定
#         src_dir = os.path.dirname(src_rel_path)
#         src_name = os.path.splitext(os.path.basename(src_rel_path))[0]

#         test_patterns = [
#             # 在同一目录下
#             f"{src_dir}/{src_name}.test.js",
#             f"{src_dir}/{src_name}.spec.js",
#             f"{src_dir}/test_{src_name}.js",
#             # 在 test 目录下
#             f"test/{src_rel_path}",
#             f"tests/{src_rel_path}",
#             f"test/{src_dir}/{src_name}.test.js",
#             f"tests/{src_dir}/{src_name}.test.js",
#             # 在 __tests__ 目录下
#             f"{src_dir}/__tests__/{os.path.basename(src_rel_path)}",
#             f"{src_dir}/__tests__/{src_name}.test.js",
#         ]

#         for pattern in test_patterns:
#             test_path = os.path.join(self.project_root, pattern)
#             if os.path.exists(test_path):
#                 return pattern

#         return ""

#     def _get_class_name(self, class_node, code):
#         """获取类名"""
#         for child in class_node.children:
#             if child.type == 'identifier':
#                 return code[child.start_byte:child.end_byte].decode('utf-8')
#         return None

#     def _get_name(self, node, code):
#         """获取节点名称"""
#         for child in node.children:
#             if child.type in ('identifier', 'property_identifier'):
#                 return code[child.start_byte:child.end_byte].decode('utf-8')
#         return None

#     def _extract_field_name(self, field_node, code):
#         """提取字段名"""
#         for child in field_node.children:
#             if child.type in ('property_identifier', 'private_property_identifier'):
#                 return code[child.start_byte:child.end_byte].decode('utf-8')
#         return None

#     def _get_ancestor_assignment_name(self, node, code):
#         """对于箭头函数，尝试向上寻找最近的赋值表达式"""
#         parent = node.parent
#         while parent:
#             if parent.type == 'assignment_expression':
#                 for child in parent.children:
#                     if child.type == 'identifier':
#                         return code[child.start_byte:child.end_byte].decode('utf-8')
#             parent = parent.parent
#         return None

#     def _is_async_function(self, func_node):
#         """判断函数是否使用 async 关键字"""
#         for child in func_node.children:
#             if child.type == 'async':
#                 return True
#         return False

#     def save_to_json(self, output_file=None):
#         """将提取的函数信息保存为 JSON"""
#         output_file = output_file or self.output_file
#         functions = self.extract_project_functions()

#         # 序列化数据
#         serializable = []
#         for fn in functions:
#             fn_copy = fn.copy()
#             # 确保所有字符串都是 unicode
#             for k, v in fn_copy.items():
#                 if isinstance(v, bytes):
#                     fn_copy[k] = v.decode('utf-8')
#                 elif isinstance(v, list):
#                     fn_copy[k] = [
#                         item.decode('utf-8') if isinstance(item, bytes) else item
#                         for item in v
#                     ]
#             serializable.append(fn_copy)

#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable, f, indent=2, ensure_ascii=False)

#         print(f"Extracted {len(serializable)} functions")

#         # 统计信息
#         method_count = sum(1 for f in serializable if f['type'] == 'method')
#         function_count = sum(1 for f in serializable if f['type'] == 'function')
#         print(f"Methods: {method_count}, Global functions: {function_count}")

#         return serializable


# if __name__ == '__main__':
#     project_root = 'project/three.js'
#     output_path = 'three_focal_class_context.json'

#     extractor = JSFocalExtractor(project_root, output_path)
#     functions = extractor.save_to_json()

#     # 打印示例
#     if functions:
#         print("\nSample function records:")
#         for i in range(min(3, len(functions))):
#             func = functions[i]
#             print(f"\n{i+1}. {func['name']} ({func['type']})")
#             print(f"   File: {func['src_file']}")
#             print(f"   Test: {func['test_file']}")
#             if func['type'] == 'method':
#                 print(f"   Class: {func['full_class_name']}")
#                 print(f"   Constructor lines: {len(func.get('constructor', []))}")
#                 print(f"   Fields: {len(func.get('fields', []))}")
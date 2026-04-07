# """
# JavaProjectTestScopeExtractor.py

# 一次性遍历整个 Java 项目，生成每个类的测试范围。
# 已修复修饰符字段全为 false 的问题。
# """

# import os
# import json
# from typing import List, Dict, Any, Set, Optional

# from multi_parser import java_parser   # 预加载好的 tree‑itter Java 解析器

# # ----------------------------------------------------------------------
# # 工具函数
# # ----------------------------------------------------------------------
# def _get_modifiers(node) -> List[str]:
#     """
#     返回该节点（方法/构造函数/类）所拥有的修饰符列表。
#     兼容多种 tree‑itter‑java 语法树结构：
#       ① 直接子节点是 'modifier'（旧版）
#       ② 直接子节点是具体修饰符类型 ('public', 'private', …)（新版）
#       ③ 子节点里出现 'modifiers' 包装节点，内部再包含修饰符节点
#     """
#     mods = []

#     # ① 直接子节点（可能是单独的修饰符类型或 'modifier'）
#     for child in node.children:
#         # ①a 旧版：modifier 节点
#         if child.type == 'modifier':
#             mods.append(child.text.decode('utf-8'))
#         # ①b 新版：修饰符本身就是一个节点
#         elif child.type in ('public', 'private', 'protected', 'static',
#                            'abstract', 'final', 'synchronized', 'native',
#                            'strictfp'):
#             mods.append(child.type)

#     # ② 兼容：如果子节点里出现 'modifiers' 包装节点
#     for child in node.children:
#         if child.type == 'modifiers':
#             for mod_child in child.children:
#                 # ②a 可能是 'modifier' 节点
#                 if mod_child.type == 'modifier':
#                     mods.append(mod_child.text.decode('utf-8'))
#                 # ②b 直接是修饰符类型
#                 elif mod_child.type in ('public', 'private', 'protected', 'static',
#                                        'abstract', 'final', 'synchronized', 'native',
#                                        'strictfp'):
#                     mods.append(mod_child.type)

#     # 去重（有时同一修饰符会出现两次）
#     return list(dict.fromkeys(mods))


# def _is_abstract(mods: List[str]) -> bool:
#     return 'abstract' in mods


# def _is_static(mods: List[str]) -> bool:
#     return 'static' in mods


# def _is_private(mods: List[str]) -> bool:
#     return 'private' in mods


# def _is_protected(mods: List[str]) -> bool:
#     return 'protected' in mods


# def _is_public(mods: List[str]) -> bool:
#     return 'public' in mods


# def _get_identifier_text(node) -> Optional[str]:
#     for child in node.children:
#         if child.type == 'identifier':
#             return child.text.decode('utf-8')
#     return None


# def _get_superclass_names(class_node) -> List[str]:
#     names = []
#     for child in class_node.children:
#         if child.type == 'superclass':
#             name = _get_identifier_text(child)
#             if name:
#                 names.append(name)
#     return names


# def _get_method_signature(method_node) -> str:
#     return _get_identifier_text(method_node) or ''


# class JavaProjectTestScopeExtractor:
#     def __init__(self, project_root: str):
#         self.project_root = os.path.abspath(project_root)
#         self.parser = java_parser
#         self.classes: Dict[str, Dict[str, Any]] = {}

#     def _parse_project(self):
#         for root, dirs, files in os.walk(self.project_root):
#             if any(ignore in root for ignore in ['test', 'target', '.git', '.idea', '.vscode', 'build']):
#                 continue
#             for file in files:
#                 if file.endswith('.java') and not file.startswith('test_'):
#                     file_path = os.path.join(root, file)
#                     try:
#                         self._parse_file(file_path)
#                     except Exception as e:
#                         print(f"Error parsing {file_path}: {e}")

#     def _parse_file(self, file_path: str):
#         with open(file_path, 'rb') as f:
#             code = f.read()
#         tree = self.parser.parse(code)
#         root_node = tree.root_node

#         stack = [(root_node, None)]  # (node, parent_class_name)
#         while stack:
#             node, parent_name = stack.pop()

#             # 识别类 / 接口 / 枚举声明
#             if node.type in ('class_declaration', 'interface_declaration', 'enum_declaration'):
#                 class_name = _get_identifier_text(node)
#                 if not class_name:
#                     continue

#                 mods = _get_modifiers(node)
#                 abstract = _is_abstract(mods)
#                 superclasses = _get_superclass_names(node)

#                 # 找到 body 节点
#                 body_node = None
#                 for child in node.children:
#                     if child.type in ('class_body', 'interface_body', 'enum_body'):
#                         body_node = child
#                         break

#                 # 在 body 内部收集方法和构造函数
#                 methods = {}
#                 if body_node:
#                     for body_child in body_node.children:
#                         if body_child.type in ('method_declaration', 'constructor_declaration'):
#                             method_name = _get_method_signature(body_child)
#                             if not method_name:
#                                 continue
#                             method_mods = _get_modifiers(body_child)

#                             methods[method_name] = {
#                                 'name': method_name,
#                                 'src_file': file_path,
#                                 'test_file': self._gen_test_file_path(file_path, method_name),
#                                 'code': code[body_child.start_byte:body_child.end_byte].decode('utf-8'),
#                                 'is_static': _is_static(method_mods),
#                                 'is_abstract': _is_abstract(method_mods),
#                                 'is_private': _is_private(method_mods),
#                                 'is_protected': _is_protected(method_mods),
#                                 'is_public': _is_public(method_mods),
#                             }

#                 self.classes[class_name] = {
#                     'node': node,
#                     'abstract': abstract,
#                     'methods': methods,
#                     'superclasses': superclasses,
#                     'file': file_path
#                 }

#                 # 继续遍历子节点（可能有嵌套类）
#                 for child in node.children:
#                     stack.append((child, class_name))
#             else:
#                 for child in node.children:
#                     stack.append((child, parent_name))

#     def _gen_test_file_path(self, file_path, function_name):
#         temp_path = file_path.split(str(self.project_root))[1]
#         temp_path2 = temp_path.split(".java")[0]
#         file_name = temp_path2.split('/')[-1]
#         temp_path3 = temp_path2.split(file_name)[0]
#         return str(self.project_root) + '/' + "gen_tests" + str(temp_path3) + "Test" + file_name + '/' + "test_" + function_name + ".java"

#     # 计算单个类的测试范围
#     def _compute_test_scope_for_class(self, class_name: str) -> List[Dict[str, Any]]:
#         if class_name not in self.classes:
#             return []

#         cls = self.classes[class_name]
#         abstract = cls['abstract']
#         methods = cls['methods']
#         result: List[Dict[str, Any]] = []

#         # 抽象类：仅保留 static 方法
#         if abstract:
#             for m in methods.values():
#                 if m['is_static']:
#                     result.append(m)
#             return result

#         # 具体类：public/protected/package‑private 方法
#         for m in methods.values():
#             if not m['is_private']:
#                 result.append(m)

#         # 从抽象超类继承并实现的抽象方法
#         abstract_supers = self._collect_abstract_superclasses(class_name, set())
#         for super_name in abstract_supers:
#             super_cls = self.classes.get(super_name)
#             if not super_cls:
#                 continue
#             for m_name, m_info in super_cls['methods'].items():
#                 if not m_info['is_abstract']:
#                     continue
#                 if m_name in methods:
#                     result.append(methods[m_name])

#         return result

#     def _collect_abstract_superclasses(self, class_name: str, visited: Set[str]) -> Set[str]:
#         if class_name in visited:
#             return set()
#         visited.add(class_name)

#         cls = self.classes.get(class_name)
#         if not cls:
#             return set()

#         abstract_supers = set()
#         for super_name in cls['superclasses']:
#             super_cls = self.classes.get(super_name)
#             if super_cls and super_cls['abstract']:
#                 abstract_supers.add(super_name)
#                 abstract_supers.update(self._collect_abstract_superclasses(super_name, visited))
#         return abstract_supers

#     # 生成整个项目的测试范围映射
#     def extract_all_test_scopes(self) -> Dict[str, List[Dict[str, Any]]]:
#         if not self.classes:
#             self._parse_project()

#         scopes = {}
#         for class_name in self.classes:
#             scopes[class_name] = self._compute_test_scope_for_class(class_name)
#         return scopes

#     def save_to_json(self, output_file: str):
#         scopes = self.extract_all_test_scopes()

#         serializable = {}
#         for cls, methods in scopes.items():
#             serializable[cls] = []
#             for m in methods:
#                 copy = m.copy()
#                 for k, v in copy.items():
#                     if isinstance(v, bytes):
#                         copy[k] = v.decode('utf-8')
#                 serializable[cls].append(copy)

#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(serializable, f, indent=2, ensure_ascii=False)


# if __name__ == '__main__':
#     project_root = 'projects/mall'   # 替换为实际项目根目录
#     output_path = 'mall_focal.json'

#     extractor = JavaProjectTestScopeExtractor(project_root)
#     extractor.save_to_json(output_path)

#     scopes = extractor.extract_all_test_scopes()
#     total_methods = sum(len(m) for m in scopes.values())
#     print(f"已提取 {len(scopes)} 个类，共 {total_methods} 条符合测试范围的函数/方法，保存到 {output_path}")

#     # 调试：打印每个类的修饰符统计
#     for cls, methods in scopes.items():
#         public_cnt = sum(1 for m in methods if m['is_public'])
#         protected_cnt = sum(1 for m in methods if m['is_protected'])
#         static_cnt = sum(1 for m in methods if m['is_static'])
#         print(f"{cls}: public={public_cnt}, protected={protected_cnt}, static={static_cnt}, total={len(methods)}")


"""
JavaProjectTestScopeExtractor.py

一次性遍历整个 Java 项目，生成每个类的测试范围。
输出扁平化的JSON格式，包含构造函数和字段的代码作为类上下文。
"""

# import os
# import json
# from typing import List, Dict, Any, Set, Optional, Tuple

# from multi_parser import java_parser   # 预加载好的 tree‑itter Java 解析器

# # ----------------------------------------------------------------------
# # 工具函数
# # ----------------------------------------------------------------------
# def _get_modifiers(node) -> List[str]:
#     """
#     返回该节点（方法/构造函数/类/字段）所拥有的修饰符列表。
#     兼容多种 tree‑itter‑java 语法树结构：
#       ① 直接子节点是 'modifier'（旧版）
#       ② 直接子节点是具体修饰符类型 ('public', 'private', …)（新版）
#       ③ 子节点里出现 'modifiers' 包装节点，内部再包含修饰符节点
#     """
#     mods = []

#     # ① 直接子节点（可能是单独的修饰符类型或 'modifier'）
#     for child in node.children:
#         # ①a 旧版：modifier 节点
#         if child.type == 'modifier':
#             mods.append(child.text.decode('utf-8'))
#         # ①b 新版：修饰符本身就是一个节点
#         elif child.type in ('public', 'private', 'protected', 'static',
#                            'abstract', 'final', 'synchronized', 'native',
#                            'strictfp', 'transient', 'volatile'):
#             mods.append(child.type)

#     # ② 兼容：如果子节点里出现 'modifiers' 包装节点
#     for child in node.children:
#         if child.type == 'modifiers':
#             for mod_child in child.children:
#                 # ②a 可能是 'modifier' 节点
#                 if mod_child.type == 'modifier':
#                     mods.append(mod_child.text.decode('utf-8'))
#                 # ②b 直接是修饰符类型
#                 elif mod_child.type in ('public', 'private', 'protected', 'static',
#                                        'abstract', 'final', 'synchronized', 'native',
#                                        'strictfp', 'transient', 'volatile'):
#                     mods.append(mod_child.type)

#     # 去重（有时同一修饰符会出现两次）
#     return list(dict.fromkeys(mods))


# def _is_abstract(mods: List[str]) -> bool:
#     return 'abstract' in mods


# def _is_static(mods: List[str]) -> bool:
#     return 'static' in mods


# def _is_private(mods: List[str]) -> bool:
#     return 'private' in mods


# def _is_protected(mods: List[str]) -> bool:
#     return 'protected' in mods


# def _is_public(mods: List[str]) -> bool:
#     return 'public' in mods


# def _get_identifier_text(node) -> Optional[str]:
#     for child in node.children:
#         if child.type == 'identifier':
#             return child.text.decode('utf-8')
#     return None


# def _get_superclass_names(class_node) -> List[str]:
#     names = []
#     for child in class_node.children:
#         if child.type == 'superclass':
#             name = _get_identifier_text(child)
#             if name:
#                 names.append(name)
#     return names


# def _get_method_signature(method_node) -> str:
#     return _get_identifier_text(method_node) or ''


# class JavaProjectTestScopeExtractor:
#     def __init__(self, project_root: str):
#         self.project_root = os.path.abspath(project_root)
#         self.parser = java_parser
#         self.classes: Dict[str, Dict[str, Any]] = {}

#     def _parse_project(self):

#         # 定义要忽略的目录模式
#         IGNORE_DIRS = ['test', 'tests', 'target', '.git', '.idea', '.vscode', 'build']

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
#                 if file.endswith('.java') and not file.endswith('Test.java') and not file.endswith('Tests.java'):
#                     file_path = os.path.join(root, file)
#                     try:
#                         self._parse_file(file_path)
#                     except Exception as e:
#                         print(f"Error parsing {file_path}: {e}")

#     def _parse_file(self, file_path: str):
#         with open(file_path, 'rb') as f:
#             code = f.read()
#         tree = self.parser.parse(code)
#         root_node = tree.root_node

#         stack = [(root_node, None)]  # (node, parent_class_name)
#         while stack:
#             node, parent_name = stack.pop()

#             # 识别类 / 接口 / 枚举声明
#             if node.type in ('class_declaration', 'interface_declaration', 'enum_declaration'):
#                 class_name = _get_identifier_text(node)
#                 if not class_name:
#                     continue

#                 mods = _get_modifiers(node)

#                 if node.type == 'interface_declaration':
#                     abstract = True  # 接口总是抽象的
#                 else:
#                     abstract = _is_abstract(mods)

#                 superclasses = _get_superclass_names(node)

#                 # 找到 body 节点
#                 body_node = None
#                 for child in node.children:
#                     if child.type in ('class_body', 'interface_body', 'enum_body'):
#                         body_node = child
#                         break

#                 # 在 body 内部收集方法、构造函数和字段
#                 methods = {}
#                 constructor_codes = []  # 存储所有构造函数的代码
#                 field_codes = []        # 存储所有字段的代码

#                 if body_node:
#                     for body_child in body_node.children:
#                         # 处理方法声明
#                         if body_child.type == 'method_declaration':
#                             method_name = _get_method_signature(body_child)
#                             if not method_name:
#                                 continue
#                             method_mods = _get_modifiers(body_child)

#                             if node.type == 'interface_declaration':
#                                 # 检查是否有方法体（通过检查是否有block子节点）
#                                 has_body = False
#                                 for child in body_child.children:
#                                     if child.type == 'block':  # block表示方法体
#                                         has_body = True
#                                         break

#                                 # 如果没有方法体，也没有default/static修饰符，则是抽象方法
#                                 if not has_body and 'default' not in method_mods and not _is_static(method_mods):
#                                     method_mods.append('abstract')

#                             methods[method_name] = {
#                                 'name': method_name,
#                                 'src_file': file_path,
#                                 'code': code[body_child.start_byte:body_child.end_byte].decode('utf-8'),
#                                 'is_static': _is_static(method_mods),
#                                 'is_abstract': _is_abstract(method_mods),
#                                 'is_private': _is_private(method_mods),
#                                 'is_protected': _is_protected(method_mods),
#                                 'is_public': _is_public(method_mods),
#                             }

#                         # 收集构造函数代码（收集公有和受保护的）
#                         elif body_child.type == 'constructor_declaration':
#                             constructor_mods = _get_modifiers(body_child)
#                             # 只排除私有的构造函数
#                             if not _is_private(constructor_mods):  # 包括 public, protected, 和 包级可见(default)
#                                 constructor_code = code[body_child.start_byte:body_child.end_byte].decode('utf-8')
#                                 constructor_codes.append(constructor_code)

#                         # 收集字段代码（收集公有和受保护的）
#                         elif body_child.type == 'field_declaration':
#                             field_mods = _get_modifiers(body_child)
#                             # 只排除私有的字段
#                             if not _is_private(field_mods):  # 包括 public, protected, 和 包级可见(default)
#                                 field_code = code[body_child.start_byte:body_child.end_byte].decode('utf-8')
#                                 field_codes.append(field_code)

#                 self.classes[class_name] = {
#                     'node': node,
#                     'abstract': abstract,
#                     'methods': methods,
#                     'constructor_codes': constructor_codes,  # 构造函数代码列表
#                     'field_codes': field_codes,              # 字段代码列表
#                     'superclasses': superclasses,
#                     'file': file_path
#                 }

#                 # 继续遍历子节点（可能有嵌套类）
#                 for child in node.children:
#                     stack.append((child, class_name))
#             else:
#                 for child in node.children:
#                     stack.append((child, parent_name))

#     def _gen_test_file_path(self, file_path, function_name):
#         temp_path = file_path.split(str(self.project_root)+"/")[1]
#         temp_path2 = temp_path.split(".java")[0]
#         file_name = temp_path2.split("/")[-1]
#         temp_path3 = temp_path.split(file_name)[0]
#         temp_path4 = temp_path3.replace("/main/", "/test/")
#         if function_name and function_name[0].islower():
#             function_name = function_name[0].upper() + function_name[1:]
#         return temp_path4 + file_name.lower()+ "/" + function_name + "Tests.java"

#     # 计算单个类的测试范围
#     def _compute_test_scope_for_class(self, class_name: str) -> List[Dict[str, Any]]:
#         if class_name not in self.classes:
#             return []

#         cls = self.classes[class_name]
#         abstract = cls['abstract']
#         methods = cls['methods']
#         result: List[Dict[str, Any]] = []

#         # 抽象类：仅保留 static 方法
#         if abstract:
#             for m in methods.values():
#                 if m['is_static']:
#                     result.append(m)
#             return result

#         # 具体类：public/protected/package‑private 方法
#         for m in methods.values():
#             if not m['is_private']:
#                 result.append(m)

#         # 从抽象超类继承并实现的抽象方法
#         abstract_supers = self._collect_abstract_superclasses(class_name, set())
#         for super_name in abstract_supers:
#             super_cls = self.classes.get(super_name)
#             if not super_cls:
#                 continue
#             for m_name, m_info in super_cls['methods'].items():
#                 if not m_info['is_abstract']:
#                     continue
#                 if m_name in methods:
#                     result.append(methods[m_name])

#         return result

#     def _collect_abstract_superclasses(self, class_name: str, visited: Set[str]) -> Set[str]:
#         if class_name in visited:
#             return set()
#         visited.add(class_name)

#         cls = self.classes.get(class_name)
#         if not cls:
#             return set()

#         abstract_supers = set()
#         for super_name in cls['superclasses']:
#             super_cls = self.classes.get(super_name)
#             if super_cls and super_cls['abstract']:
#                 abstract_supers.add(super_name)
#                 abstract_supers.update(self._collect_abstract_superclasses(super_name, visited))
#         return abstract_supers

#     # 提取所有测试项（扁平化格式）
#     def _extract_all_test_items(self) -> List[Dict[str, Any]]:
#         """
#         提取所有测试项，返回扁平化的列表
#         每个项包含：
#         {
#             "name": 方法名,
#             "src_file": 源文件路径,
#             "test_file": 测试文件路径,
#             "code": 方法代码,
#             "type": 类型 ("function" 或 "method"),
#             "class_name": 类名,
#             "full_class_name": 类名,
#             "constructor": 构造函数代码列表,
#             "fields": 字段代码列表
#         }
#         """
#         if not self.classes:
#             self._parse_project()

#         all_items = []

#         for class_name in self.classes:
#             # 计算类的测试范围（需要测试的方法）
#             test_methods = self._compute_test_scope_for_class(class_name)

#             # 获取类的构造函数代码列表和字段代码列表
#             cls_info = self.classes[class_name]
#             constructor_codes = cls_info.get('constructor_codes', [])
#             field_codes = cls_info.get('field_codes', [])

#             # 为每个测试方法创建测试项
#             for method in test_methods:
#                 src_file = method["src_file"].split(str(self.project_root)+"/")[1]
#                 item = {
#                     "name": method["name"],
#                     "src_file": src_file,
#                     "test_file": self._gen_test_file_path(method["src_file"], method["name"]),
#                     "code": method["code"],
#                     "type": "function" if method.get("is_static", False) else "method",
#                     "class_name": class_name,
#                     "full_class_name": class_name,  # 暂时使用简单类名
#                     "class_constructor": constructor_codes,  # 构造函数代码列表
#                     "class_fields": field_codes,            # 字段代码列表
#                 }
#                 all_items.append(item)

#         return all_items

#     def save_to_json(self, output_file: str):
#         """保存扁平化的测试项到JSON文件"""
#         items = self._extract_all_test_items()

#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(items, f, indent=2, ensure_ascii=False)


# import os
# import json
# from typing import List, Dict, Any, Set, Optional

# from multi_parser import java_parser   # 预加载好的 tree-itter Java 解析器


# # ----------------------------------------------------------------------
# # 工具函数
# # ----------------------------------------------------------------------
# def _get_modifiers(node) -> List[str]:
#     mods = []

#     for child in node.children:
#         if child.type == 'modifier':
#             mods.append(child.text.decode('utf-8'))
#         elif child.type in (
#             'public', 'private', 'protected', 'static', 'abstract',
#             'final', 'synchronized', 'native', 'strictfp',
#             'transient', 'volatile'
#         ):
#             mods.append(child.type)

#     for child in node.children:
#         if child.type == 'modifiers':
#             for mod_child in child.children:
#                 if mod_child.type == 'modifier':
#                     mods.append(mod_child.text.decode('utf-8'))
#                 elif mod_child.type in (
#                     'public', 'private', 'protected', 'static', 'abstract',
#                     'final', 'synchronized', 'native', 'strictfp',
#                     'transient', 'volatile'
#                 ):
#                     mods.append(mod_child.type)

#     return list(dict.fromkeys(mods))


# def _is_abstract(mods: List[str]) -> bool:
#     return 'abstract' in mods


# def _is_static(mods: List[str]) -> bool:
#     return 'static' in mods


# def _is_private(mods: List[str]) -> bool:
#     return 'private' in mods


# def _is_protected(mods: List[str]) -> bool:
#     return 'protected' in mods


# def _is_public(mods: List[str]) -> bool:
#     return 'public' in mods


# def _get_identifier_text(node) -> Optional[str]:
#     for child in node.children:
#         if child.type == 'identifier':
#             return child.text.decode('utf-8')
#     return None


# def _get_superclass_names(class_node) -> List[str]:
#     names = []
#     for child in class_node.children:
#         if child.type == 'superclass':
#             name = _get_identifier_text(child)
#             if name:
#                 names.append(name)
#     return names


# def _get_method_signature(method_node) -> str:
#     return _get_identifier_text(method_node) or ''


# def _is_deprecated(node) -> bool:
#     """
#     判断是否存在 @Deprecated / @java.lang.Deprecated 注解
#     """
#     for child in node.children:
#         if child.type in ('annotation', 'marker_annotation'):
#             text = child.text.decode('utf-8')
#             if 'Deprecated' in text:
#                 return True

#         if child.type == 'modifiers':
#             for sub in child.children:
#                 if sub.type in ('annotation', 'marker_annotation'):
#                     text = sub.text.decode('utf-8')
#                     if 'Deprecated' in text:
#                         return True
#     return False


# # ----------------------------------------------------------------------
# # 主类
# # ----------------------------------------------------------------------
# class JavaProjectTestScopeExtractor:
#     def __init__(self, project_root: str):
#         self.project_root = os.path.abspath(project_root)
#         self.parser = java_parser
#         self.classes: Dict[str, Dict[str, Any]] = {}

#     def _parse_project(self):
#         IGNORE_DIRS = ['test', 'tests', 'target', '.git', '.idea', '.vscode', 'build']

#         for root, dirs, files in os.walk(self.project_root):
#             dirs[:] = [
#                 d for d in dirs
#                 if d not in IGNORE_DIRS and not d.startswith('.')
#             ]

#             if any(part in IGNORE_DIRS for part in root.split(os.sep)):
#                 continue

#             for file in files:
#                 if file.endswith('.java') and not file.endswith(('Test.java', 'Tests.java')):
#                     path = os.path.join(root, file)
#                     try:
#                         self._parse_file(path)
#                     except Exception as e:
#                         print(f"Error parsing {path}: {e}")

#     def _parse_file(self, file_path: str):
#         with open(file_path, 'rb') as f:
#             code = f.read()

#         tree = self.parser.parse(code)
#         root_node = tree.root_node

#         stack = [(root_node, None)]

#         while stack:
#             node, parent_name = stack.pop()

#             if node.type in ('class_declaration', 'interface_declaration', 'enum_declaration'):
#                 if _is_deprecated(node):
#                     continue

#                 class_name = _get_identifier_text(node)
#                 if not class_name:
#                     continue

#                 mods = _get_modifiers(node)
#                 abstract = True if node.type == 'interface_declaration' else _is_abstract(mods)
#                 superclasses = _get_superclass_names(node)

#                 body_node = next(
#                     (c for c in node.children if c.type in ('class_body', 'interface_body', 'enum_body')),
#                     None
#                 )

#                 methods = {}
#                 constructor_codes = []
#                 field_codes = []

#                 if body_node:
#                     for body_child in body_node.children:

#                         # ---------------- 方法 ----------------
#                         if body_child.type == 'method_declaration':
#                             if _is_deprecated(body_child):
#                                 continue

#                             method_name = _get_method_signature(body_child)
#                             if not method_name:
#                                 continue

#                             method_mods = _get_modifiers(body_child)

#                             if node.type == 'interface_declaration':
#                                 has_body = any(c.type == 'block' for c in body_child.children)
#                                 if not has_body and 'default' not in method_mods and not _is_static(method_mods):
#                                     method_mods.append('abstract')

#                             methods[method_name] = {
#                                 'name': method_name,
#                                 'src_file': file_path,
#                                 'code': code[body_child.start_byte:body_child.end_byte].decode('utf-8'),
#                                 'is_static': _is_static(method_mods),
#                                 'is_abstract': _is_abstract(method_mods),
#                                 'is_private': _is_private(method_mods),
#                                 'is_protected': _is_protected(method_mods),
#                                 'is_public': _is_public(method_mods),
#                             }

#                         # ---------------- 构造函数 ----------------
#                         elif body_child.type == 'constructor_declaration':
#                             if _is_deprecated(body_child):
#                                 continue

#                             mods = _get_modifiers(body_child)
#                             if not _is_private(mods):
#                                 constructor_codes.append(
#                                     code[body_child.start_byte:body_child.end_byte].decode('utf-8')
#                                 )

#                         # ---------------- 字段 ----------------
#                         elif body_child.type == 'field_declaration':
#                             if _is_deprecated(body_child):
#                                 continue

#                             mods = _get_modifiers(body_child)
#                             if not _is_private(mods):
#                                 field_codes.append(
#                                     code[body_child.start_byte:body_child.end_byte].decode('utf-8')
#                                 )

#                 self.classes[class_name] = {
#                     'node': node,
#                     'abstract': abstract,
#                     'methods': methods,
#                     'constructor_codes': constructor_codes,
#                     'field_codes': field_codes,
#                     'superclasses': superclasses,
#                     'file': file_path
#                 }

#             for child in node.children:
#                 stack.append((child, parent_name))

#     def _gen_test_file_path(self, file_path, function_name):
#         temp_path = file_path.split(self.project_root + "/")[1]
#         temp_path2 = temp_path.split(".java")[0]
#         file_name = temp_path2.split("/")[-1]
#         temp_path3 = temp_path.split(file_name)[0]
#         temp_path4 = temp_path3.replace("/main/", "/test/")

#         if function_name and function_name[0].islower():
#             function_name = function_name[0].upper() + function_name[1:]

#         return temp_path4 + file_name.lower() + "/" + function_name + "Tests.java"

#     def _compute_test_scope_for_class(self, class_name: str):
#         cls = self.classes.get(class_name)
#         if not cls:
#             return []

#         result = []
#         methods = cls['methods']

#         if cls['abstract']:
#             for m in methods.values():
#                 if m['is_static']:
#                     result.append(m)
#             return result

#         for m in methods.values():
#             if not m['is_private']:
#                 result.append(m)

#         abstract_supers = self._collect_abstract_superclasses(class_name, set())
#         for super_name in abstract_supers:
#             super_cls = self.classes.get(super_name)
#             if not super_cls:
#                 continue
#             for m_name, m_info in super_cls['methods'].items():
#                 if m_info['is_abstract'] and m_name in methods:
#                     result.append(methods[m_name])

#         return result

#     def _collect_abstract_superclasses(self, class_name: str, visited: Set[str]):
#         if class_name in visited:
#             return set()
#         visited.add(class_name)

#         cls = self.classes.get(class_name)
#         if not cls:
#             return set()

#         result = set()
#         for super_name in cls['superclasses']:
#             super_cls = self.classes.get(super_name)
#             if super_cls and super_cls['abstract']:
#                 result.add(super_name)
#                 result |= self._collect_abstract_superclasses(super_name, visited)
#         return result

#     def _extract_all_test_items(self):
#         if not self.classes:
#             self._parse_project()

#         all_items = []

#         for class_name, cls in self.classes.items():
#             methods = self._compute_test_scope_for_class(class_name)

#             for method in methods:
#                 src_file = method["src_file"].split(self.project_root + "/")[1]
#                 all_items.append({
#                     "name": method["name"],
#                     "src_file": src_file,
#                     "test_file": self._gen_test_file_path(method["src_file"], method["name"]),
#                     "code": method["code"],
#                     "type": "function" if method["is_static"] else "method",
#                     "class_name": class_name,
#                     "full_class_name": class_name,
#                     "class_constructor": cls["constructor_codes"],
#                     "class_fields": cls["field_codes"],
#                 })

#         return all_items

#     def save_to_json(self, output_file: str):
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(self._extract_all_test_items(), f, indent=2, ensure_ascii=False)


# if __name__ == '__main__':
#     project_root = 'projects/jcasbin'   # 替换为实际项目根目录
#     output_path = 'jcasbin_focal_class_context1.json'

#     extractor = JavaProjectTestScopeExtractor(project_root)
#     extractor.save_to_json(output_path)

#     items = extractor._extract_all_test_items()

#     print(f"已提取 {len(items)} 个测试项，保存到 {output_path}")

#     # 打印统计信息
#     type_counts = {}
#     for item in items:
#         item_type = item.get('type', 'unknown')
#         type_counts[item_type] = type_counts.get(item_type, 0) + 1

#     print(f"测试项类型统计：")
#     for item_type, count in type_counts.items():
#         print(f"  {item_type}: {count}")

#     # 打印示例
#     if items:
#         print(f"\n第一个测试项示例：")
#         first_item = items[0]
#         print(f"类名: {first_item['class_name']}")
#         print(f"方法名: {first_item['name']}")
#         print(f"类型: {first_item['type']}")
#         print(f"构造函数数量: {len(first_item['class_constructor'])}")
#         print(f"字段数量: {len(first_item['class_fields'])}")
#         print(f"源文件: {first_item['src_file']}")

#         # 显示代码片段
#         if first_item['code']:
#             code_preview = first_item['code'][:100] + "..." if len(first_item['code']) > 100 else first_item['code']
#             print(f"方法代码预览: {code_preview}")

#         # 显示第一个构造函数（如果有）
#         if first_item['class_constructor']:
#             constructor_preview = first_item['class_constructor'][0][:80] + "..." if len(first_item['class_constructor'][0]) > 80 else first_item['class_constructor'][0]
#             print(f"第一个构造函数预览: {constructor_preview}")

#         # 显示第一个字段（如果有）
#         if first_item['class_fields']:
#             field_preview = first_item['class_fields'][0][:80] + "..." if len(first_item['class_fields'][0]) > 80 else first_item['class_fields'][0]
#             print(f"第一个字段预览: {field_preview}")


import os
import json
import re
import random
import numpy as np
import lizard
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict

from multi_parser import java_parser  # 预加载好的 tree-itter Java 解析器
from func_select import StratifiedFunctionSelector
from file_select import *


# ----------------------------------------------------------------------
# 工具函数
# ----------------------------------------------------------------------
def _get_modifiers(node) -> List[str]:
    mods = []

    for child in node.children:
        if child.type == 'modifier':
            mods.append(child.text.decode('utf-8'))
        elif child.type in (
                'public', 'private', 'protected', 'static', 'abstract',
                'final', 'synchronized', 'native', 'strictfp',
                'transient', 'volatile'
        ):
            mods.append(child.type)

    for child in node.children:
        if child.type == 'modifiers':
            for mod_child in child.children:
                if mod_child.type == 'modifier':
                    mods.append(mod_child.text.decode('utf-8'))
                elif mod_child.type in (
                        'public', 'private', 'protected', 'static', 'abstract',
                        'final', 'synchronized', 'native', 'strictfp',
                        'transient', 'volatile'
                ):
                    mods.append(mod_child.type)

    return list(dict.fromkeys(mods))


def _is_abstract(mods: List[str]) -> bool:
    return 'abstract' in mods


def _is_static(mods: List[str]) -> bool:
    return 'static' in mods


def _is_private(mods: List[str]) -> bool:
    return 'private' in mods


def _is_protected(mods: List[str]) -> bool:
    return 'protected' in mods


def _is_public(mods: List[str]) -> bool:
    return 'public' in mods


def _get_identifier_text(node) -> Optional[str]:
    for child in node.children:
        if child.type == 'identifier':
            return child.text.decode('utf-8')
    return None


def _get_superclass_names(class_node) -> List[str]:
    names = []
    for child in class_node.children:
        if child.type == 'superclass':
            name = _get_identifier_text(child)
            if name:
                names.append(name)
    return names


def _get_method_signature(method_node) -> str:
    return _get_identifier_text(method_node) or ''


def _is_deprecated(node) -> bool:
    """
    判断是否存在 @Deprecated / @java.lang.Deprecated 注解
    """
    for child in node.children:
        if child.type in ('annotation', 'marker_annotation'):
            text = child.text.decode('utf-8')
            if 'Deprecated' in text:
                return True

        if child.type == 'modifiers':
            for sub in child.children:
                if sub.type in ('annotation', 'marker_annotation'):
                    text = sub.text.decode('utf-8')
                    if 'Deprecated' in text:
                        return True
    return False


# ----------------------------------------------------------------------
# 主类（增强版）
# ----------------------------------------------------------------------
class JavaProjectTestScopeExtractor:
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
        self.parser = java_parser
        self.classes: Dict[str, Dict[str, Any]] = {}

        # getter/setter模式的正则表达式
        self.getter_setter_patterns = [
            r'^get[A-Z]',  # getXxx
            r'^set[A-Z]',  # setXxx
            r'^is[A-Z]',  # isXxx
            r'^has[A-Z]',  # hasXxx
            r'^create[A-Z]',  # createXxx
            r'^build[A-Z]',  # buildXxx
            r'^to[A-Z]',  # toXxx
            r'^toString$',  # toString
            r'^hashCode$',  # hashCode
            r'^equals$',  # equals
            r'^clone$',  # clone
            r'^copy$',  # copy
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
            report = lizard.analyze_file.analyze_source_code("temp.java", code)

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
                # 匹配方法参数部分
                param_match = re.search(r'\((.*?)\)', code.split('\n')[0])
                if param_match:
                    param_text = param_match.group(1)
                    param_count = len([p for p in param_text.split(',') if p.strip()])
            except:
                param_count = 0

        return complexity, loc, param_count

    def _parse_project(self):
        """解析项目中的所有文件"""
        for file in self.files:
            try:
                self._parse_file(file)
            except Exception as e:
                print(f"Error parsing {file}: {e}")

    def _parse_file(self, file_path: str):
        """解析单个文件，提取类和方法信息"""
        with open(file_path, 'rb') as f:
            code = f.read()

        tree = self.parser.parse(code)
        root_node = tree.root_node

        stack = [(root_node, None)]

        while stack:
            node, parent_name = stack.pop()

            if node.type in ('class_declaration', 'interface_declaration', 'enum_declaration'):
                if _is_deprecated(node):
                    continue

                class_name = _get_identifier_text(node)
                if not class_name:
                    continue

                mods = _get_modifiers(node)
                abstract = True if node.type == 'interface_declaration' else _is_abstract(mods)
                superclasses = _get_superclass_names(node)

                body_node = next(
                    (c for c in node.children if c.type in ('class_body', 'interface_body', 'enum_body')),
                    None
                )

                methods = {}
                constructor_codes = []
                field_codes = []

                if body_node:
                    for body_child in body_node.children:

                        # ---------------- 方法 ----------------
                        if body_child.type == 'method_declaration':
                            if _is_deprecated(body_child):
                                continue

                            method_name = _get_method_signature(body_child)
                            if not method_name:
                                continue

                            method_mods = _get_modifiers(body_child)

                            if node.type == 'interface_declaration':
                                has_body = any(c.type == 'block' for c in body_child.children)
                                if not has_body and 'default' not in method_mods and not _is_static(method_mods):
                                    method_mods.append('abstract')

                            # 获取方法代码
                            method_code = code[body_child.start_byte:body_child.end_byte].decode('utf-8')

                            # 使用lizard计算复杂度、行数和参数数量
                            complexity, loc, param_count = self._compute_complexity_and_loc(method_code)

                            # 判断是否异步（Java中的异步方法通常有特定返回类型或注解）
                            is_async = False
                            # 检查返回类型
                            for child in body_child.children:
                                if child.type == 'type_identifier':
                                    return_type = child.text.decode('utf-8').lower()
                                    if 'completablefuture' in return_type or 'future' in return_type:
                                        is_async = True
                                        break

                            # 检查异步注解
                            if '@Async' in body_child.text.decode('utf-8'):
                                is_async = True

                            methods[method_name] = {
                                'name': method_name,
                                'src_file': file_path,
                                'code': method_code,
                                'is_static': _is_static(method_mods),
                                'is_abstract': _is_abstract(method_mods),
                                'is_private': _is_private(method_mods),
                                'is_protected': _is_protected(method_mods),
                                'is_public': _is_public(method_mods),
                                'loc': loc,
                                'complexity': complexity,  # 注意：键名改为complexity，与StratifiedFunctionSelector匹配
                                'param_count': param_count,
                                'is_async': is_async,
                                'type': 'function' if _is_static(method_mods) else 'method',
                                'class_name': class_name,
                                'full_class_name': class_name,  # 添加完整类名
                                'modifiers': method_mods
                            }

                        # ---------------- 构造函数 ----------------
                        elif body_child.type == 'constructor_declaration':
                            if _is_deprecated(body_child):
                                continue

                            mods = _get_modifiers(body_child)
                            if not _is_private(mods):
                                constructor_codes.append(
                                    code[body_child.start_byte:body_child.end_byte].decode('utf-8')
                                )

                        # ---------------- 字段 ----------------
                        elif body_child.type == 'field_declaration':
                            if _is_deprecated(body_child):
                                continue

                            mods = _get_modifiers(body_child)
                            if not _is_private(mods):
                                field_codes.append(
                                    code[body_child.start_byte:body_child.end_byte].decode('utf-8')
                                )

                self.classes[class_name] = {
                    'node': node,
                    'abstract': abstract,
                    'methods': methods,
                    'constructor_codes': constructor_codes,
                    'field_codes': field_codes,
                    'superclasses': superclasses,
                    'file': file_path
                }

            for child in node.children:
                stack.append((child, parent_name))

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

        # 检查是否有字段赋值（简单的模式匹配）
        has_field_assignment = False
        lines = method_code.split('\n')
        for line in lines:
            if '=' in line and ('this.' in line or any(word in line for word in ['field', 'value', 'data'])):
                has_field_assignment = True
                break

        # 如果既没有return也没有字段赋值，则可能是void方法
        if not has_return and not has_field_assignment:
            # 排除一些特殊情况
            excluded_names = ['main', 'run', 'execute', 'process', 'handle', 'init', 'setup', 'start']
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
                important_methods = ['main', 'run', 'execute', 'process', 'handle']
                if method_name not in important_methods:
                    return True

        return False

    # def _gen_test_file_path(self, file_path: str, function_name: str) -> str:
    #     """生成测试文件路径"""
    #     # 提取相对路径
    #     src/main/java/org/apache/commons/jxpath/ri/compiler/LocationPath.java
    #     if file_path.startswith(self.project_root):
    #         rel_path = file_path[len(self.project_root):].lstrip(os.sep)
    #     else:
    #         rel_path = file_path

    #     # 移除.java扩展名
    #     rel_path_no_ext = os.path.splitext(rel_path)[0]

    #     # 将main替换为test
    #     rel_path_no_ext = rel_path_no_ext.replace('/main/', '/test/')

    #     # 确保function_name首字母大写
    #     if function_name and function_name[0].islower():
    #         function_name = function_name[0].upper() + function_name[1:]

    #     # 生成测试文件名
    #     test_file = f"{rel_path_no_ext.lower()}/{function_name}Tests.java"

    #     return test_file

    def _gen_test_file_path(self, file_path: str, function_name: str) -> str:
        """生成测试文件路径，测试文件直接放在包目录下，文件名为 <function_name>Tests.java"""
        # 提取相对路径
        if file_path.startswith(self.project_root):
            rel_path = file_path[len(self.project_root):].lstrip(os.sep)
        else:
            rel_path = file_path

        # 移除.java扩展名
        rel_path_no_ext = os.path.splitext(rel_path)[0]

        # 将main替换为test
        rel_path_no_ext = rel_path_no_ext.replace('/main/', '/test/')

        # 提取包目录（去掉最后的类名）
        package_dir = os.path.dirname(rel_path_no_ext)

        # 将function_name转换为小写
        if function_name and function_name[0].islower():
            function_name = function_name[0].upper() + function_name[1:]
        
        # 生成测试文件名，使用 '/' 拼接保持风格
        test_file = f"{package_dir}/{function_name}Tests.java"

        return test_file

    def _compute_test_scope_for_class(self, class_name: str):
        """计算类的测试范围"""
        cls = self.classes.get(class_name)
        if not cls:
            return []

        result = []
        methods = cls['methods']

        if cls['abstract']:
            for m in methods.values():
                if m['is_static']:
                    result.append(m)
            return result

        for m in methods.values():
            if not m['is_private']:
                result.append(m)

        abstract_supers = self._collect_abstract_superclasses(class_name, set())
        for super_name in abstract_supers:
            super_cls = self.classes.get(super_name)
            if not super_cls:
                continue
            for m_name, m_info in super_cls['methods'].items():
                if m_info['is_abstract'] and m_name in methods:
                    result.append(methods[m_name])

        return result

    def _collect_abstract_superclasses(self, class_name: str, visited: Set[str]):
        """收集抽象父类"""
        if class_name in visited:
            return set()
        visited.add(class_name)

        cls = self.classes.get(class_name)
        if not cls:
            return set()

        result = set()
        for super_name in cls['superclasses']:
            super_cls = self.classes.get(super_name)
            if super_cls and super_cls['abstract']:
                result.add(super_name)
                result |= self._collect_abstract_superclasses(super_name, visited)
        return result

    # 主提取和选择流程
    def extract_and_select_functions(self) -> List[Dict[str, Any]]:
        """
        完整的提取和选择流程：
        1. 解析项目提取所有方法
        2. 应用过滤规则
        3. 对每个文件进行分层抽样
        """
        # 1. 解析项目
        print(f"开始解析项目，文件数量: {len(self.files)}")
        self._parse_project()

        all_selected_methods = []

        # 按文件分组方法
        methods_by_file = defaultdict(list)
        for class_name, cls in self.classes.items():
            methods = self._compute_test_scope_for_class(class_name)
            for method in methods:
                method['class_name'] = class_name
                method['full_class_name'] = class_name
                method['class_constructor'] = cls.get('constructor_codes', [])
                method['class_fields'] = cls.get('field_codes', [])
                methods_by_file[method['src_file']].append(method)

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
                            # 生成测试文件路径
                            test_file = self._gen_test_file_path(func['src_file'], func['name'])

                            # 构建完整方法信息
                            method_info = {
                                "project_root": self.project_root,
                                "name": func['name'],
                                "src_file": os.path.relpath(func['src_file'], self.project_root),
                                "test_file": test_file,
                                "code": func['code'],
                                "is_async": func.get('is_async', False),
                                "type": func.get('type', 'method'),
                                # "loc": func.get('loc', 0),
                                # "complexity": func.get('complexity', 1),
                                # "param_count": func.get('param_count', 0),
                                # "func_score": func.get('func_score', 0),
                                # "raw_metrics": func.get('raw_metrics', {})
                            }

                            # 添加类相关信息
                            if func.get('type') == 'method':
                                method_info.update({
                                    'class_name': func.get('class_name'),
                                    'full_class_name': func.get('full_class_name'),
                                    'class_constructor': func.get('class_constructor', []),
                                    'class_fields': func.get('class_fields', []),
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
                self.stats[file_name]['public'] = len([m for m in file_methods if m.get('is_public', False)])

            except Exception as e:
                print(f"处理 {file_path} 时出错: {e}")
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
                print(f"  公共方法: {stats.get('public', 0)}")
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
        self.extract_and_select_functions()

    def print_detailed_selection_report(self):
        """打印详细的选择报告"""
        for result in self.selection_results:
            if result['selected_functions']:
                self.selector.print_selection_report(result)
                print()


# 使用示例
if __name__ == "__main__":
    # 示例用法
    project_root = "projects/fastjson"

    # 创建分析器实例
    analyzer = FileQualityAnalyzer(
        language="java",
        random_seed=42,  # 固定随机种子，确保结果可重复
        sampling_k=2  # 每个层级抽取2个文件
    )

    # 完整分析项目
    sample_files = analyzer.analyze_project(
        project_path=project_root,
        group_by_module=True  # 按模块分组
    )

    # print(sample_files)

    # 创建提取器并执行
    extractor = JavaProjectTestScopeExtractor(
        project_root=project_root,
        file_list=sample_files,
        output_file="fastjson_lite_new.json",
        min_loc_threshold=5,
        random_seed=42
    )

    selected_methods = extractor.extract_and_select_functions()
    print(f"\n总共选择了 {len(selected_methods)} 个方法用于测试生成")

    # 打印详细报告
    # extractor.print_detailed_selection_report()
"""
JavaProjectTestScopeExtractor.py

一次性遍历整个 Java 项目，生成每个类的测试范围。
已修复修饰符字段全为 false 的问题。
"""

import os
import json
import re
from typing import List, Dict, Any, Set, Optional
from collections import defaultdict
from multi_parser import java_parser   # 预加载好的 tree‑itter Java 解析器
from func_select import StratifiedFunctionSelector
from file_select import *

# ----------------------------------------------------------------------
# 工具函数
# ----------------------------------------------------------------------
def _get_modifiers(node) -> List[str]:
    """
    返回该节点（方法/构造函数/类）所拥有的修饰符列表。
    兼容多种 tree‑itter‑java 语法树结构：
      ① 直接子节点是 'modifier'（旧版）
      ② 直接子节点是具体修饰符类型 ('public', 'private', …)（新版）
      ③ 子节点里出现 'modifiers' 包装节点，内部再包含修饰符节点
    """
    mods = []

    # ① 直接子节点（可能是单独的修饰符类型或 'modifier'）
    for child in node.children:
        # ①a 旧版：modifier 节点
        if child.type == 'modifier':
            mods.append(child.text.decode('utf-8'))
        # ①b 新版：修饰符本身就是一个节点
        elif child.type in ('public', 'private', 'protected', 'static',
                           'abstract', 'final', 'synchronized', 'native',
                           'strictfp'):
            mods.append(child.type)

    # ② 兼容：如果子节点里出现 'modifiers' 包装节点
    for child in node.children:
        if child.type == 'modifiers':
            for mod_child in child.children:
                if mod_child.type == 'modifier':
                    mods.append(mod_child.text.decode('utf-8'))
                elif mod_child.type in ('public', 'private', 'protected', 'static',
                                      'abstract', 'final', 'synchronized', 'native',
                                      'strictfp'):
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


# 新增：从源码文本中提取 import 语句
def _extract_imports_from_code(code_bytes: bytes) -> List[str]:
    """从源码中提取完整的 import 语句（含关键字 import/static 与分号）。"""
    text = code_bytes.decode('utf-8', errors='ignore')
    pattern = r'^\s*import\s+(?:static\s+)?[^;]+;'
    matches = re.findall(pattern, text, flags=re.M)
    return [m.strip() for m in matches]


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

        except Exception:
            # 如果分析失败，使用默认值
            complexity = 1
            loc = len([line for line in code.split('\n') if line.strip()])
            # 尝试从代码中提取参数数量
            try:
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

        # 新增：提取当前文件的 imports
        imports = _extract_imports_from_code(code)

        stack = [(root_node, None)]  # (node, parent_class_name)

        while stack:
            node, parent_name = stack.pop()

            if node.type in ('class_declaration', 'interface_declaration', 'enum_declaration'):
                if _is_deprecated(node):
                    continue

                class_name = _get_identifier_text(node)
                if not class_name:
                    continue

                mods = _get_modifiers(node)
                abstract = _is_abstract(mods) if node.type != 'interface_declaration' else True
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

                            # 判断是否异步
                            is_async = False
                            for child in body_child.children:
                                if child.type == 'type_identifier':
                                    return_type = child.text.decode('utf-8').lower()
                                    if 'completablefuture' in return_type or 'future' in return_type:
                                        is_async = True
                                        break

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
                                'complexity': complexity,
                                'param_count': param_count,
                                'is_async': is_async,
                                'type': 'function' if _is_static(method_mods) else 'method',
                                'class_name': class_name,
                                'full_class_name': class_name,
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
                    'file': file_path,
                    'imports': imports,
                }

            for child in node.children:
                stack.append((child, parent_name))

    # 3.1 文件内候选函数过滤（硬规则）
    def _should_filter_method(self, method_info: Dict[str, Any]) -> tuple:
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

        if cc <= 15:
            return True, f"复杂度过低 (CC={cc}<=15)"

        if loc <=50:
            return True, f"行数过少 (LOC={loc}<=80)"

        return False, ""

    def _is_getter_setter(self, method_name: str) -> bool:
        """判断是否是getter/setter方法"""
        for pattern in self.getter_setter_patterns:
            if re.match(pattern, method_name):
                return True
        return False

    def _no_return_no_state_change(self, method_code: str, method_name: str) -> bool:
        """判断是否无返回值且无状态修改"""
        has_return = re.search(r'\breturn\b', method_code) is not None
        has_field_assignment = False
        lines = method_code.split('\n')
        for line in lines:
            if '=' in line and ('this.' in line or any(word in line for word in ['field', 'value', 'data'])):
                has_field_assignment = True
                break
        if not has_return and not has_field_assignment:
            excluded_names = ['main', 'run', 'execute', 'process', 'handle', 'init', 'setup', 'start']
            if method_name.lower() not in excluded_names:
                return True
        return False

    def _is_trivial_wrapper(self, method_code: str, method_name: str, loc: int) -> bool:
        """判断是否是简单包装器"""
        if loc <= 3:
            lines = [l.strip() for l in method_code.split('\n') if l.strip()]
            effective_lines = [l for l in lines if not l.startswith('//') and not l.startswith('/*')]
            if len(effective_lines) <= 2:
                important_methods = ['main', 'run', 'execute', 'process', 'handle']
                if method_name not in important_methods:
                    return True
        return False

    def _gen_test_file_path(self, file_path: str, function_name: str) -> str:
        """生成测试文件路径，测试文件直接放在包目录下，文件名为 <function_name>Tests.java"""
        if file_path.startswith(self.project_root):
            rel_path = file_path[len(self.project_root):].lstrip(os.sep)
        else:
            rel_path = file_path

        rel_path_no_ext = os.path.splitext(rel_path)[0]
        rel_path_no_ext = rel_path_no_ext.replace('/main/', '/test/')

        package_dir = os.path.dirname(rel_path_no_ext)
        if function_name and function_name[0].islower():
            function_name = function_name[0].upper() + function_name[1:]
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

    def _collect_abstract_superclasses(self, class_name: str, visited: Set[str]) -> Set[str]:
        """收集抽象父类"""
        if class_name in visited:
            return set()
        visited.add(class_name)

        cls = self.classes.get(class_name)
        if not cls:
            return set()

        abstract_supers = set()
        for super_name in cls['superclasses']:
            super_cls = self.classes.get(super_name)
            if super_cls and super_cls['abstract']:
                abstract_supers.add(super_name)
                abstract_supers.update(self._collect_abstract_superclasses(super_name, visited))
        return abstract_supers

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
                # 将文件级 imports 传递到方法对象（若存在）
                method['imports'] = cls.get('imports', [])
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
                                "loc": func.get('loc', 0),
                                "complexity": func.get('complexity', 0)
                                # 可能已有：loc, complexity, param_count 等等
                                }

                            # 如果该方法属于某个类，附带类级信息
                            if func.get('type') == 'method':
                                method_info.update({
                                    'class_name': func.get('class_name'),
                                    'full_class_name': func.get('full_class_name'),
                                    'class_constructor': func.get('class_constructor', []),
                                    'class_fields': func.get('class_fields', []),
                                })

                            # 附加 imports 信息（如果已经在 method_info 里没有，则回退到 cls 的 imports）
                            method_info['imports'] = func.get('imports', file_methods[0].get('imports', [])) if file_methods else []

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
    project_root = "projects/WePush"  # 替换为实际项目路径

    # 创建分析器实例
    analyzer = FileQualityAnalyzer(
        language="java",
        random_seed=42,  # 固定随机种子，确保结果可重复
        sampling_k=50  # 每个层级抽取50个文件
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
        output_file="wepush22.json",
        min_loc_threshold=5,
        random_seed=42
    )

    selected_methods = extractor.extract_and_select_functions()
    print(f"\n总共选择了 {len(selected_methods)} 个方法用于测试生成")

    # 打印详细报告
    # extractor.print_detailed_selection_report()

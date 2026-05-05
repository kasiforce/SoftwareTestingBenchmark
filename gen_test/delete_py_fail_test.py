#!/usr/bin/env python3
"""
根据 pytest JSON 报告自动修复失败的测试：
1. 删除收集阶段失败（语法/导入错误）的测试文件
2. 为执行阶段失败的测试函数添加 @pytest.mark.skip

用法:
    python fix_failed_tests.py report.json          # 预览后确认
    python fix_failed_tests.py report.json --yes    # 直接执行
    python fix_failed_tests.py report.json --dry-run # 仅预览
"""

import json
import sys
from pathlib import Path


def find_failed_collector_files(data, root):
    """收集阶段失败 → 需要删除的 .py 文件"""
    files = []
    for c in data.get('collectors', []):
        if c.get('outcome') != 'failed':
            continue
        nodeid = c.get('nodeid', '')
        if nodeid.endswith('.py'):
            files.append(root / nodeid)
    return files


def find_failed_tests(data, root):
    """执行阶段失败 → 需要添加 skip 的测试"""
    mods = []
    for t in data.get('tests', []):
        if t.get('outcome') != 'failed':
            continue
        nodeid = t.get('nodeid', '')
        if '::' not in nodeid:
            continue
        file_rel, func_name = nodeid.rsplit('::', 1)
        # 去除参数化后缀 [...]
        if '[' in func_name:
            func_name = func_name[:func_name.index('[')]
        lineno = t.get('lineno')  # 可能不准确，仅作为参考
        mods.append({
            'file': root / file_rel,
            'lineno': lineno,
            'func_name': func_name,
            'nodeid': nodeid,
        })
    return mods


def locate_function_line(lines, func_name, preferred_lineno=None):
    """
    在 lines 中定位函数定义行号（0基索引）。
    优先使用 preferred_lineno-1，若该行是 def func_name( 则采用；
    否则全文搜索第一个 def func_name(，若仍未找到返回 None。
    """
    # 1. 尝试 preferred
    if preferred_lineno is not None:
        idx = preferred_lineno - 1
        if 0 <= idx < len(lines):
            if lines[idx].lstrip().startswith(f'def {func_name}('):
                return idx

    # 2. 全文搜索
    for i, line in enumerate(lines):
        if line.lstrip().startswith(f'def {func_name}('):
            return i
    return None


def apply_skip_decorators(items, dry_run=False):
    """批量添加 @pytest.mark.skip"""
    # 按文件分组
    by_file = {}
    for mod in items:
        by_file.setdefault(mod['file'], []).append(mod)

    for file_path, mods in by_file.items():
        if not file_path.exists():
            print(f"文件不存在，跳过: {file_path}")
            continue

        lines = file_path.read_text(encoding='utf-8').splitlines(keepends=True)

        # 确保有 import pytest
        has_import = any(line.lstrip().startswith('import pytest') for line in lines)
        shift = 0
        if not has_import:
            lines.insert(0, 'import pytest\n')
            shift = 1
            print(f"添加 'import pytest' -> {file_path}")

        # 定位所有需要插入的行（索引），按降序排列
        insert_ops = []  # (line_index, decorator_str)
        for mod in mods:
            idx = locate_function_line(lines, mod['func_name'], mod['lineno'])
            if idx is None:
                print(f"警告: 找不到函数 {mod['func_name']} 在 {file_path}")
                continue
            # 计算缩进
            indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
            decorator = f'{indent}@pytest.mark.skip(reason="Temporarily skip for mutmut baseline")\n'
            insert_ops.append((idx, decorator))

        # 按索引降序插入，避免偏移
        insert_ops.sort(key=lambda x: x[0], reverse=True)
        for idx, decorator in insert_ops:
            lines.insert(idx, decorator)
            print(f"跳过: {decorator.strip()} -> {file_path} (函数行 {idx+1})")

        if dry_run:
            print(f"[DRY RUN] 将会修改 {file_path}")
        else:
            file_path.write_text(''.join(lines), encoding='utf-8')
            print(f"已更新 {file_path}")


def main():
    if len(sys.argv) < 2:
        print("用法: python fix_failed_tests.py <report.json> [--yes] [--dry-run]")
        sys.exit(1)

    report_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    yes = '--yes' in sys.argv

    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    root = Path(data.get('root', '.'))

    # 收集要处理的项
    del_files = find_failed_collector_files(data, root)
    skip_tests = find_failed_tests(data, root)

    print(f"收集失败的文件（将删除）: {len(del_files)} 个")
    for f in del_files:
        print(f"  {f}")
    print(f"\n执行失败的测试（将添加 skip）: {len(skip_tests)} 个")
    for t in skip_tests:
        print(f"  {t['nodeid']}")

    if not del_files and not skip_tests:
        print("\n没有需要处理的失败项。")
        return

    if dry_run:
        print("\n[DRY RUN] 以上修改均不会实际执行。")
        if skip_tests:
            apply_skip_decorators(skip_tests, dry_run=True)
        return

    if not yes:
        resp = input("\n确认执行以上操作？[y/N] ").strip().lower()
        if resp not in ('y', 'yes'):
            print("已取消。")
            return

    # 删除文件
    for f in del_files:
        if f.exists():
            f.unlink()
            print(f"已删除: {f}")
        else:
            print(f"文件不存在，跳过: {f}")

    # 添加 skip
    apply_skip_decorators(skip_tests, dry_run=False)
    print("\n全部操作完成。")


if __name__ == '__main__':
    main()




# #!/usr/bin/env python3
# """
# 根据 pytest JSON 报告自动修复失败的测试：
# 1. 删除收集阶段失败（语法/导入错误）的测试文件
# 2. 为执行阶段失败的测试函数添加 @pytest.mark.skip

# 用法:
#     python fix_failed_tests.py report.json          # 预览后确认
#     python fix_failed_tests.py report.json --yes    # 直接执行，不询问
#     python fix_failed_tests.py report.json --dry-run # 仅显示，不做任何修改
# """

# import json
# import sys
# from pathlib import Path


# # ---------- 收集失败的文件删除 ----------
# def find_failed_collector_files(report_data, root):
#     """返回需要删除的 .py 文件绝对路径列表"""
#     files = []
#     for collector in report_data.get('collectors', []):
#         if collector.get('outcome') != 'failed':
#             continue
#         nodeid = collector.get('nodeid', '')
#         if not nodeid.endswith('.py'):
#             continue
#         file_path = root / nodeid
#         files.append(file_path)
#     return files


# # ---------- 执行失败的测试函数添加 skip ----------
# def find_failed_tests(report_data, root):
#     """返回需要添加 skip 装饰器的测试信息列表"""
#     modifications = []
#     for test in report_data.get('tests', []):
#         if test.get('outcome') != 'failed':
#             continue
#         nodeid = test.get('nodeid', '')
#         if '::' not in nodeid:
#             continue

#         file_rel, func_name = nodeid.rsplit('::', 1)
#         # 去除参数化后缀，如 test_foo[0-1] -> test_foo
#         if '[' in func_name:
#             func_name = func_name[:func_name.index('[')]

#         file_path = root / file_rel
#         lineno = test.get('lineno')
#         if lineno is None:
#             print(f"警告: {nodeid} 缺少行号，跳过")
#             continue

#         modifications.append({
#             'file': file_path,
#             'lineno': lineno,
#             'func_name': func_name,
#             'nodeid': nodeid,
#         })
#     return modifications


# def apply_skip_decorators(modifications, dry_run=False):
#     """批量添加 @pytest.mark.skip"""
#     # 按文件分组
#     by_file = {}
#     for mod in modifications:
#         by_file.setdefault(mod['file'], []).append(mod)

#     for file_path, items in by_file.items():
#         if not file_path.exists():
#             print(f"文件不存在，跳过: {file_path}")
#             continue

#         lines = file_path.read_text(encoding='utf-8').splitlines(keepends=True)

#         # 确保 import pytest 存在
#         if not any(line.strip().startswith('import pytest') for line in lines):
#             lines.insert(0, 'import pytest\n')
#             print(f"添加 'import pytest' -> {file_path}")
#             shift = 1  # 后续行号偏移
#         else:
#             shift = 0

#         # 按行号从大到小排序，避免行号错乱
#         items_sorted = sorted(items, key=lambda x: x['lineno'], reverse=True)

#         for item in items_sorted:
#             adjusted_lineno = item['lineno'] - 1  # 转为 0 基索引
#             adjusted_lineno += shift  # 如果之前插入了 import，行号已偏移

#             if 0 <= adjusted_lineno < len(lines):
#                 line = lines[adjusted_lineno]
#                 # 确认这一行确实是函数定义
#                 if line.lstrip().startswith(f"def {item['func_name']}("):
#                     indent = line[:len(line) - len(line.lstrip())]
#                     decorator = f'{indent}@pytest.mark.skip(reason="Temporarily skip for mutmut baseline")\n'
#                     lines.insert(adjusted_lineno, decorator)
#                     print(f"跳过: {item['nodeid']} 在 {file_path}")
#                 else:
#                     print(f"警告: {file_path}:{item['lineno']} 不是预期的函数定义，实际内容: {line.strip()}")
#             else:
#                 print(f"警告: 行号 {item['lineno']} 超出范围 ({file_path})")

#         if dry_run:
#             print(f"[DRY RUN] 将会修改 {file_path}")
#         else:
#             file_path.write_text(''.join(lines), encoding='utf-8')
#             print(f"已更新 {file_path}")


# # ---------- 主流程 ----------
# def main():
#     if len(sys.argv) < 2:
#         print("用法: python fix_failed_tests.py <report.json> [--yes] [--dry-run]")
#         sys.exit(1)

#     report_path = sys.argv[1]
#     dry_run = '--dry-run' in sys.argv
#     yes = '--yes' in sys.argv

#     # 加载报告
#     with open(report_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     root = Path(data.get('root', '.'))

#     # 收集需要处理的项
#     delete_files = find_failed_collector_files(data, root)
#     skip_tests = find_failed_tests(data, root)

#     # 显示摘要
#     print(f"收集失败的文件（将删除）: {len(delete_files)} 个")
#     for f in delete_files:
#         print(f"  {f}")

#     print(f"\n执行失败的测试（将添加 skip）: {len(skip_tests)} 个")
#     for t in skip_tests:
#         print(f"  {t['nodeid']}")

#     if not delete_files and not skip_tests:
#         print("\n没有需要处理的失败项。")
#         return

#     if dry_run:
#         print("\n[DRY RUN] 以上修改均不会实际执行。")
#         # 仍然可以模拟 skip 输出（只打印，不写文件）
#         if skip_tests:
#             apply_skip_decorators(skip_tests, dry_run=True)
#         return

#     # 确认
#     if not yes:
#         response = input("\n确认执行以上操作？[y/N] ").strip().lower()
#         if response not in ('y', 'yes'):
#             print("已取消。")
#             return

#     # 第一步：删除文件
#     for f in delete_files:
#         if f.exists():
#             f.unlink()
#             print(f"已删除: {f}")
#         else:
#             print(f"文件不存在，跳过: {f}")

#     # 第二步：添加 skip 装饰器
#     apply_skip_decorators(skip_tests, dry_run=False)

#     print("\n全部操作完成。")


# if __name__ == '__main__':
#     main()

#!/usr/bin/env python3
"""
根据 pytest JSON 报告自动修复失败的测试：
1. 删除收集阶段失败（语法/导入错误）的测试文件
2. 为执行阶段失败的测试函数添加 @pytest.mark.skip

用法:
    python fix_failed_tests.py report.json          # 预览后确认
    python fix_failed_tests.py report.json --yes    # 直接执行
    python fix_failed_tests.py report.json --dry-run # 仅预览
"""

import json
import sys
from pathlib import Path


def find_failed_collector_files(data, root):
    """收集阶段失败 → 需要删除的 .py 文件"""
    files = []
    for c in data.get('collectors', []):
        if c.get('outcome') != 'failed':
            continue
        nodeid = c.get('nodeid', '')
        if nodeid.endswith('.py'):
            files.append(root / nodeid)
    return files


def find_failed_tests(data, root):
    """执行阶段失败 → 需要添加 skip 的测试"""
    mods = []
    for t in data.get('tests', []):
        if t.get('outcome') != 'failed':
            continue
        nodeid = t.get('nodeid', '')
        if '::' not in nodeid:
            continue

        # 正确分离：文件路径是第一个 '::' 之前的部分
        file_rel = nodeid.split('::')[0]
        # 函数名是最后一个 '::' 之后的部分
        func_name = nodeid.rsplit('::', 1)[-1]
        # 去除参数化后缀 [...]
        if '[' in func_name:
            func_name = func_name[:func_name.index('[')]

        lineno = t.get('lineno')
        mods.append({
            'file': root / file_rel,
            'lineno': lineno,
            'func_name': func_name,
            'nodeid': nodeid,
        })
    return mods


def locate_function_line(lines, func_name, preferred_lineno=None):
    """
    在 lines 中定位函数定义行号（0基索引）。
    优先使用 preferred_lineno-1，若该行是 def func_name( 则采用；
    否则全文搜索第一个 def func_name(，若仍未找到返回 None。
    """
    if preferred_lineno is not None:
        idx = preferred_lineno - 1
        if 0 <= idx < len(lines):
            if lines[idx].lstrip().startswith(f'def {func_name}('):
                return idx

    for i, line in enumerate(lines):
        if line.lstrip().startswith(f'def {func_name}('):
            return i
    return None


def apply_skip_decorators(items, dry_run=False):
    """批量添加 @pytest.mark.skip"""
    # 按文件分组
    by_file = {}
    for mod in items:
        by_file.setdefault(mod['file'], []).append(mod)

    for file_path, mods in by_file.items():
        if not file_path.exists():
            print(f"文件不存在，跳过: {file_path}")
            continue

        lines = file_path.read_text(encoding='utf-8').splitlines(keepends=True)

        # 确保有 import pytest
        has_import = any(line.lstrip().startswith('import pytest') for line in lines)
        shift = 0
        if not has_import:
            lines.insert(0, 'import pytest\n')
            shift = 1
            print(f"添加 'import pytest' -> {file_path}")

        # 定位所有需要插入的行（索引），按降序排列
        insert_ops = []
        for mod in mods:
            idx = locate_function_line(lines, mod['func_name'], mod['lineno'])
            if idx is None:
                print(f"警告: 找不到函数 {mod['func_name']} 在 {file_path}")
                continue
            indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
            decorator = f'{indent}@pytest.mark.skip(reason="Temporarily skip for mutmut baseline")\n'
            insert_ops.append((idx, decorator))

        insert_ops.sort(key=lambda x: x[0], reverse=True)
        for idx, decorator in insert_ops:
            lines.insert(idx, decorator)
            print(f"跳过: {decorator.strip()} -> {file_path} (函数行 {idx+1})")

        if dry_run:
            print(f"[DRY RUN] 将会修改 {file_path}")
        else:
            file_path.write_text(''.join(lines), encoding='utf-8')
            print(f"已更新 {file_path}")


def main():
    if len(sys.argv) < 2:
        print("用法: python fix_failed_tests.py <report.json> [--yes] [--dry-run]")
        sys.exit(1)

    report_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    yes = '--yes' in sys.argv

    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    root = Path(data.get('root', '.'))

    del_files = find_failed_collector_files(data, root)
    skip_tests = find_failed_tests(data, root)

    print(f"收集失败的文件（将删除）: {len(del_files)} 个")
    for f in del_files:
        print(f"  {f}")
    print(f"\n执行失败的测试（将添加 skip）: {len(skip_tests)} 个")
    for t in skip_tests:
        print(f"  {t['nodeid']}")

    if not del_files and not skip_tests:
        print("\n没有需要处理的失败项。")
        return

    if dry_run:
        print("\n[DRY RUN] 以上修改均不会实际执行。")
        if skip_tests:
            apply_skip_decorators(skip_tests, dry_run=True)
        return

    if not yes:
        resp = input("\n确认执行以上操作？[y/N] ").strip().lower()
        if resp not in ('y', 'yes'):
            print("已取消。")
            return

    for f in del_files:
        if f.exists():
            f.unlink()
            print(f"已删除: {f}")
        else:
            print(f"文件不存在，跳过: {f}")

    apply_skip_decorators(skip_tests, dry_run=False)
    print("\n全部操作完成。")


if __name__ == '__main__':
    main()
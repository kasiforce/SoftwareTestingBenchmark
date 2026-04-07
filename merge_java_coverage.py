import xml.etree.ElementTree as ET
import os
import sys
import json
from pathlib import Path
from collections import defaultdict

def src_file_to_file_key(src_file):
    """
    将 JSON 中的 src_file 转换为 JaCoCo XML 中的文件标识。
    例如："src/main/java/org/apache/commons/cli/help/TextHelpAppendable.java"
    转换为 "org/apache/commons/cli/help/TextHelpAppendable.java"
    """
    prefix = "src/main/java/"
    if src_file.startswith(prefix):
        return src_file[len(prefix):]
    return src_file

def load_filter_data(json_path):
    """
    从 JSON 文件中提取需要保留的文件标识和方法标识。
    返回 (file_keys_set, method_keys_set)
        file_keys_set: 需要保留的文件标识（如 "org/apache/commons/cli/help/TextHelpAppendable.java"）
        method_keys_set: 需要保留的 (file_key, method_name) 元组集合
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    file_keys = set()
    method_keys = set()

    for item in data:
        src_file = item.get('src_file')
        method_name = item.get('name')
        if src_file:
            file_key = src_file_to_file_key(src_file)
            file_keys.add(file_key)
            if method_name:
                method_keys.add((file_key, method_name))
    return file_keys, method_keys

def parse_jacoco_xml(xml_path, filter_json_path=None):
    """
    解析 JaCoCo XML 报告，提取方法级和文件级行/分支覆盖率。
    如果提供 filter_json_path，则只输出该 JSON 中指定的文件/方法覆盖率。
    返回一个字典，包含 file_coverage、function_coverage 和 summary 字段。
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 加载过滤数据（如果有）
    file_filter = None
    method_filter = None
    if filter_json_path:
        file_filter, method_filter = load_filter_data(filter_json_path)
        print(f"已加载过滤文件数: {len(file_filter)}，过滤方法数: {len(method_filter)}")

    # 存储方法级数据
    methods_data = []
    # 存储文件级行覆盖率（从<sourcefile>解析）
    file_line_coverage = {}
    # 存储文件级分支覆盖率（从<class>累加）
    file_branch_coverage = defaultdict(lambda: {'missed': 0, 'covered': 0})

    # 遍历所有package
    for package in root.findall('package'):
        package_name = package.get('name')  # 如 "org/apache/commons/cli/help"

        # --- 处理每个<class>，提取方法级数据，并累加分⽀到文件级 ---
        for cls in package.findall('class'):
            source_file = cls.get('sourcefilename')
            if source_file:
                file_key = f"{package_name}/{source_file}"  # 唯一文件标识

                # 如果设置了文件过滤，且该文件不在过滤集合中，则跳过整个类
                if file_filter is not None and file_key not in file_filter:
                    continue

                # 累加该类的分支覆盖率（用于文件级）
                branch_counter = cls.find("./counter[@type='BRANCH']")
                if branch_counter is not None:
                    file_branch_coverage[file_key]['missed'] += int(branch_counter.get('missed'))
                    file_branch_coverage[file_key]['covered'] += int(branch_counter.get('covered'))

                # 处理该类下的每个方法
                for method in cls.findall('method'):
                    method_name = method.get('name')
                    method_desc = method.get('desc')  # 方法描述，用于区分重载

                    # 如果设置了方法过滤，且 (file_key, method_name) 不在过滤集合中，则跳过
                    if method_filter is not None and (file_key, method_name) not in method_filter:
                        continue

                    # 方法行覆盖率
                    line_counter = method.find("./counter[@type='LINE']")
                    if line_counter is not None:
                        line_missed = int(line_counter.get('missed'))
                        line_covered = int(line_counter.get('covered'))
                    else:
                        line_missed = line_covered = 0

                    # 方法分支覆盖率
                    branch_counter_m = method.find("./counter[@type='BRANCH']")
                    if branch_counter_m is not None:
                        branch_missed = int(branch_counter_m.get('missed'))
                        branch_covered = int(branch_counter_m.get('covered'))
                    else:
                        branch_missed = branch_covered = 0

                    # 构建方法唯一标识（使用类名.方法名）
                    class_name = cls.get('name').replace('/', '.')
                    methods_data.append({
                        'package': package_name.replace('/', '.'),
                        'class': class_name,
                        'method': method_name,
                        'desc': method_desc,
                        'line_missed': line_missed,
                        'line_covered': line_covered,
                        'branch_missed': branch_missed,
                        'branch_covered': branch_covered
                    })

        # --- 处理<sourcefile>，获取文件级行覆盖率 ---
        for sourcefile in package.findall('sourcefile'):
            sourcefile_name = sourcefile.get('name')
            file_key = f"{package_name}/{sourcefile_name}"

            # 如果设置了文件过滤，且该文件不在过滤集合中，则跳过
            if file_filter is not None and file_key not in file_filter:
                continue

            # 统计该文件中的行覆盖
            total_lines = 0
            covered_lines = 0
            for line in sourcefile.findall('line'):
                total_lines += 1
                ci = int(line.get('ci', 0))
                if ci > 0:  # 只要该行有指令被覆盖，即视为已覆盖
                    covered_lines += 1

            file_line_coverage[file_key] = {
                'total_lines': total_lines,
                'covered_lines': covered_lines,
                'missed_lines': total_lines - covered_lines
            }

    # --- 合并文件级数据（行覆盖 + 分支覆盖） ---
    file_data = []
    all_file_keys = set(file_line_coverage.keys()) | set(file_branch_coverage.keys())
    if file_filter is not None:
        output_file_keys = file_filter & all_file_keys
    else:
        output_file_keys = all_file_keys

    for file_key in sorted(output_file_keys):
        line_info = file_line_coverage.get(file_key, {'total_lines': 0, 'covered_lines': 0, 'missed_lines': 0})
        total_lines = line_info['total_lines']
        covered_lines = line_info['covered_lines']
        missed_lines = line_info['missed_lines']

        branch_info = file_branch_coverage.get(file_key, {'missed': 0, 'covered': 0})
        branch_missed = branch_info['missed']
        branch_covered = branch_info['covered']
        total_branches = branch_missed + branch_covered

        file_data.append({
            'file': file_key,
            'line_missed': missed_lines,
            'line_covered': covered_lines,
            'total_lines': total_lines,
            'branch_missed': branch_missed,
            'branch_covered': branch_covered,
            'total_branches': total_branches
        })

    # 计算汇总统计
    method_line_total = sum(m['line_missed'] + m['line_covered'] for m in methods_data)
    method_line_covered = sum(m['line_covered'] for m in methods_data)
    method_branch_total = sum(m['branch_missed'] + m['branch_covered'] for m in methods_data)
    method_branch_covered = sum(m['branch_covered'] for m in methods_data)

    file_line_total = sum(f['total_lines'] for f in file_data)
    file_line_covered = sum(f['line_covered'] for f in file_data)
    file_branch_total = sum(f['total_branches'] for f in file_data)
    file_branch_covered = sum(f['branch_covered'] for f in file_data)

    # 构建 file_coverage 部分
    file_coverage_json = {}
    for f in file_data:
        file_coverage_json[f['file']] = {
            'total_line': f['total_lines'],
            'covered_line': f['line_covered'],
            'total_branch': f['total_branches'],
            'covered_branch': f['branch_covered']
        }

    # 构建 function_coverage 部分，使用 "class.method" 作为键
    function_coverage_json = {}
    for m in methods_data:
        key = f"{m['class']}.{m['method']}"
        function_coverage_json[key] = {
            'total_line': m['line_missed'] + m['line_covered'],
            'covered_line': m['line_covered'],
            'total_branch': m['branch_missed'] + m['branch_covered'],
            'covered_branch': m['branch_covered']
        }

    # 构建 summary 部分
    filtered_stats = {
        'file': {
            'total_lines': file_line_total,
            'covered_lines': file_line_covered,
            'total_branches': file_branch_total,
            'covered_branches': file_branch_covered
        },
        'function': {
            'total_lines': method_line_total,
            'covered_lines': method_line_covered,
            'total_branches': method_branch_total,
            'covered_branches': method_branch_covered
        }
    }

    # 组装最终 JSON
    result_json = {
        'file_coverage': file_coverage_json,
        'function_coverage': function_coverage_json,
        'summary': filtered_stats
    }

    return result_json

def merge_coverage_to_summary(cover_data, summary_path):
    """
    将 cover_data 合并到 summary_path 指向的 JSON 文件中。
    如果文件不存在，则直接写入 cover_data；
    如果存在，则进行顶层合并（cover_data 的顶层键覆盖原文件中的同名键）。
    """
    summary_path = Path(summary_path)
    if summary_path.exists():
        with open(summary_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        # 仅顶层合并：用 cover_data 中的键覆盖 existing 中同名的键
        existing.update(cover_data)
        merged = existing
    else:
        merged = cover_data

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

def list_first_level_dirs(target_dir: str = ".") -> list:
    """
    返回 target_dir 下的所有第一级子目录路径列表。
    """
    path = Path(target_dir)
    if not path.exists():
        print(f"错误：路径 '{target_dir}' 不存在。", file=sys.stderr)
        return []
    if not path.is_dir():
        print(f"错误：'{target_dir}' 不是一个目录。", file=sys.stderr)
        return []
    subdirs = [entry for entry in path.iterdir() if entry.is_dir()]
    return subdirs

if __name__ == '__main__':
    # 根目录：可从命令行参数获取，默认为当前目录
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    # 可选的全局过滤 JSON 文件
    filter_json = 'data_file.json' if Path('data_file.json').exists() else None

    # 获取所有第一级子目录
    subdirs = list_first_level_dirs(root_dir)
    if not subdirs:
        print("未找到任何子目录。")
        sys.exit(0)

    processed = 0
    for subdir in subdirs:
        xml_path = subdir / "target_jacoco.xml"
        if not xml_path.exists():
            continue

        print(f"处理目录: {subdir}")
        try:
            # 解析覆盖率
            cover_data = parse_jacoco_xml(str(xml_path), filter_json_path=filter_json)
            # 合并到 summary.json
            summary_path = subdir / "summary.json"
            merge_coverage_to_summary(cover_data, summary_path)
            print(f"  已将覆盖率数据合并到 {summary_path}")
            processed += 1
        except Exception as e:
            print(f"  处理 {xml_path} 时出错: {e}", file=sys.stderr)

    print(f"完成。共处理 {processed} 个目录。")
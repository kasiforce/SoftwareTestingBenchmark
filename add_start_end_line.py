import json
import os
import glob

def sync_from_data_file(data_file, root_dir='.', pattern='*modern-error*.json', output_suffix=None):
    """
    从 data_file.json 中读取完整的 start_line/end_line 信息，
    然后为 root_dir 下所有匹配 pattern 的 JSON 文件中的条目补充缺失的字段。
    
    参数:
        data_file: 数据源 JSON 文件路径，其中每个条目应有 src_file, code, start_line, end_line
        root_dir: 扫描根目录，默认为当前目录
        pattern: 目标文件名模式，默认为 '*modern-error*.json'
        output_suffix: 若不为 None，则生成带后缀的新文件而不覆盖原文件；若为 None，则直接覆盖原文件
    """
    # 读取数据源文件
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except Exception as e:
        print(f"读取数据源文件失败：{e}")
        return

    # 构建映射 (src_file, code) -> (start_line, end_line)
    mapping = {}
    for item in source_data:
        src_file = item.get('src_file')
        code = item.get('code')
        start_line = item.get('start_line')
        end_line = item.get('end_line')
        type1 = item.get('type')
        if src_file is not None and code is not None and type1 is not None and start_line is not None and end_line is not None:
            key = (src_file, code, type1)
            # 如果同一个 key 出现多次，可在此处处理冲突，默认保留最后一次遇到的
            mapping[key] = (start_line, end_line)

    print(f"数据源映射构建完成，共 {len(mapping)} 条记录")

    # 查找目标文件
    search_path = os.path.join(root_dir, pattern)
    json_files = glob.glob(search_path, recursive=True)
    if not json_files:
        print(f"未找到匹配 {pattern} 的文件")
        return

    print(f"找到 {len(json_files)} 个文件待处理")

    # 处理每个目标文件
    updated_total = 0
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                print(f"跳过 {file_path}：内容不是数组")
                continue

            file_updated = False
            for item in data:
                need_start = 'start_line' not in item
                need_end = 'end_line' not in item
                if need_start or need_end:
                    src_file = item.get('src_file')
                    code = item.get('code')
                    type1 = item.get('type')
                    key = (src_file, code, type1)
                    if key in mapping:
                        start_line, end_line = mapping[key]
                        if need_start:
                            item['start_line'] = start_line
                        if need_end:
                            item['end_line'] = end_line
                        file_updated = True
                        updated_total += 1

            if file_updated:
                output_path = file_path
                if output_suffix:
                    base, ext = os.path.splitext(file_path)
                    output_path = f"{base}{output_suffix}{ext}"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"已更新：{output_path}")
        except Exception as e:
            print(f"处理文件 {file_path} 时出错：{e}")

    print(f"全部处理完成，共补充了 {updated_total} 条记录")

if __name__ == '__main__':
    # 使用示例
    sync_from_data_file(
        data_file='data_file.json',          # 你的数据源文件
        root_dir='.',                         # 扫描根目录，可修改为实际路径
        pattern='*modern-error_specification_jest_CodeLlama-7b.json',        # 文件名模式
        output_suffix=None                    # 若设为 '.updated' 则生成新文件不覆盖原文件
    )
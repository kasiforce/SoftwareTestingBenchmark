import json

def merge_data(data_file_path: str, coverage_file_path: str, output_file_path: str) -> None:
    """
    将 data_file.json 中的字段合并到 coverage.json 对应的部分。

    Args:
        data_file_path: data_file.json 路径
        coverage_file_path: coverage.json 路径
        output_file_path: 输出文件路径
    """
    # 读取 JSON 文件
    with open(data_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(coverage_file_path, 'r', encoding='utf-8') as f:
        coverage = json.load(f)

    # 1. 合并 by_model
    by_model_data = data.get("by_model", {})
    for model, stats in by_model_data.items():
        if model in coverage.get("by_model", {}):
            coverage["by_model"][model].update(stats)
        else:
            print(f"警告: 模型 {model} 不存在于 coverage['by_model'] 中")

    # 2. 合并 by_model_framework (键格式为 "模型名_jest")
    framework_data = data.get("by_model_and_framework", {})
    for model, frameworks in framework_data.items():
        if "jest" in frameworks:
            jest_stats = frameworks["jest"]
            key = f"{model}_jest"
            if key in coverage.get("by_model_framework", {}):
                coverage["by_model_framework"][key].update(jest_stats)
            else:
                print(f"警告: 键 {key} 不存在于 coverage['by_model_framework'] 中")

    # 3. 合并 by_model_spec (键格式为 "模型名_True" / "模型名_False")
    spec_data = data.get("by_model_and_specification", {})
    for model, spec_types in spec_data.items():
        # 有规格说明 -> True
        if "with_specification" in spec_types:
            with_stats = spec_types["with_specification"]
            key_true = f"{model}_True"
            if key_true in coverage.get("by_model_spec", {}):
                coverage["by_model_spec"][key_true].update(with_stats)
            else:
                print(f"警告: 键 {key_true} 不存在于 coverage['by_model_spec'] 中")
        # 无规格说明 -> False
        if "without_specification" in spec_types:
            without_stats = spec_types["without_specification"]
            key_false = f"{model}_False"
            if key_false in coverage.get("by_model_spec", {}):
                coverage["by_model_spec"][key_false].update(without_stats)
            else:
                print(f"警告: 键 {key_false} 不存在于 coverage['by_model_spec'] 中")

    # 写入结果
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)
    print(f"合并完成，结果已保存至: {output_file_path}")

if __name__ == "__main__":
    merge_data("test_results/javascript/test_results.json", "test_results/javascript/aggregated_results.json", "test_results/javascript/coverage_merged.json")
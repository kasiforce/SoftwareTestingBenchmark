import json
import sys


def normalize(path):
    return path.replace("\\", "/")


def filter_function_level_mutants(
        test_results_dir,
        data_json_path,
        mutation_json_path):

    # =========================================================
    # 读取 data.json
    # =========================================================

    with open(data_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # =========================================================
    # 构建函数范围
    # =========================================================

    function_ranges = []

    for item in data:

        src_file = normalize(item["src_file"])

        start_line = item["start_line"]

        end_line = item["end_line"]

        func_name = item.get("name", "unknown")

        function_ranges.append({
            "src_file": src_file,
            "start_line": start_line,
            "end_line": end_line,
            "name": func_name
        })

    print("函数范围:")
    for x in function_ranges:
        print(
            f'{x["name"]}: '
            f'{x["src_file"]} '
            f'[{x["start_line"]}, {x["end_line"]}]'
        )

    # =========================================================
    # 读取 mutation json
    # =========================================================

    with open(mutation_json_path, "r", encoding="utf-8") as f:
        mutation_data = json.load(f)

    files = mutation_data.get("files", {})

    # =========================================================
    # 过滤 mutants
    # =========================================================

    filtered_files = {}

    total_before = 0
    total_after = 0

    for file_path, file_info in files.items():

        normalized_path = normalize(file_path)

        mutants = file_info.get("mutants", [])

        total_before += len(mutants)

        filtered_mutants = []

        for mutant in mutants:

            line = mutant["location"]["start"]["line"]

            keep = False

            for func in function_ranges:

                if func["src_file"] != normalized_path:
                    continue

                if (
                    func["start_line"]
                    <= line
                    <= func["end_line"]
                ):
                    keep = True
                    break

            if keep:
                filtered_mutants.append(mutant)

        if filtered_mutants:

            new_file_info = dict(file_info)

            new_file_info["mutants"] = filtered_mutants

            filtered_files[file_path] = new_file_info

            total_after += len(filtered_mutants)

    # =========================================================
    # 输出
    # =========================================================

    result = dict(mutation_data)

    result["files"] = filtered_files

    with open(test_results_dir + "/filtered_mutation.json", "w", encoding="utf-8") as f:

        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("===================================")
    print(f"过滤前 mutants: {total_before}")
    print(f"过滤后 mutants: {total_after}")
    print("===================================")


if __name__ == "__main__":

    if len(sys.argv) != 3:

        print(
            "python filter_function_mutants.py "
            "data.json "
            "stryker_mutation.json "
        )

        sys.exit(1)

    filter_function_level_mutants(
        sys.argv[1],
        sys.argv[2]
    )
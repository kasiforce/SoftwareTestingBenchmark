# import json
# from collections import Counter


# def count_sloc(code: str) -> int:
#     return sum(
#         1
#         for line in code.splitlines()
#         if line.strip()
#     )


# def count_loc_distribution(json_file):

#     with open(json_file, "r", encoding="utf8") as f:
#         data = json.load(f)

#     if isinstance(data, dict):
#         data = [data]

#     dist = Counter()

#     for item in data:

#         code = item.get("code", "")

#         loc = count_sloc(code)

#         dist[loc] += 1

#     return dict(sorted(dist.items()))


# dist = count_loc_distribution("dataset/nfe.json")

# print(dist)














# import json
# from collections import Counter

# import lizard


# def count_loc_distribution(json_file):

#     with open(json_file, "r", encoding="utf8") as f:
#         data = json.load(f)

#     if isinstance(data, dict):
#         data = [data]

#     dist = Counter()

#     for item in data:

#         code = item.get("code", "")
#         # language = item.get("language", "python")

#         try:

#             analysis = lizard.analyze_file.analyze_source_code(
#                 filename=f"temp.java",
#                 code=code,
#             )

#             loc = analysis.nloc

#             dist[loc] += 1

#         except Exception:
#             continue

#     return dict(sorted(dist.items()))

# print(count_loc_distribution("dataset/nfe.json"))














import json
from collections import Counter


# def extract_total_lines(data):

#     counter = Counter()

#     coverage = data.get("coverage", {})
#     functions = coverage.get("function", {})

#     for func_name, metrics in functions.items():

#         total_lines = metrics.get("total_lines")

#         if total_lines is None:
#             continue

#         counter[total_lines] += 1

#     return counter


# def load_and_stat(json_file):

#     with open(json_file, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     # 兼容单个 / list
#     if isinstance(data, dict):
#         data = [data]

#     global_counter = Counter()

#     for item in data:
#         c = extract_total_lines(item)
#         global_counter.update(c)

#     return dict(sorted(global_counter.items()))



import json
from collections import Counter


def get_bucket(total_lines: int) -> str:
    """
    将 total_lines 映射到区间
    """

    if total_lines <= 10:
        return "0-10"

    elif total_lines <= 20:
        return "11-20"

    elif total_lines <= 40:
        return "21-40"

    elif total_lines <= 80:
        return "41-80"

    else:
        return ">80"


def extract_total_lines(data):

    counter = Counter()

    # coverage = data.get("coverage", {})
    functions = data.get("function_coverage", {})

    for func_name, metrics in functions.items():

        total_lines = metrics.get("total_line")

        if total_lines is None:
            continue

        bucket = get_bucket(total_lines)

        counter[bucket] += 1

    return counter


def load_and_stat(json_file):

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 兼容单个对象 / list
    if isinstance(data, dict):
        data = [data]

    global_counter = Counter()

    for item in data:

        c = extract_total_lines(item)

        global_counter.update(c)

    # 固定输出顺序
    ordered_result = {
        "0-10": global_counter["0-10"],
        "11-20": global_counter["11-20"],
        "21-40": global_counter["21-40"],
        "41-80": global_counter["41-80"],
        ">80": global_counter[">80"],
    }

    return ordered_result


if __name__ == "__main__":

    result = load_and_stat("test_results/python/pylint/pytest_gpt5/summary_filtered.json")

    print(result)


# if __name__ == "__main__":

#     dist = load_and_stat("test_results/javascript/simple-statistics/jest_gpt4o/summary.json")

#     print(dist)
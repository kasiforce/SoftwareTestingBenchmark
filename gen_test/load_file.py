import json
import os
from argparse import ArgumentParser

def load_file(data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    file_paths = set()

    for func in data:
        # print(func)
        test_file = func.get("src_file", "")
        root = func.get("project_root", "").split('/')
        # print(root)
        if len(root) > 2 :
            test_file = os.path.join(root[-1], test_file)
            file_paths.add(test_file)
    
    return ','.join(file_paths)

if __name__ == "__main__":
    parser = ArgumentParser()
    # parser.add_argument(
    #     "--project-root",
    #     type=str,
    #     help="The root dir of project.",
    # )
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to data.",
    )
    args = parser.parse_args()

    # delete_test_files_in_test_dirs(args.project_root)
    print(load_file(args.data_path))
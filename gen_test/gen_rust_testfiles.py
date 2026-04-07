import json
import subprocess
import shutil
from pathlib import Path
from argparse import ArgumentParser

def run_cmd(cmd, cwd):

    r = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return r.returncode == 0


def cargo_check(project):

    return run_cmd(
        ["cargo", "check", "--quiet"],
        project
    )


def cargo_build(project):

    return run_cmd(
        ["cargo", "build", "--quiet"],
        project
    )


def cargo_test(project):

    return run_cmd(
        ["cargo", "test", "--quiet"],
        project
    )


def write_test(test_file, code):

    with open(test_file, "a", encoding="utf8") as f:
        f.write("\n\n")
        f.write(code)
        f.write("\n")


def remove_test(test_file, code):

    text = Path(test_file).read_text()

    text = text.replace(code, "")

    Path(test_file).write_text(text)


def rename_test_module(code, name):

    return code.replace(
        "mod tests",
        f"mod tests_{name}"
    )


def evaluate(json_file, project_root):

    data = json.load(open(json_file))

    project_root = Path(project_root)

    syntax_pass = 0
    compile_pass = 0
    test_pass = 0
    total = 0

    results = []

    print("Pre-build project (compile dependencies)...")

    cargo_build(project_root)

    for item in data:

        if item["test_generation_status"] != "success":
            continue

        total += 1

        name = item["name"]

        test_file = project_root / item["test_file"]

        test_codes = item["generated_tests"]

        if not test_codes:
            continue

        code = test_codes[0]

        code = rename_test_module(code, name)

        write_test(test_file, code)

        syntax_ok = cargo_check(project_root)

        compile_ok = False
        test_ok = False

        if syntax_ok:

            syntax_pass += 1

            compile_ok = cargo_build(project_root)

            if compile_ok:

                compile_pass += 1

                # test_ok = cargo_test(project_root)

                # if test_ok:
                #     test_pass += 1

        results.append({
            "name": name,
            "syntax_pass": syntax_ok,
            "compile_pass": compile_ok,
            # "test_pass": test_ok
        })

        remove_test(test_file, code)

        print(name, syntax_ok, compile_ok)

    summary = {
        "total": total,
        "syntax_pass": syntax_pass,
        "compile_pass": compile_pass,
        # "test_pass": test_pass,
        "syntax_pass_rate": syntax_pass / total if total else 0,
        "compile_pass_rate": compile_pass / total if total else 0,
        # "test_pass_rate": test_pass / total if total else 0,
        "details": results
    }

    return summary


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=str,
        help="The root dir of project.",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to data.",
    )
    args = parser.parse_args()

    summary = evaluate(args.data_path, args.project_root)
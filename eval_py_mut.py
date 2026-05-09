import argparse
import json
import os
import subprocess
from pathlib import Path


def _to_module_path(path_str: str) -> str:
    path = path_str.replace("\\", "/")
    if path.endswith(".py"):
        path = path[:-3]
    return path.strip("/").replace("/", ".")


def detect_target_module(data_file: str) -> str:
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return ""

    for item in data:
        src_file = item.get("src_file", "")
        if src_file.endswith(".py"):
            module = _to_module_path(src_file)
            if module:
                return module
    return ""


def detect_test_module(project_root: str) -> str:
    root = Path(project_root)
    if not root.exists():
        return ""

    ignore_tokens = {".venv", "venv", "site-packages", "node_modules", ".git", "__pycache__"}
    for py_file in root.rglob("*.py"):
        if any(token in py_file.parts for token in ignore_tokens):
            continue
        name_low = py_file.name.lower()
        if name_low.startswith("test_") or name_low.endswith("_test.py"):
            rel = py_file.relative_to(root).as_posix()
            return _to_module_path(rel)
    return ""


def run_mutpy(target: str, unit_test: str, output_file: str, project_root: str) -> int:
    cmd = [
        "mut.py",
        "--target", target,
        "--unit-test", unit_test,
        "--runner", "pytest",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        content = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    except FileNotFoundError:
        content = "skip mutpy: mut.py not found in PATH\n"
        result = None

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    return 0 if result is None else result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run mutpy in best-effort mode and save stdout.")
    parser.add_argument("--data-file", required=True, help="Path to data_file.json")
    parser.add_argument("--project-root", default=".", help="Project root for test/module discovery")
    parser.add_argument("--output", required=True, help="Output path to write mutpy stdout")
    args = parser.parse_args()

    target = detect_target_module(args.data_file)
    test_module = detect_test_module(args.project_root)

    if not target or not test_module:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("skip mutpy: target or unit-test not found\n")
        return

    run_mutpy(target=target, unit_test=test_module, output_file=args.output, project_root=args.project_root)


if __name__ == "__main__":
    main()
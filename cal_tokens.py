import json
from collections import defaultdict
from pathlib import Path

try:
    import tiktoken
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: tiktoken. Please install it first (pip install tiktoken)."
    ) from exc

BASE_DIR = Path("tests/test_gen")
OUT_FILE = Path("tests/test_gen/generated_tests_token_counts_by_model.json")
ENCODING_NAME = "o200k_base"


def model_from_filename(path: Path) -> str:
    """Extract model name from *_{model}.json filename."""
    return path.stem.rsplit("_", 1)[-1]


def main() -> None:
    encoding = tiktoken.get_encoding(ENCODING_NAME)

    grouped = defaultdict(list)
    for json_path in sorted(BASE_DIR.glob("*.json")):
        if json_path.name == OUT_FILE.name:
            continue

        model = model_from_filename(json_path)
        data = json.loads(json_path.read_text(encoding="utf-8"))

        for idx, item in enumerate(data):
            generated_tests = item.get("generated_tests", [])
            if isinstance(generated_tests, list):
                text = "\n".join(str(x) for x in generated_tests)
            elif generated_tests is None:
                text = ""
            else:
                text = str(generated_tests)

            token_count = len(encoding.encode(text))
            grouped[model].append(
                {
                    "source_file": json_path.name,
                    "item_index": idx,
                    "name": item.get("name"),
                    "generated_tests_token_count": token_count,
                }
            )

    summary = {
        model: {
            "items": items,
            "item_count": len(items),
            "total_generated_tests_tokens": sum(x["generated_tests_token_count"] for x in items),
            "avg_generated_tests_tokens": (
                sum(x["generated_tests_token_count"] for x in items) / len(items)
                if items
                else 0
            ),
        }
        for model, items in sorted(grouped.items())
    }

    OUT_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {OUT_FILE} with {len(summary)} model groups "
        f"using encoding={ENCODING_NAME}."
    )


if __name__ == "__main__":
    main()
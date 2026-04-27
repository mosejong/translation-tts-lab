import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Convert reviewed Korean-Vietnamese pairs to multilingual long format.")
    parser.add_argument("--input", nargs="+", default=["outputs/translation/review_batch_001_merged.csv"])
    parser.add_argument("--output", default="outputs/translation/multilingual_pairs.csv")
    parser.add_argument("--lang", default="vi")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = []
    for input_path in args.input:
        rows.extend(read_csv(Path(input_path)))

    output_rows = []
    seen = set()
    for row in rows:
        key = (row.get("id", ""), args.lang)
        if key in seen:
            continue
        seen.add(key)

        output_rows.append(
            {
                "id": row.get("id", ""),
                "lang": args.lang,
                "source_type": row.get("source_type", ""),
                "category": row.get("category", ""),
                "ko": row.get("easy_korean", ""),
                "target_text": row.get("human_vi", ""),
                "review_status": row.get("review_status", "pending"),
                "review_note": "",
                "tts_target": "",
            }
        )

    write_csv(Path(args.output), output_rows)
    print(f"Saved {len(output_rows)} rows to {args.output}")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "lang",
        "source_type",
        "category",
        "ko",
        "target_text",
        "review_status",
        "review_note",
        "tts_target",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

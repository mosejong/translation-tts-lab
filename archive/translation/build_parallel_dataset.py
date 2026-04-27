import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Build Korean-Vietnamese parallel dataset from reviewed rows.")
    parser.add_argument("--input", nargs="+", default=["outputs/translation/review_batch_001_merged.csv"])
    parser.add_argument("--output", default="outputs/translation/parallel_train_candidates.csv")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = []
    for input_path in args.input:
        rows.extend(read_csv(Path(input_path)))

    reviewed = []
    seen_ids = set()

    for row in rows:
        if row.get("review_status") != "reviewed":
            continue
        if row.get("id", "") in seen_ids:
            continue
        seen_ids.add(row.get("id", ""))
        reviewed.append(
            {
                "id": row.get("id", ""),
                "source_type": row.get("source_type", ""),
                "category": row.get("category", ""),
                "ko": row.get("easy_korean", ""),
                "vi": row.get("human_vi", ""),
            }
        )

    write_csv(Path(args.output), reviewed)
    print(f"Saved {len(reviewed)} reviewed pairs to {args.output}")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "source_type", "category", "ko", "vi"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Merge human Vietnamese translations into a review batch.")
    parser.add_argument("--batch", default="outputs/translation/review_batch_001.csv")
    parser.add_argument("--human", default="outputs/translation/human_translation_batch_001_partial.csv")
    parser.add_argument("--output", default="outputs/translation/review_batch_001_merged.csv")
    return parser.parse_args()


def main():
    args = parse_args()
    batch_rows = read_csv(Path(args.batch))
    human_rows = read_csv(Path(args.human))
    human_by_id = {row["id"]: row for row in human_rows}

    merged = []
    for row in batch_rows:
        human = human_by_id.get(row["id"])
        merged_row = dict(row)
        merged_row["human_vi"] = human["human_vi"] if human else ""
        merged_row["review_status"] = human.get("review_status", "") if human else "pending"
        merged.append(merged_row)

    write_csv(Path(args.output), merged)
    print(f"Saved merged file to {args.output}")
    print(f"Reviewed: {sum(1 for row in merged if row['review_status'] == 'reviewed')}")
    print(f"Pending: {sum(1 for row in merged if row['review_status'] != 'reviewed')}")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

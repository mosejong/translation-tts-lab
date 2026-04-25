import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Create an empty human translation template from a review batch.")
    parser.add_argument("--batch", default="outputs/translation/review_batch_002.csv")
    parser.add_argument("--output", default="outputs/translation/human_translation_batch_002_partial.csv")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_csv(Path(args.batch))
    template_rows = []

    for row in rows:
        template_rows.append(
            {
                "id": row.get("id", ""),
                "source_type": row.get("source_type", ""),
                "category": row.get("category", ""),
                "easy_korean": row.get("easy_korean", ""),
                "human_vi": "",
                "review_status": "pending",
            }
        )

    write_csv(Path(args.output), template_rows)
    print(f"Saved template with {len(template_rows)} rows to {args.output}")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "source_type", "category", "easy_korean", "human_vi", "review_status"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

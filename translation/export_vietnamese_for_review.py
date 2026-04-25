import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Export Vietnamese translation lines for copy/paste review.")
    parser.add_argument("--input", default="outputs/translation/nllb_v3_20.csv")
    parser.add_argument("--text-column", default="prediction_vi")
    parser.add_argument("--output", default="outputs/translation/vietnamese_only.txt")
    parser.add_argument("--review-output", default="outputs/translation/vietnamese_review.txt")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_rows(Path(args.input))

    vietnamese_lines = []
    review_lines = []

    for row in rows:
        row_id = row.get("id", "")
        source = row.get("source_text", "").strip()
        vietnamese = row.get(args.text_column, "").strip()

        vietnamese_lines.append(f"{row_id}. {vietnamese}")
        review_lines.append(f"{row_id}. KO: {source}")
        review_lines.append(f"{row_id}. VI: {vietnamese}")
        review_lines.append("")

    write_text(Path(args.output), "\n".join(vietnamese_lines) + "\n")
    write_text(Path(args.review_output), "\n".join(review_lines))

    print(f"Saved Vietnamese only file to {args.output}")
    print(f"Saved review file to {args.review_output}")


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

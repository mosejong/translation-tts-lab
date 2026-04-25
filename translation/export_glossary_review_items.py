import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Export glossary rows that need manual review.")
    parser.add_argument("--input", default="translation/term_glossary.csv")
    parser.add_argument("--output", default="outputs/translation/glossary_review_items.csv")
    parser.add_argument("--text-output", default="outputs/translation/glossary_review_items.txt")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_csv(Path(args.input))
    review_rows = [
        row
        for row in rows
        if not row.get("preferred_vi", "").strip() or "검수 필요" in row.get("note", "")
    ]

    write_csv(Path(args.output), review_rows)
    write_text(Path(args.text_output), review_rows)
    print(f"Saved {len(review_rows)} review rows to {args.output}")
    print(f"Saved text checklist to {args.text_output}")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["korean", "preferred_vi", "note"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"{index}. KO: {row.get('korean', '')}")
        lines.append(f"   VI: {row.get('preferred_vi', '')}")
        lines.append(f"   note: {row.get('note', '')}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

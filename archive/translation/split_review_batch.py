import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Split a review batch txt/csv into smaller human-friendly chunks.")
    parser.add_argument("--batch-csv", default="outputs/translation/review_batch_002.csv")
    parser.add_argument("--output-dir", default="outputs/translation/review_batch_002_parts")
    parser.add_argument("--chunk-size", type=int, default=5)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_csv(Path(args.batch_csv))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for chunk_index, start in enumerate(range(0, len(rows), args.chunk_size), start=1):
        chunk = rows[start : start + args.chunk_size]
        txt_path = output_dir / f"part_{chunk_index:02d}.txt"
        csv_path = output_dir / f"part_{chunk_index:02d}.csv"

        write_txt(txt_path, chunk, start + 1)
        write_csv(csv_path, chunk)

    print(f"Saved {len(rows)} rows into {output_dir}")


def write_txt(path, rows, start_number):
    lines = []
    for offset, row in enumerate(rows):
        number = start_number + offset
        lines.append(f"{number}. id={row.get('id', '')} / {row.get('source_type', '')} / {row.get('category', '')}")
        lines.append(f"KO: {row.get('easy_korean', '')}")
        lines.append("VI:")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows):
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

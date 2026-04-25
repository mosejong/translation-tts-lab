import argparse
import csv
from pathlib import Path

from select_review_samples import parse_id_ranges, read_csv, score_row, write_csv, write_text


def parse_args():
    parser = argparse.ArgumentParser(description="Create multiple high-value review batches.")
    parser.add_argument("--input", default="data/notice_sample_v3.csv")
    parser.add_argument("--glossary", default="translation/term_glossary.csv")
    parser.add_argument("--output-dir", default="outputs/translation")
    parser.add_argument("--start-batch", type=int, default=2)
    parser.add_argument("--batch-count", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--exclude-ids", default="1-20")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_csv(Path(args.input))
    glossary_terms = [row["korean"] for row in read_csv(Path(args.glossary))]
    used_ids = parse_id_ranges(args.exclude_ids)

    candidates = []
    for row in rows:
        if row.get("id") in used_ids:
            continue
        text = row.get("easy_korean") or row.get("original_text", "")
        score, reasons = score_row(row, text, glossary_terms)
        if score <= 0:
            continue
        candidates.append((score, reasons, row))

    candidates.sort(key=lambda item: (-item[0], int(item[2].get("id", "0"))))
    output_dir = Path(args.output_dir)

    for batch_offset in range(args.batch_count):
        batch_no = args.start_batch + batch_offset
        start = batch_offset * args.batch_size
        end = start + args.batch_size
        selected = candidates[start:end]
        if not selected:
            break

        batch_rows, review_text = build_batch(selected)
        csv_path = output_dir / f"review_batch_{batch_no:03d}.csv"
        txt_path = output_dir / f"review_batch_{batch_no:03d}.txt"
        human_path = output_dir / f"human_translation_batch_{batch_no:03d}_partial.csv"

        write_csv(csv_path, batch_rows)
        write_text(txt_path, review_text)
        write_human_template(human_path, batch_rows)

        print(f"Saved batch {batch_no:03d}: {len(batch_rows)} rows")
        print(f"  {csv_path}")
        print(f"  {txt_path}")
        print(f"  {human_path}")


def build_batch(selected):
    output_rows = []
    review_lines = []

    for index, (score, reasons, row) in enumerate(selected, start=1):
        text = row.get("easy_korean") or row.get("original_text", "")
        output_rows.append(
            {
                "batch_no": index,
                "id": row.get("id", ""),
                "source_type": row.get("source_type", ""),
                "category": row.get("category", ""),
                "easy_korean": text,
                "original_text": row.get("original_text", ""),
                "current_vietnamese": row.get("vietnamese", ""),
                "review_reason": "|".join(reasons),
            }
        )
        review_lines.append(f"{index}. id={row.get('id', '')} / {row.get('source_type', '')} / {row.get('category', '')}")
        review_lines.append(f"KO: {text}")
        review_lines.append("VI:")
        review_lines.append(f"reason: {'|'.join(reasons)}")
        review_lines.append("")

    return output_rows, "\n".join(review_lines)


def write_human_template(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "source_type", "category", "easy_korean", "human_vi", "review_status"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "id": row["id"],
                    "source_type": row["source_type"],
                    "category": row["category"],
                    "easy_korean": row["easy_korean"],
                    "human_vi": "",
                    "review_status": "pending",
                }
            )


if __name__ == "__main__":
    main()

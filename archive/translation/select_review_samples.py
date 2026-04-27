import argparse
import csv
import re
from pathlib import Path


HIGH_VALUE_CATEGORIES = {"제출", "준비물", "비용", "건강·안전", "일정"}
HIGH_VALUE_KEYWORDS = (
    "월",
    "일",
    "까지",
    "제출",
    "준비",
    "납부",
    "신청",
    "동의서",
    "조사서",
    "통학버스",
    "돌봄",
    "방과후",
    "체험학습",
    "원복",
    "하원",
    "등원",
    "응급처치",
    "투약",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Select high-value samples for translation review.")
    parser.add_argument("--input", default="data/notice_sample_v3.csv")
    parser.add_argument("--glossary", default="translation/term_glossary.csv")
    parser.add_argument("--output", default="outputs/translation/review_batch_001.csv")
    parser.add_argument("--review-output", default="outputs/translation/review_batch_001.txt")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--exclude-ids", default="1-20")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_csv(Path(args.input))
    glossary_terms = [row["korean"] for row in read_csv(Path(args.glossary))]
    exclude_ids = parse_id_ranges(args.exclude_ids)

    candidates = []
    for row in rows:
        if row.get("id") in exclude_ids:
            continue

        text = row.get("easy_korean") or row.get("original_text", "")
        score, reasons = score_row(row, text, glossary_terms)
        if score <= 0:
            continue

        candidates.append((score, reasons, row))

    candidates.sort(key=lambda item: (-item[0], int(item[2].get("id", "0"))))
    selected = candidates[: args.limit]

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

    write_csv(Path(args.output), output_rows)
    write_text(Path(args.review_output), "\n".join(review_lines))
    print(f"Saved review csv to {args.output}")
    print(f"Saved review txt to {args.review_output}")


def score_row(row, text, glossary_terms):
    score = 0
    reasons = []

    if row.get("category") in HIGH_VALUE_CATEGORIES:
        score += 2
        reasons.append(f"category:{row.get('category')}")

    matched_terms = [term for term in glossary_terms if term and term in text]
    if matched_terms:
        score += min(5, len(matched_terms))
        reasons.append("terms:" + ",".join(matched_terms[:5]))

    matched_keywords = [keyword for keyword in HIGH_VALUE_KEYWORDS if keyword in text]
    if matched_keywords:
        score += min(4, len(matched_keywords))
        reasons.append("keywords:" + ",".join(matched_keywords[:5]))

    if re.search(r"\d[\d,]*원", text):
        score += 2
        reasons.append("money")

    if not row.get("vietnamese", "").strip():
        score += 1
        reasons.append("empty_vi")

    return score, reasons


def parse_id_ranges(value):
    ids = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            ids.update(str(number) for number in range(int(start), int(end) + 1))
        else:
            ids.add(part)
    return ids


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


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

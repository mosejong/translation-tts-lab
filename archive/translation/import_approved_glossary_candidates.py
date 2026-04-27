import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Import approved glossary candidates into term_glossary.csv.")
    parser.add_argument("--candidates", default="outputs/translation/glossary_candidates_gemini.csv")
    parser.add_argument("--glossary", default="translation/term_glossary.csv")
    parser.add_argument("--output", default="translation/term_glossary.csv")
    return parser.parse_args()


def main():
    args = parse_args()
    glossary_path = Path(args.glossary)
    candidate_rows = read_csv(Path(args.candidates))
    glossary_rows = read_csv(glossary_path)
    existing_terms = {row.get("korean", "").strip() for row in glossary_rows}

    added_rows = []
    for row in candidate_rows:
        korean = row.get("korean", "").strip()
        preferred_vi = row.get("preferred_vi_suggested", "").strip()
        if row.get("review_status", "").strip().lower() != "approved":
            continue
        if not korean or not preferred_vi or korean in existing_terms:
            continue
        glossary_rows.append(
            {
                "korean": korean,
                "preferred_vi": preferred_vi,
                "note": row.get("gemini_category") or row.get("category_guess") or "기타",
            }
        )
        existing_terms.add(korean)
        added_rows.append(korean)

    write_csv(Path(args.output), glossary_rows)
    print(f"Added {len(added_rows)} approved terms to {args.output}")
    if added_rows:
        print("Added terms: " + ", ".join(added_rows))


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


if __name__ == "__main__":
    main()

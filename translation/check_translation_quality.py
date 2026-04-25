import argparse
import csv
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Flag obvious translation quality issues.")
    parser.add_argument("--input", default="outputs/translation/nllb_v3_20.csv")
    parser.add_argument("--glossary", default="translation/term_glossary.csv")
    parser.add_argument("--bad-terms", default="translation/bad_terms.csv")
    parser.add_argument("--output", default="outputs/translation/nllb_v3_20_checked.csv")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_csv(Path(args.input))
    glossary = read_csv(Path(args.glossary))
    bad_terms = read_csv(Path(args.bad_terms))

    checked_rows = []
    for row in rows:
        labels = []
        notes = []
        source_text = row.get("source_text", "")
        prediction = row.get("prediction_vi", "")

        for term in glossary:
            korean = term["korean"]
            preferred_vi = term["preferred_vi"]
            if korean in source_text and preferred_vi.lower() not in prediction.lower():
                labels.append("wrong_term")
                notes.append(f"{korean}->{preferred_vi}")

        for term in bad_terms:
            bad_vi = term["bad_vi"]
            if bad_vi.lower() in prediction.lower():
                labels.append("bad_vi_term")
                notes.append(f"{bad_vi}: {term['example_fix']}")

        checked = dict(row)
        checked["quality_label"] = "|".join(dict.fromkeys(labels)) if labels else "unchecked"
        checked["quality_note"] = "; ".join(notes)
        checked_rows.append(checked)

    write_csv(Path(args.output), checked_rows)
    print(f"Saved checked file to {args.output}")


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

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / ".." / "multicultural-ai" / "model" / "extraction" / "data" / "processed" / "v3_school_split_fixed_v2.jsonl"
DEFAULT_GLOSSARY = Path(__file__).resolve().parent / "term_glossary.csv"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "school_notice_eval_ko_20260506.csv"

TARGET_LANGS = ["vi", "en", "zh", "th", "ms", "mn", "ru", "ja"]

PRIORITY_KEYWORDS = [
    "\uc720\uce58\uc6d0\uc0dd", "\ub2f4\uc784 \uc120\uc0dd\ub2d8", "\ub2f4\uc784\uc120\uc0dd\ub2d8", "\ub2f4\uc784\uad50\uc0ac",
    "\ud604\uc7a5\uccb4\ud5d8\ud559\uc2b5", "\uccb4\ud5d8\ud559\uc2b5", "\uc804\uad50\uc0dd", "\ud559\ub144",
    "\ub4f1\uc6d0", "\ud558\uc6d0", "\ub4f1\uad50", "\ud558\uad50", "\uacb0\uc11d", "\uc9c0\uac01", "\uc870\ud1f4",
    "\uc81c\ucd9c", "\uae30\ud55c", "\uae4c\uc9c0", "\uc2e0\uccad\uc11c", "\ub3d9\uc758\uc11c", "\uc11c\uba85", "\ud68c\uc2e0",
    "\uc900\ube44\ubb3c", "\uac04\uc2dd", "\ub3c4\uc2dc\ub77d", "\ubb3c\ud1b5", "\uc6b0\uc0b0", "\ub9c8\uc2a4\ud06c",
    "\ub0a9\ubd80", "\ud658\ubd88", "\ube44\uc6a9", "\uc218\uac15\ub8cc", "\ucc38\uac00\ube44", "\uae09\uc2dd\ube44",
    "\uc77c\uc2dc", "\uc2dc\uac04", "\uc7a5\uc18c", "\ub300\uc0c1", "\ubb38\uc758", "\uc5f0\ub77d\ucc98",
    "\uac1c\uc778\uc815\ubcf4", "\ubcf4\ud638\uc790", "\uc608\ubc29\uc811\uc885", "\uae09\uc2dd", "\ubc29\uacfc\ud6c4", "\uc0c1\ub2f4",
    "\uc548\uc804\uad50\uc721", "\ud559\uad50\ud3ed\ub825", "\uac10\uc5fc\ubcd1", "\ubcf4\uac74\uc2e4",
]

NOISY_KEYWORDS = [
    "\ubc88\uc9c0", "\ud638~", "\uc544\ud30c\ud2b8", "\ud1b5\uc7a5", "\uc81c1\ubc18", "\uc81c2\ubc18", "\uc81c3\ubc18", "\uc81c4\ubc18",
    "\uac1c\uc778\uc815\ubcf4\ucc98\ub9ac\ubc29\uce68", "\uc800\uc791\uad8c", "\ud648\ud398\uc774\uc9c0 \uc774\uc6a9\uc57d\uad00",
]

FOCUS_RULES = [
    ("domain_term", ["\uc720\uce58\uc6d0\uc0dd", "\ub2f4\uc784 \uc120\uc0dd\ub2d8", "\ub2f4\uc784\uc120\uc0dd\ub2d8", "\ub2f4\uc784\uad50\uc0ac", "\ud604\uc7a5\uccb4\ud5d8\ud559\uc2b5", "\uccb4\ud5d8\ud559\uc2b5", "\uc804\uad50\uc0dd"]),
    ("schedule", ["\uc77c\uc2dc", "\uc2dc\uac04", "\uc7a5\uc18c", "\ub300\uc0c1", "\uc624\uc804", "\uc624\ud6c4", "\uae4c\uc9c0", "\ubd80\ud130", "\uae30\ud55c"]),
    ("submission", ["\uc81c\ucd9c", "\uc2e0\uccad\uc11c", "\ub3d9\uc758\uc11c", "\uc11c\uba85", "\ud68c\uc2e0", "\ucc38\uac00 \uc5ec\ubd80"]),
    ("money", ["\ub0a9\ubd80", "\ud658\ubd88", "\ube44\uc6a9", "\uc218\uac15\ub8cc", "\ucc38\uac00\ube44", "\uae09\uc2dd\ube44", "\uc6d0"]),
    ("attendance", ["\ub4f1\uc6d0", "\ud558\uc6d0", "\ub4f1\uad50", "\ud558\uad50", "\uacb0\uc11d", "\uc9c0\uac01", "\uc870\ud1f4", "\ucd9c\uacb0"]),
    ("supplies", ["\uc900\ube44\ubb3c", "\uac04\uc2dd", "\ub3c4\uc2dc\ub77d", "\ubb3c\ud1b5", "\uc6b0\uc0b0", "\ub9c8\uc2a4\ud06c", "\uc2e4\ub0b4\ud654"]),
    ("health_safety", ["\uc608\ubc29\uc811\uc885", "\uae09\uc2dd", "\uac10\uc5fc\ubcd1", "\ubcf4\uac74\uc2e4", "\ud559\uad50\ud3ed\ub825", "\uc548\uc804\uad50\uc721"]),
    ("guardian_privacy", ["\ud559\ubd80\ubaa8", "\ubcf4\ud638\uc790", "\uac1c\uc778\uc815\ubcf4", "\uc5f0\ub77d\ucc98"]),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Build a Korean source eval set for school-notice translation model comparison.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()


def main():
    args = parse_args()
    glossary = load_glossary(args.glossary)
    texts = load_texts(args.source)
    rows = select_rows(texts, glossary, args.limit)
    write_csv(args.output, rows)
    print(f"Saved {len(rows)} eval rows to {args.output}")


def load_glossary(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return [row for row in rows if row.get("korean", "").strip()]


def load_texts(path):
    texts = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            obj = json.loads(line)
            text = normalize_text(obj.get("text", ""))
            if is_usable_text(text):
                texts.append((line_no, text))
    return texts


def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()


def is_usable_text(text):
    if not (15 <= len(text) <= 220):
        return False
    if any(keyword in text for keyword in NOISY_KEYWORDS):
        return False
    hangul_count = len(re.findall(r"[\uac00-\ud7a3]", text))
    return hangul_count >= max(8, len(text) * 0.25)


def select_rows(texts, glossary, limit):
    scored = []
    for line_no, text in texts:
        terms = find_terms(text, glossary)
        priority = [keyword for keyword in PRIORITY_KEYWORDS if keyword in text]
        focus = infer_focus(text, terms, priority)
        score = len(terms) * 2 + len(priority) * 3
        if re.search(r"\d[\d,]*\s*?", text):
            score += 4
            if "money" not in focus:
                focus.append("money")
        if re.search(r"\d{1,2}:\d{2}|\d+?\s*\d+?", text):
            score += 3
            if "schedule" not in focus:
                focus.append("schedule")
        if not terms and not priority:
            continue
        scored.append((score, line_no, text, terms, priority, focus))

    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = []
    seen_text = set()
    focus_counts = defaultdict(int)
    for score, line_no, text, terms, priority, focus in scored:
        if text in seen_text:
            continue
        primary_focus = focus[0] if focus else "general"
        if focus_counts[primary_focus] >= 16 and len(selected) < limit * 0.8:
            continue
        selected.append(make_row(len(selected) + 1, line_no, text, terms, priority, focus, score))
        seen_text.add(text)
        focus_counts[primary_focus] += 1
        if len(selected) >= limit:
            break
    return selected


def find_terms(text, glossary):
    matches = []
    compact_text = text.replace(" ", "")
    for row in glossary:
        term = row["korean"].strip()
        if len(term) < 2:
            continue
        compact_term = term.replace(" ", "")
        if term in text or (" " in term and compact_term in compact_text):
            matches.append(term)
    matches.sort(key=lambda value: (-len(value), value))
    return matches[:12]


def infer_focus(text, terms, priority):
    haystack = " ".join([text, *terms, *priority])
    focus = []
    for label, keywords in FOCUS_RULES:
        if any(keyword in haystack for keyword in keywords):
            focus.append(label)
    return focus or ["general"]


def make_row(row_no, line_no, text, terms, priority, focus, score):
    row = {
        "eval_id": f"SCHOOL-KO-{row_no:03d}",
        "source_file": "v3_school_split_fixed_v2.jsonl",
        "source_line": line_no,
        "text_ko": text,
        "char_len": len(text),
        "eval_focus": ";".join(focus),
        "matched_terms": ";".join(terms),
        "priority_keywords": ";".join(priority),
        "selection_score": score,
        "review_status": "needs_reference_translation",
    }
    for lang in TARGET_LANGS:
        row[f"reference_{lang}"] = ""
    return row


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "eval_id", "source_file", "source_line", "text_ko", "char_len",
        "eval_focus", "matched_terms", "priority_keywords", "selection_score", "review_status",
        *[f"reference_{lang}" for lang in TARGET_LANGS],
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

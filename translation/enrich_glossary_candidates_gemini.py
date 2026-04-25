import argparse
import csv
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def parse_args():
    parser = argparse.ArgumentParser(description="Suggest Vietnamese glossary entries with Gemini.")
    parser.add_argument("--input", default="outputs/translation/glossary_candidates.csv")
    parser.add_argument("--output", default="outputs/translation/glossary_candidates_gemini.csv")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--api-key-env", default="GEMINI_API_KEY")
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        raise RuntimeError(f"Set {args.api_key_env} before running this script.")

    rows = read_csv(Path(args.input))
    rows = [row for row in rows if row.get("is_registered") != "Y"]
    if args.limit > 0:
        rows = rows[: args.limit]

    enriched_rows = []
    for row in rows:
        suggestion = request_suggestion(row, api_key, args.model)
        enriched_rows.append(
            {
                **row,
                "preferred_vi_suggested": suggestion.get("preferred_vi", ""),
                "gemini_category": suggestion.get("category", ""),
                "gemini_note": suggestion.get("note", ""),
                "review_status": "pending",
            }
        )

    write_csv(Path(args.output), enriched_rows)
    print(f"Saved {len(enriched_rows)} Gemini-enriched rows to {args.output}")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def request_suggestion(row, api_key, model):
    prompt = build_prompt(row)
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=model),
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API failed: HTTP {error.code} {detail}") from error

    text = extract_text(payload)
    return parse_json_object(text)


def build_prompt(row):
    return f"""
You are helping build a Korean-to-Vietnamese glossary for Korean school and kindergarten notices.

Return only JSON with these keys:
- preferred_vi: concise Vietnamese term suitable for parents
- category: one of 일정, 준비물, 제출, 비용, 건강·안전, 기타
- note: short Korean note for a human reviewer

Korean term: {row.get("korean", "")}
Category guess: {row.get("category_guess", "")}
Source sentence: {row.get("source_sentence", "")}
Matched existing glossary terms: {row.get("matched_glossary_term", "")}
""".strip()


def extract_text(payload):
    candidates = payload.get("candidates", [])
    if not candidates:
        return "{}"
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(part.get("text", "") for part in parts)


def parse_json_object(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {"preferred_vi": "", "category": "", "note": f"JSON 파싱 실패: {text[:120]}"}
    return value if isinstance(value, dict) else {"preferred_vi": "", "category": "", "note": "JSON 객체 아님"}


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "korean",
        "category_guess",
        "source_sentence",
        "is_registered",
        "matched_glossary_term",
        "note",
        "preferred_vi_suggested",
        "gemini_category",
        "gemini_note",
        "review_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

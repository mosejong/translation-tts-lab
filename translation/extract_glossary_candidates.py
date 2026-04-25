import argparse
import csv
import re
from pathlib import Path


DEFAULT_TEXT_COLUMNS = ("easy_korean", "original_text")
CATEGORY_RULES = {
    "일정": (
        "일",
        "날짜",
        "기간",
        "기한",
        "마감",
        "행사",
        "수업",
        "체험학습",
        "상담",
        "시험",
        "총회",
        "수련회",
        "종업식",
        "신체검사",
    ),
    "준비물": (
        "준비",
        "지참",
        "가져",
        "색종이",
        "풀",
        "가위",
        "실내화",
        "체육복",
        "물병",
        "돗자리",
        "네임펜",
        "크레파스",
    ),
    "제출": (
        "제출",
        "회신",
        "동의",
        "신청",
        "확인서",
        "참가 여부",
        "불참",
        "서류",
        "서명",
    ),
    "비용": (
        "비용",
        "비",
        "원",
        "납부",
        "입금",
        "교육비",
        "체험학습비",
        "급식비",
        "수업비",
    ),
    "건강·안전": (
        "건강",
        "안전",
        "예방",
        "독감",
        "알레르기",
        "감염병",
        "마스크",
        "손 소독제",
        "응급",
        "생활지도",
    ),
}
PARTICLES = (
    "으로부터",
    "으로써",
    "으로서",
    "에게서",
    "까지",
    "부터",
    "에게",
    "께서",
    "으로",
    "에서",
    "에는",
    "보다",
    "처럼",
    "만큼",
    "라도",
    "이나",
    "이나마",
    "하고",
    "이며",
    "이고",
    "와",
    "과",
    "을",
    "를",
    "은",
    "는",
    "이",
    "가",
    "에",
    "의",
    "도",
    "만",
    "로",
)
STOPWORDS = {
    "주세요",
    "합니다",
    "있습니다",
    "됩니다",
    "보내",
    "내",
    "써",
    "알려",
    "참여",
    "확인",
    "같이",
    "꼭",
    "때",
    "날",
    "전",
    "후",
    "다음",
    "매월",
    "오전",
    "오후",
    "학교",
    "학생",
    "학부모",
}
NOUN_SUFFIXES = (
    "가정통신문",
    "안내문",
    "동의서",
    "신청서",
    "확인서",
    "조사서",
    "의뢰서",
    "검사",
    "훈련",
    "교육",
    "상담",
    "총회",
    "수련회",
    "체험학습",
    "학습",
    "수업",
    "행사",
    "비",
    "료",
    "비용",
    "준비물",
    "물병",
    "마스크",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Extract school glossary candidates from Korean notices.")
    parser.add_argument("--input", default="data/notice_sample_v3.csv")
    parser.add_argument("--glossary", default="translation/term_glossary.csv")
    parser.add_argument("--output", default="outputs/translation/glossary_candidates.csv")
    parser.add_argument(
        "--text-columns",
        default=",".join(DEFAULT_TEXT_COLUMNS),
        help="Comma-separated CSV text columns. Ignored for txt input.",
    )
    parser.add_argument("--include-registered", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    glossary_terms = read_glossary_terms(Path(args.glossary))
    text_columns = [column.strip() for column in args.text_columns.split(",") if column.strip()]
    source_rows = read_source_rows(input_path, text_columns)

    output_rows = extract_rows(source_rows, glossary_terms, include_registered=args.include_registered)
    write_csv(Path(args.output), output_rows)
    print(f"Saved {len(output_rows)} glossary candidate rows to {args.output}")


def read_glossary_terms(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            row.get("korean", "").strip()
            for row in csv.DictReader(file)
            if row.get("korean", "").strip()
        }


def read_source_rows(path, text_columns):
    if path.suffix.lower() == ".txt":
        return [
            {"source_sentence": line.strip(), "keyword_text": ""}
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    source_rows = []
    for row in rows:
        texts = [row.get(column, "").strip() for column in text_columns if row.get(column, "").strip()]
        keyword_text = row.get("keywords", "")
        for text in dict.fromkeys(texts):
            source_rows.append({"source_sentence": text, "keyword_text": keyword_text})
    return source_rows


def extract_rows(source_rows, glossary_terms, include_registered=False):
    seen = set()
    output_rows = []

    for row in source_rows:
        sentence = row["source_sentence"]
        matched_terms = find_registered_terms(sentence, glossary_terms)
        candidates = extract_candidates(sentence, row.get("keyword_text", ""))

        if include_registered:
            candidates.update(matched_terms)

        for candidate in sorted(candidates):
            is_registered = candidate in glossary_terms
            if is_registered and not include_registered:
                continue

            key = candidate
            if key in seen:
                continue
            seen.add(key)

            output_rows.append(
                {
                    "korean": candidate,
                    "category_guess": guess_category(candidate, sentence),
                    "source_sentence": sentence,
                    "is_registered": "Y" if is_registered else "N",
                    "matched_glossary_term": "; ".join(matched_terms),
                    "note": "기존 사전 용어" if is_registered else "preferred_vi 입력 필요",
                }
            )

    return output_rows


def find_registered_terms(sentence, glossary_terms):
    return sorted(
        (term for term in glossary_terms if term and term in sentence),
        key=lambda term: (-len(term), term),
    )


def extract_candidates(sentence, keyword_text):
    candidates = set()

    for keyword in re.split(r"[|,;/\s]+", keyword_text):
        add_candidate(candidates, keyword)

    tokens = [strip_particle(token) for token in re.findall(r"[가-힣A-Za-z0-9]+", sentence)]
    tokens = [token for token in tokens if is_candidate_token(token)]

    for token in tokens:
        if is_high_value_token(token):
            add_candidate(candidates, token)

    for size in (2, 3):
        for index in range(0, max(0, len(tokens) - size + 1)):
            phrase = " ".join(tokens[index : index + size])
            compact = "".join(tokens[index : index + size])
            if looks_like_noun_phrase(phrase):
                add_candidate(candidates, phrase)
            if looks_like_noun_phrase(compact):
                add_candidate(candidates, compact)

    return candidates


def strip_particle(token):
    for particle in sorted(PARTICLES, key=len, reverse=True):
        if token.endswith(particle) and len(token) > len(particle) + 1:
            return token[: -len(particle)]
    return token


def is_candidate_token(token):
    if len(token) < 2:
        return False
    if token in STOPWORDS:
        return False
    if re.fullmatch(r"\d+", token):
        return False
    return bool(re.search(r"[가-힣]", token))


def add_candidate(candidates, value):
    value = normalize_candidate(value)
    if not value or len(value.replace(" ", "")) < 2:
        return
    if value in STOPWORDS:
        return
    candidates.add(value)


def normalize_candidate(value):
    value = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return strip_particle(value)


def looks_like_noun_phrase(value):
    compact = value.replace(" ", "")
    if len(compact) < 3:
        return False
    return any(compact.endswith(suffix) or suffix in compact for suffix in NOUN_SUFFIXES)


def is_high_value_token(value):
    compact = value.replace(" ", "")
    if any(compact.endswith(suffix) or suffix in compact for suffix in NOUN_SUFFIXES):
        return True
    return any(keyword in compact for keywords in CATEGORY_RULES.values() for keyword in keywords)


def guess_category(candidate, sentence):
    text = f"{candidate} {sentence}"
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "기타"


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "korean",
        "category_guess",
        "source_sentence",
        "is_registered",
        "matched_glossary_term",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

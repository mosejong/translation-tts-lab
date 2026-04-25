import argparse
import csv
import json
import re
from pathlib import Path

import torch
from scipy.io.wavfile import write as write_wav
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, VitsModel


TRANSLATION_MODEL = "facebook/nllb-200-distilled-600M"
TTS_MODEL = "facebook/mms-tts-vie"
SOURCE_LANG = "kor_Hang"
TARGET_LANG = "vie_Latn"
DEFAULT_CATEGORIES = ("일정", "준비물", "제출", "비용", "건강·안전", "기타")
CATEGORY_RULES = {
    "일정": ("일", "월", "날짜", "기간", "기한", "마감", "행사", "수업", "체험학습", "상담", "시험", "총회", "수련회", "종업식", "신체검사"),
    "준비물": ("준비", "지참", "가져", "색종이", "풀", "가위", "실내화", "체육복", "물병", "돗자리", "네임펜", "크레파스"),
    "제출": ("제출", "내 주세요", "회신", "동의", "신청", "확인서", "참가 여부", "불참", "서류", "서명"),
    "비용": ("비용", "비", "원", "납부", "입금", "교육비", "체험학습비", "급식비", "수업비"),
    "건강·안전": ("건강", "안전", "예방", "독감", "알레르기", "감염병", "마스크", "손 소독제", "응급", "생활지도"),
}
EASY_REPLACEMENTS = {
    "실시됩니다": "있습니다",
    "참여합니다": "참여합니다",
    "참여해 주시기 바랍니다": "참여해 주세요",
    "준비해 주시기 바랍니다": "준비해 주세요",
    "제출해 주시기 바랍니다": "내 주세요",
    "납부해 주시기 바랍니다": "내 주세요",
    "등원해 주세요": "등원해 주세요",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run one end-to-end MVP demo pipeline.")
    parser.add_argument("--input", default="data/notice_sample_v3.csv")
    parser.add_argument("--row-id", default="")
    parser.add_argument("--glossary", default="translation/term_glossary.csv")
    parser.add_argument("--output-dir", default="outputs/mvp")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--skip-tts", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    device = resolve_device(args.device)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = read_source(Path(args.input), args.row_id)
    glossary = read_glossary(Path(args.glossary))

    baseline = build_baseline(source, glossary)
    easy_ko_text = build_easy_korean(source, baseline)
    vi_text = translate(easy_ko_text, device, args.max_length)
    glossary_hits = find_glossary_hits(easy_ko_text, glossary)
    glossary_check_rows = build_glossary_check_rows(easy_ko_text, vi_text, glossary_hits)
    quality_label, quality_note = summarize_quality(glossary_check_rows)

    wav_path = ""
    if not args.skip_tts:
        wav_path = str(output_dir / "06_tts_output.wav")
        try:
            generate_tts(vi_text, Path(wav_path), device)
        except Exception as error:
            wav_path = ""
            (output_dir / "tts_error.txt").write_text(str(error) + "\n", encoding="utf-8")

    (output_dir / "01_input_notice.txt").write_text(source["original_text"] + "\n", encoding="utf-8")
    write_json(output_dir / "02_baseline_result.json", baseline)
    (output_dir / "03_easy_ko.txt").write_text(easy_ko_text + "\n", encoding="utf-8")
    (output_dir / "04_vi_translation.txt").write_text(vi_text + "\n", encoding="utf-8")
    write_glossary_check(output_dir / "05_glossary_check.csv", glossary_check_rows)
    write_mvp_csv(
        output_dir / "mvp_result.csv",
        {
            "source_text": source["original_text"],
            "category": baseline["category"],
            "keywords": "|".join(baseline["keywords"]),
            "easy_ko_text": easy_ko_text,
            "vi_text": vi_text,
            "glossary_hits": "; ".join(f"{item['korean']}->{item['preferred_vi']}" for item in glossary_hits),
            "quality_label": quality_label,
            "quality_note": quality_note,
            "tts_path": wav_path,
        },
    )

    print(f"Saved MVP outputs to {output_dir}")


def resolve_device(device):
    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available. Falling back to CPU.")
        return "cpu"
    return device


def read_source(path, row_id):
    if path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8-sig").strip()
        return {
            "id": "txt",
            "original_text": text,
            "easy_korean": "",
            "category": "",
            "keywords": "",
            "source_type": "",
        }

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"No rows found in {path}")
    if row_id:
        for row in rows:
            if row.get("id") == row_id:
                return row
        raise ValueError(f"row id {row_id} was not found in {path}")
    return rows[0]


def read_glossary(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [
            row
            for row in csv.DictReader(file)
            if row.get("korean", "").strip() and row.get("preferred_vi", "").strip()
        ]


def build_baseline(source, glossary):
    original_text = source.get("original_text", "").strip()
    keywords = parse_keywords(source.get("keywords", ""))
    glossary_hits = find_glossary_hits(original_text, glossary)
    category = source.get("category", "").strip()
    if category not in DEFAULT_CATEGORIES:
        category = guess_category(original_text)

    return {
        "id": source.get("id", ""),
        "source_type": source.get("source_type", ""),
        "original_text": original_text,
        "category": category,
        "keywords": keywords,
        "glossary_hits": glossary_hits,
        "action_required": source.get("action_required", ""),
    }


def parse_keywords(value):
    return [item.strip() for item in re.split(r"[|,;/]+", value or "") if item.strip()]


def guess_category(text):
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "기타"


def build_easy_korean(source, baseline):
    if source.get("easy_korean", "").strip():
        return source["easy_korean"].strip()

    text = baseline["original_text"]
    for old, new in EASY_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    sentences = [part.strip() for part in re.split(r"[.!?。]+", text) if part.strip()]
    return "\n".join(sentences) if sentences else text


def translate(text, device, max_length):
    tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL, src_lang=SOURCE_LANG)
    model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL).to(device)
    model.eval()
    target_lang_id = tokenizer.convert_tokens_to_ids(TARGET_LANG)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length).to(device)
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=max_length,
            num_beams=4,
        )
    return tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0]


def find_glossary_hits(text, glossary):
    return [
        {"korean": row["korean"], "preferred_vi": row["preferred_vi"]}
        for row in glossary
        if row["korean"] in text
    ]


def check_quality(vi_text, glossary_hits):
    rows = build_glossary_check_rows("", vi_text, glossary_hits)
    return summarize_quality(rows)


def build_glossary_check_rows(input_text, vi_text, glossary_hits):
    if not glossary_hits:
        return [
            {
                "korean_term": "",
                "preferred_vi": "",
                "found_in_input": "N",
                "found_in_translation": "N",
                "quality_label": "unchecked",
                "note": "입력문에서 사전 용어가 감지되지 않아 자동 판단 불가",
            }
        ]

    rows = []
    for item in glossary_hits:
        found_in_input = item["korean"] in input_text if input_text else True
        found_in_translation = item["preferred_vi"].lower() in vi_text.lower()
        rows.append(
            {
                "korean_term": item["korean"],
                "preferred_vi": item["preferred_vi"],
                "found_in_input": "Y" if found_in_input else "N",
                "found_in_translation": "Y" if found_in_translation else "N",
                "quality_label": "ok" if found_in_translation else "missing_term",
                "note": "권장 번역어 반영" if found_in_translation else "권장 번역어 미반영, 사람 검수 필요",
            }
        )
    return rows


def summarize_quality(glossary_check_rows):
    labels = [row["quality_label"] for row in glossary_check_rows]
    if "missing_term" in labels:
        notes = [
            f"{row['korean_term']}->{row['preferred_vi']}"
            for row in glossary_check_rows
            if row["quality_label"] == "missing_term"
        ]
        return "review_needed", "; ".join(notes)
    if labels == ["unchecked"]:
        return "unchecked", glossary_check_rows[0]["note"]
    return "ok", ""


def generate_tts(text, wav_path, device):
    tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL)
    model = VitsModel.from_pretrained(TTS_MODEL).to(device)
    model.eval()
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model(**inputs).waveform
    waveform = output.squeeze().detach().cpu().numpy()
    write_wav(wav_path, model.config.sampling_rate, waveform)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_glossary_check(path, rows):
    fieldnames = [
        "korean_term",
        "preferred_vi",
        "found_in_input",
        "found_in_translation",
        "quality_label",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_mvp_csv(path, row):
    fieldnames = [
        "source_text",
        "category",
        "keywords",
        "easy_ko_text",
        "vi_text",
        "glossary_hits",
        "quality_label",
        "quality_note",
        "tts_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    main()

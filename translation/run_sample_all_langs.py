"""
샘플 가정통신문을 8개 언어로 번역하고 용어사전 적중 여부를 확인.

사용법:
    python run_sample_all_langs.py
    python run_sample_all_langs.py --text-file my_notice.txt
"""
import argparse
import sys
import io
import time
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from languages import LANGUAGES
from run_mvp_pipeline import read_glossary, find_glossary_hits, inject_glossary_terms, build_glossary_check_rows, summarize_quality

# ── 샘플 텍스트 ────────────────────────────────────────────────
SAMPLE_TEXT = """\
2026학년도 3학년 현장체험학습 안내

안녕하세요, 학부모님. 따뜻한 봄날씨에 아이들이 학교생활을 즐겁게
하고 있습니다. 언제나 학교 교육에 관심과 협조를 보내주셔서 진심으로
감사드립니다. 우리 아이들이 자연 속에서 다양한 경험을 쌓을 수 있도록
이번 현장체험학습을 아래와 같이 실시하오니 안내드립니다.

■ 체험학습 일시: 2026년 5월 14일(수) 오전 9시 출발
■ 장소: 서울숲 생태체험관
■ 대상: 3학년 전체 학생
■ 이동수단: 전세버스 이용 (학교 정문 앞 탑승)
■ 준비물: 도시락, 물통, 돗자리, 편한 운동화, 여벌 옷
■ 참가비: 15,000원 (5월 9일(금)까지 스쿨뱅킹으로 납부)
■ 제출 서류: 체험학습 동의서를 5월 9일(금)까지 담임교사에게 제출

봄소풍은 아이들에게 소중한 추억이 됩니다. 서울숲은 자연생태를
직접 관찰할 수 있는 훌륭한 교육 공간으로, 선생님들도 매우 기대하고
있습니다. 날씨가 흐릴 경우 우산이나 우비를 별도로 챙겨주시면 좋겠습니다.

귀중품은 분실 위험이 있으니 가져오지 않도록 지도 부탁드립니다.
아이들이 안전하고 즐거운 하루를 보낼 수 있도록 가정에서도 많은 응원
부탁드립니다. 감사합니다.

2026년 4월 28일
갈산초등학교 3학년 담임 일동
"""

NLLB_MODEL = "facebook/nllb-200-distilled-600M"
SOURCE_LANG = "kor_Hang"
GLOSSARY_PATH = Path(__file__).parent / "term_glossary.csv"
LANGS = [k for k in LANGUAGES if k != "easy_ko"]


def load_model():
    print(f"[모델 로딩] {NLLB_MODEL} ...")
    tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL, src_lang=SOURCE_LANG)
    model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
    model.eval()
    print("[모델 로딩 완료]\n")
    return tokenizer, model


def translate_chunks(text: str, nllb_code: str, tokenizer, model,
                     max_input=384, max_output=512) -> str:
    import re
    sentences = re.split(r"(?<=[.!?。])\s+|\n", text.strip())
    chunks, current = [], []
    cur_len = 0
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        toks = len(tokenizer.encode(sent))
        if cur_len + toks > max_input and current:
            chunks.append(" ".join(current))
            current, cur_len = [], 0
        current.append(sent)
        cur_len += toks
    if current:
        chunks.append(" ".join(current))

    target_id = tokenizer.convert_tokens_to_ids(nllb_code)
    outputs = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=max_input)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                forced_bos_token_id=target_id,
                max_length=max_output,
                num_beams=4,
                no_repeat_ngram_size=3,
                repetition_penalty=1.3,
                early_stopping=True,
            )
        outputs.append(tokenizer.batch_decode(out, skip_special_tokens=True)[0])
    return "\n".join(outputs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", default="", help="번역할 텍스트 파일 경로 (없으면 내장 샘플 사용)")
    parser.add_argument("--langs", nargs="*", default=LANGS, help="번역할 언어 목록")
    args = parser.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else SAMPLE_TEXT

    glossary = []
    if GLOSSARY_PATH.exists():
        glossary = read_glossary(GLOSSARY_PATH)
        print(f"[사전 로딩] {len(glossary)}개 용어\n")

    tokenizer, model = load_model()

    results = []
    for lang in args.langs:
        cfg = LANGUAGES.get(lang)
        if not cfg or not cfg["nllb_code"]:
            continue
        label = cfg["label"]
        nllb_code = cfg["nllb_code"]

        print(f"▶ {lang} ({label}) 번역 중...", end=" ", flush=True)
        t0 = time.time()
        hits = find_glossary_hits(text, glossary, lang)
        injected_text = inject_glossary_terms(text, hits) if hits else text
        translated = translate_chunks(injected_text, nllb_code, tokenizer, model)
        elapsed = time.time() - t0
        print(f"{elapsed:.1f}초  (사전 주입 {len(hits)}개)")

        rows = build_glossary_check_rows(text, translated, hits)
        label_q, note_q = summarize_quality(rows)

        missing = [r for r in rows if r.get("quality_label") == "missing_term"]

        results.append({
            "lang": lang,
            "label": label,
            "translation": translated,
            "quality": label_q,
            "missing": missing,
            "elapsed": elapsed,
        })

    # ── 결과 출력 ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("번역 결과 요약")
    print("=" * 60)
    for r in results:
        print(f"\n[{r['lang']}] {r['label']}  ({r['elapsed']:.1f}초)  품질: {r['quality']}")
        print("-" * 50)
        print(r["translation"][:500] + ("..." if len(r["translation"]) > 500 else ""))
        if r["missing"]:
            print(f"\n  ⚠ 누락 용어: {', '.join(x['korean_term'] + '->' + x['preferred_term'] for x in r['missing'])}")

    # ── 파일 저장 ────────────────────────────────────────────────
    out_dir = Path(__file__).parent / "outputs" / "sample_all_langs"
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in results:
        (out_dir / f"{r['lang']}.txt").write_text(r["translation"], encoding="utf-8")

    summary_lines = ["# 샘플 전언어 번역 결과\n"]
    for r in results:
        summary_lines += [
            f"## {r['lang']} ({r['label']})  {r['elapsed']:.1f}초  품질: {r['quality']}",
            "",
            r["translation"],
            "",
        ]
        if r["missing"]:
            summary_lines += [
                "**누락 용어:** " + ", ".join(f"`{x['korean_term']}→{x['preferred_term']}`" for x in r["missing"]),
                "",
            ]
    (out_dir / "summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\n[저장] {out_dir}")


if __name__ == "__main__":
    main()

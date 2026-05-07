"""Expanded template translation experiment for SchoolBridge notices.

Runs the same NLLB / direct-replace / template comparison on a wider set of
school-notice action sentences. Keeps the original experiment file intact.

Outputs:
    outputs/template_translation_compare_expanded.csv
    outputs/template_translation_compare_expanded.md
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import template_translation_experiment as base

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs"

EXPANDED_SAMPLES: list[tuple[str, list[str]]] = [
    ("대회에 나가면 도화지와 색칠 도구를 준비해 주세요", ["giấy vẽ", "đồ dùng tô màu"]),
    ("유성매직과 사인펜을 준비해 주세요", ["bút dạ dầu", "bút lông"]),
    ("풍선과 찰흙을 가져오세요", ["bóng bay", "đất sét"]),
    ("실내화와 물통을 챙겨 주세요", ["giày trong nhà", "bình nước"]),
    ("수채화 물감과 붓을 준비해 주세요", ["màu nước", "cọ vẽ"]),
    ("전교생은 체육복과 실내화를 지참해 주세요", ["quần áo thể dục", "giày trong nhà"]),
    ("받아쓰기 공책과 클리어 화일을 제출해 주세요", ["vở chính tả", "túi đựng tài liệu"]),
    ("물감과 붓, 도화지를 담임선생님께 제출해 주세요", ["màu vẽ", "cọ vẽ", "giấy vẽ"]),
    ("금요일까지 참가 동의서를 담임선생님께 제출해 주세요", ["giấy đồng ý tham gia"]),
    ("스쿨뱅킹 계좌로 체험학습비를 납부해 주세요", ["tài khoản School Banking", "phí học tập trải nghiệm"]),
    ("발열 또는 기침 증상이 있으면 등교하지 마세요", ["sốt", "ho", "đi học"]),
    ("간식과 물통을 가져오세요", ["đồ ăn nhẹ", "bình nước"]),
    ("우산과 여벌 옷을 준비해 주세요", ["cái ô", "quần áo dự phòng"]),
    ("학부모 상담 신청서를 제출해 주세요", ["đơn đăng ký tư vấn phụ huynh"]),
    ("체육대회 당일에는 운동화와 물통을 지참해 주세요", ["giày thể thao", "bình nước"]),
    ("현장체험학습비 15000원을 납부해 주세요", ["phí học tập trải nghiệm", "15000원"]),
    ("도서관 봉사활동에 참여해 주세요", ["hoạt động tình nguyện thư viện"]),
    ("방과후학교 수강신청서를 제출해 주세요", ["đơn đăng ký lớp học sau giờ học"]),
    ("마스크와 개인 물병을 준비해 주세요", ["khẩu trang", "bình nước cá nhân"]),
    ("급식비 미납 금액을 납부해 주세요", ["tiền ăn ở trường chưa thanh toán"]),
]

EXTRA_ITEM_GLOSSARY_VI = {
    "참가 동의서": "giấy đồng ý tham gia",
    "스쿨뱅킹 계좌": "tài khoản School Banking",
    "체험학습비": "phí học tập trải nghiệm",
    "발열": "sốt",
    "기침": "ho",
    "등교": "đi học",
    "간식": "đồ ăn nhẹ",
    "우산": "cái ô",
    "여벌 옷": "quần áo dự phòng",
    "학부모 상담 신청서": "đơn đăng ký tư vấn phụ huynh",
    "운동화": "giày thể thao",
    "현장체험학습비": "phí học tập trải nghiệm",
    "도서관 봉사활동": "hoạt động tình nguyện thư viện",
    "방과후학교 수강신청서": "đơn đăng ký lớp học sau giờ học",
    "마스크": "khẩu trang",
    "개인 물병": "bình nước cá nhân",
    "급식비 미납 금액": "tiền ăn ở trường chưa thanh toán",
    "15000원": "15000원",
}

EXTRA_TYPES = {
    "avoid": ["하지 마세요", "하지 않습니다", "금지"],
}

EXTRA_TEMPLATES_VI = {
    "avoid": "Vui lòng không {items}.",
}


def classify_sentence(text: str) -> str:
    for stype, keywords in EXTRA_TYPES.items():
        if any(kw in text for kw in keywords):
            return stype
    return base.classify_sentence(text)


def build_from_template(stype: str, items, lang: str, audience=None, recipient=None):
    if stype == "avoid" and items and lang == "vi":
        return EXTRA_TEMPLATES_VI[stype].format(
            items=base.join_translated_items([vi for _, vi in items], lang)
        )
    return base.build_from_template(stype, items, lang, audience, recipient)


def write_outputs(rows: list[dict], totals: dict, times: dict, device: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    csv_path = OUT_DIR / "template_translation_compare_expanded.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path = OUT_DIR / "template_translation_compare_expanded.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Expanded Template-Based Translation Experiment\n\n")
        f.write("- 실험일: 2026-05-06\n")
        f.write(f"- 모델: {base.NLLB_MODEL}\n")
        f.write(f"- 디바이스: {device}\n")
        f.write(f"- 샘플 수: {len(rows)}\n\n")
        f.write("## 최종 비교\n\n")
        f.write("| 방식 | 용어 보존율 | 평균 추론시간 |\n")
        f.write("|---|---:|---:|\n")
        for key, label in [("baseline", "Baseline NLLB"), ("strategy_a", "Strategy A 직접치환"), ("template", "Template-based")]:
            found, total = totals[key]
            pct = found / total * 100 if total else 0
            avg_t = sum(times[key]) / len(times[key]) if times[key] else 0
            f.write(f"| {label} | {found}/{total} ({pct:.0f}%) | {avg_t:.2f}s |\n")
        f.write("\n## 해석\n\n")
        f.write("- 이 실험은 전체 번역 자연스러움이 아니라 핵심 학교 용어 보존율을 측정한다.\n")
        f.write("- 템플릿 방식은 준비물/제출물/납부/참여/금지 문장을 구조화해 NLLB 오역 구간을 우회한다.\n")
        f.write("- review_required는 템플릿 미적용 또는 용어 누락 케이스를 후속 검수 대상으로 표시한다.\n\n")
        f.write("## 샘플별 결과\n\n")
        for row in rows:
            f.write(f"### [{row['sample_id']}] {row['korean']}\n\n")
            f.write(f"- 유형: `{row['sentence_type']}`\n")
            f.write(f"- 항목: {row['items_found'] or '(없음)'}\n")
            f.write(f"- 기대 용어: {row['expected_vi']}\n")
            f.write(f"- Baseline: {row['baseline_score']} / {row['baseline_out']}\n")
            f.write(f"- Strategy A: {row['strategy_a_score']} / {row['strategy_a_out']}\n")
            f.write(f"- Template: {row['template_score']} / {row['template_out']}\n")
            f.write(f"- review_required: {row['review_required']}\n\n")
    print(f"CSV saved: {csv_path}")
    print(f"MD  saved: {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="vi", choices=list(base.NLLB_LANG))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    device = ("cuda" if base.torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    tokenizer, model = base.load_nllb(device)
    glossary = {**base.ITEM_GLOSSARY_VI, **EXTRA_ITEM_GLOSSARY_VI}
    samples = EXPANDED_SAMPLES[:args.limit] if args.limit else EXPANDED_SAMPLES

    rows = []
    totals = {k: [0, 0] for k in ("baseline", "strategy_a", "template")}
    times = {k: [] for k in ("baseline", "strategy_a", "template")}

    print("\n" + "=" * 72)
    print("Expanded Template-Based Translation Experiment")
    print("=" * 72)

    for idx, (text, expected_vi) in enumerate(samples, 1):
        items = base.extract_glossary_items(text, glossary)
        stype = classify_sentence(text)
        audience = base.extract_audience(text, args.lang)
        recipient = base.extract_recipient(text, args.lang)
        tpl_out = build_from_template(stype, items, args.lang, audience, recipient)

        print(f"\n[{idx}/{len(samples)}] {text}")
        print(f"  type={stype}  items={[ko for ko, _ in items]}")

        out_base, t_base = base.translate_nllb(text, tokenizer, model, device, args.lang)
        f_base, total = base.term_score(out_base, expected_vi)
        totals["baseline"][0] += f_base; totals["baseline"][1] += total
        times["baseline"].append(t_base)

        text_a = base.apply_direct_replace(text, items) if items else text
        out_a, t_a = base.translate_nllb(text_a, tokenizer, model, device, args.lang)
        f_a, _ = base.term_score(out_a, expected_vi)
        totals["strategy_a"][0] += f_a; totals["strategy_a"][1] += total
        times["strategy_a"].append(t_a)

        if tpl_out is None:
            tpl_out, t_tpl = base.translate_nllb(text, tokenizer, model, device, args.lang)
            method = "nllb_fallback"
        else:
            t_tpl = 0.0
            method = "template"
        f_tpl, _ = base.term_score(tpl_out, expected_vi)
        totals["template"][0] += f_tpl; totals["template"][1] += total
        times["template"].append(t_tpl)

        review = "Y" if method != "template" or f_tpl < total else "N"
        print(f"  baseline={f_base}/{total} strategy_a={f_a}/{total} template={f_tpl}/{total} review={review}")

        rows.append({
            "sample_id": idx,
            "korean": text,
            "sentence_type": stype,
            "items_found": " | ".join(ko for ko, _ in items),
            "expected_vi": " | ".join(expected_vi),
            "baseline_out": out_base,
            "baseline_score": f"{f_base}/{total}",
            "baseline_time": f"{t_base:.2f}",
            "strategy_a_input": text_a,
            "strategy_a_out": out_a,
            "strategy_a_score": f"{f_a}/{total}",
            "strategy_a_time": f"{t_a:.2f}",
            "template_out": tpl_out,
            "template_score": f"{f_tpl}/{total}",
            "template_time": f"{t_tpl:.2f}",
            "template_method": method,
            "review_required": review,
        })

    print("\n" + "=" * 72)
    print("최종 비교")
    print("=" * 72)
    for key, label in [("baseline", "Baseline NLLB"), ("strategy_a", "Strategy A"), ("template", "Template")]:
        found, total = totals[key]
        pct = found / total * 100 if total else 0
        avg_t = sum(times[key]) / len(times[key]) if times[key] else 0
        print(f"{label:<18} {found}/{total} ({pct:.0f}%) avg={avg_t:.2f}s")

    write_outputs(rows, totals, times, device)


if __name__ == "__main__":
    main()

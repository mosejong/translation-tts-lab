"""Slot-protection pipeline demo (no NLLB model required).

Shows how URL / phone / date / time / amount values are masked before
translation and restored after, using __SLOTn__ placeholders.

Usage:
    python translation/protect_slots_demo.py
    python translation/protect_slots_demo.py --lang en
    python translation/protect_slots_demo.py --text "참가비 15,000원을 5월 9일(금)까지 납부해주세요"
"""
from __future__ import annotations

import argparse
import io
import re
import sys

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# ── Slot extraction (mirrors backend/app/services/slot_extractor.py) ──

URL_RE = re.compile(r"https?://\S+|www\.\S+\.\S+")
PHONE_RE = re.compile(r"\b\d{2,4}-\d{3,4}-\d{4}\b|\b\d{4}-\d{4}\b")
DATE_KO_RE = re.compile(r"(\d{4}년\s*)?\d{1,2}월\s*\d{1,2}일(?:\([월화수목금토일]\))?")
TIME_KO_RE = re.compile(r"(?:오전|오후)\s*\d{1,2}시(?:\s*\d{1,2}분)?")
AMOUNT_KO_RE = re.compile(r"\d[\d,]*원")

VI_DOW = {"월": "Thứ Hai", "화": "Thứ Ba", "수": "Thứ Tư", "목": "Thứ Năm",
          "금": "Thứ Sáu", "토": "Thứ Bảy", "일": "Chủ Nhật"}
EN_DOW = {"월": "Mon", "화": "Tue", "수": "Wed", "목": "Thu",
          "금": "Fri", "토": "Sat", "일": "Sun"}
EN_MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _fmt_date_vi(s: str) -> str:
    dow_m = re.search(r"\(([월화수목금토일])\)", s)
    dm = re.search(r"(\d{1,2})월\s*(\d{1,2})일", s)
    if not dm:
        return s
    month, day = dm.group(1), dm.group(2)
    dow = f" ({VI_DOW[dow_m.group(1)]})" if dow_m else ""
    ym = re.search(r"(\d{4})년", s)
    return f"Ngày {day}/{month}/{ym.group(1)}{dow}" if ym else f"Ngày {day}/{month}{dow}"


def _fmt_date_en(s: str) -> str:
    dow_m = re.search(r"\(([월화수목금토일])\)", s)
    dm = re.search(r"(\d{1,2})월\s*(\d{1,2})일", s)
    if not dm:
        return s
    mi = int(dm.group(1)) - 1
    month_str = EN_MONTH[mi] if 0 <= mi < 12 else dm.group(1)
    day = dm.group(2)
    dow = f" ({EN_DOW[dow_m.group(1)]})" if dow_m else ""
    ym = re.search(r"(\d{4})년", s)
    return f"{month_str} {day}, {ym.group(1)}{dow}" if ym else f"{month_str} {day}{dow}"


def _fmt_time_vi(s: str) -> str:
    ampm = "sáng" if "오전" in s else "chiều"
    nums = re.findall(r"\d+", s)
    return f"{nums[0]} giờ {nums[1]} {ampm}" if len(nums) == 2 else f"{nums[0]} giờ {ampm}"


def _fmt_amount(s: str) -> str:
    return re.sub(r"원$", " won", s)


def mask_slots(text: str, lang: str | None = None) -> tuple[str, list[str]]:
    holders: list[str] = []
    result = text

    def _sub(pattern: re.Pattern, fmt=None):
        nonlocal result
        matches = sorted(pattern.finditer(result), key=lambda m: -m.start())
        for m in matches:
            token = f"__SLOT{len(holders)}__"
            val = fmt(m.group()) if fmt else m.group()
            holders.append(val)
            result = result[:m.start()] + token + result[m.end():]

    _sub(URL_RE)
    _sub(PHONE_RE)
    if lang:
        if lang == "vi":
            _sub(DATE_KO_RE, _fmt_date_vi)
            _sub(TIME_KO_RE, _fmt_time_vi)
        elif lang == "en":
            _sub(DATE_KO_RE, _fmt_date_en)
        _sub(AMOUNT_KO_RE, _fmt_amount)

    return result, holders


def restore_slots(text: str, holders: list[str]) -> str:
    for i, val in enumerate(holders):
        text = text.replace(f"__SLOT{i}__", val)
    return text


# ── Demo samples ──────────────────────────────────────────────────

DEMO_SAMPLES = [
    ("신청은 https://apply.kr 에서 하시고 문의는 02-2649-7232 로", "vi"),
    ("5월 9일(금)까지 담임선생님께 제출해 주세요", "vi"),
    ("오전 9시부터 시작하며 참가비 15,000원을 사전 납부해 주세요", "vi"),
    ("2026년 5월 6일(목) 8:50 ~ 14:40 현장체험학습", "vi"),
    ("4월 30일(화)까지 참가비 15,000원을 납부해 주세요", "en"),
    ("수강료 81,950원 / 교재비 12,000원 / 재료비 24,000원", "vi"),
]


def _print_demo(text: str, lang: str) -> None:
    masked, holders = mask_slots(text, lang)

    print(f"\n{'─'*60}")
    print(f"입력  : {text}")
    print(f"언어  : {lang}")
    print(f"마스킹: {masked}")
    if holders:
        for i, h in enumerate(holders):
            print(f"  SLOT{i}: {h!r}")

    # Simulate NLLB identity pass (placeholder survival check)
    simulated_nllb_out = masked  # identity
    restored = restore_slots(simulated_nllb_out, holders)
    print(f"복원  : {restored}")

    # Verify no slots leaked
    if "__SLOT" in restored:
        print("  [WARN] 미복원 슬롯 존재")
    else:
        print("  [OK] 슬롯 완전 복원")


def main() -> None:
    parser = argparse.ArgumentParser(description="Slot-protection pipeline demo")
    parser.add_argument("--text", help="번역할 한국어 텍스트")
    parser.add_argument("--lang", default="vi", choices=["vi", "en", "ru", "ms", "mn", "zh", "th", "ja"])
    args = parser.parse_args()

    print("=" * 60)
    print("Slot-Protection Pipeline Demo")
    print("NLLB 호출 없이 마스킹/복원 사이클만 시뮬레이션합니다.")
    print("=" * 60)

    if args.text:
        _print_demo(args.text, args.lang)
    else:
        for text, lang in DEMO_SAMPLES:
            _print_demo(text, lang)

    print(f"\n{'─'*60}")
    print("Note: 실제 NLLB 번역에서는 __SLOTn__ 토큰이 ASCII 약어로 인식되어")
    print("      그대로 통과합니다. [P0] 형태(U+27E6/E7)는 SentencePiece가 드롭하므로 사용 불가.")


if __name__ == "__main__":
    main()

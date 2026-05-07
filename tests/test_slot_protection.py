"""Standalone slot-protection unit tests (no FastAPI, no NLLB model required).

Tests the pure-logic parts of the slot-protection pipeline:
  - Regex-based slot detection
  - i18n date/time/amount formatting
  - Placeholder survival through identity translate
  - Postprocess vi pattern correction

Run: pytest tests/test_slot_protection.py -v
"""
from __future__ import annotations

import re
import pytest


# ── Inline re-implementations (no backend import needed) ──────────
# These mirror the logic in backend/app/services/translator.py
# and backend/app/services/slot_extractor.py.
# Goal: verify pipeline logic without a running server or NLLB weights.

URL_RE = re.compile(r"https?://\S+|www\.\S+\.\S+")
PHONE_RE = re.compile(r"\b\d{2,4}-\d{3,4}-\d{4}\b|\b\d{4}-\d{4}\b")

DATE_KO_RE = re.compile(r"(\d{4}년\s*)?\d{1,2}월\s*\d{1,2}일(?:\([월화수목금토일]\))?")
TIME_KO_RE = re.compile(r"(?:오전|오후)\s*\d{1,2}시(?:\s*\d{1,2}분)?")
AMOUNT_KO_RE = re.compile(r"\d[\d,]*원")

VI_DOW = {"월": "Thứ Hai", "화": "Thứ Ba", "수": "Thứ Tư", "목": "Thứ Năm",
          "금": "Thứ Sáu", "토": "Thứ Bảy", "일": "Chủ Nhật"}
EN_DOW = {"월": "Mon", "화": "Tue", "수": "Wed", "목": "Thu",
          "금": "Fri", "토": "Sat", "일": "Sun"}


def _fmt_date_vi(m: str) -> str:
    dow_m = re.search(r"\(([월화수목금토일])\)", m)
    day_m = re.search(r"(\d{1,2})월\s*(\d{1,2})일", m)
    if not day_m:
        return m
    month, day = day_m.group(1), day_m.group(2)
    year_m = re.search(r"(\d{4})년", m)
    dow = f" ({VI_DOW[dow_m.group(1)]})" if dow_m else ""
    if year_m:
        return f"Ngày {day}/{month}/{year_m.group(1)}{dow}"
    return f"Ngày {day}/{month}{dow}"


def _fmt_date_en(m: str) -> str:
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dow_m = re.search(r"\(([월화수목금토일])\)", m)
    day_m = re.search(r"(\d{1,2})월\s*(\d{1,2})일", m)
    if not day_m:
        return m
    month_idx = int(day_m.group(1)) - 1
    day = day_m.group(2)
    month_str = MONTHS[month_idx] if 0 <= month_idx < 12 else day_m.group(1)
    dow = f" ({EN_DOW[dow_m.group(1)]})" if dow_m else ""
    year_m = re.search(r"(\d{4})년", m)
    if year_m:
        return f"{month_str} {day}, {year_m.group(1)}{dow}"
    return f"{month_str} {day}{dow}"


def _fmt_time_vi(m: str) -> str:
    ampm = "sáng" if "오전" in m else "chiều"
    nums = re.findall(r"\d+", m)
    if len(nums) == 2:
        return f"{nums[0]} giờ {nums[1]} {ampm}"
    return f"{nums[0]} giờ {ampm}"


def _fmt_amount(m: str) -> str:
    return re.sub(r"원$", " won", m)


def mask_slots(text: str, lang: str | None = None):
    """Returns (masked_text, holders). Mirrors translator._mask_protected_entities."""
    holders = []
    result = text

    def _replace(pattern, fmt_fn=None):
        nonlocal result
        for m in sorted(pattern.finditer(result), key=lambda x: -x.start()):
            token = f"__SLOT{len(holders)}__"
            value = fmt_fn(m.group()) if fmt_fn else m.group()
            holders.append(value)
            result = result[:m.start()] + token + result[m.end():]

    _replace(URL_RE)
    _replace(PHONE_RE)

    if lang:
        if lang == "vi":
            _replace(DATE_KO_RE, _fmt_date_vi)
            _replace(TIME_KO_RE, _fmt_time_vi)
        elif lang == "en":
            _replace(DATE_KO_RE, _fmt_date_en)
        _replace(AMOUNT_KO_RE, _fmt_amount)

    return result, holders


def restore_slots(text: str, holders: list[str]) -> str:
    for i, val in enumerate(holders):
        text = text.replace(f"__SLOT{i}__", val)
    return text


# ── URL / Phone masking ────────────────────────────────────────────

def test_url_masked_to_slot():
    masked, holders = mask_slots("신청은 https://apply.kr 에서")
    assert "https://apply.kr" not in masked
    assert "__SLOT0__" in masked
    assert holders == ["https://apply.kr"]


def test_phone_masked_to_slot():
    masked, holders = mask_slots("문의 02-2649-7232")
    assert "02-2649-7232" not in masked
    assert "__SLOT0__" in masked
    assert holders == ["02-2649-7232"]


def test_url_and_phone_get_separate_slots():
    masked, holders = mask_slots("https://a.com 문의 02-1234-5678")
    assert "__SLOT0__" in masked and "__SLOT1__" in masked
    assert set(holders) == {"https://a.com", "02-1234-5678"}


def test_no_entities_unchanged():
    masked, holders = mask_slots("그냥 평범한 통신문")
    assert masked == "그냥 평범한 통신문"
    assert holders == []


def test_restore_url():
    masked, holders = mask_slots("문의 https://school.go.kr 참조")
    restored = restore_slots(masked, holders)
    assert restored == "문의 https://school.go.kr 참조"


# ── Date masking ───────────────────────────────────────────────────

def test_date_vi_format():
    masked, holders = mask_slots("5월 9일(금)까지 제출", "vi")
    assert "5월 9일(금)" not in masked
    assert "__SLOT0__" in masked
    assert holders[0] == "Ngày 9/5 (Thứ Sáu)"


def test_date_en_format():
    masked, holders = mask_slots("5월 9일(금)까지 제출", "en")
    assert "5월 9일(금)" not in masked
    assert "May 9 (Fri)" in holders[0]


def test_date_with_year_vi():
    masked, holders = mask_slots("2026년 5월 6일(목)", "vi")
    assert "Ngày 6/5/2026 (Thứ Năm)" in holders[0]


def test_date_not_masked_without_lang():
    masked, holders = mask_slots("5월 9일(금)까지 제출")
    assert "5월 9일(금)" in masked
    assert holders == []


# ── Time masking ───────────────────────────────────────────────────

def test_time_am_vi():
    masked, holders = mask_slots("오전 9시부터 시작", "vi")
    assert "오전 9시" not in masked
    assert holders[0] == "9 giờ sáng"


def test_time_pm_with_minute_vi():
    masked, holders = mask_slots("오후 3시 30분에 종료", "vi")
    assert "오후 3시 30분" not in masked
    assert "chiều" in holders[0]
    assert "30" in holders[0]


# ── Amount masking ─────────────────────────────────────────────────

def test_amount_vi():
    masked, holders = mask_slots("참가비 15,000원을 납부", "vi")
    assert "15,000원" not in masked
    assert holders[0] == "15,000 won"


def test_amount_large_vi():
    masked, holders = mask_slots("수강료 81,950원", "vi")
    assert "81,950원" not in masked
    assert "81,950 won" in holders[0]


# ── Slot token survival (identity translate simulation) ────────────

def test_slot_survives_identity_translate():
    """__SLOTn__ tokens must pass through a model that doesn't touch ASCII tokens."""
    masked, holders = mask_slots("신청은 https://apply.kr 에서 5월 9일(금)까지", "vi")
    # Simulate model returning text unchanged (identity)
    model_output = masked
    restored = restore_slots(model_output, holders)
    assert "https://apply.kr" in restored
    assert "Ngày 9/5 (Thứ Sáu)" in restored
    assert "__SLOT" not in restored


def test_multiple_slots_restored_in_order():
    text = "https://a.com 에서 https://b.com 확인"
    masked, holders = mask_slots(text)
    assert len(holders) == 2
    restored = restore_slots(masked, holders)
    assert "https://a.com" in restored
    assert "https://b.com" in restored


# ── Date + Amount together ─────────────────────────────────────────

def test_date_and_amount_both_masked():
    text = "4월 30일(화)까지 참가비 15,000원을 납부해 주세요"
    masked, holders = mask_slots(text, "vi")
    assert "4월 30일(화)" not in masked
    assert "15,000원" not in masked
    assert len(holders) == 2
    assert any("Ngày" in h for h in holders)
    assert any("won" in h for h in holders)
    assert masked.count("__SLOT") == 2


# ── Postprocess vi pattern correctness ────────────────────────────

def test_postprocess_vi_student_term(monkeypatch):
    """학생 맥락에서 sinh viên → học sinh 교정 확인."""
    from translation.postprocess_vi import apply_vi_postprocess
    result = apply_vi_postprocess("학생이 제출해야 합니다", "sinh viên phải nộp")
    assert "học sinh" in result
    assert "sinh viên" not in result


def test_postprocess_vi_homeroom_term(monkeypatch):
    """담임 맥락에서 giáo viên giám đốc → giáo viên chủ nhiệm 교정."""
    from translation.postprocess_vi import apply_vi_postprocess
    result = apply_vi_postprocess("담임선생님께 제출하세요", "nộp cho giáo viên giám đốc")
    assert "giáo viên chủ nhiệm" in result


def test_postprocess_vi_no_source_no_change():
    """소스에 맥락 없으면 vi 텍스트 변경 없음."""
    from translation.postprocess_vi import apply_vi_postprocess
    text = "sinh viên phải nộp tài liệu"
    result = apply_vi_postprocess("", text)
    assert result == text


# ── Slot token format robustness ──────────────────────────────────

def test_slot_token_is_ascii_uppercase():
    """__SLOTn__ 형식이 ASCII 대문자임을 확인 (NLLB tokenizer 통과 조건)."""
    masked, _ = mask_slots("https://apply.kr")
    assert re.fullmatch(r"__SLOT\d+__", masked.strip())


def test_slot_index_increments():
    text = "https://a.com 02-1234-5678 https://b.com"
    masked, holders = mask_slots(text)
    assert "__SLOT0__" in masked
    assert "__SLOT1__" in masked
    assert "__SLOT2__" in masked
    assert len(holders) == 3

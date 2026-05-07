# Slot-Protected Translation 파이프라인

**적용 날짜**: 2026-05-06  
**구현 위치**: `backend/app/services/translator.py`  
**실험 레포**: `translation-tts-lab/translation/protect_slots_demo.py`

---

## 문제 배경

NLLB 번역 시 URL·전화번호·날짜·시간·금액 등 구조적 값이 변형 또는 소실되는 현상:

| 입력 | NLLB 출력 (before) |
|---|---|
| `https://apply.kr` | `ứng dụng.kr` 또는 소실 |
| `02-2649-7232` | 소실 또는 변형 |
| `5월 9일(금)` | `ngày 9 tháng 5 (thứ sáu)` (언어별 포맷 불일치) |
| `15,000원` | `15,000 USD` 또는 소실 |

### 왜 `⟦P0⟧`가 실패했나

초기 설계에서는 `⟦P0⟧` 형태의 플레이스홀더를 사용했으나 NLLB SentencePiece tokenizer가 `⟦`(U+27E6), `⟧`(U+27E7)를 OOV로 처리해 토큰 자체를 드롭, 복원 불가능해짐.

**해결**: ASCII 대문자 + 언더스코어 형식 `__SLOT0__` 사용. NLLB가 약어/코드로 인식해 그대로 통과.

---

## 파이프라인 구조

```
한국어 원문
    │
    ▼
_clean_for_translation[:100]         ← MAX 100자 trim
    │
    ▼
_mask_protected_entities(text, lang) ← URL·전화·날짜·시간·금액 → __SLOTn__
    │                                    holders = [원본값 or i18n 변환값]
    ▼
_find_glossary_hits_safe(...)        ← 1글자 오탐 방지, 공백 normalize, longest-first
    │
    ▼
[glossary 용어 주입 힌트 prepend]
    │
    ▼
_translate(masked_text, target_nllb) ← NLLB 추론 (greedy, rep_penalty=1.3)
    │
    ▼
_post_process_vi(source_ko, vi_out)  ← 학생/담임/유치원 등 패턴 교정 (vi only)
    │
    ▼
_restore_protected_entities(text, holders) ← __SLOTn__ → 원본 or i18n 값 복원
    │
    ▼
최종 번역문
```

---

## 슬롯 추출 규칙

### URL / 전화번호
정규식으로 추출. `holders`에는 **원본 문자열** 그대로 저장.

```python
_is_url_or_phone("https://apply.kr")  # → True
_is_url_or_phone("02-2649-7232")       # → True
_is_url_or_phone("1588-0260")          # → True
```

### 날짜 (target_lang 있을 때만)
`slot_extractor.extract_dates()` → i18n 포맷 변환 후 holders에 저장.

| 입력 | vi 포맷 | en 포맷 |
|---|---|---|
| `5월 9일(금)` | `Ngày 9/5 (Thứ Sáu)` | `May 9 (Fri)` |
| `2026년 5월 6일(목)` | `Ngày 6/5/2026 (Thứ Năm)` | `May 6, 2026 (Thu)` |

### 시간
`slot_extractor.extract_times()` → i18n 포맷 변환.

| 입력 | vi 포맷 |
|---|---|
| `오전 9시` | `9 giờ sáng` |
| `오후 3시 30분` | `3 giờ 30 chiều` |

### 금액
`slot_extractor.extract_amounts()` → `숫자 won` 형태 통일 (언어 무관).

| 입력 | 변환 결과 |
|---|---|
| `15,000원` | `15,000 won` |
| `81,950원` | `81,950 won` |

---

## 중요 제약사항

### 1. 100자 trim 전에 마스킹 없음

```python
# translator.py
text = _clean_for_translation(text)[:MAX_TRANSLATE_CHARS]  # 100자 trim BEFORE masking
masked, holders = _mask_protected_entities(text, target_lang)
```

100자 이내의 슬롯은 보호되지만, 100자를 초과하는 문장에서 trim으로 잘린 슬롯은 보호 불가. 현재 가통문 평균 길이가 100자 이하로 실용상 문제 없음.

### 2. 마스킹 순서 (URL → 날짜 → 시간 → 금액)

이미 `__SLOTn__`으로 마스킹된 영역을 날짜/시간/금액 패턴이 재추출하지 않도록 처리됨. 순서 변경 시 중복 마스킹 위험.

### 3. SMaLL-100에서의 슬롯 생존율

현재 SMaLL-100에서 `__SLOT0__` 통과 여부 미검증. `tests/test_slot_protection.py` 및 `translation/protect_slots_demo.py`로 검증 필요.

---

## 테스트 커버리지 (2026-05-06 기준)

`backend/tests/test_translator_protection.py` — 27개 테스트 ALL PASS

| 카테고리 | 테스트 수 |
|---|---|
| 마스킹/복원 단위 | 6 |
| URL/전화 가드 | 4 |
| 날짜/시간/금액 마스킹 | 7 |
| translate_short_sentence E2E | 5 |
| glossary 안전 가드 | 2 |
| 베트남어 후처리 패턴 | 2 |
| 100자 trim 안전성 | 1 |

# SchoolBridge 번역 실험 계획

**레포**: translation-tts-lab  
**목적**: SchoolBridge 가정통신문 번역 파이프라인의 모델 선택 및 품질 검증 실험 기록.  
**팀 메인 레포**: `multicultural-ai/backend/app/services/translator.py`

---

## 실험 흐름

```
1. 모델 A/B 비교 (NLLB vs SMaLL-100)
        ↓
2. 번역 실패 패턴 수집 → data/translation_failure_cases_20260506.csv
        ↓
3. Slot-protected translation 설계 및 구현
        ↓
4. 후처리 패턴 규칙 도출 → translation/postprocess_vi.py
        ↓
5. SMaLL-100 재실험 (penalty 튜닝)
        ↓
6. 팀 메인 레포 반영 결정
```

---

## 현재 상태 (2026-05-06)

| 실험 | 상태 | 결과 문서 |
|---|---|---|
| NLLB vs SMaLL-100 20샘플 비교 | ✅ 완료 | `docs/nllb_vs_small100_result.md` |
| 번역 실패 케이스 분류 | ✅ 완료 | `data/translation_failure_cases_20260506.csv` |
| Slot-protected translation 설계 | ✅ 완료 | `docs/slot_protected_translation.md` |
| vi 후처리 패턴 (5종) | ✅ 완료 | `translation/postprocess_vi.py` |
| SMaLL-100 재실험 (penalty) | ⏳ 대기 | `docs/small100_retest_plan.md` |
| 슬롯 placeholder 생존율 검증 | ⏳ 대기 | `tests/test_slot_protection.py` |

---

## 평가 데이터셋

| 파일 | 설명 | 샘플 수 |
|---|---|---|
| `data/school_notice_eval_ko_20260506.csv` | 평가용 한국어 학교 공지 | 20개 |
| `data/translation_failure_cases_20260506.csv` | SMaLL-100 실패 케이스 분류 | 8개 |

---

## 스크립트 목록

| 스크립트 | 역할 |
|---|---|
| `translation/compare_translation_models.py` | NLLB/SMaLL-100 나란히 번역 + 결과 CSV 저장 |
| `translation/postprocess_vi.py` | 베트남어 도메인 오역 후처리 |
| `translation/protect_slots_demo.py` | URL·날짜·금액 슬롯 보호 시각적 데모 |
| `translation/run_mvp_pipeline.py` | 전체 파이프라인 실행 (슬롯 보호 포함) |
| `model/translation_tts/TODO_small100_quality_retest.py` | SMaLL-100 재실험 설정 및 코드 |
| `tests/test_slot_protection.py` | 슬롯 보호 standalone 단위 테스트 |

---

## 팀 메인 레포로 가져갈 수 있는 후보

| 항목 | 대상 경로 |
|---|---|
| `translation/postprocess_vi.py` | `backend/app/services/` |
| 실패 케이스 CSV | `backend/tests/fixtures/` |
| 슬롯 보호 단위 테스트 | `backend/tests/test_slot_protection.py` |

---

## 다음 실험 우선순위

1. **[P0]** SMaLL-100 슬롯 생존율 검증 — 서비스 적용 가능성 판단의 선행 조건
2. **[P0]** SMaLL-100 재실험 config A/B/C 실행
3. **[P1]** 추가 언어(en/ru/ms) 번역 품질 기초 평가
4. **[P2]** OCR bbox 연동 후 번역 파이프라인 통합 테스트 (팀 전체 방향)

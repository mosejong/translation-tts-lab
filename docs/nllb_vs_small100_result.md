# NLLB vs SMaLL-100 번역 품질 비교 결과

**평가일**: 2026-05-06  
**평가 스크립트**: `translation/compare_translation_models.py`  
**출력 CSV**: `outputs/model_compare/small100_vs_nllb_vi.csv`  
**평가 샘플**: 20개 학교 공지 (한국어 → 베트남어)

---

## 요약 결론

| 항목 | NLLB-200-600M | SMaLL-100 |
|---|---|---|
| 번역 품질 (20샘플) | **20/20 우세** | 0/20 우세 |
| 평균 추론 속도 | 4.32초 | **1.93초 (2.24배 빠름)** |
| 반복 출력 발생률 | 0% | **30% (6/20)** |
| 금액 단위 오류 | 없음 | **81,950원 → USD 오번역** |
| 도메인 용어 안정성 | 중간 (후처리 필요) | 불안정 (반복 시 전체 실패) |

**최종 결론 (2026-05-06 재실험 후)**: SMaLL-100 서비스 탑재 불가 확정. 슬롯 토큰(`__SLOT0__`) 생존 실패가 근본 원인 — penalty 조정으로 해결 불가. NLLB 유지.

---

## SMaLL-100 주요 실패 패턴

### 패턴 1: 반복 출력 (30% 발생)

반복이 발생한 샘플 ID: `SCHOOL-KO-005`, `SCHOOL-KO-006`, `SCHOOL-KO-010`, `SCHOOL-KO-018` 등

```
입력: 강좌: 이야기한국사 / 모집대상: 1-3학년 ...
SMaLL-100: Lời bài hát: Lời bài hát: Lời bài hát: Lời bài hát: ...
```

```
입력: 2026년 월 일보호자 ...
SMaLL-100: Chương trình giảng dạy năm 2026: Chương trình giảng dạy ... (x50+)
```

```
입력: 1) 담임교사 수업공개 대상 학년교과시간참관 ...
SMaLL-100: học sinh học sinh học sinh học sinh ... (x60+)
```

**원인 분석**: `repetition_penalty`와 `no_repeat_ngram_size` 파라미터 미적용. NLLB는 `num_beams=1`(greedy)로도 반복 없음.

### 패턴 2: 금액 단위 오번역

```
입력: 11차시 수강료 81,950원 / 교재비 55,000원
SMaLL-100: 89.950 USD / phí học tập 55.000 USD
```

`원(won)`을 USD로 오번역. 후처리로 해결하거나 slot 마스킹으로 격리 필요.

### 패턴 3: 테이블 구조 파괴

```
입력: 학년|교과|시간|장소|참관대상 형식의 시간표
SMaLL-100: 반복 출력으로 전체 구조 소실
```

### 패턴 4: 도메인 용어 오역 (반복 없는 경우에도)

| 한국어 | 기대 | SMaLL-100 | NLLB |
|---|---|---|---|
| 담임선생님 | giáo viên chủ nhiệm | giáo viên (부정확) | giáo viên giám đốc (후처리 필요) |
| 학생 | học sinh | sinh viên (대학생 오역) | học viên (후처리 필요) |
| 현장체험학습 | buổi trải nghiệm thực tế | 의미 전달 약함 | 의미 전달 약함 |

NLLB도 용어 오역은 있지만, 후처리(postprocess_vi.py)로 교정 가능. SMaLL-100은 반복 발생 시 후처리 자체가 무의미.

---

## 속도 분포

| 샘플 | NLLB (초) | SMaLL-100 (초) | 배율 |
|---|---|---|---|
| SCHOOL-KO-001 | 1.96 | 1.30 | 1.51x |
| SCHOOL-KO-005 | 5.11 | 3.15 | 1.62x |
| SCHOOL-KO-006 | 7.46 | 3.27 | 2.28x |
| SCHOOL-KO-009 | 6.04 | 2.22 | 2.72x |
| SCHOOL-KO-010 | 5.33 | 3.26 | 1.63x |
| **평균** | **4.32** | **1.93** | **2.24x** |

긴 문장(SCHOOL-KO-009 등)일수록 SMaLL-100의 속도 이점이 커지는 경향.

---

## 현재 NLLB 설정 (서비스 적용 중)

```python
# backend/app/services/translator.py
model.generate(
    **inputs,
    forced_bos_token_id=target_id,
    max_new_tokens=160,
    num_beams=1,           # greedy
    repetition_penalty=1.3,
    no_repeat_ngram_size=3,
)
```

---

## 재실험 결과 (2026-05-06)

`translation/compare_translation_models.py --repetition-penalty 1.5 --no-repeat-ngram-size 4`

| 설정 | 슬롯 생존 | 무한반복 | 토큰반복 | 평균속도 |
|---|---|---|---|---|
| **기존 (greedy, penalty 없음)** | 미검증 | 30% | 있음 | 1.93s |
| Config A (beam4, rp=1.5, ngram=4) | **FAIL** | 0% | ~15% | 3.47s |
| Config C (greedy, rp=1.5, ngram=4) | **FAIL (더 심함)** | 0% | ~15% | ~1.9s |
| **NLLB greedy (현재 서비스)** | **PASS** | 0% | 0% | 4.32s |

### 슬롯 생존 실패 상세

SMaLL-100(M2M100 기반) tokenizer는 `__SLOT0__`의 앞 `__`를 단어 경계 토큰으로 분리해 드롭:

```
입력:  신청은 __SLOT0__ 에서 문의는 __SLOT1__
출력:  Ứng dụng liên hệ với __SLOT0__ _ SLO1__  (SLOT1 망가짐)

입력:  __SLOT0__까지 제출해 주세요
출력:  Xin gửi cho bạn đến SLOT0__  (앞 __ 소실)

입력:  참가비 __SLOT0__ 납부
출력:  Đánh giá _SLOT0__ Thanh toán  (언더스코어 1개 소실)
```

이는 penalty 파라미터와 무관한 tokenizer 구조 문제. `__SLOT__` 형식을 바꾸지 않으면 해결 불가.

### 최종 판단

**SMaLL-100: 서비스 탑재 불가 확정.** NLLB 유지.

SMaLL-100 재도입 조건 (참고용):
- 슬롯 토큰 형식을 M2M100 tokenizer가 단일 토큰으로 처리하는 형식으로 변경 (예: `SLOT0`, `[SLOT0]` 등 별도 실험 필요)
- 토큰 반복 문제 추가 해결
- 이 두 조건 충족 후 재평가

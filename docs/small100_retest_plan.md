# SMaLL-100 품질 재실험 계획

**작성일**: 2026-05-06  
**배경**: SMaLL-100이 NLLB보다 2.24배 빠르지만 30%의 반복 출력 문제 존재.  
**목표**: `repetition_penalty` + `no_repeat_ngram_size` 적용 후 품질 gap 측정.

---

## 현재 비교 스크립트 문제점

`translation/compare_translation_models.py`의 `Small100Translator.translate()`에 다음 파라미터가 누락됨:

```python
# 현재 (문제):
tokens = self.model.generate(**inputs, max_new_tokens=max_new_tokens, num_beams=num_beams)

# 필요 (수정):
tokens = self.model.generate(
    **inputs,
    max_new_tokens=max_new_tokens,
    num_beams=num_beams,
    repetition_penalty=repetition_penalty,
    no_repeat_ngram_size=no_repeat_ngram_size,
    length_penalty=length_penalty,
)
```

스크립트 수정 사항 → `compare_translation_models.py` 참조.

---

## 실험 설정 후보

### A. beam4_rp15 (반복 억제 최우선)
```python
num_beams=4, repetition_penalty=1.5, no_repeat_ngram_size=4,
max_new_tokens=256, length_penalty=1.0
```
**목적**: 반복 출력 완전 제거. 속도 손해 있음.

### B. beam4_rp13_ngram4 (NLLB 동일 패널티)
```python
num_beams=4, repetition_penalty=1.3, no_repeat_ngram_size=4,
max_new_tokens=256, length_penalty=1.0
```
**목적**: NLLB와 동일한 penalty로 SMaLL-100이 beam4에서 얼마나 개선되는지 확인.

### C. greedy_rp15_ngram4 (속도+반복 균형)
```python
num_beams=1, repetition_penalty=1.5, no_repeat_ngram_size=4,
max_new_tokens=256, length_penalty=1.0
```
**목적**: greedy 속도 유지하면서 강한 penalty로 반복 억제. 속도 이점 최대화 시도.

---

## 슬롯 placeholder 생존율 검증

재실험 전 필수 검증 항목:

```python
SLOT_TEST_SAMPLES = [
    ("신청은 __SLOT0__ 에서 문의는 __SLOT1__", ["__SLOT0__", "__SLOT1__"]),
    ("__SLOT0__까지 제출해 주세요", ["__SLOT0__"]),
    ("참가비 __SLOT0__ 납부", ["__SLOT0__"]),
]
```

`__SLOT0__`이 SMaLL-100 tokenizer를 통과하지 못하면 slot-protected translation 자체가 불가능 → 서비스 적용 불가.

실험 코드: `model/translation_tts/TODO_small100_quality_retest.py` (주석 해제 후 실행).

---

## 수용 기준

서비스 적용 판단 기준 (NLLB 대비):

| 기준 | 목표 | 현재 SMaLL-100 |
|---|---|---|
| 반복 출력 발생률 | **0%** (필수) | 30% |
| `__SLOT0__` 보존율 | **100%** (필수) | 미검증 |
| 날짜/금액/용어 보존율 | ≥ NLLB 수준 | 낮음 (USD 오류 등) |
| 속도 이점 (beam4 사용 시) | 1.5배 이상 | 2.24배 (greedy 기준) |

beam4 사용 시 속도 이점이 줄어들 수 있음. C 설정(greedy+강한penalty)이 속도/품질 균형에서 최적 후보.

---

## 실행 순서

```bash
# 1. 모델 다운로드 확인
python -c "from transformers import AutoModelForSeq2SeqLM; AutoModelForSeq2SeqLM.from_pretrained('alirezamsh/small100')"

# 2. 슬롯 생존율 먼저 검증
python model/translation_tts/TODO_small100_quality_retest.py

# 3. 재실험 (config A/B/C)
python translation/compare_translation_models.py \
    --models small100 \
    --target-lang vi \
    --num-beams 4 \
    --repetition-penalty 1.5 \
    --no-repeat-ngram-size 4

# 4. 결과 비교
# outputs/model_compare/small100_retest_*.csv 확인
```

---

## 결과 기록 위치

- 슬롯 생존율: `outputs/model_compare/small100_slot_survival.json`
- 번역 품질 비교: `outputs/model_compare/small100_retest_A.csv` / `B.csv` / `C.csv`
- 최종 판단: `docs/nllb_vs_small100_result.md` 업데이트

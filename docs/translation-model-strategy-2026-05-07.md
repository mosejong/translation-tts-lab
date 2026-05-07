# Translation Model Strategy

날짜: 2026-05-07  
담당: 세종 파트  
상태: 번역 모델 실험 정리

---

## 결론

SchoolBridge 번역 파트는 Gemini/API 번역으로 전면 교체하지 않고, NLLB 기반 파이프라인을 유지한다.

다만 모든 문장을 NLLB에 자유 번역시키는 방식은 중단하고, 학교 안내문에서 중요한 사실값과 행동 문장은 구조화해서 보호한다.

```text
NLLB main: keep
Gemini translation: not main
Glossary / slot protection / template translation: strengthen
```

---

## 현재 확인된 문제

NLLB는 일반 다국어 번역 모델이라 학교 가정통신문 도메인에서 다음 문제가 발생했다.

- 학교 도메인 용어 오역
- glossary injection 일부 무시
- 짧은 날짜/시간 fragment 이상 번역
- URL/전화번호/금액/날짜가 번역 중 깨질 위험
- 준비물/제출물처럼 명사 중심 문장에서 의미 왜곡

실제 실패 예시:

```text
23.(토) / 13:00 ~ 15:00
→ Tôi không biết.

대상
→ Giải thưởng lớn

스쿨뱅킹
→ School Banking (School Banking) 중복
```

---

## SMaLL-100 비교 결론

SMaLL-100은 NLLB보다 빠른 경향이 있었지만, 실제 학교 안내문 문장에서는 반복 출력과 의미 왜곡이 심했다.

```text
SMaLL-100 장점:
- NLLB보다 빠름
- 경량 모델 후보로 실험 가치 있음

SMaLL-100 한계:
- 반복 출력 발생
- 문장 의미 왜곡
- 학교 도메인 용어 안정성 낮음
- 적은 데이터 파인튜닝으로 즉시 해결될 가능성 낮음
```

따라서 현재 서비스 baseline은 NLLB를 유지한다.

---

## placeholder survival 실험

NLLB가 보존할 수 있는 placeholder 형식을 실험했다.

결과:

| Placeholder | 생존율 | 용어 보존율 | 판단 |
| --- | ---: | ---: | --- |
| `AAAA/BBBB/CCCC` | 100% | 100% | 최우선 후보 |
| `XITEMX/YITEMY/ZITEMZ` | 100% | 100% | 후보 |
| `ITEMA/ITEMB/ITEMC` | 96% | 96% | 빠르지만 1건 실패 |
| `[ITEM_A]` | 42% | 42% | 부적합 |
| `<ITEM_A>` | 6% | 6% | 부적합 |
| `ITEM_A_TOKEN` | 48% | 48% | 부적합 |

기존 `__SLOT0__` 방식은 SentencePiece에서 분리되거나 NLLB 출력 중 손상될 수 있어 안정적이지 않았다.

---

## template translation 실험

준비물/제출물 문장은 NLLB에 전부 맡기지 않고, 문장 유형을 분류한 뒤 glossary와 템플릿으로 번역한다.

예시:

```text
원문:
유성매직과 사인펜을 준비해 주세요

구조화:
sentence_type = prepare
items = [유성매직, 사인펜]

템플릿 번역:
Vui lòng chuẩn bị bút dạ dầu và bút lông.
```

핵심 방식:

```text
1. sentence_type 분류
   prepare / bring / submit / attend / pay / info

2. glossary item 추출
   도화지, 색칠 도구, 유성매직, 실내화, 물통, 수채화 물감 등

3. template 적용
   prepare → Vui lòng chuẩn bị {items}.
   bring   → Vui lòng mang theo {items}.
   submit  → Vui lòng nộp {items}.
   pay     → Vui lòng thanh toán {amount}.

4. 템플릿 불가능한 설명 문장만 NLLB fallback
```

결론:

```text
모든 문장을 자유 번역하지 않는다.
학교 안내문에서 중요한 행동 문장은 구조화해서 안전하게 번역한다.
```

---

## slot protected translation

날짜, 시간, 금액, URL, 전화번호는 NLLB가 번역하지 않게 보호한다.

```text
번역 전:
5월 7일(목)까지 44,870원을 납부해 주세요.

slot 보호:
AAAA까지 BBBB을 납부해 주세요.

번역 후 복원:
Vui lòng thanh toán 44,870원 trước 5월 7일(목).
```

실제 서비스에서는 언어별 날짜/시간 포맷 복원까지 연결한다.

보호 대상:

- 날짜
- 시간
- 금액
- URL
- 전화번호
- 준비물/제출물 glossary 용어
- 대상/학년/장소 같은 핵심 slot

---

## 현재 최종 구조

```text
sentence_list
  ↓
slot preservation
  - 날짜 / 시간 / 금액 / URL / 전화 / 대상 / 준비물 보호
  - 신청기간 / 운영일시 / 결과발표 / 문의 role 분리
  - 날짜·시간 fragment NLLB skip
  ↓
translation route decision
  A. 준비물/제출/납부/참석 문장 → template translation
  B. 일반 설명문 → NLLB
  C. URL/전화/날짜 fragment → translation skip
  ↓
glossary restoration
  ↓
review_required 판단
```

---

## API와의 관계

Gemini Vision이 도입되더라도 번역 파트가 사라지는 것은 아니다.

| 레이어 | 역할 |
| --- | --- |
| Gemini Vision | 문서에서 sentence_list 생성 |
| slot preservation | 사실값 보호 |
| NLLB | 일반 설명문 번역 |
| template translation | 준비물/제출물/비용 등 행동 문장 안정 번역 |
| glossary | 학교 도메인 용어 확정 번역 |
| review_required | 위험 출력 검수 표시 |

한 줄로 정리하면:

```text
Gemini는 문서를 구조화하고, 세종 파트는 번역 중 핵심 정보가 깨지지 않도록 통제한다.
```

---

## 보존할 실험 산출물

문서:

- `docs/nllb_vs_small100_result.md`
- `docs/small100_retest_plan.md`
- `docs/slot_protected_translation.md`
- `docs/template_translation_controlled_experiment_20260506.md`

스크립트:

- `translation/placeholder_survival_compare.py`
- `translation/template_translation_experiment.py`
- `translation/template_translation_expanded.py`
- `translation/protect_slots_demo.py`
- `translation/glossary_injection_compare.py`

결과:

- `outputs/glossary_placeholder_compare.csv`
- `outputs/glossary_placeholder_compare.md`
- `outputs/template_translation_compare.csv`
- `outputs/template_translation_compare.md`
- `outputs/template_translation_compare_expanded.csv`
- `outputs/template_translation_compare_expanded.md`

---

## 발표/공유용 한 줄

NLLB를 단순 호출하는 방식으로는 학교 안내문 핵심 정보가 깨질 수 있어, 날짜·시간·금액·URL·준비물 같은 slot을 먼저 보호하고, 준비물/제출물 문장은 템플릿 번역으로 우회하는 하이브리드 번역 안정화 구조로 개선했다.

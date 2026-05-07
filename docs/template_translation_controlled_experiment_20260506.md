# NLLB Controlled Template Translation Experiment

- 날짜: 2026-05-06
- 작업 위치: translation-tts-lab 개인 실험 레포
- 목표: Gemini/API 전환 없이 NLLB 기반 번역 품질을 전처리, glossary, slot 보호, 템플릿 번역으로 안정화

## 배경

기존 NLLB 번역은 학교 안내문 도메인에서 준비물, 제출물, 납부 항목 같은 짧은 명사구를 자주 오역했다. 괄호 힌트, prefix vocab, 직접치환, `__SLOT0__` 마스킹을 실험했지만 안정성이 충분하지 않았다.

이번 실험은 모든 문장을 자유 번역하지 않고, 학교 안내문에서 반복되는 행동 문장을 먼저 구조화한 뒤 번역 방식을 선택하는 방향으로 진행했다.

```text
원문 문장
-> 문장 유형 분류
-> 핵심 용어 추출
-> 대상/제출 대상/준비물 역할 분리
-> 템플릿 가능 문장은 템플릿 번역
-> 일반 문장은 NLLB fallback
```

## 실험 1: Placeholder 생존율

출력 파일:

- `outputs/glossary_placeholder_compare.csv`
- `outputs/glossary_placeholder_compare.md`
- `translation/placeholder_survival_compare.py`

핵심 결과:

| Placeholder 형식 | 생존율 | 용어 보존율 | 비고 |
|---|---:|---:|---|
| `AAAA/BBBB/CCCC` | 100% | 100% | 최상위 후보 |
| `XITEMX/YITEMY/ZITEMZ` | 100% | 100% | 최상위 후보 |
| `ITEMA/ITEMB/ITEMC` | 96% | 96% | 속도 우수 |
| `[ITEM_A]`, `<ITEM_A>`, `ITEM_A_TOKEN` | 낮음 | 낮음 | NLLB가 분해/삭제 |

해석:

- 기호 기반 placeholder는 NLLB/SentencePiece에서 깨지기 쉽다.
- 단순 대문자 토큰이 더 잘 살아남는다.
- 다만 placeholder 방식은 문장 구조 자체를 안정화하지 못하므로, 핵심 행동 문장에는 템플릿 방식이 더 적합하다.

## 실험 2: 8문장 Controlled Template Translation

출력 파일:

- `translation/template_translation_experiment.py`
- `outputs/template_translation_compare.csv`
- `outputs/template_translation_compare.md`

결과:

| 방식 | 핵심 용어 보존율 | 평균 추론시간 |
|---|---:|---:|
| Baseline NLLB | 1/17 (6%) | 0.87s |
| Strategy A 직접치환 | 9/17 (53%) | 0.84s |
| Template-based | 17/17 (100%) | 0.00s |

개선 내용:

- `전교생`은 준비물이 아니라 대상(audience)으로 분리
- `담임선생님`은 제출물이 아니라 제출 대상(recipient)으로 분리
- `수채화 물감` 안에서 `물감`이 중복 매칭되는 문제 제거
- 3개 이상 항목은 `A, B và C` 형태로 자연스럽게 나열

## 실험 3: 20문장 Expanded Template Translation

출력 파일:

- `translation/template_translation_expanded.py`
- `outputs/template_translation_compare_expanded.csv`
- `outputs/template_translation_compare_expanded.md`

추가한 케이스:

- 납부: 스쿨뱅킹 계좌, 체험학습비, 급식비 미납 금액
- 건강/안전: 발열, 기침, 등교 금지
- 제출: 참가 동의서, 학부모 상담 신청서, 방과후학교 수강신청서
- 준비물: 마스크, 개인 물병, 우산, 여벌 옷, 운동화

결과:

| 방식 | 핵심 용어 보존율 | 평균 추론시간 |
|---|---:|---:|
| Baseline NLLB | 5/37 (14%) | 0.82s |
| Strategy A 직접치환 | 15/37 (41%) | 0.79s |
| Template-based | 37/37 (100%) | 0.00s |

## 결론

이번 결과는 전체 번역 품질이 100%라는 뜻이 아니라, 실험 문장 내 핵심 학교 용어 보존율이 100%였다는 뜻이다. 하지만 서비스 관점에서는 중요한 의미가 있다.

```text
NLLB가 약한 구간을 모델 교체로만 해결하지 않고,
학교 안내문 문장 구조를 이용해 번역 모델의 자유도를 제한하면
핵심 정보 보존율을 크게 높일 수 있다.
```

즉, API로 덮는 방향이 아니라 NLLB 기반 파이프라인을 다음처럼 개선할 수 있다.

```text
NLLB baseline
+ glossary
+ slot 보호
+ 행동 문장 구조화
+ 템플릿 번역
+ review_required 검수 플래그
```

## 한계

- 현재 샘플은 사람이 설계한 controlled sample이다.
- 실제 가정통신문 30~50문장으로 확장 검증이 필요하다.
- 템플릿 문장은 용어 보존에는 강하지만, 조건절이나 부사구까지 자연스럽게 반영하려면 추가 slot 설계가 필요하다.
- 베트남어 외 7개 언어는 언어별 템플릿과 glossary 확장이 필요하다.

## 다음 작업

1. 실제 가정통신문에서 준비물/제출/납부/참여/건강 문장 30~50개 수집
2. template 적용 여부와 review_required 여부 기록
3. 날짜/금액/시간 placeholder 보호와 템플릿 번역 결합
4. 베트남어 템플릿을 먼저 안정화한 뒤 영어/중국어/일본어 등으로 확장
5. main pipeline에 넣기 전 개인 레포에서 회귀 테스트 구축

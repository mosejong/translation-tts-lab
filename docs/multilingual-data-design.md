# Multilingual Data Design

## Goal

가정통신문 번역/TTS 기능은 베트남어를 기준 언어로 먼저 검증하되, 이후 영어, 중국어, 일본어 등으로 확장할 수 있어야 합니다.

핵심 원칙:

- 한국어 기준 문장은 하나로 관리합니다.
- 언어별 번역문은 별도 행으로 관리합니다.
- 언어별 용어 사전은 분리합니다.
- 모델 파인튜닝 데이터와 검수 데이터는 같은 구조에서 뽑을 수 있게 합니다.

## Recommended Format

다국어 데이터는 wide format보다 long format을 권장합니다.

### Wide Format

```csv
id,ko,vi,en,zh,ja
135,다음 주 월요일까지...,Vui lòng...,Please...,请...,来週...
```

장점:

- 사람이 한 행에서 여러 언어를 보기 쉽습니다.

단점:

- 언어가 늘어날수록 컬럼이 계속 늘어납니다.
- 언어별 검수 상태를 관리하기 어렵습니다.
- 특정 언어만 학습 데이터로 뽑기 불편합니다.

### Long Format

```csv
id,lang,source_type,category,ko,target_text,review_status
135,vi,초등학교,제출,다음 주 월요일까지...,Vui lòng...,reviewed
135,en,초등학교,제출,다음 주 월요일까지...,Please...,sample
135,zh,초등학교,제출,다음 주 월요일까지...,请...,sample
```

장점:

- 언어를 추가해도 컬럼 구조가 변하지 않습니다.
- 언어별 검수 상태를 따로 관리할 수 있습니다.
- 특정 언어만 쉽게 필터링해서 학습 데이터로 만들 수 있습니다.
- TTS 대상 언어도 같은 구조로 연결할 수 있습니다.

## Proposed Columns

| Column | Meaning |
| --- | --- |
| `id` | 원본 샘플 id |
| `lang` | 대상 언어 코드, 예: `vi`, `en`, `zh`, `ja` |
| `source_type` | 초등학교 / 유치원 |
| `category` | 제출 / 준비물 / 비용 / 일정 / 건강·안전 / 기타 |
| `ko` | 쉬운 한국어 기준 문장 |
| `target_text` | 대상 언어 번역문 |
| `review_status` | `pending`, `reviewed`, `sample`, `rejected` |
| `review_note` | 검수 메모 |
| `tts_target` | 음성 안내 대상 여부 |

## File Plan

```text
translation/
  glossary_vi.csv
  glossary_en.csv
  glossary_zh.csv
  glossary_ja.csv

outputs/translation/
  review_batch_001_merged.csv
  review_batch_002_merged.csv
  parallel_train_candidates.csv
  multilingual_pairs.csv
```

## Language Strategy

### Phase 1: Vietnamese Deep Validation

- 베트남어 100개 이상 검수
- 용어 사전 구축
- 오역 패턴 수집
- LoRA 파인튜닝 실험
- 베트남어 TTS 연결

### Phase 2: Multilingual Sample Validation

- 영어, 중국어, 일본어 등은 각 10~20개 샘플만 검수
- 데이터 구조가 언어 확장에 대응 가능한지 확인
- 언어별 용어 사전 파일만 추가

### Phase 3: Language Expansion

- 사용자가 많은 언어부터 검수 데이터 확대
- 언어별 모델 또는 다국어 모델 성능 비교
- TTS 지원 여부 확인

## Why Vietnamese First

프로젝트 대상은 베트남 결혼이민 학부모이므로 베트남어를 기준 언어로 깊게 검증합니다.

다만 서비스 구조는 베트남어에 고정하지 않고, 같은 한국어 기준 문장과 같은 검수 파이프라인을 사용해 다른 언어로 확장할 수 있게 설계합니다.

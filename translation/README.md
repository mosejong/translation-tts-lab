# Translation Experiment

한국어 가정통신문 문장을 다국어로 번역하고, 학교 도메인 용어사전과 Gemini-as-Judge로 품질을 검증하는 실험입니다.

## Current Scripts

| Script | Purpose |
| --- | --- |
| `run_mvp_pipeline.py` | 쉬운 한국어 -> NLLB 번역 -> 용어사전 검수 -> TTS MVP 실행 |
| `run_ab_compare.py` | A(원문 전체) vs B(TODO만) 입력량/속도 비교 |
| `run_ab_quality_eval.py` | A/B 번역 품질 평가. 현지 자연스러움과 Round-trip 검사 포함 |
| `run_glossary_compare.py` | NLLB 원번역의 용어사전 반영률 확인 |
| `run_quality_eval.py` | 용어사전 전/후 품질 평가 |
| `fill_glossary_all_langs.py` | 비어 있는 언어 컬럼을 Gemini로 채움 |
| `validate_glossary_with_gemini.py` | 용어사전 항목 검수 |

## Latest Result Snapshot

| Metric | Result |
| --- | ---: |
| A/B 입력 단축 | -30.1% |
| A/B 속도향상 | x1.84 |
| A/B 품질평가 | A 45.8 / B 50.1 |
| 용어사전 전/후 품질평가 | 39.0 -> 89.6 |

공유용 요약은 `../docs/share-summary-2026-04-28-quality-eval.md`를 참고하세요.

## Base Model

- Model: `facebook/nllb-200-distilled-600M`
- Korean source language code: `kor_Hang`
- Vietnamese target language code: `vie_Latn`
- Default source column: `easy_korean`

## Run

`cmd` 기준:

```cmd
chcp 65001
```

```cmd
docker compose run --rm lab python translation/run_nllb_translate.py --input data/notice_sample_v3.csv --output outputs/translation/nllb_v3_20.csv --limit 20
```

원문 컬럼으로 테스트:

```cmd
docker compose run --rm lab python translation/run_nllb_translate.py --input data/notice_sample_v3.csv --output outputs/translation/nllb_v3_original_20.csv --text-column original_text --limit 20
```

## Check Result

```cmd
python -c "import csv; f=open('outputs/translation/nllb_v3_20.csv',encoding='utf-8'); r=csv.DictReader(f); [print(row['id']+'. '+row['source_text']+'\n=> '+row['prediction_vi']+'\n') for row in r]"
```

## What To Check

- 날짜와 시간이 유지되는가
- 금액이 유지되는가
- `제출`, `준비`, `납부`, `연락` 같은 행동이 맞는가
- 학교/유치원 용어가 엉뚱하게 번역되지 않는가
- 학부모가 이해할 수 있는 짧은 문장인가

## Known Weak Terms

현재 기본 NLLB 결과에서 특히 조심해야 하는 용어입니다.

| Korean | Preferred Vietnamese |
| --- | --- |
| 앞치마 | tạp dề |
| 머릿수건 | khăn trùm đầu |
| 체험학습 | hoạt động trải nghiệm |
| 현장체험학습 | chuyến tham quan học tập |
| 원복 | đồng phục |
| 도화지 | giấy vẽ |
| 색칠 도구 | dụng cụ tô màu |
| 정서행동 검사 | kiểm tra đặc điểm cảm xúc và hành vi |
| 돌봄교실 | lớp chăm sóc sau giờ học |
| 방과후학교 | lớp sau giờ học |
| 하원 | giờ đón trẻ |
| 등원 | giờ đưa trẻ đến lớp |

용어 사전 파일:

```cmd
type translation\term_glossary.csv
```

명백한 오역 목록:

```cmd
type translation\bad_terms.csv
```

예시:

```text
앞치마와 머릿수건을 준비해 주세요
잘못된 번역: Hãy chuẩn bị đầu gối và đầu gối.
문제: đầu gối = 무릎
권장: Hãy chuẩn bị tạp dề và khăn trùm đầu.
```

## Quality Check Script

번역 결과에서 알려진 오역을 자동 표시합니다.

```cmd
python translation\check_translation_quality.py --input outputs\translation\nllb_v3_20.csv --output outputs\translation\nllb_v3_20_checked.csv
```

결과 확인:

```cmd
python -c "import csv; f=open('outputs/translation/nllb_v3_20_checked.csv',encoding='utf-8'); r=csv.DictReader(f); [print(row['id'], row['quality_label'], row['quality_note']) for row in r]"
```

## Export Vietnamese Text

베트남어 문장만 복붙하기 쉽게 `txt`로 뽑습니다.

```cmd
python translation\export_vietnamese_for_review.py --input outputs\translation\nllb_v3_20.csv --output outputs\translation\vietnamese_only.txt --review-output outputs\translation\vietnamese_review.txt
```

파일 확인:

```cmd
type outputs\translation\vietnamese_only.txt
```

두 파일이 만들어집니다.

| File | Use |
| --- | --- |
| `outputs\translation\vietnamese_only.txt` | 베트남어 문장만 번호 붙여 복붙 |
| `outputs\translation\vietnamese_review.txt` | 한국어 원문과 베트남어 번역을 같이 보며 검수 |

## Select Next Review Batch

용어 사전, 비용, 날짜, 제출/준비 행동이 들어간 문장을 우선으로 다음 검수 샘플을 뽑습니다.

```cmd
python translation\select_review_samples.py --input data\notice_sample_v3.csv --output outputs\translation\review_batch_001.csv --review-output outputs\translation\review_batch_001.txt --limit 30 --exclude-ids 1-20
```

검수 담당에게 줄 파일:

```cmd
type outputs\translation\review_batch_001.txt
```

## Merge Human Translation

검수 담당이 채운 베트남어 번역은 아래 형식의 CSV로 저장합니다.

```csv
id,source_type,category,easy_korean,human_vi,review_status
135,초등학교,제출,다음 주 월요일까지 현장체험학습 신청서를 내 주세요,Vui lòng nộp đơn xin học tập trải nghiệm trước thứ Hai tuần sau.,reviewed
```

병합 실행:

```cmd
python translation\merge_human_translations.py --batch outputs\translation\review_batch_001.csv --human outputs\translation\human_translation_batch_001_partial.csv --output outputs\translation\review_batch_001_merged.csv
```

`review_status`가 `reviewed`인 행은 파인튜닝 정답 후보로 쓰고, `pending`인 행은 추가 검수 대상으로 남깁니다.

빈 검수 템플릿을 먼저 만들 수 있습니다.

```cmd
python translation\create_human_template.py --batch outputs\translation\review_batch_002.csv --output outputs\translation\human_translation_batch_002_partial.csv
```

여러 배치를 합쳐 파인튜닝 후보 파일을 만들 수 있습니다.

```cmd
python translation\build_parallel_dataset.py --input outputs\translation\review_batch_001_merged.csv outputs\translation\review_batch_002_merged.csv --output outputs\translation\parallel_train_candidates.csv
```

검수 부담을 줄이려면 5개씩 쪼개서 줄 수 있습니다.

```cmd
python translation\split_review_batch.py --batch-csv outputs\translation\review_batch_002.csv --output-dir outputs\translation\review_batch_002_parts --chunk-size 5
```

목표 개수까지 여러 배치를 미리 만들 수 있습니다.

```cmd
python translation\make_review_batches.py --start-batch 2 --batch-count 3 --batch-size 30 --exclude-ids 1-20
```

이 명령은 `review_batch_002.txt`, `review_batch_003.txt`, `review_batch_004.txt`처럼 파일을 미리 만들어 줍니다.

## Fine-Tuning Plan

파인튜닝은 바로 시작하기보다 정답 번역 데이터를 먼저 채운 뒤 진행합니다.

1. `vietnamese` 빈 칸을 채운다.
2. 20개 단위로 NLLB 결과와 정답을 비교한다.
3. 자주 틀리는 용어 사전을 만든다.
4. train / validation 파일을 나눈다.
5. LoRA 또는 full fine-tuning 중 하나를 선택한다.

현재 200개 데이터는 파인튜닝 실험의 시작점으로는 괜찮지만, 안정적인 번역 모델을 만들기에는 부족합니다. 우선은 용어 보정과 정답 번역 누적이 중요합니다.

# Translation TTS Lab

Python 3.11 Docker 환경에서 한국어 가정통신문을 베트남어로 번역하고, 베트남어 TTS까지 실험하는 로컬 작업 폴더입니다.

이 폴더는 서비스 repo와 분리해서 사용합니다. 모델 다운로드, 실험 결과, wav 파일이 `multicultural-ai` repo에 섞이지 않게 하기 위한 목적입니다.

## Current Goal

현재 목표는 바로 백엔드에 붙이는 것이 아니라, 아래 순서로 모델 품질을 확인하는 것입니다.

1. NLLB 기본 번역 결과를 만든다.
2. 날짜, 금액, 제출/준비 행동, 학교 용어가 잘 번역되는지 확인한다.
3. 자주 틀리는 용어를 정리한다.
4. `vietnamese` 정답 데이터를 채운다.
5. 정답 데이터가 충분해지면 번역 모델 파인튜닝을 시도한다.
6. 좋은 번역문만 TTS에 넣어 음성 품질을 확인한다.

## Structure

```text
translation-tts-lab/
  data/                 # copied sample csv files
  translation/          # NLLB translation experiment
  tts/                  # MMS-TTS experiment
  outputs/              # generated csv/wav outputs, ignored by git
  models/               # Hugging Face cache, ignored by git
```

## Current Key Outputs

현재 바로 참고할 핵심 산출물은 아래 두 개입니다.

| File | Use |
| --- | --- |
| `outputs/translation/parallel_train_candidates.csv` | 베트남어 파인튜닝 후보 데이터, `ko` -> `vi` |
| `outputs/translation/multilingual_pairs.csv` | 다국어 확장용 long format 데이터 |

중간 산출물은 아래 폴더로 옮겨 보관합니다.

```text
outputs/translation/old/
```

예: 검수 요청 배치, partial CSV, NLLB 20개 테스트 결과, 베트남어 추출 txt 등

## Build

`cmd` 기준:

```cmd
chcp 65001
```

```cmd
docker compose build
```

## Run Translation

처음에는 20개만 돌립니다.

```cmd
docker compose run --rm lab python translation/run_nllb_translate.py --input data/notice_sample_v3.csv --output outputs/translation/nllb_v3_20.csv --limit 20
```

결과를 보기 좋게 확인합니다.

```cmd
python -c "import csv; f=open('outputs/translation/nllb_v3_20.csv',encoding='utf-8'); r=csv.DictReader(f); [print(row['id']+'. '+row['source_text']+'\n=> '+row['prediction_vi']+'\n') for row in r]"
```

## Run TTS

번역 결과를 먼저 확인한 뒤, 5개만 음성으로 테스트합니다.

```cmd
docker compose run --rm lab python tts/run_mms_tts.py --input outputs/translation/nllb_v3_20.csv --output-dir outputs/tts/vie --limit 5
```

출력 파일 확인:

```cmd
dir outputs\tts\vie
```

## Fine-Tuning Direction

지금 데이터 200개만으로 처음부터 번역 모델을 새로 만드는 것은 어렵습니다. 현실적인 방향은 사전학습 모델을 가져와서 우리 가정통신문 데이터로 파인튜닝하는 것입니다.

파인튜닝 전에 먼저 해야 할 일:

- `vietnamese` 빈 칸을 사람이 검수한 정답 번역으로 채우기
- 자주 틀리는 용어 사전 만들기
- `easy_korean` 문장을 더 짧고 일관되게 다듬기
- train / validation 분리하기
- 20개 단위로 번역 품질을 수동 평가하기

## Quality Labels

번역 결과를 볼 때 아래처럼 문제 유형을 표시하면 좋습니다.

| Label | Meaning |
| --- | --- |
| `good` | 그대로 사용 가능 |
| `date_missing` | 날짜, 시간, 요일 누락 |
| `money_wrong` | 금액, 납부 정보 오류 |
| `wrong_action` | 제출/준비/납부/연락 행동 오류 |
| `wrong_term` | 체험학습, 원복, 돌봄교실 등 용어 오류 |
| `awkward` | 의미는 맞지만 표현이 어색함 |

## Models

- Translation: `facebook/nllb-200-distilled-600M`
- Vietnamese TTS: `facebook/mms-tts-vie`

첫 실행 때는 모델 파일이 `models/` 아래로 다운로드됩니다.

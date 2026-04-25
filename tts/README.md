# TTS Experiment

베트남어 번역문을 음성 파일로 만드는 실험입니다.

## Base Model

- Model: `facebook/mms-tts-vie`
- Input: Vietnamese text
- Output: `.wav`

## Run

번역 결과 CSV를 만든 뒤 실행합니다.

```cmd
docker compose run --rm lab python tts/run_mms_tts.py --input outputs/translation/nllb_v3_20.csv --text-column prediction_vi --output-dir outputs/tts/vie --limit 5
```

결과 확인:

```cmd
dir outputs\tts\vie
```

## What To Check

- 발음이 알아들을 만한가
- 속도가 너무 빠르거나 느리지 않은가
- 날짜와 시간이 어색하게 읽히지 않는가
- 금액을 알아듣기 쉽게 읽는가
- `Kids Note`, 학교 앱, 스쿨뱅킹 같은 외래어/서비스명이 이상하지 않은가

## Important

TTS는 번역 결과가 괜찮은 문장만 넣어야 합니다. 번역문이 어색하면 음성이 자연스러워도 실제 서비스 품질은 좋아지지 않습니다.

## Fine-Tuning Direction

TTS 모델을 직접 파인튜닝하려면 텍스트와 음성 쌍 데이터가 필요합니다. 지금 우리에게는 음성 데이터가 없기 때문에, 당장은 TTS 파인튜닝보다 아래 작업이 먼저입니다.

1. 번역문 품질 확인
2. 베트남어 문장 길이 줄이기
3. 날짜/금액 읽기 좋은 형태로 전처리
4. MMS-TTS 기본 음성 품질 확인
5. 필요하면 나중에 별도 음성 데이터 수집

즉, 현재 단계에서 파인튜닝 우선순위는 번역 모델이 먼저이고 TTS는 기본 모델 품질 평가가 먼저입니다.

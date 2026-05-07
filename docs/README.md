# Docs

Translation TTS Lab의 번역/TTS 실험 문서를 정리하는 폴더입니다.

## 핵심 문서

| File | Purpose |
| --- | --- |
| `translation-model-strategy-2026-05-07.md` | NLLB 유지, SMaLL-100 비교, slot/template 번역 전략 최종 정리 |
| `nllb_vs_small100_result.md` | NLLB와 SMaLL-100 비교 실험 결과 |
| `small100_retest_plan.md` | SMaLL-100 재실험 계획 |
| `slot_protected_translation.md` | 날짜/시간/금액/URL/전화번호 보호 번역 설계 |
| `template_translation_controlled_experiment_20260506.md` | 준비물/제출물 템플릿 번역 실험 정리 |
| `presentation-evidence.md` | 발표 근거 정리 |
| `multilingual-data-design.md` | 다국어 데이터 구조 설계 |

## 현재 결론

```text
NLLB baseline 유지
SMaLL-100은 원본 품질 불안정으로 서비스 모델 탈락
Gemini/API 번역 전면 교체는 하지 않음
핵심 정보는 slot으로 보호
준비물/제출물 문장은 template translation 적용
일반 설명문만 NLLB fallback
```

## OCR 문서 위치

OCR 관련 문서와 코드 스냅샷은 별도 OCR 레포에서 관리합니다.

```text
ocr_lab_schoolbridge/docs/schoolbridge-pivot/
ocr_lab_schoolbridge/archive/schoolbridge-integration/
```

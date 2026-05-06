# NLLB vs SMaLL-100 Korean-to-Vietnamese Comparison

Date: 2026-05-06
Eval set: `data/school_notice_eval_ko_20260506.csv`
Output CSV: `outputs/model_compare/small100_vs_nllb_vi.csv`
Target language: `vi`
Sample size: 20 school-notice sentences
Device: CPU
Beam size: 2

## Result Snapshot

| Model | Avg generation time | Observed quality |
|---|---:|---|
| NLLB-200-distilled-600M | 4.565 sec/sentence | More stable than SMaLL-100, but still weak on school-domain terms |
| SMaLL-100 | 2.037 sec/sentence | About 2.24x faster, but frequent semantic drift/repetition |

## Key Findings

- SMaLL-100 loads successfully with the repository-specific `tokenization_small100.py` tokenizer.
- The standard `AutoTokenizer` path is unsafe for this model because it may use the base M2M100 tokenizer behavior and produce the wrong target language.
- SMaLL-100 can produce Vietnamese output for Korean input after using its tokenizer prefix behavior.
- SMaLL-100 is faster on CPU, but quality is not yet reliable enough for direct adoption.
- Both models struggle with school-domain phrases, which supports keeping glossary/post-processing in the pipeline.

## Decision

SMaLL-100 remains a lightweight experiment candidate, not a production replacement yet.

Recommended next step:

1. Manually review 20 rows in `small100_vs_nllb_vi.csv`.
2. Mark `winner` and `note`.
3. If SMaLL-100 loses most rows due to semantic drift/repetition, drop it as the fine-tuning base and test another lightweight candidate.
4. Keep NLLB as the baseline/service model until a lightweight model proves acceptable quality.

"""Compare NLLB and SMaLL-100 on the school-notice Korean eval set.

Examples:
    python translation/compare_translation_models.py --limit 20 --target-lang vi
    python translation/compare_translation_models.py --models nllb small100 --device cpu
"""
import argparse
import io
import csv
import importlib.util
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL = ROOT / "data" / "school_notice_eval_ko_20260506.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "model_compare" / "small100_vs_nllb_vi.csv"
HF_HOME = ROOT / "models" / "huggingface"

NLLB_MODEL = "facebook/nllb-200-distilled-600M"
SMALL100_MODEL = "alirezamsh/small100"
NLLB_SOURCE_LANG = "kor_Hang"

NLLB_LANG = {
    "vi": "vie_Latn",
    "en": "eng_Latn",
    "zh": "zho_Hans",
    "th": "tha_Thai",
    "ms": "zsm_Latn",
    "mn": "khk_Cyrl",
    "ru": "rus_Cyrl",
    "ja": "jpn_Jpan",
}

SMALL100_LANG = {
    "vi": "vi",
    "en": "en",
    "zh": "zh",
    "th": "th",
    "ms": "ms",
    "mn": "mn",
    "ru": "ru",
    "ja": "ja",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Compare NLLB and SMaLL-100 on a Korean school-notice eval set.")
    parser.add_argument("--input", type=Path, default=DEFAULT_EVAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target-lang", default="vi", choices=sorted(NLLB_LANG))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--models", nargs="+", default=["nllb", "small100"], choices=["nllb", "small100"])
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--num-beams", type=int, default=4)
    parser.add_argument("--repetition-penalty", type=float, default=1.3)
    parser.add_argument("--no-repeat-ngram-size", type=int, default=3)
    parser.add_argument("--length-penalty", type=float, default=1.0)
    parser.add_argument("--slot-test", action="store_true",
                        help="Run __SLOT0__ placeholder survival check before main eval")
    return parser.parse_args()


def main():
    args = parse_args()
    configure_cache()
    device = resolve_device(args.device)
    rows = read_eval_rows(args.input, args.limit)

    translators = {}
    if "nllb" in args.models:
        translators["nllb"] = load_nllb(device, args.target_lang)
    if "small100" in args.models:
        translators["small100"] = load_small100(device, args.target_lang)

    gen_kwargs = {
        "max_new_tokens": args.max_new_tokens,
        "num_beams": args.num_beams,
        "repetition_penalty": args.repetition_penalty,
        "no_repeat_ngram_size": args.no_repeat_ngram_size,
        "length_penalty": args.length_penalty,
    }
    print(f"Generation params: {gen_kwargs}")

    if args.slot_test:
        run_slot_survival_test(translators, gen_kwargs)

    output_rows = []
    for idx, row in enumerate(rows, start=1):
        text = row["text_ko"]
        print(f"[{idx}/{len(rows)}] {row['eval_id']} {text[:60]}")
        out = {
            "eval_id": row["eval_id"],
            "text_ko": text,
            "eval_focus": row.get("eval_focus", ""),
            "matched_terms": row.get("matched_terms", ""),
            "target_lang": args.target_lang,
            "nllb_translation": "",
            "nllb_time_sec": "",
            "small100_translation": "",
            "small100_time_sec": "",
            "winner": "",
            "note": "",
        }
        for name, translator in translators.items():
            translated, elapsed = translator.translate(text, **gen_kwargs)
            repeat_flag = _detect_repetition(translated)
            out[f"{name}_translation"] = translated
            out[f"{name}_time_sec"] = f"{elapsed:.3f}"
            flag = " [REPEAT]" if repeat_flag else ""
            print(f"  - {name}: {elapsed:.2f}s{flag} | {translated[:90]}")
        output_rows.append(out)

    write_csv(args.output, output_rows)
    print(f"Saved {len(output_rows)} rows to {args.output}")


class NllbTranslator:
    def __init__(self, tokenizer, model, device, target_lang):
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.target_id = tokenizer.convert_tokens_to_ids(NLLB_LANG[target_lang])

    def translate(self, text, max_new_tokens=160, num_beams=4,
                  repetition_penalty=1.3, no_repeat_ngram_size=3, length_penalty=1.0):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=384).to(self.device)
        start = time.perf_counter()
        with torch.no_grad():
            tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.target_id,
                max_new_tokens=max_new_tokens,
                num_beams=num_beams,
                repetition_penalty=repetition_penalty,
                no_repeat_ngram_size=no_repeat_ngram_size,
                length_penalty=length_penalty,
            )
        elapsed = time.perf_counter() - start
        return self.tokenizer.batch_decode(tokens, skip_special_tokens=True)[0], elapsed


class Small100Translator:
    def __init__(self, tokenizer, model, device, target_lang):
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.target_lang = SMALL100_LANG[target_lang]
        self.tokenizer.src_lang = "ko"
        self.tokenizer.tgt_lang = self.target_lang

    def translate(self, text, max_new_tokens=160, num_beams=4,
                  repetition_penalty=1.3, no_repeat_ngram_size=3, length_penalty=1.0):
        self.tokenizer.src_lang = "ko"
        self.tokenizer.tgt_lang = self.target_lang
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=384).to(self.device)
        start = time.perf_counter()
        with torch.no_grad():
            tokens = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=num_beams,
                repetition_penalty=repetition_penalty,
                no_repeat_ngram_size=no_repeat_ngram_size,
                length_penalty=length_penalty,
            )
        elapsed = time.perf_counter() - start
        return self.tokenizer.batch_decode(tokens, skip_special_tokens=True)[0], elapsed


SLOT_TEST_SAMPLES = [
    ("신청은 __SLOT0__ 에서 문의는 __SLOT1__", ["__SLOT0__", "__SLOT1__"]),
    ("__SLOT0__까지 제출해 주세요", ["__SLOT0__"]),
    ("참가비 __SLOT0__ 납부", ["__SLOT0__"]),
]


def _detect_repetition(text: str) -> bool:
    if len(text) < 20:
        return False
    prefix = text[:20]
    return text.count(prefix) > 3


def run_slot_survival_test(translators: dict, gen_kwargs: dict) -> None:
    print("\n── Slot placeholder survival test ──")
    all_pass = True
    for text, expected_slots in SLOT_TEST_SAMPLES:
        for name, translator in translators.items():
            result, _ = translator.translate(text, **gen_kwargs)
            passed = all(slot in result for slot in expected_slots)
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
            print(f"  [{status}] {name} | in={text!r} | out={result!r}")
    if not all_pass:
        print("  WARNING: slot survival failed — service integration NOT safe for this model.")
    else:
        print("  All slots survived.")
    print()


def configure_cache():
    HF_HOME.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(HF_HOME))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(HF_HOME / "hub"))


def resolve_device(value):
    if value == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if value == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false.")
    return value


def load_nllb(device, target_lang):
    print(f"Loading {NLLB_MODEL} on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL, src_lang=NLLB_SOURCE_LANG)
    model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL).to(device)
    model.eval()
    return NllbTranslator(tokenizer, model, device, target_lang=target_lang)


def load_small100(device, target_lang):
    print(f"Loading {SMALL100_MODEL} on {device}...")
    model = AutoModelForSeq2SeqLM.from_pretrained(SMALL100_MODEL).to(device)
    model.eval()
    tokenizer = load_small100_tokenizer(target_lang)
    return Small100Translator(tokenizer, model, device, target_lang=target_lang)


def load_small100_tokenizer(target_lang):
    # SMaLL-100 modifies the M2M100 tokenizer language-prefix behavior.
    # AutoTokenizer may silently load the base M2M100 tokenizer, which can produce
    # the wrong target language, so always import the repo tokenizer explicitly.
    tgt = SMALL100_LANG[target_lang]
    tokenizer_py = ensure_small100_tokenizer_file()
    spec = importlib.util.spec_from_file_location("tokenization_small100", tokenizer_py)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {tokenizer_py}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["tokenization_small100"] = module
    spec.loader.exec_module(module)
    tokenizer = module.SMALL100Tokenizer.from_pretrained(SMALL100_MODEL, tgt_lang=tgt)
    tokenizer.src_lang = "ko"
    tokenizer.tgt_lang = tgt
    return tokenizer


def ensure_small100_tokenizer_file():
    local_path = ROOT / "translation" / "vendor" / "tokenization_small100.py"
    if local_path.exists():
        return local_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError("huggingface_hub is required to fetch tokenization_small100.py") from exc
    downloaded = Path(hf_hub_download(repo_id=SMALL100_MODEL, filename="tokenization_small100.py"))
    local_path.write_text(downloaded.read_text(encoding="utf-8"), encoding="utf-8")
    return local_path


def read_eval_rows(path, limit):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return rows[:limit] if limit else rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "eval_id", "text_ko", "eval_focus", "matched_terms", "target_lang",
        "nllb_translation", "nllb_time_sec",
        "small100_translation", "small100_time_sec",
        "winner", "note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

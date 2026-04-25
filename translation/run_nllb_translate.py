import argparse
import csv
from pathlib import Path

import torch
from tqdm import tqdm
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = "facebook/nllb-200-distilled-600M"
SOURCE_LANG = "kor_Hang"
TARGET_LANG = "vie_Latn"


def parse_args():
    parser = argparse.ArgumentParser(description="Run Korean to Vietnamese translation with NLLB.")
    parser.add_argument("--input", default="data/notice_sample_v3.csv")
    parser.add_argument("--output", default="outputs/translation/nllb_predictions.csv")
    parser.add_argument("--text-column", default="easy_korean", choices=["easy_korean", "original_text"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--max-length", type=int, default=128)
    return parser.parse_args()


def main():
    args = parse_args()
    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available. Falling back to CPU.")
        device = "cpu"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang=SOURCE_LANG)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
    model.eval()

    rows = read_rows(Path(args.input), args.limit)
    target_lang_id = tokenizer.convert_tokens_to_ids(TARGET_LANG)
    output_rows = []

    for row in tqdm(rows, desc="Translating"):
        source_text = row[args.text_column].strip()
        prediction = translate_one(source_text, tokenizer, model, target_lang_id, device, args.max_length)
        output_rows.append({
            "id": row["id"],
            "source_type": row["source_type"],
            "category": row["category"],
            "source_text": source_text,
            "reference_vi": row.get("vietnamese", ""),
            "prediction_vi": prediction,
        })

    write_rows(Path(args.output), output_rows)
    print(f"Saved {len(output_rows)} rows to {args.output}")


def read_rows(path, limit):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return rows[:limit] if limit > 0 else rows


def translate_one(source_text, tokenizer, model, target_lang_id, device, max_length):
    inputs = tokenizer(source_text, return_tensors="pt", truncation=True, max_length=max_length).to(device)
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=max_length,
            num_beams=4,
        )
    return tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0]


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "source_type", "category", "source_text", "reference_vi", "prediction_vi"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
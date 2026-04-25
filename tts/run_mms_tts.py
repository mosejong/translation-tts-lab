import argparse
import csv
import re
from pathlib import Path

import torch
from scipy.io.wavfile import write as write_wav
from tqdm import tqdm
from transformers import AutoTokenizer, VitsModel

MODEL_NAME = "facebook/mms-tts-vie"


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Vietnamese TTS wav files with MMS-TTS.")
    parser.add_argument("--input", default="outputs/translation/nllb_predictions.csv")
    parser.add_argument("--text-column", default="prediction_vi")
    parser.add_argument("--output-dir", default="outputs/tts/vie")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    return parser.parse_args()


def main():
    args = parse_args()
    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available. Falling back to CPU.")
        device = "cpu"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = VitsModel.from_pretrained(MODEL_NAME).to(device)
    model.eval()

    rows = read_rows(Path(args.input), args.limit)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, row in enumerate(tqdm(rows, desc="Generating TTS"), start=1):
        text = row.get(args.text_column, "").strip()
        if not text:
            continue
        wav_path = output_dir / f"{index:03d}_{safe_name(row.get('id', str(index)))}.wav"
        generate_one(text, tokenizer, model, wav_path, device)

    print(f"Saved wav files to {output_dir}")


def read_rows(path, limit):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return rows[:limit] if limit > 0 else rows


def generate_one(text, tokenizer, model, wav_path, device):
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model(**inputs).waveform
    waveform = output.squeeze().detach().cpu().numpy()
    write_wav(wav_path, model.config.sampling_rate, waveform)


def safe_name(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_") or "sample"


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Fine-tune Qwen 2.5 0.5B Instruct for per-language Parlance SLM.

Trains two separate LoRA adapters — one for Spanish, one for French —
on top of the same base model. Each adapter learns dialect-aware grammar
feedback for interpreter training.

Usage:
    pip install -r requirements.txt

    # Spanish
    python finetune_slm.py --lang es --epochs 3

    # French
    python finetune_slm.py --lang fr --epochs 3

    # Both sequentially
    python finetune_slm.py --lang both --epochs 3

Output (under this script's directory):
    models/parlance-es/   (merged model + tokenizer)
    models/parlance-fr/   (merged model + tokenizer)
"""

import argparse
import json
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTTrainer, SFTConfig


BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
TRAINING_DIR = Path(__file__).resolve().parent

LANG_DIRS = {
    "es": TRAINING_DIR / "data" / "spanish",
    "fr": TRAINING_DIR / "data" / "french",
}


def load_dataset_from_jsonl(path: Path) -> Dataset:
    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            examples.append(json.loads(line))
    return Dataset.from_list(examples)


def format_chat(example, tokenizer):
    text = tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False
    )
    return {"text": text}


def finetune_language(lang: str, epochs: int, batch_size: int, lr: float, max_seq_len: int):
    lang_name = "Spanish" if lang == "es" else "French"
    lang_dir = LANG_DIRS[lang]
    output_dir = TRAINING_DIR / "models" / f"parlance-{lang}"
    checkpoint_dir = TRAINING_DIR / "checkpoints" / f"parlance-{lang}"

    print(f"\n{'='*60}")
    print(f"  Fine-tuning Parlance SLM — {lang_name}")
    print(f"  Base model: {BASE_MODEL}")
    print(f"  Train: {lang_dir / 'train.jsonl'}")
    print(f"  Valid: {lang_dir / 'valid.jsonl'}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}\n")

    train_ds = load_dataset_from_jsonl(lang_dir / "train.jsonl")
    valid_ds = load_dataset_from_jsonl(lang_dir / "valid.jsonl")
    print(f"  Train examples: {len(train_ds)}")
    print(f"  Valid examples: {len(valid_ds)}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_ds = train_ds.map(lambda ex: format_chat(ex, tokenizer))
    valid_ds = valid_ds.map(lambda ex: format_chat(ex, tokenizer))

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
    )

    model = get_peft_model(model, lora_config)
    trainable, total = model.get_nb_trainable_parameters()
    print(f"  Trainable parameters: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    training_args = SFTConfig(
        output_dir=str(checkpoint_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=lr,
        weight_decay=0.01,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=2,
        logging_steps=10,
        bf16=True,
        max_seq_length=max_seq_len,
        dataset_text_field="text",
        packing=True,
        report_to="none",
        seed=42,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=valid_ds,
        tokenizer=tokenizer,
    )

    print("\n  Starting training...\n")
    trainer.train()

    final_eval = trainer.evaluate()
    print(f"\n  Final eval loss: {final_eval['eval_loss']:.4f}")

    print(f"\n  Merging LoRA weights and saving to {output_dir}...")
    merged = model.merge_and_unload()
    merged.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    print(f"  Done — {lang_name} SLM saved to {output_dir}\n")
    return final_eval


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Parlance SLM")
    parser.add_argument("--lang", choices=["es", "fr", "both"], default="both")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-seq-len", type=int, default=1024)
    args = parser.parse_args()

    results = {}

    if args.lang in ("es", "both"):
        results["es"] = finetune_language("es", args.epochs, args.batch_size, args.lr, args.max_seq_len)

    if args.lang in ("fr", "both"):
        results["fr"] = finetune_language("fr", args.epochs, args.batch_size, args.lr, args.max_seq_len)

    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    for lang, res in results.items():
        name = "Spanish" if lang == "es" else "French"
        print(f"  {name}: eval_loss = {res['eval_loss']:.4f}")
    print()


if __name__ == "__main__":
    main()

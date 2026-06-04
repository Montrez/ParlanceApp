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

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import torch
from datasets import Dataset
from peft import LoraConfig, PeftModel, get_peft_model, TaskType
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
    messages = example.get("messages") or []
    if len(messages) < 2:
        raise ValueError("example missing chat messages")
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )
    return {"text": text}


def latest_checkpoint(checkpoint_dir: Path) -> Optional[Path]:
    """Newest `checkpoint-N` directory under the language checkpoint folder."""
    dirs = [d for d in checkpoint_dir.glob("checkpoint-*") if d.is_dir()]
    if not dirs:
        return None

    def step_num(path: Path) -> int:
        try:
            return int(path.name.split("-", 1)[1])
        except (IndexError, ValueError):
            return 0

    return max(dirs, key=step_num)


def finetune_language(
    lang: str,
    epochs: int,
    batch_size: int,
    lr: float,
    max_seq_len: int,
    use_mac_mps: bool = False,
    resume: bool = False,
    resume_from: Optional[Path] = None,
    eval_strategy: str = "steps",
    eval_steps: int = 50,
    save_steps: int = 100,
):
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

    if use_mac_mps and torch.backends.mps.is_available():
        print("  Device: Apple MPS (full-precision LoRA, no bitsandbytes)")
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            trust_remote_code=True,
            torch_dtype=torch.float16,
        ).to("mps")
    else:
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

    resume_checkpoint = resume_from
    if resume and resume_checkpoint is None:
        resume_checkpoint = latest_checkpoint(checkpoint_dir)

    if resume_checkpoint and resume_checkpoint.exists():
        print(f"  Resuming from {resume_checkpoint}")
        model = PeftModel.from_pretrained(model, str(resume_checkpoint), is_trainable=True)
    else:
        if resume:
            print("  --resume set but no checkpoint found; starting fresh")
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
        eval_strategy=eval_strategy,
        eval_steps=eval_steps if eval_strategy == "steps" else None,
        save_strategy="steps",
        save_steps=save_steps,
        save_total_limit=2,
        logging_steps=10,
        bf16=not use_mac_mps,
        fp16=False,
        max_length=max_seq_len,
        dataset_text_field="text",
        packing=not use_mac_mps,
        report_to="none",
        seed=42,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=valid_ds,
        processing_class=tokenizer,
    )

    print("\n  Starting training...\n")
    if resume_checkpoint and resume_checkpoint.exists():
        trainer.train(resume_from_checkpoint=str(resume_checkpoint))
    else:
        trainer.train()

    final_eval = trainer.evaluate()
    print(f"\n  Final eval loss: {final_eval['eval_loss']:.4f}")

    adapter_dir = checkpoint_dir / "final_adapter"
    print(f"\n  Saving LoRA adapter to {adapter_dir}...")
    model.save_pretrained(str(adapter_dir))

    print(f"  Merging LoRA into full-precision base and saving to {output_dir}...")
    save_merged_fp16_model(adapter_dir, output_dir, tokenizer, use_mac_mps=use_mac_mps)

    print(f"  Done — {lang_name} SLM saved to {output_dir}\n")
    return final_eval


def save_merged_fp16_model(
    adapter_dir: Path, output_dir: Path, tokenizer, use_mac_mps: bool = False
) -> None:
    """Merge adapter into an unquantized base model (avoids saving 4-bit packed weights)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if torch.cuda.is_available():
        device_map = "cuda"
        dtype = torch.bfloat16
    elif use_mac_mps and torch.backends.mps.is_available():
        device_map = "mps"
        dtype = torch.float16
    else:
        device_map = "cpu"
        dtype = torch.float32
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=dtype,
        device_map=device_map,
        trust_remote_code=True,
    )
    peft_model = PeftModel.from_pretrained(base, str(adapter_dir))
    merged = peft_model.merge_and_unload()
    if hasattr(merged.config, "quantization_config"):
        del merged.config.quantization_config
    merged.save_pretrained(str(output_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(output_dir))


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Parlance SLM")
    parser.add_argument("--lang", choices=["es", "fr", "both"], default="both")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-seq-len", type=int, default=1024)
    parser.add_argument(
        "--mac",
        action="store_true",
        help="Train on Apple Silicon MPS (no CUDA/bitsandbytes)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from latest checkpoint-N in checkpoints/parlance-{lang}/",
    )
    parser.add_argument(
        "--resume-from",
        type=Path,
        default=None,
        help="Explicit checkpoint directory (overrides --resume auto-detect)",
    )
    parser.add_argument(
        "--eval-strategy",
        choices=["steps", "epoch", "no"],
        default="steps",
        help="When to run validation (epoch = fewer MPS eval passes)",
    )
    parser.add_argument("--eval-steps", type=int, default=50)
    parser.add_argument("--save-steps", type=int, default=100)
    args = parser.parse_args()

    results = {}

    if args.lang in ("es", "both"):
        results["es"] = finetune_language(
            "es",
            args.epochs,
            args.batch_size,
            args.lr,
            args.max_seq_len,
            args.mac,
            resume=args.resume,
            resume_from=args.resume_from,
            eval_strategy=args.eval_strategy,
            eval_steps=args.eval_steps,
            save_steps=args.save_steps,
        )

    if args.lang in ("fr", "both"):
        results["fr"] = finetune_language(
            "fr",
            args.epochs,
            args.batch_size,
            args.lr,
            args.max_seq_len,
            args.mac,
            resume=args.resume,
            resume_from=args.resume_from,
        )

    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    for lang, res in results.items():
        name = "Spanish" if lang == "es" else "French"
        print(f"  {name}: eval_loss = {res['eval_loss']:.4f}")
    print()


if __name__ == "__main__":
    main()

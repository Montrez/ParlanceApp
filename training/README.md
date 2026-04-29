# Parlance Training Data

Scripts for generating fine-tuning data for interpreter training models. This was an early approach before Parlance pivoted to RAG + cloud API inference.

## What Was Generated

2,241 total training examples in JSONL chat format:

| Category | Spanish | French |
|----------|---------|--------|
| Grammar feedback (A1-C2) | 495 | 498 |
| DELE/DELF exam prep | 224 | 224 |
| Medical interpreting (CCHI/NBCMI) | 150 | 150 |
| Legal interpreting | 150 | 150 |
| Interpreter ethics | 100 | 100 |

## Scripts

- `generate_data.py` — Core grammar feedback examples across all CEFR levels
- `generate_specialty_data.py` — DELE/DELF, medical, legal, and ethics examples
- `merge_data.py` — Merges all JSONL files, shuffles, creates 90/10 train/val split
- `finetune_qlora.py` — QLoRA fine-tuning script for Qwen 2.5 3B (Google Colab)
- `export_model.py` — Merges LoRA adapter weights into base model
- `Parlance_FineTune.ipynb` — Colab notebook for the fine-tuning pipeline

## Why This Was Shelved

- Google Colab GPU quota expired mid-training (step 251/378, loss 0.41)
- Local MLX training on M4 Mac (24GB) crashed the system at 12.5GB memory usage
- The RAG + Groq (Qwen 3 32B) approach produces better results with zero training infrastructure

The training data is preserved in `training/data/` (gitignored) for potential future use.

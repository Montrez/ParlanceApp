# Parlance SLM Training

Per-language small language models for interpreter training feedback. Two separate Qwen 2.5 0.5B models — one for Spanish, one for French — fine-tuned with LoRA on dialect-aware grammar feedback data.

## Data Pipeline

1. **Base data** — `generate_data.py` + `generate_specialty_data.py` (grammar, DELE/DELF, medical, legal, ethics)
2. **Dialect data** — `generate_dialect_data.py` (6 Spanish dialects, 5 French dialects)
3. **Split & balance** — `prepare_slm_data.py` (merge, dedup, cap levels at 350, 90/10 split)

### Current Data

| Level | Spanish | French |
|-------|---------|--------|
| A1 | 278 | 252 |
| A2 | 225 | 250 |
| B1 | 250 | 168 |
| B2 | 157 | 160 |
| C1 | 350 | 350 |
| C2 | 157 | 149 |
| **Total** | **1,417** | **1,329** |

## Fine-tuning

```bash
pip install -r requirements.txt
python finetune_slm.py --lang es --epochs 3
python finetune_slm.py --lang fr --epochs 3
```

Uses QLoRA (4-bit) on Qwen 2.5 0.5B Instruct. Needs a GPU with ~6GB VRAM (T4 or better).

Output: `training/models/parlance-es/` and `training/models/parlance-fr/`

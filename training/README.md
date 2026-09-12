# Parlance SLM Training

## Next coach (Gemma 4 E2B, grammar only)

The shipping 0.5B models stay as they are. This path trains a bigger on-device
model to leave correct sentences alone or make the smallest real fix.

```bash
cd training
./run_gec_bootstrap.sh
# Needs Homebrew Python 3.13 (Xcode python3 is 3.9 and cannot load Gemma 4):
python3.13 -m venv .venv
.venv/bin/pip install -U 'mlx-lm>=0.31'
# Accept https://huggingface.co/google/gemma-4-E2B-it then:
python3 finetune_gec.py --lang fr
```

Data: COWS-L2H (Spanish), graelo/cancre (French), multilingual-gec (ES/FR/EN),
plus existing Parlance seeds. FRIDA and cLang-8 are not used (not public / not
commercial). Judgment cases in `golden/gec_judgment.jsonl` are held out.

---

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

### Google Colab (T4 GPU)

Open `Parlance_FineTune.ipynb` from this folder (Colab extension syncs `finetune_slm.py` and `data/`), or upload manually:

| File | Path |
|------|------|
| Script | `finetune_slm.py` |
| Spanish train/valid | `data/spanish/train.jsonl` (1,275), `valid.jsonl` (142) |
| French train/valid | `data/french/train.jsonl` (1,196), `valid.jsonl` (133) |

```bash
pip install torch transformers peft datasets accelerate bitsandbytes trl
cd training   # if notebook opened from repo root
python finetune_slm.py --lang es --epochs 3
python finetune_slm.py --lang fr --epochs 3
```

Zip `models/parlance-es/` and `models/parlance-fr/` and copy back to your Mac.

### Local GPU

```bash
pip install -r requirements.txt
python finetune_slm.py --lang es --epochs 3
python finetune_slm.py --lang fr --epochs 3
```

Uses QLoRA (4-bit) on Qwen 2.5 0.5B Instruct. Needs ~6GB VRAM (T4 or better).

Output: `models/parlance-es/` and `models/parlance-fr/` (under this directory)

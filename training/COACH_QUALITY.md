# Parlance Coach — level inference retrain

## Goal

Train the on-device 0.5B coach to emit reliable **`assessed_level`** and **`complexity_note`** (no user-picked CEFR), aligned with inference prompts in `parlance_slm_validate.py`.

## Pipeline (Mac)

```bash
cd training
chmod +x run_level_retrain.sh
./run_level_retrain.sh es 2    # Spanish, 2 epochs (use 3 for production)
```

Steps: migrate → `prepare_slm_data.py` → `finetune_slm.py --mac` → smoke → golden regression.

## Manual steps

```bash
python3 migrate_training_schema.py --lang es --include-train-valid
python3 merge_golden_seeds.py
python3 prepare_slm_data.py --lang es
python3 finetune_slm.py --lang es --epochs 2 --mac
python3 run_coach_regression.py --lang es
python3 export_parlance_mlx.py --lang es
./prepare_ios_coach_model.sh
```

## Golden set

- `training/golden/coach_regression_es.jsonl` — 14 cases (A1–C2)
- `training/golden/coach_regression_fr.jsonl` — 12 cases (A1–C2)

Run:

```bash
python3 run_coach_regression.py --lang es
python3 run_coach_regression.py --lang fr
```

Both languages use `sanitize_feedback(..., lang=...)` in `parlance_slm_infer.py` (French was previously raw model JSON only).

### Regression failures (how to read them)

1. **Pipeline** — `normalize_feedback` must keep `assessed_level` / `complexity_note`; validators should not replace good SLM JSON because of unrelated `next_level_alt` or tip examples. Fix in `parlance_slm_validate.py` first.
2. **Model** — wrong or missing CEFR after pipeline fixes: add rows to `seed_assessed_level_es.jsonl`, migrate, and run a short retrain (or accept `run_coach_regression.py --level-tolerance 1` for ±1 band while iterating).

## Curated seeds

- `training/data/spanish/seed_assessed_level_es.jsonl` — level-calibrated examples (A1–C2)
- `training/data/french/seed_assessed_level_fr.jsonl` — same band coverage for French

Merge into training shards:

```bash
python3 merge_golden_seeds.py --lang both
```

## Keep after retrain

- **Validators** (`parlance_slm_validate.py`, Swift validator) — safety net for leísmo, si-clauses, low-quality output.
- **RAG** — reference topics at inference; not replaced by weights alone.

## Data layout after migrate

Legacy shards move to `data/spanish/archive_legacy_schema/`. Active training input: `assessed_level_es.jsonl` (+ `prepare_slm_data` → `train.jsonl` / `valid.jsonl`).

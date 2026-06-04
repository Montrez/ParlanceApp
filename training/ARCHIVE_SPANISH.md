# Archive checklist — Parlance Coach on-device (Spanish + French)

## What ships

- **Parlance Coach** in `Parlance/web/journal.js` (Spanish and French journals)
- On-device inference: `ParlanceSLMEngine.swift` + `ParlanceSLMAnalyzer.swift` (MLX Swift)
- Weights are **not** in git — copied into the app at build time (~294 MB MLX 4-bit per language)

## Before you archive (on your Mac)

1. **Merged models** (~942 MB each)

   ```bash
   ls -lh training/models/parlance-es/model.safetensors
   ls -lh training/models/parlance-fr/model.safetensors
   # expect ~942M each, not ~437M
   ```

2. **Prepare MLX bundles + smoke tests**

   ```bash
   ./training/prepare_ios_coach_model.sh
   ```

   Exports `parlance-es-mlx` and `parlance-fr-mlx` if needed; runs `smoke_test_slm.py` for both.

3. **Xcode**

   - If build fails with *missing Metal Toolchain*: `xcodebuild -downloadComponent MetalToolchain`
   - Open `Parlance.xcodeproj`
   - Wait for Swift packages to resolve (`mlx-swift-lm`, `swift-transformers-mlx`)
   - Select a **physical iPhone** (recommended) or device build destination
   - Product → **Archive** → Distribute (TestFlight)

4. **Test on device**

   - Journal language → **Spanish** or **French**
   - ⚙ AI → **Parlance Coach**
   - Write a sentence → first run loads the model (1–2 min); later runs faster
   - No Mac server required

## Build details

| Piece | Spanish | French |
|-------|---------|--------|
| HF merged (training) | `training/models/parlance-es/` | `training/models/parlance-fr/` |
| MLX 4-bit (iOS) | `training/models/parlance-es-mlx/` | `training/models/parlance-fr-mlx/` |
| Copy into `.app` | `parlance-es-mlx/` | `parlance-fr-mlx/` |

App size increase: ~300 MB per language (~600 MB with both).

## Optional: dev Mac server

```bash
python3 training/parlance_slm_server.py
```

Enable dev routing in the app (UserDefaults key `parlance_slm_dev_server` = true) — not enabled by default in release.

## Optional: back up weights outside git

```bash
zip -r ~/Desktop/parlance-es-mlx.zip training/models/parlance-es-mlx/
zip -r ~/Desktop/parlance-fr-mlx.zip training/models/parlance-fr-mlx/
```

## Export one language only

```bash
python3 training/export_parlance_mlx.py --lang fr
rsync -a --delete training/models/parlance-fr-mlx/ Parlance/Models/parlance-fr-mlx/
```

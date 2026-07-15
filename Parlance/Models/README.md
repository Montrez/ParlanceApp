# Parlance Coach MLX weights (not in git)

Fine-tuned Spanish and French models for on-device coaching:

| Language | Bundle folder | Training export |
|----------|---------------|-----------------|
| Spanish | `Parlance/Models/parlance-es-mlx/` | `training/models/parlance-es-mlx/` |
| French | `Parlance/Models/parlance-fr-mlx/` | `training/models/parlance-fr-mlx/` |

Run before archiving (exports MLX if missing, smoke tests, rsyncs both):

```bash
./training/prepare_ios_coach_model.sh
```

Expected size: ~294 MB per language (4-bit MLX). Xcode **Copy Bundle Resources** includes blue folder references `parlance-es-mlx` and `parlance-fr-mlx` so weights appear at the app bundle root.

App size increase: ~300 MB per bundled language (~600 MB for Spanish + French).

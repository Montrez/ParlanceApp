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

Spanish is Qwen 0.5B (~294 MB). French is the fused Gemma 4 GEC model (~2.5 GB) staged from `training/models/parlance-gec-fr` into the same `parlance-fr-mlx` folder name Xcode already copies.

Xcode **Copy Bundle Resources** includes blue folder references `parlance-es-mlx` and `parlance-fr-mlx` so weights appear at the app bundle root.

# SLM Research: Fine-Tuning for Interpreter-Level Language Feedback

## Goal
Train a custom small language model for Parlance's "Deep Feedback" feature, replacing the Claude API dependency. The model specializes in interpreter-level language analysis (grammar rules, Anglicism detection, level-appropriate alternatives) for Spanish and French.

## Deployment Strategy (Zero Ongoing Cost)
1. **Apple FoundationModels adapter** — Train a LoRA adapter for Apple's on-device ~3B model via their adapter training toolkit. Free, private, already integrated in OnDeviceAnalyzer.swift. Fastest path.
2. **Gemma 4 E2B (2B) bundled in-app** — Fully owned fallback. ~1.5 GB at 4-bit quantization. Apache 2.0 license (commercial, sellable). No server required.

---

## Top Candidate Models

### Gemma 4 E2B (2B) — RECOMMENDED
- **License**: Apache 2.0 (fully permissive, commercial, sellable)
- **Size**: ~1.5 GB at 4-bit quantization
- **Multilingual**: 140+ languages (Spanish, French well-represented)
- **On-device**: Proven on iPhone via MLX at ~40 tokens/sec
- **Fine-tuning**: MLX + LoRA on any M-series Mac (16GB+ RAM)
- **Core ML**: Conversion supported via coremltools

### Qwen3-4B — Best quality-to-size ratio
- **License**: Apache 2.0
- **Size**: ~2.5 GB at 4-bit
- **Multilingual**: 119 languages, 36T training tokens
- **Strength**: JSON structured output explicitly optimized
- **Tradeoff**: Slightly larger for on-device

### SmolLM3 (3B) — Best fine-tuning transparency
- **License**: Apache 2.0
- **Size**: ~2 GB at 4-bit
- **Multilingual**: Natively supports English, French, Spanish (exactly our needs)
- **Strength**: Hugging Face published full training blueprint

### Llama 3.2 3B — Most proven ecosystem
- **License**: Meta Community License (commercial OK, but attribution required, can't distill to non-Llama)
- **Size**: ~2 GB at 4-bit
- **Tradeoff**: License restrictions make it less ideal for a sellable product

---

## Training Data Strategy

### Existing Datasets
| Dataset | Language | Size | Notes |
|---------|----------|------|-------|
| COWS-L2H | Spanish | ~12,336 sentences | UC Davis L2 learner corpus with error annotations |
| FRIDA | French | ~450K words | French learner corpus with three-tiered error annotation |
| cLang-8 | Multilingual | Large | Cleaned Lang-8 GEC corrections corpus |

### Synthetic Data Generation
Use Claude API to generate 2,000-5,000 examples per language matching the SentenceReview JSON schema:

```json
{
  "sentence": "Je pense que nous devons faire une decision.",
  "language": "fr",
  "level": "B2",
  "status": "Needs Improvement",
  "grammar_rule": "Verb collocation: prendre une decision, not faire une decision",
  "explanation": "French uses 'prendre une decision' (take a decision), not 'faire une decision' — the latter is an Anglicism from English 'make a decision'.",
  "correction": "Je pense que nous devons prendre une decision.",
  "b1_alternative": "Je pense que nous devons choisir.",
  "c1_alternative": "J'estime qu'il nous incombe de trancher.",
  "tip": "Watch for direct translations of English collocations — they're the #1 Anglicism at B2."
}
```

Include:
- Deliberate Anglicism examples (English sentence structures in Spanish/French)
- Correct "Excellent" sentences (so model learns to praise too)
- B1/B2/C1 level coverage
- Native speaker review of ~200 samples for quality

---

## Fine-Tuning Process

### Tools
| Tool | Purpose |
|------|---------|
| MLX (Apple) | Fine-tuning + inference on Apple Silicon |
| Unsloth | 2x faster fine-tuning, 60% less VRAM |
| coremltools | Convert to Core ML for iOS |
| Hugging Face TRL | SFT + DPO training |

### Workflow
```
1. PREPARE DATA (1-2 weeks)
   - Generate synthetic examples with Claude API
   - Format as instruction/response pairs
   - Quality review by native speakers

2. FINE-TUNE ON MAC (3-5 days)
   - Tool: MLX or Unsloth with LoRA (rank 16-32)
   - Hardware: M-series Mac, 16GB+ unified memory
   
   mlx_lm.lora --model google/gemma-4-e2b \
                --train --data ./training_data \
                --adapter-path ./adapters \
                --num-layers 8 --rank 16

3. EVALUATE (1-2 days)
   - Test on held-out 200+ examples
   - Compare against baseline and Claude API
   - Check for hallucinated rules, incorrect corrections

4. CONVERT FOR iOS (1-2 days)
   - Export to Core ML via coremltools
   - Bundle in app or use on-demand download (~1.5 GB)
```

### Timeline: 4-6 weeks part-time

---

## Apple Adapter Path (Quick Start)
Apple's adapter training toolkit lets you train LoRA adapters (rank 32) for their on-device model:
- https://developer.apple.com/apple-intelligence/foundation-models-adapter/
- Python workflow, generates adapter loadable in Swift
- Zero cost, but adapters may need retraining per OS version
- Requires Apple's adapter entitlement for App Store

## Key Resources
- Gemma 4: https://deepmind.google/models/gemma/gemma-4/
- MLX fine-tuning guide: https://github.com/ml-explore/mlx-lm
- Unsloth: https://unsloth.ai/
- COWS-L2H: https://github.com/ucdaviscl/cowsl2h
- Apple adapter toolkit: https://developer.apple.com/apple-intelligence/foundation-models-adapter/
- coremltools: https://github.com/apple/coremltools

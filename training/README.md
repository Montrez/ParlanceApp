# Parlance SLM Training

Fine-tuning Qwen 2.5 3B for Spanish/French grammar feedback.

## Step 1: Generate Training Data

Uses Gemini 2.0 Flash (free tier: 1,500 req/day).

```bash
pip install google-generativeai
export GEMINI_API_KEY="your-key"

# Generate Spanish data (all levels, ~500 examples)
python training/generate_data.py --lang es --count 500

# Generate French data
python training/generate_data.py --lang fr --count 500

# Generate for a specific level
python training/generate_data.py --lang es --level A1 --count 100
```

Output goes to `training/data/*.jsonl` in chat-format ready for fine-tuning.

## Step 2: Fine-Tune (coming soon)

QLoRA fine-tuning with Hugging Face TRL on Qwen 2.5 3B.

## Step 3: Deploy (coming soon)

Quantize and deploy as self-hosted API or ONNX for edge.

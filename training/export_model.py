#!/usr/bin/env python3
"""
Merge LoRA adapter weights into base model and export for deployment.
Supports GGUF export for llama.cpp / Ollama serving.

Usage:
    python export_model.py --adapter ./parlance-interpreter-model
    python export_model.py --adapter ./parlance-interpreter-model --gguf q4_k_m
"""

import argparse
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True, help="Path to LoRA adapter")
    parser.add_argument("--output", default="./parlance-merged", help="Output path for merged model")
    parser.add_argument("--gguf", default=None, help="GGUF quantization type (e.g., q4_k_m, q8_0)")
    args = parser.parse_args()

    print(f"Loading base model: {MODEL_ID}")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

    print(f"Loading adapter: {args.adapter}")
    model = PeftModel.from_pretrained(base_model, args.adapter)

    print("Merging weights...")
    model = model.merge_and_unload()

    print(f"Saving merged model to {args.output}")
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)

    if args.gguf:
        print(f"\nTo convert to GGUF ({args.gguf}):")
        print(f"  pip install llama-cpp-python")
        print(f"  python -m llama_cpp.convert {args.output} --outtype {args.gguf} --outfile parlance-3b-{args.gguf}.gguf")
        print(f"\nOr use llama.cpp directly:")
        print(f"  python convert_hf_to_gguf.py {args.output}")
        print(f"  ./llama-quantize parlance-3b-f16.gguf parlance-3b-{args.gguf}.gguf {args.gguf}")

    print("\nDone!")


if __name__ == "__main__":
    main()

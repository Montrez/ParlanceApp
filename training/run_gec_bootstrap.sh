#!/usr/bin/env bash
# Download public GEC corpora and build train/valid splits.
# Does not start the multi-hour Gemma fine-tune.
set -euo pipefail
cd "$(dirname "$0")"
python3 import_gec_corpora.py --source all --lang all
python3 prepare_gec_data.py --lang all
echo
echo "Next: python3 finetune_gec.py --lang fr"
echo "Gemma 4 E2B-it is gated. Accept the license on Hugging Face first."

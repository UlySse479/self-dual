#!/bin/bash
datasets=("math-500" "aime" "gsm8k" "svamp")

for i in "${!datasets[@]}"; do
    echo "Running fix budget BAND for dataset: ${datasets[i]}"
    python -m core.infer.fix_budget.band_double_cot \
        --prompt_type "fix_budget_band_dct" \
        --dataset "${datasets[i]}" \
        --model "google/gemma-3-4b-it" \
        --temperature 0.5 \
        --seed 9 \
        --batch_size 40 \
        --use_checkpoint 
done
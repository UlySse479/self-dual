#!/bin/bash
datasets=("math-500" "aime" "gsm8k" "svamp")

for i in "${!datasets[@]}"; do
    echo "Running self dual BAND for dataset: ${datasets[i]}"
    python -m core.infer.self_dual_band \
        --prompt_type "self_dual_band" \
        --dataset "${datasets[i]}" \
        --model "google/gemma-3-4b-it" \
        --temperature 0.5 \
        --seed 1 \
        --batch_size 40 \
        --use_checkpoint 
done
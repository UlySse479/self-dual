#!/bin/bash
datasets=("math-500" "aime" "gsm8k" "svamp")
nl_file=("./outputs/google/gemma-3-4b-it/math-500/test/XXX.jsonl")

for i in "${!datasets[@]}"; do
    echo "Running REFLEXTION for dataset: ${datasets[i]}"
    echo "Using nl file: ${nl_file[i]}" 
    python -m core.infer.reflextion \
        --prompt_type "reflextion" \
        --dataset "${datasets[i]}" \
        --model "google/gemma-3-4b-it" \
        --temperature 0.5 \
        --seed 1 \
        --batch_size 30 \
        --nl_path "${nl_file[i]}" \
        --use_checkpoint 
done
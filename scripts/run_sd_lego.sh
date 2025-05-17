#!/bin/bash
datasets=("math-500" "aime" "gsm8k" "svamp")
pl_file=("./outputs/google/gemma-3-4b-it/math-500/test/XXX.jsonl")
nl_file=("./outputs/google/gemma-3-4b-it/math-500/test/XXX.jsonl")

for i in "${!datasets[@]}"; do
    echo "Running self dual LEGO for dataset: ${datasets[i]}"
    echo "Using pl file: ${pl_file[i]}" 
    echo "Using nl file: ${nl_file[i]}" 
    python -m core.infer.self_dual_lego \
        --prompt_type "self_dual_lego" \
        --dataset "${datasets[i]}" \
        --model "google/gemma-3-4b-it" \
        --temperature 0.5 \
        --seed 1 \
        --batch_size 40 \
        --pl_path "${pl_file[i]}" \
        --nl_path "${nl_file[i]}" \
        --use_checkpoint 
done
#!/bin/bash
datasets=("math-500" "aime" "gsm8k" "svamp")
pal_file=("./outputs/google/gemma-3-4b-it/math-500/test/XXX.jsonl")

for i in "${!datasets[@]}"; do
    echo "Running critic for dataset: ${datasets[i]}"
    echo "Using pal file: ${pal_file[i]}"
    python -m core.infer.critic \
        --prompt_type "critic" \
        --dataset "${datasets[i]}" \
        --model "google/gemma-3-4b-it" \
        --temperature 0.5 \
        --seed 88 \
        --batch_size 40 \
        --max_iter 4 \
        --critic_path "${pal_file[i]}" \
        --use_checkpoint \
        --no_tools
done
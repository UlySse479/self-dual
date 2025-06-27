#!/bin/bash
datasets=("minervamath" "aime2024" "amc23")

for dataset in "${datasets[@]}"; do
    python -m core.infer.infer \
        --prompt_type "cot" \
        --dataset $dataset \
        --model "google/gemma-3-4b-it" \
        --temperature 0.5 \
        --seed 99 \
        --batch_size 40 \
        --use_checkpoint
done
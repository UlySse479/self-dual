import argparse
import os
from datetime import datetime
from tqdm import tqdm
import json

from core.utils.utils import load_prompt, strip_string
from core.eval.grader import math_equal
from core.utils.utils import set_seed
from core.datasets.datasets_loader import load_format_test_datasets

online_models = ['deepseek-chat']
offline_models = ['google/gemma-3-4b-it', 'google/gemma-3-12b-it', 'google/gemma-3-27b-it']

def parse_args():
    parser = argparse.ArgumentParser(description="Basic inference script")
    parser.add_argument(
        "--prompt_type",
        type=str,
        required=True,
        help="Type of prompt"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Name of the dataset to use(e.g., gsm8k, etc.)",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Name of the model to use(e.g., deepseek-v3, etc.)",
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=8192,
        help="Maximum number of tokens to generate",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for inference",
    )
    parser.add_argument(
        "--dataset_split",
        type=str,
        default="test",
        help="Split of the dataset to use(e.g., train, test, etc.)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--sampled_num",
        type=int,
        default=-1,
        help="Sampled number of dataset to use for inference. -1 means all samples",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Batch size for inference",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs",
        help="Directory to save the outputs",
    )
    parser.add_argument(
        "--use_checkpoint",
        action="store_true",
        default=False,
        help="Use checkpoint for inference(The dataset idx will be used as the checkpoint name)",
    )
    args = parser.parse_args()
    return args

def infer(args):
    # Process the model name and check if it is online or offline
    if args.model in online_models:
        from core.llms.online_llms import OnlineLLMs
        llm = OnlineLLMs(
            model=args.model,
        )
    elif args.model in offline_models:
        from core.llms.offline_llms import OfflineLLMs
        llm = OfflineLLMs(
            model=args.model,
        )
    else:
        print(f"Unknown model: {args.model}")
        return 

    # Process the dataset name and load the dataset
    dataset_name = args.dataset
    try:
        dataset = load_format_test_datasets(dataset_name=dataset_name, split=args.dataset_split)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    if args.sampled_num > 0:
        # Random sampling of the dataset
        dataset = dataset.shuffle(seed=args.seed)
        dataset = dataset.select(range(args.sampled_num))

    # Initialize the output directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Initialize the output file
    output_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{args.prompt_type}_{args.sampled_num}_{args.seed}_{args.temperature}_{datetime.now().strftime('%m-%d-%H-%M')}.jsonl")
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    output_writer = open(output_file, 'w', encoding='utf-8')

    # Checkpoint file to store the current index
    checkpoint_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{args.prompt_type}_{args.sampled_num}_{args.seed}_{args.temperature}_checkpoint.json")
    if not os.path.exists(os.path.dirname(checkpoint_file)):
        os.makedirs(os.path.dirname(checkpoint_file))
    # Load checkpoint if use_checkpoint is True
    start_index = 0
    # Generate the output using the LLM of args.batch_size
    num_correct = 0
    total_res_tokens = 0
    if args.use_checkpoint and os.path.exists(checkpoint_file) and args.sampled_num == -1:
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
            start_index = checkpoint_data.get("index", 0)
            num_correct = checkpoint_data.get("num_correct", 0)
            total_res_tokens = checkpoint_data.get("total_res_tokens", 0)
        print(f"Resuming from checkpoint at index {start_index}...")

    type_prompt = load_prompt(prompt_type=args.prompt_type, dataset_name=args.dataset)
    
    with tqdm(total=len(dataset), initial=start_index) as pbar:
        for i in range(start_index, len(dataset), args.batch_size):
            batch = dataset[i:i + args.batch_size]
            if args.prompt_type == 'vanilla':
                from core.infer.basis import vanilla
                process_func = vanilla
            elif args.prompt_type == 'cot':
                from core.infer.basis import cot
                process_func = cot
            elif args.prompt_type == 'pal':
                from core.infer.basis import pal
                process_func = pal
            else:
                print(f"Unknown prompt type: {args.prompt_type}")
                return
            
            infer_results = process_func(
                type_prompt=type_prompt,
                batch_dataset=batch,
                temperature=args.temperature,
                max_new_tokens=args.max_new_tokens,
                llm=llm,
                args=args,
            )
            for j, infer_result  in enumerate(infer_results):
                is_correct = math_equal(
                        strip_string(batch['answer'][j]), strip_string(infer_result.answer)
                        )
                num_correct += is_correct
                output = {
                    "question": batch['question'][j],
                    "pred": infer_result.answer,
                    "ground_truth": batch['answer'][j],
                    "is_correct": is_correct,
                    "level": batch['level'][j] if args.dataset == 'math' else None,
                    "type": batch['type'][j] if args.dataset == 'math' else None,
                    "prompt_tokens": infer_result.response.prompt_tokens,
                    "response_tokens": infer_result.response.response_tokens,
                    "pred_solution": infer_result.response.response,
                    "solution": batch['solution'][j] if args.dataset != 'svamp' and args.dataset != 'aime' else None,
                }
                output_writer.write(json.dumps(output) + '\n')
                total_res_tokens += infer_result.response.response_tokens
                print(f"idx: {i+j}, is_correct: {is_correct}, accuracy: {num_correct / (i+j+1):.4f}, o_tokens: {infer_result.response.response_tokens}, o_tokens/Q: {total_res_tokens / (i+j+1):.4f}")
            # Save checkpoint after processing each batch
            if args.use_checkpoint and args.sampled_num == -1:
                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(
                        {
                            "index": i + j + 1, 
                            "num_correct": num_correct,
                            "accuracy": round(num_correct / (i+j+1), 4), 
                            "total_res_tokens": total_res_tokens,
                            "output_tokens/Q": round(total_res_tokens / (i+j+1), 4)
                         },
                         f)
            output_writer.flush()
            pbar.update(args.batch_size)
        
    output_writer.close()

    

if __name__ == '__main__':
    args = parse_args()
    set_seed(args.seed)
    infer(args)

import argparse
import argparse
import os
from datetime import datetime
from tqdm import tqdm
import json
import numpy as np

from core.utils.utils import load_prompt, strip_string
from core.eval.grader import math_equal
from core.utils.utils import set_seed, load_jsonl, extract_boxed_from_str
from core.infer.infer import online_models, offline_models


def parse_args():
    parser = argparse.ArgumentParser(description="Basic inference script")
    parser.add_argument(
        "--prompt_type",
        type=str,
        required=True,
        help="Type of prompt"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Name of the model to use(e.g., deepseek-v3, etc.)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Name of the dataset to use(e.g., gsm8k, etc.)",
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=8192,
        help="Maximum number of tokens to generate",
    )
    parser.add_argument(
        "--dataset_split",
        type=str,
        default="test",
        help="Split of the dataset to use(e.g., train, test, etc.)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for inference",
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
    parser.add_argument(
        "--pl_path",
        type=str,
        default=None,
        help="The pal path for Slef-Dual-LEGO", 
    )
    parser.add_argument(
        "--nl_path",
        type=str,
        default=None,
        help="The nl path for Slef-Dual-LEGO",
    )
    parser.add_argument(
        "--no_tools",
        action="store_true",
        default=False,
        help="Use no tools for inference",
    )
    args = parser.parse_args()
    return args

def self_dual_lego(args):
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

    try:
        pl_dataset = load_jsonl(args.pl_path)
        nl_dataset = load_jsonl(args.nl_path)

    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    if args.sampled_num > 0:
        # Random sampling of the origin_pal dataset
        sampled_indices = np.random.choice(len(pl_dataset), args.sampled_num, replace=False)
        pl_dataset = [pl_dataset[i] for i in sampled_indices]
        nl_dataset = [nl_dataset[i] for i in sampled_indices]
        
    assert len(pl_dataset) == len(nl_dataset), "The length of the two datasets must be the same"
    # Initialize the output directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    sd_lego_par = os.path.basename(args.pl_path).split('_')[0] + '_' + os.path.basename(args.nl_path).split('_')[0]
    str_no_tools = "no-tools/" if args.no_tools else ""
    # Initialize the output file
    output_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{str_no_tools}{args.prompt_type}_{sd_lego_par}_{args.sampled_num}_{args.seed}_{args.temperature}_{datetime.now().strftime('%m-%d-%H-%M')}.jsonl")
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    output_writer = open(output_file, 'w', encoding='utf-8')

    # Checkpoint file to store the current index
    checkpoint_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{str_no_tools}{args.prompt_type}_{sd_lego_par}_{args.sampled_num}_{args.seed}_{args.temperature}_checkpoint.json")
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


    with tqdm(total=len(pl_dataset), initial=start_index) as pbar:
        for i in range(start_index, len(pl_dataset), args.batch_size):
            pl_batch = pl_dataset[i:i + args.batch_size]
            nl_batch = nl_dataset[i:i + args.batch_size]
            prompts = []
            nl_solutions = []
            pl_solutions = []
            for pl, nl in zip(pl_batch, nl_batch):
                question = pl['question']
                if 'critic' in args.pl_path:
                    pl_pred_solution = pl['pred_solution'][-1]
                    pl_pred = pl['pred'][-1]
                elif 'tir' in args.pl_path:
                    pl_pred_solution = pl['pred_solution'].split('Answer:')[-1].strip()
                    pl_pred = pl['pred']
                else:
                    pl_pred_solution = pl['pred_solution']
                    pl_pred = pl['pred']
                nl_pred_solution = nl['pred_solution']
                if not args.no_tools:
                    str_output = f"```output\n{pl_pred}\n```\n"
                else:
                    str_output = ""
                prompts.append(
                    type_prompt + f"Question: {question}\n Natural language based solution process:\n{nl_pred_solution}\n"
                    + f"Programming language based solution process:\n{pl_pred_solution}\n" + str_output
                )
                nl_solutions.append(nl_pred_solution)
                pl_solutions.append(pl_pred_solution)
            responses = llm.completion_batch(
                prompts,
                temperature=args.temperature,
                max_tokens=args.max_new_tokens,
                stop_tokens=["Question:", "---"],
            )
            for j, response in enumerate(responses):
                pred = extract_boxed_from_str(response.response)
                is_correct = math_equal(strip_string(pred), strip_string(pl_batch[j]['ground_truth']))
                num_correct += is_correct
                total_res_tokens += response.response_tokens
                output = {
                    "question": pl_batch[j]['question'],
                    "ground_truth": pl_batch[j]['ground_truth'],
                    "pl_pred_solution":pl_solutions[j],
                    "nl_pred_solution": nl_solutions[j],
                    "lego_solution": response.response,
                    "pred": pred,
                    "is_correct": is_correct,
                    "prompt_tokens": response.prompt_tokens,
                    "response_tokens": response.response_tokens,
                    "error": response.error,
                }
                output_writer.write(json.dumps(output) + '\n')
                print(f"idx: {i+j}, is_correct: {is_correct}, accuracy: {num_correct / (i+j+1):.4f}, o_tokens: {response.response_tokens}, o_tokens/Q: {total_res_tokens / (i+j+1):.4f}")
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
    self_dual_lego(args)

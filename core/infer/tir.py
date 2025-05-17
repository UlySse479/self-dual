import argparse
import argparse
import os
from datetime import datetime
from tqdm import tqdm
import json

from core.utils.utils import load_prompt, strip_string
from core.eval.grader import math_equal
from core.utils.python_executor import PythonExecutor
from core.utils.utils import set_seed, extract_boxed_from_str, extract_last_code_block
from core.datasets.datasets_loader import load_format_test_datasets
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
        default=1024,
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
        "--no_tools",
        action="store_true",
        default=False,
        help="Use tool for TIR",
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=4,
        help="The max iteration for TIR",
    )
    args = parser.parse_args()
    return args

def tir(args):
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
        dataset = load_format_test_datasets(dataset_name=dataset_name)
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

    str_no_tools = "no-tools/" if args.no_tools else ""
    # Initialize the output file
    output_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{str_no_tools}{args.prompt_type}_{args.sampled_num}_{args.seed}_{args.temperature}_{datetime.now().strftime('%m-%d-%H-%M')}.jsonl")
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    output_writer = open(output_file, 'w', encoding='utf-8')

    # Checkpoint file to store the current index
    checkpoint_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{str_no_tools}{args.prompt_type}_{args.sampled_num}_{args.seed}_{args.temperature}_checkpoint.json")
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
    python_executor = PythonExecutor()
    if not args.no_tools:
        stop_tokens = ["</s>", "```output", "Question"]
    else:
        stop_tokens = ["Question"]

    with tqdm(total=len(dataset), initial=start_index) as pbar:
        for idx in range(start_index, len(dataset), args.batch_size):
            # Cal tokens number
            prompt_tokens = [0 for _ in range(args.batch_size)]
            o_tokens = [0 for _ in range(args.batch_size)]
            batch = dataset[idx:idx + args.batch_size]

            remain_prompts = [type_prompt + f"Question: {q}\nAnswer: " for q in batch['question']]
            remain_prompts = [(i, prompt) for i, prompt in enumerate(remain_prompts)]
            end_prompts = []
            for epoch in range(args.max_iter):
                print("="*20 + f"TIR epoch: {epoch + 1}" + "="*20)
                current_prompts = remain_prompts
                if len(current_prompts) == 0:
                    break

                prompts = [prompt for _, prompt in current_prompts]
                responses = llm.completion_batch(
                            prompts=prompts,
                            temperature=args.temperature,
                            max_tokens=args.max_new_tokens,
                            stop_tokens=stop_tokens
                        )
                
                # process outputs
                remain_prompts = []
                remain_codes = []
                for (i, query), response in zip(current_prompts, responses):
                    if response.error:
                        raise ValueError(f"LLM error: {response.error}")
                    prompt_tokens[i] += response.prompt_tokens
                    o_tokens[i] += response.response_tokens
                    output = response.response.rstrip()
                    query += output
                    if ("boxed" not in output and output.endswith("```")) and not args.no_tools:
                        code = extract_last_code_block(query)
                        remain_prompts.append((i, query))
                        remain_codes.append(code)
                    else:
                        end_prompts.append((i, query))

                remain_results = python_executor.batch_execute_codes(remain_codes)
                for k in range(len(remain_prompts)):
                    i, query = remain_prompts[k]
                    res, report = remain_results[k].output, remain_results[k].error
                    exec_result = res if res else report
                    exec_result = f"\n```output\n{exec_result}\n```\n"
                    query += exec_result
                    if epoch == args.max_iter - 1:
                        query += "\nReach max function call limit."
                    remain_prompts[k] = (i, query)

            end_prompts.extend(remain_prompts)
            end_prompts = sorted(end_prompts, key=lambda x: x[0])
            assert len(end_prompts) == len(batch['question'])
            raw_results = [prompt.split("Question:")[-1].strip() for _, prompt in end_prompts]
            results =  [extract_boxed_from_str(res) for res in raw_results]

            for j in range(len(batch['question'])):
                is_correct = math_equal(
                        strip_string(batch['answer'][j]), strip_string(results[j])
                        )
                num_correct += is_correct
                output = {
                    "question": batch['question'][j],
                    "pred": results[j],
                    "ground_truth": batch['answer'][j],
                    "is_correct": is_correct,
                    "level": batch['level'][j] if args.dataset == 'math' else None,
                    "type": batch['type'][j]if args.dataset == 'math' else None,
                    "prompt_tokens": prompt_tokens[j],
                    "response_tokens": o_tokens[j],
                    "pred_solution": raw_results[j],
                    "solution": batch['solution'][j] if args.dataset != 'svamp' and args.dataset != 'aime' else None,
                    "is_run_code": True if extract_last_code_block(raw_results[j]) else False,
                }
                output_writer.write(json.dumps(output) + '\n')
                total_res_tokens += o_tokens[j]
                print(f"idx: {idx+j}, is_correct: {is_correct}, accuracy: {num_correct / (idx+j+1):.4f}, o_tokens: {o_tokens[j]}, o_tokens/Q: {total_res_tokens / (idx+j+1):.4f}")
                if args.use_checkpoint and args.sampled_num == -1:
                    with open(checkpoint_file, 'w', encoding='utf-8') as f:
                        json.dump(
                            {
                                "index": idx + j + 1, 
                                "num_correct": num_correct,
                                "accuracy": round(num_correct / (idx+j+1), 4), 
                                "total_res_tokens": total_res_tokens,
                                "output_tokens/Q": round(total_res_tokens / (idx+j+1), 4)
                            },
                            f)
            output_writer.flush()
            pbar.update(args.batch_size)
        
        output_writer.close()

if __name__ == '__main__':
    args = parse_args()
    set_seed(args.seed)
    tir(args)

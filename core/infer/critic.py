import argparse
import argparse
import os
from datetime import datetime
from tqdm import tqdm
import json
import numpy as np

from core.utils.utils import load_prompt, strip_string
from core.eval.grader import math_equal
from core.utils.python_executor import PythonExecutor
from core.utils.utils import set_seed, load_jsonl, extract_last_code_block, remove_comment
from core.llms.online_llms import OnlineLLMs
from core.llms.offline_llms import OfflineLLMs
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
        "--no_tools",
        action="store_true",
        default=False,
        help="Use tool for CRITIC",
    )
    parser.add_argument(
        "--critic_path",
        type=str,
        default='./outputs/deepseek-chat/svamp/test/pal_20_50_0.5_04-15-21-34.jsonl',
        help="The pal path for CIRITC", 
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=4,
        help="The max iteration for critic",
    )
    args = parser.parse_args()
    return args

def critic(args):
    # Process the model name and check if it is online or offline
    if args.model in online_models:
        llm = OnlineLLMs(
            model=args.model,
        )
    elif args.model in offline_models:
        llm = OfflineLLMs(
            model=args.model,
        )
    else:
        print(f"Unknown model: {args.model}")
        return 

    try:
        dataset = load_jsonl(args.critic_path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    if args.sampled_num > 0:
        # Random sampling of the origin_pal dataset
        sampled_indices = np.random.choice(len(dataset), args.sampled_num, replace=False)
        dataset = [dataset[i] for i in sampled_indices]
        

    # Initialize the output directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    str_no_tools = "no-tools/" if args.no_tools else ""
    # Initialize the output file
    output_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{str_no_tools}{args.prompt_type}_pal_{args.sampled_num}_{args.seed}_{args.temperature}_{datetime.now().strftime('%m-%d-%H-%M')}.jsonl")
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    output_writer = open(output_file, 'w', encoding='utf-8')

    # Checkpoint file to store the current index
    checkpoint_file = os.path.join(args.output_dir, f"{args.model}/{args.dataset}/{args.dataset_split}/{str_no_tools}{args.prompt_type}_pal_{args.sampled_num}_{args.seed}_{args.temperature}_checkpoint.json")
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

    with tqdm(total=len(dataset), initial=start_index) as pbar:
        for i in range(start_index, len(dataset), args.batch_size):
            batch = dataset[i:i + args.batch_size]
            raw_responses = [[item['pred_solution']] for item in batch]
            code_blocks = [[extract_last_code_block(item['pred_solution'])] for item in batch]
            report_msg = [[None] for _ in range(len(batch))]

            pred = [[item['pred']] for item in batch]
            prompt_tokens = [0 for _ in range(len(batch))]
            o_tokens = [0 for _ in range(len(batch))]
            for itr in range(1, args.max_iter + 1):
                print(f"Iteration {itr}...")
                base_idx = [itr - 1] * len(batch)
                previous_codes = []
                contexts = []
                # construct the critic prompt (batch_size)
                for j in range(len(batch)):
                    while base_idx[j] > 0 and pred[j][base_idx[j]] is None:
                        base_idx[j] -= 1
                    previous_codes.append(remove_comment(code_blocks[j][base_idx[j]]))
                    
                    context = f"\nQuestion: {batch[j]['question']}\n"
                    context += f"```python\n{previous_codes[j]}\n```\n"
                    if not args.no_tools:
                        t_str = "Done"
                        context += f"Execution: {t_str if report_msg[j][base_idx[j]] is None else report_msg[j][base_idx[j]]}\n"
                        context += f"Output: answer = {pred[j][base_idx[j]]}\n"
                    context += "\nWhat's the problem with the above code?\n\n"
                    context = type_prompt + context
                    contexts.append(context)
                # verrify previous codes    
                responses = llm.completion_batch(
                        prompts=contexts,
                        temperature=args.temperature,
                        max_tokens=500,
                        stop_tokens=["Here's", "---"]
                    )
                
                # generate new code
                for j, response in enumerate(responses):
                    if response.error:
                        raise ValueError(f"LLM error: {response.error}")
                    o_tokens[j] += response.response_tokens
                    prompt_tokens[j] += response.prompt_tokens
                    context = response.response.strip()
                    context += "Here's a better solution:\n```python\n"
                    contexts[j] += context
                
                responses = llm.completion_batch(
                        prompts=contexts,
                        temperature=args.temperature,
                        max_tokens=400,
                        stop_tokens=["```", "---", "Question:"]
                    )
                
                tmp_code_blocks = []
                # Update the code blocks with the new code
                for j, response in enumerate(responses):
                    if response.error:
                        raise ValueError(f"LLM error: {response.error}")
                    prompt_tokens[j] += response.prompt_tokens
                    o_tokens[j] += response.response_tokens
                    tmp_code_blocks.append(response.response.strip())
                    raw_responses[j].append(response.response.strip())
                   
                # Update the report message and prediction
                exec_results = python_executor.batch_execute_codes(tmp_code_blocks)
                for j, (exec_result, code) in enumerate(zip(exec_results, tmp_code_blocks)):
                    if code is None or code_blocks[j][base_idx[j]] is None:
                        report_msg[j].append("No code generated")
                        pred[j].append(None)
                        code_blocks[j].append(None)
                    elif code.strip() == code_blocks[j][base_idx[j]].strip(): # no correction
                        code_blocks[j].append(code)
                        report_msg[j].append(report_msg[j][base_idx[j]])
                        pred[j].append(pred[j][base_idx[j]])
                    else: # correction
                        code_blocks[j].append(code)
                        report_msg[j].append(exec_result.error)
                        pred[j].append(exec_result.output)

            for j in range(len(batch)):
                is_correct = math_equal(
                        strip_string(batch[j]['ground_truth']), strip_string(pred[j][-1])
                        )
                num_correct += is_correct
                output = {
                    "question": batch[j]['question'],
                    "pred": pred[j],
                    "ground_truth": batch[j]['ground_truth'],
                    "is_correct": is_correct,
                    "prompts": contexts[j],
                    "level": batch[j]['level'] if args.dataset == 'math' else None,
                    "type": batch[j]['type'] if args.dataset == 'math' else None,
                    "prompt_tokens": prompt_tokens[j],
                    "response_tokens": o_tokens[j],
                    "pred_solution": code_blocks[j],
                    "raw_solution": raw_responses[j],
                    "solution": batch[j]['solution'] if args.dataset != 'svamp' else None,
                    "code_error": report_msg[j],
                }
                output_writer.write(json.dumps(output) + '\n')
                total_res_tokens += o_tokens[j]
                print(f"idx: {i+j}, is_correct: {is_correct}, accuracy: {num_correct / (i+j+1):.4f}, o_tokens: {o_tokens[j]}, o_tokens/Q: {total_res_tokens / (i+j+1):.4f}")
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
    critic(args)

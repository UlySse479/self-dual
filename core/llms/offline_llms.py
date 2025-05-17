from typing import List
from vllm import LLM, SamplingParams
from huggingface_hub import login
import os
import torch._dynamo
torch._dynamo.config.suppress_errors = True

from core.llms.online_llms import LLMsResponse

HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable not set. Please set it to your Hugging Face token.")

login(token=HF_TOKEN)

class OfflineLLMs:
    def __init__(self, 
                 model: str = "google/gemma-3-4b-it", 
                 system_prompt: str = "You are a helpful assistant"):
        super().__init__()
        self.model = model
        self.llm = LLM(model=self.model)
        self.tokenizer = self.llm.get_tokenizer()
        self.system_prompt = system_prompt
    
    def completion_batch(self,
                   prompts: List[str],
                   temperature: float = 0,
                   max_tokens: int = 256,
                   stop_tokens: List[str] = None,
                   n: int = 1,) -> List[LLMsResponse]:
        
        responses = []
        params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop_tokens,
            n=n,
        )
        try:
            ouputs = self.llm.generate(prompts, params)
        except Exception as e:
            # Handle the error and return None
            error = str(e)
            return [LLMsResponse(None, None, None, error)] * len(prompts)
        for output in ouputs:
            # Get the response content and tokens
            res_content = output.outputs[0].text.strip()
            prompt = output.prompt
            prompt_tokens = len(self.tokenizer.encode(prompt, add_special_tokens=False))
            res_tokens = len(self.tokenizer.encode(res_content, add_special_tokens=False))
            error = None
            # Append the response to the list
            responses.append(LLMsResponse(res_content, prompt_tokens, res_tokens, error))
                   
        return responses
               

if __name__ == "__main__":
    llm = OfflineLLMs()
    prompts = ["What is the capital of France?", "What is the capital of Italy?"] * 10
    print(f"Prompt: {prompts}")
    # Get the response from the LLM
    responses= llm.completion_batch(prompts, temperature=0.5, max_tokens=256, stop_tokens=["```", "---"], n=1)
    for response in responses:
        # Get the response content and tokens
        if response.error:
            print(f"Error: {response.error}")
            continue
        res_content = response.response
        prompt_tokens = response.prompt_tokens
        response_tokens = response.response_tokens
        # Print the response content and tokens
        print(f"Response: {res_content}, Prompt Tokens: {prompt_tokens}, Response Tokens: {response_tokens}, error: {response.error}")

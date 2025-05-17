from openai import OpenAI
from typing import List
import concurrent.futures
import os
from dataclasses import dataclass

# Get os environment variable
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY is None:
    raise ValueError("DEEPSEEK_API_KEY environment variable not set. Please set it to your Deepseek API key.")

@dataclass
class LLMsResponse:
    """Response from the LLM"""
    response: str
    prompt_tokens: int
    response_tokens: int
    error: str = None

class OnlineLLMs:
    def __init__(self, 
                 model: str = "deepseek-chat", 
                 base_url: str = "https://api.deepseek.com",
                 system_prompt: str = "You are a helpful assistant"):
        super().__init__()
        self.model = model
        self.base_url = base_url
        self.system_prompt = system_prompt
    
    def completion_batch(self,
                   prompts: List[str],
                   temperature: float = 0,
                   max_tokens: int = 256,
                   stop_tokens: List[str] = None,
                   n: int = 1,
                   num_threads: int = 10,) -> List[LLMsResponse]:
        
        responses = []
        # Start batch size of threads to process the requests
        for i in range(0, len(prompts), num_threads):
            thread_prompts = prompts[i:i + num_threads]
            # Start Thread to process the requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(self.completion, prompt, temperature, max_tokens, stop_tokens, 1) for prompt in thread_prompts]
                
                for future in futures:
                    # Get the response content and tokens
                    responses.append(future.result())
                   
        return responses
               
    def completion(self, 
                   prompt: str,
                   temperature: float = 0,
                   max_tokens: int = 256,
                   stop_tokens: List[str] = None,
                   n: int = 1,) -> LLMsResponse:
        client = OpenAI(
            base_url=self.base_url,
            api_key=DEEPSEEK_API_KEY,
        )
        res_content = None
        prompt_tokens = 0
        res_tokens = 0
        error = None
        try:
            # Help to get the number of tokens in the prompt and response
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop_tokens,
                n=n, # Deepseek API is not supporting batch size yet.
            )
            # Get the prompt tokens
            prompt_tokens = response.usage.prompt_tokens
            # Get the response content and tokens
            res_content = response.choices[0].message.content
            res_tokens = response.usage.completion_tokens
        except Exception as e:
            # Handle the error and return None
            print("ERROR:\n" + prompt)
            error = str(e)
        
        return LLMsResponse(res_content, prompt_tokens, res_tokens, error)

if __name__ == "__main__":
    llm = OnlineLLMs()
    prompts = ["What is the capital of France?", 
               "What is the capital of Germany?", 
               "What is the capital of Italy?"]
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

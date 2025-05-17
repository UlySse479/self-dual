import re
import os
import numpy as np
import random
from pathlib import Path
import json

def extract_boxed_from_str(text: str) -> str:
    start = text.rfind('oxed{')
    if start == -1:
        return None  

    # Skip the 'oxed{' part to find the first '{'
    balance = 1
    i = start + 5
    end = i
    while i < len(text) and balance > 0:
        if text[i] == '{':
            balance += 1
        elif text[i] == '}':
            balance -= 1
        i += 1
        if balance == 0:
            end = i  
    # extract the content between 'oxed{' and the last '}'
    return text[start + 5:end - 1]

def extract_last_code_block(text: str) -> str:
    pattern_python = re.compile(r'```python\s+([^`]+)```', re.DOTALL)

    matches = []
    for pattern in [pattern_python]:
        matches.extend(pattern.finditer(text))
    
    if not matches:
        return None  

    last_match = max(matches, key=lambda m: m.end())
    return last_match.group(1).strip()

def load_prompt( prompt_type: str, dataset_name: str) -> str:
    """
    Load a prompt from a file.
    """
    # Define the path to the prompts directory
    prompts_dir = Path(__file__).parent.parent.parent / "prompts" / dataset_name
    
    # Construct the full path to the prompt file
    prompt_path = os.path.join(prompts_dir, f"{prompt_type}.md")
    
    # Check if the file exists
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file '{prompt_path}' does not exist.")
    
    # Read the content of the prompt file
    with open(prompt_path, 'r', encoding='utf-8') as file:
        prompt_content = file.read()
    
    return prompt_content

def load_jsonl(file_path):
    """Load a JSON Lines file."""
    data = []
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def set_seed(seed: int = 0) -> None:
    np.random.seed(seed)
    random.seed(seed)
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    print(f"Random seed set as {seed}")

def _fix_fracs(string: str):
    substrs = string.split("\\frac")
    new_str = substrs[0]
    if len(substrs) > 1:
        substrs = substrs[1:]
        for substr in substrs:
            new_str += "\\frac"
            if len(substr) > 0 and substr[0] == "{":
                new_str += substr
            else:
                try:
                    assert len(substr) >= 2
                except:
                    return string
                a = substr[0]
                b = substr[1]
                if b != "{":
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}{" + b + "}" + post_substr
                    else:
                        new_str += "{" + a + "}{" + b + "}"
                else:
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}" + b + post_substr
                    else:
                        new_str += "{" + a + "}" + b
    string = new_str
    return string

def _fix_a_slash_b(string: str):
    if len(string.split("/")) != 2:
        return string
    a = string.split("/")[0]
    b = string.split("/")[1]
    try:
        if "sqrt" not in a:
            a = int(a)
        if "sqrt" not in b:
            b = int(b)
        assert string == "{}/{}".format(a, b)
        new_string = "\\frac{" + str(a) + "}{" + str(b) + "}"
        return new_string
    except:
        return string

def _fix_sqrt(string: str):
    _string = re.sub(r"\\sqrt(\w+)", r"\\sqrt{\1}", string)
    return _string

def strip_string(string: str):
    string = str(string).strip()
    # linebreaks
    string = string.replace("\n", "")

    # right "."
    string = string.rstrip(".")

    # remove inverse spaces
    string = string.replace("\\!", "")
    string = string.replace("\\ ", "")

    # replace \\ with \
    string = string.replace("\\\\", "\\")
    string = string.replace("\\\\", "\\")

    # replace tfrac and dfrac with frac
    string = string.replace("tfrac", "frac")
    string = string.replace("dfrac", "frac")

    # remove \left and \right
    string = string.replace("\\left", "")
    string = string.replace("\\right", "")

    # Remove unit: miles, dollars if after is not none
    _string = re.sub(r"\\text{.*?}$", "", string).strip()
    if _string != "" and _string != string:
        # print("Warning: unit not removed: '{}' -> '{}'".format(string, _string))
        string = _string

    # Remove circ (degrees)
    string = string.replace("^{\\circ}", "")
    string = string.replace("^\\circ", "")

    # remove dollar signs
    string = string.replace("\\$", "")
    string = string.replace("$", "")

    string = string.replace("\\text", "")
    string = string.replace("x\\in", "")

    # remove percentage
    string = string.replace("\\%", "")
    string = string.replace("%", "")

    # " 0." equivalent to " ." and "{0." equivalent to "{." Alternatively, add "0" if "." is the start of the string
    string = string.replace(" .", " 0.")
    string = string.replace("{.", "{0.")

    # cdot
    string = string.replace("\\cdot", "")

    # inf
    string = string.replace("infinity", "\\infty")
    if "\\infty" not in string:
        string = string.replace("inf", "\\infty")
    string = string.replace("+\\inity", "\\infty")

    # and 
    string = string.replace("and", "")
    string = string.replace("\\mathbf", "")

    # use regex to remove \mbox{...}
    string = re.sub(r"\\mbox{.*?}", "", string)

    # quote
    string.replace("'", "")
    string.replace("\"", "")
    
    # i, j
    if "j" in string and "i" not in string:
        string = string.replace("j", "i")

    # replace a.000b where b is not number or b is end, with ab, use regex
    string = re.sub(r"(\d+)\.0+([^\d])", r"\1\2", string)
    string = re.sub(r"(\d+)\.0+$", r"\1", string)

    # if empty, return empty string
    if len(string) == 0:
        return string
    if string[0] == ".":
        string = "0" + string

    # to consider: get rid of e.g. "k = " or "q = " at beginning
    if len(string.split("=")) == 2:
        if len(string.split("=")[0]) <= 2:
            string = string.split("=")[1]

    string = _fix_sqrt(string)
    string = string.replace(" ", "")

    # \frac1b or \frac12 --> \frac{1}{b} and \frac{1}{2}, etc. Even works with \frac1{72} (but not \frac{72}1). Also does a/b --> \\frac{a}{b}
    string = _fix_fracs(string)

    # NOTE: X/Y changed to \frac{X}{Y} in dataset, but in simple cases fix in case the model output is X/Y
    string = _fix_a_slash_b(string)

    return string

def remove_comment(code):
    if not code:
        return code
    code = code.split("\n")
    code = [line for line in code if not line.startswith("#")]
    code = [line for line in code if line.strip() != ""]
    return "\n".join(code)
if __name__ == '__main__':
    text = """
    ```python
    import math
    def calculate_circle_area(radius):
        area = math.pi * radius**2
        return area
    ```
    ```output
    print('hello')
    ```
    """
    code_block = extract_last_code_block(text)
    print(code_block) 
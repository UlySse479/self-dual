import subprocess
import uuid
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from dataclasses import dataclass
import traceback

@dataclass
class ExecutionResult:
    output: str
    error: str
    execution_time: float

class PythonExecutor:
    def __init__(self, filename_prefix:str='./tmp_code', len_output_str:int=1000, timeout:int=10):
        self.filename_prefix = filename_prefix
        self.len_output_str = len_output_str
        self.timeout = timeout
        
    def save_and_execute_code(self, code_str) -> ExecutionResult:
        if code_str is None:
            return ExecutionResult(output=None, error="Code is None", execution_time=0)
        unique_suffix = uuid.uuid4().hex
        filename = f"{self.filename_prefix}_{unique_suffix}.py"
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(code_str)
            
            start_time = time.time()

            result = subprocess.run(
                ['python', filename], 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            end_time = time.time()
            

            execution_time = end_time - start_time

            output = result.stdout.strip()
            error = result.stderr.strip()
            # Remove the file path from the error message
            error = re.sub(r'File "(?!<string>).*?", ', '', error) if error else None

        except subprocess.TimeoutExpired:
            output = None
            error = f"Execution exceeded timeout of {self.timeout} seconds."
            execution_time = self.timeout
        finally:
            if os.path.exists(filename):
                os.remove(filename)
        if output:
            output = self.truncate_string(str=output)
        if error: 
            error = self.truncate_string(str=error)

        return ExecutionResult(output, error, execution_time)

    def batch_execute_codes(self, code_list:List[str]) -> List[ExecutionResult]:
        results = [None] * len(code_list)

        def execute_and_store(index, code):
            result = self.save_and_execute_code(code)
            results[index] = result
        
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(execute_and_store, i, code) for i, code in enumerate(code_list)]
            for future in as_completed(futures):
                future.result()  
                
        return results

    # truncate string to max_len_str
    def truncate_string(self, str:str) -> str:
        if len(str) > self.len_output_str:
            return str[:self.len_output_str]
    
        return str

if __name__ == "__main__":
    executor = PythonExecutor()
    
    code1 = """
from sympy import Eq, solve, pi, I, Rational, sqrt
import time

# Define the complex numbers w and z
w = (sqrt(3) + I) / 2
z = (-1 + I * sqrt(3)) / 2
time.sleep(6)
# Function to count valid (r, s) pairs
def count_pairs():
    count = 0
    for r in range(1, 101):
        for s in range(1, 101):
            if I * w**r == z**s:
                count += 1
    return count

# Count the valid pairs
valid_pairs = count_pairs()
print(valid_pairs)
"""
    code2 = """
from sympy import symbols, Eq, solve

def find_P0_plus_Q0():
    x, b, c, d, e = symbols('x b c d e')

    # Define the polynomials
    P = 2*x**2 + b*x + c
    Q = -2*x**2 + d*x + e

    # Define the equations based on the given points
    eq1 = Eq(P.subs(x, 16), 54)
    eq2 = Eq(P.subs(x, 20), 53)
    eq3 = Eq(Q.subs(x, 16), 54)
    eq4 = Eq(Q.subs(x, 20), 53)

    # Solve the equations
    sol = solve((eq1, eq2, eq3, eq4), (b, c, d, e))

    # Calculate P(0) + Q(0)
    P0 = P.subs(sol)
    Q0 = Q.subs(sol)
    P0_plus_Q0 = P0.subs(x, 0) + Q0.subs(x, 0)

    return P0_plus_Q0

result = find_P0_plus_Q0()
print(result)
"""
    code3 = """
from sympy import symbols, Eq, solve

def find_coefficients():
    b, c, d, e = symbols('b c d e')
    eq1 = Eq(16*b + c, -458)
    eq2 = Eq(20*d + e, 853)
    solution = solve((eq1, eq2), (b, c, d, e))
    return solution

coefficients = find_coefficients()
print(coefficients)
"""
    code4 = """
from sympy import isprime, sqrt

def largest_prime():
    max_p = 0
    for a in range(1, 32):
        for b in range(1, 32):
            p = a**2 + b**2
            if isprime(p) and p < 1000:
                max_p = max(max_p, p)
    return max_p

largest_prime_value = largest_prime()
print(largest_prime_value)
"""
    code5 = """
def binary_addition(*bin_numbers):
    max_len = max(len(num) for num in bin_numbers)
    bin_numbers = [num.zfill(max_len) for num in bin_numbers]
    carry = 0
    result = []
    for i in range(max_len - 1, -1, -1):
        total = carry
        for num in bin_numbers:
            total += int(num[i])
        result.append(str(total % 2))
        carry = total // 2
    if carry:
        result.appendf(str(carry))
    return ''.join(reversed(result))

binary_numbers = ['101', '11', '1100', '11101']
answer = binary_addition(*binary_numbers)
print(answer)
"""
    
    code_list = [code1, code2, code3, code4, None, code5]
    start_time = time.time()
    results = executor.batch_execute_codes(code_list)
    
    for idx, result in enumerate(results):
        print(f"Code {idx + 1} - Result: {result.output}, Error: {result.error}, Execution Time: {result.execution_time:.2f} seconds")
    end_time = time.time()
    print(end_time - start_time)
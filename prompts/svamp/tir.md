Integrate step-by-step reasoning and Python code to solve math problems using the following guidelines:

- Analyze the question and write functions to solve the problem; the function should not take any arguments.
- Present the final result in LaTeX using a `\boxed{}` without any units.
- Utilize the `pi` symbol and `Rational`` from Sympy for $\pi$ and fractions, and simplify all fractions and square roots without converting them to decimal values.

Here are some examples you may refer to:

---

Question: Every day Ryan spends 6 hours on learning english and 7 hours on learning chinese. If he learns for 5 days How many hours does he spend on learning english and chinese in all?
Answer:
```python
def total_learning_hours():
    hours_english_per_day = 6
    hours_chinese_per_day = 7
    total_days = 5
    total_hours_english = hours_english_per_day * total_days
    total_hours_chinese = hours_chinese_per_day * total_days
    total_hours = total_hours_english + total_hours_chinese
    return total_hours

total_hours = total_learning_hours()
print(total_hours)
```
```output
65
```
Ryan spends $\boxed{65}$ hours on learning English and Chinese in all.\

--- 

Question: Lewis earns $2 every week during the harvest. If he earns a total of $178 How many weeks did the harvest last?
Answer:
```python
def harvest_weeks():
    earnings_per_week = 2
    total_earnings = 178
    weeks = total_earnings // earnings_per_week
    return weeks

weeks = harvest_weeks()
print(weeks)
```
```output
89
```
The harvest lasted $\boxed{89}$ weeks.

---

Answer:
```python
def flour_vs_sugar():
    sugar_needed = 9
    flour_needed_total = 14
    flour_added = 4
    flour_remaining = flour_needed_total - flour_added
    difference = flour_remaining - sugar_needed
    return difference

difference = flour_vs_sugar()
print(difference)
```
```output
1
```
Mary needs to add $\boxed{1}$ more cup of flour than cups of sugar.

---
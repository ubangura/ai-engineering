import ast
import json
import re
from statistics import mean
from typing import Literal, TypedDict

from messaging import add_assistant_message, add_user_message, chat

MAX_TOKENS = 1000


class TestCase(TypedDict):
    task: str
    format: Literal["Python", "JSON", "Regex"]
    solution_criteria: str


class TestResult(TypedDict):
    output: str
    test_case: TestCase
    score: int
    reasoning: str


class ModelEval(TypedDict):
    strengths: list[str]
    weaknesses: list[str]
    reasoning: str
    score: int


def validate_python(text: str) -> int:
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError:
        return 0


def validate_regex(text: str) -> int:
    try:
        re.compile(text.strip())
        return 10
    except re.error:
        return 0


def validate_json(text: str) -> int:
    try:
        json.loads(text.strip())
        return 10
    except json.JSONDecodeError:
        return 0


def grade_syntax(response: str, test_case: TestCase) -> int:
    validators = {
        "JSON": validate_json,
        "Python": validate_python,
        "Regex": validate_regex,
    }
    return validators[test_case["format"]](response)


def run_prompt(test_case: TestCase) -> str:
    prompt = f"""
    Please provide a solution to the following task:

    {test_case["task"]}

    * Respond only with Python, JSON, or plain Regex
    * Do not add any comments, commentary, or explanation
    """

    messages = add_user_message([], prompt)
    messages = add_assistant_message(messages, "```code")
    return chat(messages, max_tokens=MAX_TOKENS, stop_sequences=["\n```"])


def grade_by_model(test_case: TestCase, output: str) -> ModelEval:
    eval_prompt = f"""
    You are an expert AWS code reviewer. Your task is to evaluate the following AI-generated solution.

    Original Task:
    <task>
    {test_case["task"]}
    </task>

    Solution to Evaluate:
    <solution>
    {output}
    </solution>

    Solution Criteria:
    <criteria>
    {test_case["solution_criteria"]}
    </criteria>

    Output Format
    Provide your evaluation as a structured JSON object with the following fields, in this specific order:
    - "strengths": An array of 1-3 key strengths
    - "weaknesses": An array of 1-3 key areas for improvement
    - "reasoning": A concise explanation of your overall assessment
    - "score": A number between 1-10

    Respond with JSON. Keep your response concise and direct.
    Example response shape:
    {{
        "strengths": string[],
        "weaknesses": string[],
        "reasoning": string,
        "score": number
    }}
    """

    messages = add_user_message([], eval_prompt)
    messages = add_assistant_message(messages, "```json")
    output = chat(messages, max_tokens=MAX_TOKENS, stop_sequences=["\n```"])
    return json.loads(output)


def run_test_case(test_case: TestCase) -> TestResult:
    output = run_prompt(test_case)

    model_eval = grade_by_model(test_case, output)
    syntax_score = grade_syntax(output, test_case)

    # model_eval score is 1-10 (continuous); syntax_score is 0 or 10 (binary pass/fail)
    score = (model_eval["score"] + syntax_score) // 2

    return {
        "output": output,
        "test_case": test_case,
        "score": score,
        "reasoning": model_eval["reasoning"],
    }


def run_eval(dataset: list[TestCase]) -> list[TestResult]:
    evals = [run_test_case(test_case) for test_case in dataset]

    average_score = mean([eval["score"] for eval in evals])
    print(f"Average score: {average_score}")
    return evals


with open("dataset.json", "r") as f:
    dataset: list[TestCase] = json.load(f)

evals = run_eval(dataset)
print(json.dumps(evals, indent=2))

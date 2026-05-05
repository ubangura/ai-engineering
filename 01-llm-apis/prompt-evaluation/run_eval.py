from prompt_eval.constants import MAX_TOKENS
from prompt_eval.evaluator import PromptEvaluator
from prompt_eval.prompts import MEAL_PLAN_PROMPT_TEMPLATE

from messaging import add_user_message, chat

evaluator = PromptEvaluator(max_concurrent_tasks=1)


def run_prompt(prompt_inputs):
    prompt = MEAL_PLAN_PROMPT_TEMPLATE.format(**prompt_inputs)
    messages = []
    add_user_message(messages, prompt)
    return chat(messages, max_tokens=MAX_TOKENS)


results = evaluator.run_evaluation(
    run_prompt_function=run_prompt,
    dataset_file="data/dataset.json",
    extra_criteria="""
    The output should include:
    - Daily caloric total
    - Macronutrient breakdown
    - Meals with exact foods, portions, and timing
""",
    json_output_file="output/output_v3.json",
    html_output_file="output/output_v3.html",
)

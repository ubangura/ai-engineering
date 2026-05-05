from prompt_eval.constants import MAX_TOKENS
from prompt_eval.evaluator import PromptEvaluator

from messaging import add_user_message, chat

evaluator = PromptEvaluator(max_concurrent_tasks=1)


def run_prompt(prompt_inputs):
    prompt = f"""
    Generate a one-day meal plan for an athelete that meets their dietary restrictions.

    - Height: {prompt_inputs["height"]}
    - Weight: {prompt_inputs["weight"]}
    - Goal: {prompt_inputs["goal"]}
    - Dietary restrictions: {prompt_inputs["restrictions"]}
    """

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
    json_output_file="output/output_v2.json",
    html_output_file="output/output_v2.html",
)

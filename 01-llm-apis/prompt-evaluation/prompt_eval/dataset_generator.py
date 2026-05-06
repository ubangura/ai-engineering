import concurrent.futures
import json

from messaging import add_assistant_message, add_user_message, chat, text_from_message

from .constants import MAX_TOKENS
from .models import GeneratedTestCase, TestCase
from .progress import ProgressReporter
from .prompts import (
    GENERATE_IDEAS_SYSTEM_PROMPT,
    GENERATE_IDEAS_TEMPLATE,
    GENERATE_TEST_CASE_SYSTEM_PROMPT,
    GENERATE_TEST_CASE_TEMPLATE,
)
from .template import escape_newlines, render


class DatasetGenerator:
    """Generates evaluation datasets by prompting an LLM for diverse test scenarios and converting them into `TestCase` objects."""

    def __init__(self, max_concurrent_tasks: int = 3) -> None:
        self.max_concurrent_tasks = max_concurrent_tasks

    def generate_unique_ideas(
        self,
        task_description: str,
        prompt_inputs_spec: dict[str, str],
        num_cases: int,
    ) -> list[str]:
        """Ask an LLM for `num_cases` distinct scenario descriptions that exercise different aspects of `task_description`. Returns a list of short idea strings."""
        example_prompt_inputs = "".join(
            f'"{key}": str # {escape_newlines(value)},'
            for key, value in prompt_inputs_spec.items()
        )

        rendered_prompt = render(
            GENERATE_IDEAS_TEMPLATE,
            {
                "task_description": task_description,
                "num_cases": num_cases,
                "prompt_inputs_spec": example_prompt_inputs,
            },
        )

        messages = add_user_message([], rendered_prompt)
        add_assistant_message(messages, "```json")
        text = text_from_message(chat(
            messages,
            max_tokens=MAX_TOKENS,
            stop_sequences=["```"],
            system=GENERATE_IDEAS_SYSTEM_PROMPT,
            temperature=1.0,
        ))

        return json.loads(text)

    def generate_test_case(
        self,
        task_description: str,
        idea: str,
        prompt_inputs_spec: dict[str, str] | None = None,
    ) -> TestCase:
        """Turn a scenario `idea` into a fully-populated `TestCase`. Keys in `prompt_inputs_spec` constrain which input fields the LLM may populate."""
        if prompt_inputs_spec is None:
            prompt_inputs_spec = {}

        example_prompt_inputs = "".join(
            f'"{key}": "EXAMPLE_VALUE", // {escape_newlines(value)}\n'
            for key, value in prompt_inputs_spec.items()
        )
        allowed_keys = ", ".join(f'"{key}"' for key in prompt_inputs_spec)

        rendered_prompt = render(
            GENERATE_TEST_CASE_TEMPLATE,
            {
                "allowed_keys": allowed_keys,
                "task_description": task_description,
                "idea": idea,
                "example_prompt_inputs": example_prompt_inputs,
            },
        )

        messages = add_user_message([], rendered_prompt)
        add_assistant_message(messages, "```json")
        text = text_from_message(chat(
            messages,
            max_tokens=MAX_TOKENS,
            stop_sequences=["```"],
            system=GENERATE_TEST_CASE_SYSTEM_PROMPT,
            temperature=0.7,
        ))

        generated = GeneratedTestCase.model_validate_json(text)
        return TestCase(
            **generated.model_dump(),
            task_description=task_description,
            scenario=idea,
        )

    def generate_dataset(
        self,
        task_description: str,
        prompt_inputs_spec: dict[str, str] | None = None,
        num_cases: int = 1,
        output_file: str = "dataset.json",
    ) -> list[TestCase]:
        """Generate `num_cases` test cases concurrently and write them to `output_file` as JSON."""
        if prompt_inputs_spec is None:
            prompt_inputs_spec = {}

        ideas = self.generate_unique_ideas(
            task_description, prompt_inputs_spec, num_cases
        )
        progress = ProgressReporter(total=len(ideas), label="Generated")
        dataset: list[TestCase] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_concurrent_tasks
        ) as executor:
            futures = {
                executor.submit(
                    self.generate_test_case, task_description, idea, prompt_inputs_spec
                ): idea
                for idea in ideas
            }

            for future in concurrent.futures.as_completed(futures):
                try:
                    dataset.append(future.result())
                    progress.tick()
                except Exception as e:
                    print(f"Error generating test case: {e}")

        with open(output_file, "w") as f:
            json.dump([test_case.model_dump() for test_case in dataset], f, indent=2)

        return dataset

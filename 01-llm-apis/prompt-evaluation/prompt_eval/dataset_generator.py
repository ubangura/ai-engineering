import concurrent.futures
import json
from textwrap import dedent

from messaging import add_assistant_message, add_user_message, chat

from .constants import MAX_TOKENS
from .models import GeneratedTestCase, TestCase
from .progress import ProgressReporter
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
        prompt = """
        Generate {num_cases} unique, diverse ideas for testing a prompt that accomplishes this task:

        <task_description>
        {task_description}
        </task_description>

        The prompt will receive the following inputs
        <prompt_inputs>
        {prompt_inputs_spec}
        </prompt_inputs>

        Each idea should represent a distinct scenario or example that tests different aspects of the task.

        Output Format:
        Provide your response as a structured JSON array where each item is a brief description of the idea.

        Example:
        ```json
        [
            "Testing with technical computer science terminology",
            "Testing with medical research findings",
            "Testing with complex mathematical concepts",
            ...
        ]
        ```

        Ensure each idea is:
        - Clearly distinct from the others
        - Relevant to the task description
        - Specific enough to guide generation of a full test case
        - Quick to solve without requiring extensive computation or multi-step processing
        - Solvable with no more than 400 tokens of output

        Remember, only generate {num_cases} unique ideas
        """

        system_prompt = "You are a test scenario designer specialized in creating diverse, unique testing scenarios."

        example_prompt_inputs = "".join(
            f'"{key}": str # {escape_newlines(value)},'
            for key, value in prompt_inputs_spec.items()
        )

        rendered_prompt = render(
            dedent(prompt),
            {
                "task_description": task_description,
                "num_cases": num_cases,
                "prompt_inputs_spec": example_prompt_inputs,
            },
        )

        messages = add_user_message([], rendered_prompt)
        add_assistant_message(messages, "```json")
        text = chat(
            messages,
            max_tokens=MAX_TOKENS,
            stop_sequences=["```"],
            system=system_prompt,
            temperature=1.0,
        )

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

        prompt = """
        Generate a single detailed test case for a prompt evaluation based on:

        <task_description>
        {task_description}
        </task_description>

        <specific_idea>
        {idea}
        </specific_idea>

        <allowed_input_keys>
        {allowed_keys}
        </allowed_input_keys>

        Output Format:
        ```json
        {{
            "prompt_inputs": {{
            {example_prompt_inputs}
            }},
            "solution_criteria": ["criterion 1", "criterion 2", ...] // Concise list of criteria for evaluating the solution, 1 to 4 items
        }}
        ```

        IMPORTANT REQUIREMENTS:
        - You MUST ONLY use these exact input keys in your prompt_inputs: {allowed_keys}
        - Do NOT add any additional keys to prompt_inputs
        - All keys listed in allowed_input_keys must be included in your response
        - Make the test case realistic and practically useful
        - Include measurable, concise solution criteria
        - The solution criteria should ONLY address the direct requirements of the task description and the generated prompt_inputs
        - Avoid over-specifying criteria with requirements that go beyond the core task
        - Keep solution criteria simple, focused, and directly tied to the fundamental task
        - The test case should be tailored to the specific idea provided
        - Quick to solve without requiring extensive computation or multi-step processing
        - Solvable with no more than 400 tokens of output
        - DO NOT include any fields beyond those specified in the output format

        Here's an example of a sample input with an ideal output:
        <sample_input>
        <sample_task_description>
        Extract topics out of a passage of text
        </sample_task_description>
        <sample_specific_idea>
        Testing with a text that contains multiple nested topics and subtopics (e.g., a passage about renewable energy that covers solar power economics, wind turbine technology, and policy implications simultaneously)
        </sample_specific_idea>

        <sample_allowed_input_keys>
        "content"
        </sample_allowed_input_keys>
        </sample_input>
        <ideal_output>
        ```json
        {
            "prompt_inputs": {
                "content": "The transition to renewable energy encompasses numerous interdependent dimensions. Solar photovoltaic technology has seen dramatic cost reductions, with panel efficiency improving 24% since 2010 while manufacturing costs declined by 89%, making it economically competitive with fossil fuels in many markets. Concurrently, wind energy has evolved through innovative turbine designs featuring carbon-fiber composite blades and advanced control systems that increase energy capture by 35% in low-wind conditions."
            },
            "solution_criteria": [
                "Includes all topics mentioned"
            ]
        }
        ```
        </ideal_output>
        This is ideal output because the solution criteria is concise and doesn't ask for anything outside of the scope of the task description.
        """

        system_prompt = "You are a test case creator specializing in designing evaluation scenarios."

        rendered_prompt = render(
            dedent(prompt),
            {
                "allowed_keys": allowed_keys,
                "task_description": task_description,
                "idea": idea,
                "example_prompt_inputs": example_prompt_inputs,
            },
        )

        messages = add_user_message([], rendered_prompt)
        add_assistant_message(messages, "```json")
        text = chat(
            messages,
            max_tokens=MAX_TOKENS,
            stop_sequences=["```"],
            system=system_prompt,
            temperature=0.7,
        )

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

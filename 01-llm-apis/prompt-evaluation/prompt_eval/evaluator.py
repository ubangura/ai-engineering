import concurrent.futures
import json
from collections.abc import Callable
from statistics import mean
from textwrap import dedent

from messaging import add_assistant_message, add_user_message, chat

from .constants import MAX_TOKENS
from .models import EvaluationResult, Grade, TestCase
from .progress import ProgressReporter
from .report import generate_prompt_evaluation_report
from .template import escape_newlines, render


class PromptEvaluator:
    """Runs a prompt function against an evaluation dataset and grades each output with an LLM judge."""

    def __init__(self, max_concurrent_tasks: int = 3) -> None:
        self.max_concurrent_tasks = max_concurrent_tasks

    def grade_output(
        self,
        test_case: TestCase,
        output: str,
        extra_criteria: str | None,
    ) -> Grade:
        """Ask an LLM judge to score `output` against the test case's solution criteria. `extra_criteria`, if provided, are treated as mandatory requirements — any violation caps the score at 3."""
        prompt_inputs = "".join(
            f'"{key}":"{escape_newlines(value)}",\n'
            for key, value in test_case.prompt_inputs.items()
        )

        extra_criteria_section = ""
        if extra_criteria:
            extra_criteria_template = """
            Mandatory Requirements - ANY VIOLATION MEANS AUTOMATIC FAILURE (score of 3 or lower):
            <extra_important_criteria>
            {extra_criteria}
            </extra_important_criteria>
            """
            extra_criteria_section = render(
                dedent(extra_criteria_template),
                {"extra_criteria": extra_criteria},
            )

        eval_template = """
        Your task is to evaluate the following AI-generated solution with EXTREME RIGOR.

        Original task description:
        <task_description>
        {task_description}
        </task_description>

        Original task inputs:
        <task_inputs>
        {{ {prompt_inputs} }}
        </task_inputs>

        Solution to Evaluate:
        <solution>
        {output}
        </solution>

        Criteria you should use to evaluate the solution:
        <criteria>
        {solution_criteria}
        </criteria>

        {extra_criteria_section}

        Scoring Guidelines:
        * Score 1-3: Solution fails to meet one or more MANDATORY requirements
        * Score 4-6: Solution meets all mandatory requirements but has significant deficiencies in secondary criteria
        * Score 7-8: Solution meets all mandatory requirements and most secondary criteria, with minor issues
        * Score 9-10: Solution meets all mandatory and secondary criteria

        IMPORTANT SCORING INSTRUCTIONS:
        * Grade the output based ONLY on the listed criteria. Do not add your own extra requirements.
        * If a solution meets all of the mandatory and secondary criteria give it a 10
        * Don't complain that the solution "only" meets the mandatory and secondary criteria. Solutions shouldn't go above and beyond - they should meet the exact listed criteria.
        * ANY violation of a mandatory requirement MUST result in a score of 3 or lower
        * The full 1-10 scale should be utilized - don't hesitate to give low scores when warranted

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

        eval_prompt = render(
            dedent(eval_template),
            {
                "task_description": test_case.task_description,
                "prompt_inputs": prompt_inputs,
                "output": output,
                "solution_criteria": "\n".join(test_case.solution_criteria),
                "extra_criteria_section": extra_criteria_section,
            },
        )

        messages = add_user_message([], eval_prompt)
        add_assistant_message(messages, "```json")
        eval_text = chat(
            messages,
            max_tokens=MAX_TOKENS,
            stop_sequences=["```"],
            temperature=0.0,
        )
        return Grade.model_validate_json(eval_text)

    def run_test_case(
        self,
        test_case: TestCase,
        run_prompt_function: Callable[[dict[str, str]], str],
        extra_criteria: str | None = None,
    ) -> EvaluationResult:
        """Run a single test case: call `run_prompt_function(prompt_inputs)`, then grade the returned string."""
        output = run_prompt_function(test_case.prompt_inputs)
        grade = self.grade_output(test_case, output, extra_criteria)
        return EvaluationResult(
            output=output,
            test_case=test_case,
            score=grade.score,
            reasoning=grade.reasoning,
        )

    def run_evaluation(
        self,
        run_prompt_function: Callable[[dict[str, str]], str],
        dataset_file: str,
        extra_criteria: str | None = None,
        json_output_file: str = "output/output.json",
        html_output_file: str = "output/output.html",
    ) -> list[EvaluationResult]:
        """Load test cases from `dataset_file`, run and grade each one concurrently, then write results to `json_output_file` and `html_output_file`. Prints the average score."""
        with open(dataset_file, "r") as f:
            dataset = [TestCase.model_validate(obj) for obj in json.load(f)]

        progress = ProgressReporter(total=len(dataset), label="Graded")
        results: list[EvaluationResult] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_concurrent_tasks
        ) as executor:
            futures = {
                executor.submit(
                    self.run_test_case, test_case, run_prompt_function, extra_criteria
                ): test_case
                for test_case in dataset
            }

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                progress.tick()

        average_score = mean(result.score for result in results)
        print(f"Average score: {average_score}")

        with open(json_output_file, "w") as f:
            json.dump([result.model_dump() for result in results], f, indent=2)

        html = generate_prompt_evaluation_report(results)
        with open(html_output_file, "w", encoding="utf-8") as f:
            f.write(html)

        return results

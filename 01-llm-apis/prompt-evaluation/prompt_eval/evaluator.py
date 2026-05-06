import concurrent.futures
import json
from collections.abc import Callable
from statistics import mean

from messaging import add_assistant_message, add_user_message, chat, text_from_message

from .constants import MAX_TOKENS
from .models import EvaluationResult, Grade, TestCase
from .progress import ProgressReporter
from .prompts import GRADE_OUTPUT_EXTRA_CRITERIA_TEMPLATE, GRADE_OUTPUT_TEMPLATE
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
            extra_criteria_section = render(
                GRADE_OUTPUT_EXTRA_CRITERIA_TEMPLATE,
                {"extra_criteria": extra_criteria},
            )

        eval_prompt = render(
            GRADE_OUTPUT_TEMPLATE,
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
        eval_text = text_from_message(chat(
            messages,
            max_tokens=MAX_TOKENS,
            stop_sequences=["```"],
            temperature=0.0,
        ))
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

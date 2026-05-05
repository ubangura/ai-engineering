from pydantic import BaseModel


class GeneratedTestCase(BaseModel):
    """Raw test case produced by the LLM — inputs and criteria, without task context."""

    prompt_inputs: dict[str, str]
    solution_criteria: list[str]


class TestCase(GeneratedTestCase):
    """A fully-specified test case, combining generated inputs/criteria with task context."""

    task_description: str
    scenario: str


class Grade(BaseModel):
    """LLM judge's structured assessment of a single output."""

    strengths: list[str]
    weaknesses: list[str]
    reasoning: str
    score: int


class EvaluationResult(BaseModel):
    """The outcome of running and grading one test case."""

    test_case: TestCase
    output: str
    score: int
    reasoning: str

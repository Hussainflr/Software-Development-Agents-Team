from pydantic import BaseModel, Field


class EvaluationScore(BaseModel):
    correctness: int = Field(ge=0, le=10)
    completeness: int = Field(ge=0, le=10)
    code_quality: int = Field(ge=0, le=10)
    passed: bool
    summary: str


class EvaluationScorer:
    """Simple deterministic evaluator that can later be replaced by LLM judges."""

    pass_threshold = 7

    def score(self, artifacts: dict[str, str], bugs: list[str]) -> EvaluationScore:
        has_backend = any(path.startswith("generated_backend/") for path in artifacts)
        has_frontend = any(path.startswith("generated_frontend/") for path in artifacts)
        has_tests = any(path.startswith("generated_tests/") for path in artifacts)

        correctness = 5 + int(has_backend) * 2 + int(has_tests) * 2 - min(len(bugs), 3)
        completeness = 4 + int(has_backend) * 2 + int(has_frontend) * 2 + int(has_tests) * 2
        code_quality = 6 + int(not bugs) * 2 + int(has_tests)

        correctness = max(0, min(10, correctness))
        completeness = max(0, min(10, completeness))
        code_quality = max(0, min(10, code_quality))
        passed = min(correctness, completeness, code_quality) >= self.pass_threshold and not bugs

        summary = (
            "Evaluation passed. Generated artifacts are complete enough for approval."
            if passed
            else "Evaluation failed. Send feedback through the refinement loop."
        )
        return EvaluationScore(
            correctness=correctness,
            completeness=completeness,
            code_quality=code_quality,
            passed=passed,
            summary=summary,
        )

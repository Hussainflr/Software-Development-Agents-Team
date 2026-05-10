from typing import Any

from evaluation.deterministic import DeterministicEvaluator
from evaluation.llm_judge import LLMJudge
from evaluation.schemas import ChecklistResult, EvaluationScore, LLMJudgeResult


class EvaluationScorer:
    """Coordinates deterministic evaluation and optional LLM-as-judge review."""

    pass_threshold = 7

    def __init__(
        self,
        deterministic: DeterministicEvaluator | None = None,
        llm_judge_evaluator: LLMJudge | None = None,
    ) -> None:
        self.deterministic = deterministic or DeterministicEvaluator()
        self.llm_judge_evaluator = llm_judge_evaluator or LLMJudge()

    def score(
        self,
        artifacts: dict[str, str],
        bugs: list[str],
        requirement: str = "",
        llm_judge: Any | None = None,
    ) -> EvaluationScore:
        deterministic = self.deterministic.score(artifacts, bugs)
        llm_result: LLMJudgeResult | None = None
        llm_error = ""

        if llm_judge is not None:
            try:
                llm_result = self.llm_judge_evaluator.score(
                    requirement=requirement,
                    artifacts=artifacts,
                    bugs=bugs,
                    chat_model=llm_judge,
                )
            except Exception as exc:
                llm_error = f"LLM judge unavailable: {exc}"

        if llm_result:
            correctness = min(deterministic.score.correctness, llm_result.correctness)
            completeness = min(deterministic.score.completeness, llm_result.completeness)
            code_quality = min(deterministic.score.code_quality, llm_result.code_quality)
            passed = (
                deterministic.score.passed
                and llm_result.passed
                and min(correctness, completeness, code_quality) >= self.pass_threshold
            )
            summary = self._combined_summary(deterministic, llm_result)
        else:
            correctness = deterministic.score.correctness
            completeness = deterministic.score.completeness
            code_quality = deterministic.score.code_quality
            passed = deterministic.score.passed
            summary = deterministic.score.summary
            if llm_error:
                summary = f"{summary} {llm_error}"

        return EvaluationScore(
            correctness=correctness,
            completeness=completeness,
            code_quality=code_quality,
            passed=passed,
            summary=summary,
        )

    @staticmethod
    def _combined_summary(deterministic: ChecklistResult, llm_result: LLMJudgeResult) -> str:
        failed = "; ".join(deterministic.failed_checks[:5]) or "none"
        findings = "; ".join(llm_result.findings[:5]) or "none"
        return (
            f"Hybrid evaluation complete. Deterministic: {deterministic.score.summary} "
            f"LLM judge: {llm_result.summary}. "
            f"Deterministic failed checks: {failed}. LLM findings: {findings}."
        )


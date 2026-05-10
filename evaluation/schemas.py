from dataclasses import dataclass

from pydantic import BaseModel, Field


class EvaluationScore(BaseModel):
    correctness: int = Field(ge=0, le=10)
    completeness: int = Field(ge=0, le=10)
    code_quality: int = Field(ge=0, le=10)
    passed: bool
    summary: str


class LLMJudgeResult(EvaluationScore):
    findings: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ChecklistResult:
    score: EvaluationScore
    passed_checks: list[str]
    failed_checks: list[str]


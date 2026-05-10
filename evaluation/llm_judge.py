import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from evaluation.deterministic import DeterministicEvaluator
from evaluation.schemas import LLMJudgeResult


class LLMJudge:
    """LLM-as-judge evaluator for requirement fit and integration quality."""

    artifact_preview_limit = 12000

    def score(
        self,
        *,
        requirement: str,
        artifacts: dict[str, str],
        bugs: list[str],
        chat_model: Any,
    ) -> LLMJudgeResult:
        artifact_preview = self._artifact_preview(artifacts)
        messages = [
            SystemMessage(
                content=(
                    "You are an impartial senior software QA judge. Evaluate generated code for a local demo. "
                    "Be strict about runnable code, requirement fit, tests, integration, and obvious security issues. "
                    "Return only valid JSON."
                )
            ),
            HumanMessage(
                content=(
                    "Evaluate these generated artifacts.\n\n"
                    f"Requirement:\n{requirement or 'No requirement provided.'}\n\n"
                    f"Reported tester bugs:\n{json.dumps(bugs, indent=2)}\n\n"
                    f"Artifacts:\n{artifact_preview}\n\n"
                    "Return JSON with this exact shape:\n"
                    "{\n"
                    '  "correctness": 0,\n'
                    '  "completeness": 0,\n'
                    '  "code_quality": 0,\n'
                    '  "passed": false,\n'
                    '  "summary": "short reason",\n'
                    '  "findings": ["specific issue or positive finding"]\n'
                    "}\n"
                    "Scores must be integers from 0 to 10. Pass only if the app is likely runnable locally."
                )
            ),
        ]
        response = chat_model.with_retry(stop_after_attempt=2).invoke(messages)
        raw_content = str(getattr(response, "content", response)).strip()
        data = self._parse_json_object(raw_content)
        return LLMJudgeResult(
            correctness=DeterministicEvaluator._clamp_score(data.get("correctness")),
            completeness=DeterministicEvaluator._clamp_score(data.get("completeness")),
            code_quality=DeterministicEvaluator._clamp_score(data.get("code_quality")),
            passed=bool(data.get("passed")),
            summary=str(data.get("summary") or "LLM judge completed evaluation."),
            findings=[str(item) for item in data.get("findings", []) if item],
        )

    def _artifact_preview(self, artifacts: dict[str, str]) -> str:
        chunks: list[str] = []
        remaining = self.artifact_preview_limit
        for path, content in sorted(artifacts.items()):
            if remaining <= 0:
                break
            snippet = content[: min(len(content), remaining)]
            chunks.append(f"## {path}\n{snippet}")
            remaining -= len(snippet)
        return "\n\n".join(chunks)

    @staticmethod
    def _parse_json_object(raw_content: str) -> dict[str, Any]:
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("LLM judge did not return a JSON object.")
            return json.loads(cleaned[start : end + 1])


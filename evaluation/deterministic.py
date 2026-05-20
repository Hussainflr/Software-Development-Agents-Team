from typing import Any

from evaluation.consistency import EndpointConsistencyChecker
from evaluation.schemas import ChecklistResult, EvaluationScore


class DeterministicEvaluator:
    """Checklist-based evaluator for cheap, stable quality gates."""

    pass_threshold = 7

    def __init__(self, endpoint_checker: EndpointConsistencyChecker | None = None) -> None:
        self.endpoint_checker = endpoint_checker or EndpointConsistencyChecker()

    def score(self, artifacts: dict[str, str], bugs: list[str], requirement: str = "") -> ChecklistResult:
        backend = artifacts.get("generated_backend/main.py", "")
        frontend = artifacts.get("generated_frontend/app.py", "")
        tests = "\n\n".join(
            content for path, content in artifacts.items() if path.startswith("generated_tests/") and path.endswith(".py")
        )
        requirement_checks = self._requirement_alignment_checks(requirement, backend, frontend, tests)
        endpoint_consistency = self.endpoint_checker.check(artifacts)

        correctness_checks = {
            "backend FastAPI app exists": bool(backend and "FastAPI" in backend),
            "backend exposes routes": "@app." in backend,
            "backend has health endpoint": "/health" in backend,
            "frontend Streamlit app exists": bool(frontend and ("streamlit" in frontend.lower() or "st." in frontend)),
            "tests contain assertions": bool(tests and "assert " in tests),
            "frontend/tests reference existing backend routes": endpoint_consistency.passed,
            **requirement_checks,
        }
        completeness_checks = {
            "backend main artifact present": "generated_backend/main.py" in artifacts,
            "frontend app artifact present": "generated_frontend/app.py" in artifacts,
            "test artifact present": bool(tests),
            "backend README present": "generated_backend/README.md" in artifacts,
            "frontend README present": "generated_frontend/README.md" in artifacts,
            "tester report present": "generated_tests/TEST_REPORT.md" in artifacts,
        }
        quality_checks = {
            "no reported bugs": not bugs,
            "no hardcoded secret markers": not self._contains_secret_marker(artifacts),
            "no obvious unfinished placeholders": not self._contains_placeholder(artifacts),
            "backend has meaningful implementation": len(backend.strip()) >= 200,
            "frontend uses configurable backend URL": not frontend or "GENERATED_API_URL" in frontend,
            "tests use client or pytest conventions": not tests or ("TestClient" in tests or "pytest" in tests),
        }

        correctness = self._check_score(correctness_checks, penalty=len(bugs) * 2)
        completeness = self._check_score(completeness_checks)
        code_quality = self._check_score(quality_checks, penalty=len(bugs))

        failed_checks = [
            *self._failed_names(correctness_checks),
            *self._failed_names(completeness_checks),
            *self._failed_names(quality_checks),
        ]
        passed_checks = [
            *self._passed_names(correctness_checks),
            *self._passed_names(completeness_checks),
            *self._passed_names(quality_checks),
        ]
        passed = min(correctness, completeness, code_quality) >= self.pass_threshold and not bugs

        if passed:
            summary = "Deterministic evaluation passed. Core backend, frontend, tests, and quality checks are satisfied."
        else:
            top_failures = "; ".join(failed_checks[:5]) or "reported bugs exist"
            summary = f"Deterministic evaluation failed. Missing or weak checks: {top_failures}."

        return ChecklistResult(
            score=EvaluationScore(
                correctness=correctness,
                completeness=completeness,
                code_quality=code_quality,
                passed=passed,
                summary=summary,
            ),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
        )

    @classmethod
    def _check_score(cls, checks: dict[str, bool], penalty: int = 0) -> int:
        if not checks:
            return 0
        raw = round(10 * sum(checks.values()) / len(checks)) - penalty
        return cls._clamp_score(raw)

    @staticmethod
    def _clamp_score(value: Any) -> int:
        try:
            number = int(round(float(value)))
        except (TypeError, ValueError):
            number = 0
        return max(0, min(10, number))

    @staticmethod
    def _failed_names(checks: dict[str, bool]) -> list[str]:
        return [name for name, passed in checks.items() if not passed]

    @staticmethod
    def _passed_names(checks: dict[str, bool]) -> list[str]:
        return [name for name, passed in checks.items() if passed]

    @staticmethod
    def _contains_secret_marker(artifacts: dict[str, str]) -> bool:
        markers = ("api_key=", "secret=", "password=", "token=", "sk-", "BEGIN PRIVATE KEY")
        combined = "\n".join(artifacts.values()).lower()
        return any(marker.lower() in combined for marker in markers)

    @staticmethod
    def _contains_placeholder(artifacts: dict[str, str]) -> bool:
        markers = ("todo", "notimplemented", "your_api_key", "insert api key", "pass  #")
        combined = "\n".join(artifacts.values()).lower()
        return any(marker in combined for marker in markers)

    @staticmethod
    def _requirement_alignment_checks(
        requirement: str,
        backend: str,
        frontend: str,
        tests: str,
    ) -> dict[str, bool]:
        normalized_requirement = requirement.lower()
        if not all(term in normalized_requirement for term in ("rock", "paper", "scissors")):
            return {}

        backend_lower = backend.lower()
        frontend_lower = frontend.lower()
        tests_lower = tests.lower()
        return {
            "rock paper scissors backend play endpoint": "/play" in backend_lower,
            "rock paper scissors frontend controls": all(move in frontend_lower for move in ("rock", "paper", "scissors")),
            "rock paper scissors frontend calls play API": "/play" in frontend_lower,
            "rock paper scissors tests cover play API": "/play" in tests_lower,
        }

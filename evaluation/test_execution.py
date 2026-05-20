from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratedTestRunResult:
    attempted: bool
    passed: bool
    returncode: int | None
    summary: str
    stdout: str = ""
    stderr: str = ""

    def to_markdown(self) -> str:
        return "\n".join(
            [
                "# Generated Test Execution",
                "",
                f"- attempted: `{self.attempted}`",
                f"- passed: `{self.passed}`",
                f"- returncode: `{self.returncode}`",
                "",
                "## Summary",
                "",
                self.summary,
                "",
                "## stdout",
                "",
                "```text",
                self.stdout[-6000:],
                "```",
                "",
                "## stderr",
                "",
                "```text",
                self.stderr[-6000:],
                "```",
            ]
        ).strip()


class GeneratedTestRunner:
    """Runs generated pytest files in an isolated temporary directory."""

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def run(self, artifacts: dict[str, str]) -> GeneratedTestRunResult:
        test_paths = [
            path for path in artifacts if path.startswith("generated_tests/") and path.endswith(".py")
        ]
        if not test_paths:
            return GeneratedTestRunResult(
                attempted=False,
                passed=False,
                returncode=None,
                summary="No generated pytest files were found.",
            )

        with tempfile.TemporaryDirectory(prefix="agentic-os-generated-tests-") as temp_dir:
            root = Path(temp_dir)
            for path, content in artifacts.items():
                destination = self._safe_destination(root, path)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")

            for package_dir in ("generated_backend", "generated_frontend", "generated_tests"):
                directory = root / package_dir
                if directory.exists():
                    init_file = directory / "__init__.py"
                    init_file.touch(exist_ok=True)

            env = {**os.environ, "PYTHONPATH": str(root)}
            try:
                completed = subprocess.run(
                    [sys.executable, "-m", "pytest", "generated_tests", "-q"],
                    cwd=root,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return GeneratedTestRunResult(
                    attempted=True,
                    passed=False,
                    returncode=None,
                    summary=f"Generated tests timed out after {self.timeout_seconds} seconds.",
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                )

        passed = completed.returncode == 0
        return GeneratedTestRunResult(
            attempted=True,
            passed=passed,
            returncode=completed.returncode,
            summary="Generated tests passed." if passed else "Generated tests failed.",
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    @staticmethod
    def _safe_destination(root: Path, relative_path: str) -> Path:
        destination = (root / relative_path).resolve()
        if not destination.is_relative_to(root.resolve()):
            raise ValueError(f"Generated artifact path escapes run directory: {relative_path}")
        return destination

from __future__ import annotations

import textwrap

from agents.schemas import AgentOutput


class ArtifactValidationError(ValueError):
    """Raised when a generated artifact cannot be normalized into valid content."""


def normalize_agent_output(output: AgentOutput) -> AgentOutput:
    """Return an AgentOutput with generated artifacts normalized for persistence."""

    return output.model_copy(update={"artifacts": normalize_artifacts(output.artifacts)})


def normalize_artifacts(artifacts: dict[str, str]) -> dict[str, str]:
    return {path: normalize_artifact(path, content) for path, content in artifacts.items()}


def normalize_artifact(path: str, content: str) -> str:
    cleaned = _strip_code_fence(str(content)).replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if path.endswith(".py"):
        return normalize_python_source(path, cleaned)
    return cleaned


def normalize_python_source(path: str, source: str) -> str:
    """Normalize accidental markdown/model indentation and require valid Python."""

    candidates = [
        source,
        textwrap.dedent(source).strip("\n"),
        _dedent_indented_lines(source).strip("\n"),
        textwrap.dedent(_dedent_indented_lines(source)).strip("\n"),
    ]
    errors: list[str] = []
    for candidate in _unique(candidates):
        normalized = candidate.rstrip() + "\n"
        try:
            compile(normalized, path, "exec")
            return normalized
        except SyntaxError as exc:
            errors.append(f"{exc.__class__.__name__}: {exc.msg} at line {exc.lineno}")

    detail = "; ".join(errors[:3]) or "unknown syntax error"
    raise ArtifactValidationError(f"Generated Python artifact '{path}' is not valid after normalization: {detail}")


def _strip_code_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return content

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _dedent_indented_lines(source: str) -> str:
    lines = source.splitlines()
    indents = [
        len(line) - len(line.lstrip(" "))
        for line in lines
        if line.strip() and len(line) > len(line.lstrip(" "))
    ]
    if not indents:
        return source

    extra_indent = min(indents)
    prefix = " " * extra_indent
    return "\n".join(line[extra_indent:] if line.startswith(prefix) else line for line in lines)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered

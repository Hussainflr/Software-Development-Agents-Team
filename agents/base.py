import json
from dataclasses import dataclass, field
from textwrap import dedent

from llm_providers.base import ChatMessage, LLMClient


@dataclass
class AgentContext:
    run_id: int
    requirement: str
    artifacts: dict[str, str] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    bug_report: str = ""
    revision: bool = False


@dataclass
class AgentResult:
    summary: str
    artifacts: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    bugs: list[str] = field(default_factory=list)
    raw_response: str = ""


class BaseAgent:
    name = "Base Agent"
    role = "Generalist"

    def execute(self, context: AgentContext, llm_client: LLMClient) -> AgentResult:
        messages = self._build_messages(context)
        raw_response = llm_client.generate(messages=messages, temperature=0.2)
        try:
            parsed = parse_agent_json(raw_response)
            if not parsed.artifacts:
                return self.fallback_output(context, raw_response)
            parsed.raw_response = raw_response
            return parsed
        except ValueError:
            return self.fallback_output(context, raw_response)

    def _build_messages(self, context: AgentContext) -> list[ChatMessage]:
        artifact_index = "\n".join(f"- {path}" for path in sorted(context.artifacts)) or "- No artifacts yet"
        revision_note = (
            f"\nTester feedback to address:\n{context.bug_report}\n"
            if context.revision and context.bug_report
            else ""
        )
        system_prompt = dedent(
            f"""
            You are {self.name}, acting as the {self.role} in an agentic software development team.
            Work like a senior engineer. Be practical, concise, and implementation-oriented.
            Return only valid JSON. Do not wrap the JSON in Markdown fences.
            """
        ).strip()
        user_prompt = dedent(
            f"""
            Human manager requirement:
            {context.requirement}

            Existing artifact paths:
            {artifact_index}
            {revision_note}

            Your task:
            {self.task_instructions()}

            Return this exact JSON shape:
            {{
              "summary": "short summary of what you did",
              "artifacts": {{
                "relative/path.ext": "complete file contents"
              }},
              "notes": ["important implementation note"],
              "bugs": []
            }}
            """
        ).strip()
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def task_instructions(self) -> str:
        raise NotImplementedError

    def fallback_output(self, context: AgentContext, raw_response: str) -> AgentResult:
        raise NotImplementedError


def parse_agent_json(raw_response: str) -> AgentResult:
    """Parse a model JSON response, tolerating small amounts of surrounding text."""

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("LLM response did not contain a JSON object.")
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response contained invalid JSON.") from exc

    artifacts = data.get("artifacts") or {}
    if isinstance(artifacts, list):
        artifacts = {
            str(item.get("path")): str(item.get("content", ""))
            for item in artifacts
            if isinstance(item, dict) and item.get("path")
        }
    if not isinstance(artifacts, dict):
        artifacts = {}

    notes = data.get("notes") or []
    if isinstance(notes, str):
        notes = [notes]

    bugs = data.get("bugs") or []
    if isinstance(bugs, str):
        bugs = [bugs]

    return AgentResult(
        summary=str(data.get("summary") or "Agent completed its task."),
        artifacts={str(path): str(content) for path, content in artifacts.items()},
        notes=[str(note) for note in notes],
        bugs=[str(bug) for bug in bugs],
    )


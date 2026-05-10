import json
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from agents.schemas import AgentInput, AgentOutput
from prompts.loader import load_prompt
from skills.registry import render_skill_registry


class BaseAgent(ABC):
    name = "Base Agent"
    role = "Generalist"
    task_prompt = "agent_task.txt"
    skill_names: list[str] = []

    def invoke(self, agent_input: AgentInput, chat_model: Any) -> AgentOutput:
        """Run this agent as a LangChain prompt -> chat model -> Pydantic parser chain."""

        payload = self._build_payload(agent_input)
        chain = self.as_runnable(chat_model)
        try:
            result = chain.invoke(payload)
            if not result.artifacts:
                return self.fallback_output(agent_input, "LangChain parser returned no artifacts.")
            return result
        except Exception as exc:
            raw_response = self._invoke_raw(chat_model, payload)
            fallback_reason = raw_response or f"LangChain agent failed: {exc}"
            return self.fallback_output(agent_input, fallback_reason)

    def as_runnable(self, chat_model: Any):
        parser = PydanticOutputParser(pydantic_object=AgentOutput)
        return self.prompt_template() | chat_model.bind(temperature=0.2).with_retry(stop_after_attempt=3) | parser

    def runnable(self, chat_model: Any):
        return RunnableLambda(lambda data: self.invoke(AgentInput.model_validate(data), chat_model))

    def prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                ("system", load_prompt("system.txt")),
                ("human", load_prompt("agent_task.txt")),
            ]
        )

    def _build_payload(self, agent_input: AgentInput) -> dict[str, str]:
        artifact_index = "\n".join(f"- {path}" for path in sorted(agent_input.artifacts)) or "- No artifacts yet"
        revision_note = (
            f"\nTester feedback to address:\n{agent_input.bug_report}\n"
            if agent_input.revision and agent_input.bug_report
            else ""
        )
        parser = PydanticOutputParser(pydantic_object=AgentOutput)
        focused_context = agent_input.focused_context or {
            "user_requirement": agent_input.requirement,
            "agent_role": self.role,
            "relevant_outputs": artifact_index,
            "constraints": "Return complete file contents for every artifact. Keep secrets out of outputs.",
            "errors_or_feedback": revision_note.strip() or "None",
        }
        return {
            "agent_name": self.name,
            "agent_role": self.role,
            "user_requirement": agent_input.requirement,
            "focused_context": json.dumps(focused_context, indent=2),
            "skills": render_skill_registry(self.skill_names),
            "task": load_prompt(self.task_prompt),
            "format_instructions": parser.get_format_instructions(),
        }

    def _invoke_raw(self, chat_model: Any, payload: dict[str, str]) -> str:
        try:
            response = (self.prompt_template() | chat_model.bind(temperature=0.2)).invoke(payload)
            return str(getattr(response, "content", response)).strip()
        except Exception:
            return ""

    @abstractmethod
    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        raise NotImplementedError


def parse_agent_output(raw_response: str) -> AgentOutput:
    parser = PydanticOutputParser(pydantic_object=AgentOutput)
    try:
        return parser.parse(raw_response)
    except Exception as exc:
        try:
            return AgentOutput(**parse_agent_json(raw_response).model_dump())
        except ValueError:
            raise ValueError("LLM response did not match the required agent schema.") from exc


def parse_agent_json(raw_response: str) -> AgentOutput:
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

    return AgentOutput(
        summary=str(data.get("summary") or "Agent completed its task."),
        artifacts={str(path): str(content) for path, content in artifacts.items()},
        notes=[str(note) for note in notes],
        bugs=[str(bug) for bug in bugs],
    )

from dataclasses import dataclass


MAX_OUTPUT_CHARS = 6000


@dataclass(frozen=True)
class AgentFocus:
    current_task: str
    relevant_prefixes: tuple[str, ...]


FOCUS_BY_AGENT = {
    "Backend Agent": AgentFocus("Design backend APIs, data model, and backend files.", ("generated_backend/",)),
    "Frontend Agent": AgentFocus("Design frontend UI and connect it to backend APIs.", ("generated_backend/", "generated_frontend/")),
    "Tester Agent": AgentFocus("Review generated code, write tests, and report bugs.", ("generated_backend/", "generated_frontend/", "generated_tests/")),
    "Deployment Agent": AgentFocus("Package generated artifacts for local and Docker deployment.", ("generated_", "deployment/")),
}


class ContextBuilder:
    """Build small, focused context packages instead of sending full history.

    Beginners can think of this as packing a small brief for each specialist:
    the backend agent does not need every old chat message, but the tester does
    need the generated files and any known feedback.
    """

    def build(
        self,
        *,
        user_requirement: str,
        current_task: str,
        agent_name: str,
        agent_role: str,
        artifacts: dict[str, str],
        constraints: str,
        errors_or_feedback: str = "",
        long_term_memory: list[str] | None = None,
    ) -> dict[str, str]:
        focus = FOCUS_BY_AGENT.get(agent_name)
        relevant_outputs = self._select_relevant_outputs(artifacts, focus.relevant_prefixes if focus else ())
        remembered = "\n".join(f"- {item}" for item in long_term_memory or []) or "No long-term memory retrieved."
        return {
            "user_requirement": user_requirement,
            "current_task": current_task or (focus.current_task if focus else ""),
            "agent_role": agent_role,
            "relevant_outputs": relevant_outputs,
            "constraints": constraints,
            "errors_or_feedback": errors_or_feedback or "None",
            "retrieved_long_term_memory": remembered,
        }

    def _select_relevant_outputs(self, artifacts: dict[str, str], prefixes: tuple[str, ...]) -> str:
        if not artifacts:
            return "No artifacts generated yet."

        selected: list[str] = []
        for path, content in sorted(artifacts.items()):
            if prefixes and not path.startswith(prefixes):
                continue
            selected.append(f"## {path}\n{content[:MAX_OUTPUT_CHARS]}")

        if not selected:
            selected = [f"- {path}" for path in sorted(artifacts)]
        return "\n\n".join(selected)[:MAX_OUTPUT_CHARS]

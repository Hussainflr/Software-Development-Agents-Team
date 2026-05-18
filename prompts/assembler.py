from __future__ import annotations

from dataclasses import dataclass, field

from skills.registry import render_skill_registry


@dataclass(frozen=True)
class PromptAssemblyInput:
    agent_name: str
    agent_role: str
    task: str
    user_goal: str
    selected_skills: list[str] = field(default_factory=list)
    memory: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    context: dict[str, object] = field(default_factory=dict)


class PromptAssembler:
    """Composable prompt builder for Agentic OS agents."""

    def assemble(self, data: PromptAssemblyInput) -> str:
        sections = [
            "# Agent Role",
            f"{data.agent_name}: {data.agent_role}",
            "# User Goal",
            data.user_goal.strip(),
            "# Task",
            data.task.strip(),
            "# Available Tools",
            "\n".join(f"- {tool}" for tool in data.tools) or "- No tools granted",
            "# Guardrails",
            "\n".join(f"- {rule}" for rule in data.guardrails) or "- Follow project safety policy",
            "# Relevant Memory",
            "\n".join(f"- {item}" for item in data.memory) or "- No retrieved memory",
            "# Skills",
            render_skill_registry(data.selected_skills) if data.selected_skills else "No skills selected",
        ]
        if data.context:
            sections.extend(
                [
                    "# Runtime Context",
                    "\n".join(f"- {key}: {value}" for key, value in data.context.items()),
                ]
            )
        return "\n\n".join(sections).strip()

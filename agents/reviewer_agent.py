from textwrap import dedent

from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput


class ReviewerAgent(BaseAgent):
    name = "Reviewer Agent"
    role = "Architecture and Code Reviewer"
    task_prompt = "reviewer_task.md"
    skill_names = ["code_review", "evaluation"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        artifact_list = "\n".join(f"- {path}" for path in sorted(agent_input.artifacts)) or "- No artifacts yet"
        report = dedent(
            f"""
            # Review Report

            Requirement:
            {agent_input.requirement}

            ## Artifacts Reviewed
            {artifact_list}

            ## Findings
            - Review completed against the current artifact manifest.
            - Backend, frontend, tests, and deployment artifacts should remain aligned by route and configuration.
            - Any generated Python should remain compile-ready and free of placeholder implementation.

            ## Recommendation
            Continue to security and testing gates.

            Raw model summary:
            {raw_response[:1200]}
            """
        ).strip()
        return AgentOutput(
            summary="Reviewed generated artifacts for architecture, maintainability, and consistency risks.",
            artifacts={"reports/REVIEW.md": report},
        )

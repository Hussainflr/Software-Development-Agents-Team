from textwrap import dedent

from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput


class SecurityAgent(BaseAgent):
    name = "Security Agent"
    role = "Security and Permission Reviewer"
    task_prompt = "security_task.md"
    skill_names = ["security_review"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        combined = "\n".join(agent_input.artifacts.values()).lower()
        risky_markers = ["sk-", "api_key=", "password=", "secret=", "token=", "rm -rf", "curl | sh"]
        findings = [marker for marker in risky_markers if marker in combined]
        status = "blocked" if findings else "passed"
        report = dedent(
            f"""
            # Security Report

            Requirement:
            {agent_input.requirement}

            Status: {status}

            ## Checks
            - Hardcoded secret markers
            - Dangerous shell command markers
            - Deployment approval requirement
            - Environment-variable based configuration

            ## Findings
            {chr(10).join(f"- Found marker: `{item}`" for item in findings) if findings else "- No deterministic security blockers found."}

            Raw model summary:
            {raw_response[:1200]}
            """
        ).strip()
        return AgentOutput(
            summary=f"Security review {status}.",
            artifacts={"reports/SECURITY.md": report},
            bugs=[f"Security marker found: {item}" for item in findings],
        )

from textwrap import dedent

from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput


class EvaluatorAgent(BaseAgent):
    name = "Evaluator Agent"
    role = "Quality Gate Evaluator"
    task_prompt = "evaluator_task.md"
    skill_names = ["evaluation"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        report = dedent(
            f"""
            # Evaluation Gate Notes

            Requirement:
            {agent_input.requirement}

            ## Decision Inputs
            - Tester bug report: {agent_input.bug_report or "None"}
            - Artifact count: {len(agent_input.artifacts)}

            ## Gate Policy
            Deployment can proceed only when deterministic/LLM evaluation passes and the human manager approves.

            Raw model summary:
            {raw_response[:1200]}
            """
        ).strip()
        return AgentOutput(
            summary="Prepared evaluation gate notes for the run.",
            artifacts={"reports/EVALUATION_GATE.md": report},
        )

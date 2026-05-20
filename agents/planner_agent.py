from textwrap import dedent

from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput


class PlannerAgent(BaseAgent):
    name = "Planner Agent"
    role = "Software Delivery Planner"
    task_prompt = "planner_task.md"
    skill_names = ["planning"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        plan = dedent(
            f"""
            # Execution Plan

            Requirement:
            {agent_input.requirement}

            ## Delivery Sequence
            1. Backend Agent designs and implements the API/domain behavior.
            2. Frontend Agent builds the Streamlit user interface and connects it to backend APIs.
            3. Reviewer Agent checks artifact consistency and maintainability.
            4. Security Agent checks secrets, unsafe actions, and deployment risk.
            5. Tester Agent writes and validates generated tests.
            6. Evaluator Agent decides whether to approve, refine, or block deployment.
            7. Deployment Agent prepares local and Docker deployment artifacts after human approval.

            ## Acceptance Criteria
            - Generated backend, frontend, tests, and deployment files match the requirement.
            - Backend routes match frontend calls and test calls.
            - Python artifacts compile and generated tests are executable where possible.
            - No secrets or unsafe commands are hardcoded.
            - Deployment waits for human approval.

            Raw model summary:
            {raw_response[:1200]}
            """
        ).strip()
        return AgentOutput(
            summary="Prepared an execution plan, acceptance criteria, and approval checkpoints.",
            artifacts={"reports/PLAN.md": plan},
            notes=["Planner fallback is deterministic so local runs can proceed when the LLM output is invalid."],
        )

from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput
from skills.fallback_artifacts import frontend_fallback


class FrontendAgent(BaseAgent):
    name = "Frontend Agent"
    role = "Frontend Engineer"
    task_prompt = "frontend_task.md"
    skill_names = ["code_generation"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        return frontend_fallback(raw_response)

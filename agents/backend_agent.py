from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput
from skills.fallback_artifacts import backend_fallback


class BackendAgent(BaseAgent):
    name = "Backend Agent"
    role = "Backend Architect"
    task_prompt = "backend_task.md"
    skill_names = ["code_generation"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        return backend_fallback(agent_input.requirement, raw_response)

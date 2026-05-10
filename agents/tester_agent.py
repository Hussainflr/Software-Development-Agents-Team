from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput
from skills.fallback_artifacts import tester_fallback


class TesterAgent(BaseAgent):
    name = "Tester Agent"
    role = "QA Engineer"
    task_prompt = "tester_task.md"
    skill_names = ["test_generation", "code_review"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        return tester_fallback(raw_response)

from agents.base import BaseAgent
from agents.schemas import AgentInput, AgentOutput
from skills.fallback_artifacts import deployment_fallback


class DeploymentAgent(BaseAgent):
    name = "Deployment Agent"
    role = "DevOps Engineer"
    task_prompt = "deployment_task.txt"
    skill_names = ["dockerfile_generation"]

    def fallback_output(self, agent_input: AgentInput, raw_response: str) -> AgentOutput:
        return deployment_fallback(raw_response)

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from agents.backend_agent import BackendAgent
from agents.schemas import AgentInput


def test_agent_invokes_langchain_runnable_chain():
    model = FakeListChatModel(
        responses=[
            '{"summary":"ok","artifacts":{"generated_backend/main.py":"print(1)"},"notes":[],"bugs":[]}'
        ]
    )
    agent_input = AgentInput(
        run_id=1,
        requirement="Build a small API",
        focused_context={
            "user_requirement": "Build a small API",
            "current_task": "backend",
            "agent_role": "Backend Architect",
            "relevant_outputs": "No artifacts generated yet.",
            "constraints": "No secrets",
            "errors_or_feedback": "None",
        },
    )

    result = BackendAgent().invoke(agent_input, model)

    assert result.summary == "ok"
    assert result.artifacts == {"generated_backend/main.py": "print(1)"}

from context.context_builder import ContextBuilder


def test_context_builder_filters_relevant_outputs():
    context = ContextBuilder().build(
        user_requirement="Build a task tracker",
        current_task="frontend",
        agent_name="Frontend Agent",
        agent_role="Frontend Engineer",
        artifacts={
            "generated_backend/main.py": "backend code",
            "deployment/Dockerfile": "docker",
        },
        constraints="No secrets",
    )

    assert "generated_backend/main.py" in context["relevant_outputs"]
    assert "deployment/Dockerfile" not in context["relevant_outputs"]

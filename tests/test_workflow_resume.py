from types import SimpleNamespace

from workflows.software_team_graph import SoftwareTeamWorkflow


def _workflow_with_recorded_nodes():
    workflow = SoftwareTeamWorkflow.__new__(SoftwareTeamWorkflow)
    calls = []

    def node(stage: str):
        def run(state):
            calls.append(stage)
            return {**state, "last_stage": stage}

        return run

    workflow._planner_node = node("planning")
    workflow._backend_node = node("backend")
    workflow._frontend_node = node("frontend")
    workflow._reviewer_node = node("review")
    workflow._security_node = node("security")
    workflow._tester_node = node("testing")
    workflow._evaluator_node = node("evaluation")
    workflow._backend_revision_node = node("backend_revision")
    workflow._frontend_revision_node = node("frontend_revision")
    workflow._route_after_testing = lambda state: "approval"
    return workflow, calls


def test_resume_sequence_starts_from_saved_stage():
    workflow, calls = _workflow_with_recorded_nodes()

    workflow._run_initial_sequence_from_stage({"run_id": 1}, "review")

    assert calls == ["review", "security", "testing", "evaluation"]


def test_resume_sequence_continues_revision_pair():
    workflow, calls = _workflow_with_recorded_nodes()

    workflow._run_initial_sequence_from_stage({"run_id": 1}, "backend_revision")

    assert calls == [
        "backend_revision",
        "frontend_revision",
        "review",
        "security",
        "testing",
        "evaluation",
    ]


class StatusRepository:
    def __init__(self, statuses):
        self.statuses = statuses

    def list_agent_statuses(self, run_id: int):
        return self.statuses


def status(agent_name: str, value: str):
    return SimpleNamespace(agent_name=agent_name, status=value)


def test_resume_stage_uses_failed_agent_when_saved_stage_is_stale():
    workflow = SoftwareTeamWorkflow.__new__(SoftwareTeamWorkflow)
    workflow.repository = StatusRepository(
        [
            status("Planner Agent", "completed"),
            status("Backend Agent", "completed"),
            status("Frontend Agent", "failed"),
        ]
    )
    run = SimpleNamespace(id=1, current_stage="planning")

    assert workflow._resolve_resume_stage(run) == "frontend"


def test_resume_stage_uses_next_incomplete_stage_for_old_stopped_rows():
    workflow = SoftwareTeamWorkflow.__new__(SoftwareTeamWorkflow)
    workflow.repository = StatusRepository(
        [
            status("Planner Agent", "completed"),
            status("Backend Agent", "completed"),
            status("Frontend Agent", "idle"),
        ]
    )
    run = SimpleNamespace(id=1, current_stage="stopped")

    assert workflow._resolve_resume_stage(run) == "frontend"

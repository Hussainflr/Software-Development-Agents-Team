from workflows.software_team_graph import SoftwareTeamWorkflow
from app.core.control_loop import ControlLoopPolicy


class FakeRepository:
    def __init__(self):
        self.updated = []
        self.logs = []

    def update_run(self, run_id: int, **fields):
        self.updated.append((run_id, fields))

    def add_log(self, run_id: int, agent_name: str, action: str, output_summary: str, status: str = "info"):
        self.logs.append(
            {
                "run_id": run_id,
                "agent_name": agent_name,
                "action": action,
                "output_summary": output_summary,
                "status": status,
            }
        )


def test_workflow_blocks_approval_after_final_failed_evaluation():
    workflow = SoftwareTeamWorkflow.__new__(SoftwareTeamWorkflow)
    workflow.repository = FakeRepository()
    workflow.control_policy = ControlLoopPolicy(max_refinements=2)
    workflow._record_trace = lambda *_args, **_kwargs: None

    route = workflow._route_after_testing(
        {
            "run_id": 23,
            "bugs_found": False,
            "evaluation_passed": False,
            "revision_count": 2,
        }
    )

    assert route == "end"
    assert workflow.repository.updated[-1][1]["status"] == "failed"
    assert workflow.repository.logs[-1]["action"] == "Deployment blocked"


def test_workflow_allows_second_revision_pass():
    workflow = SoftwareTeamWorkflow.__new__(SoftwareTeamWorkflow)
    workflow.repository = FakeRepository()
    workflow.control_policy = ControlLoopPolicy(max_refinements=2)
    workflow._record_trace = lambda *_args, **_kwargs: None

    route = workflow._route_after_testing(
        {
            "run_id": 24,
            "bugs_found": True,
            "evaluation_passed": False,
            "revision_count": 1,
            "control_loop": {},
            "requirement": "Build a task tracker",
        }
    )

    assert route == "revise"
    assert workflow.repository.logs[-1]["action"] == "Feedback loop 2/2"

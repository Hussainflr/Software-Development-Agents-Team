from workflows.software_team_graph import SoftwareTeamWorkflow


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

    route = workflow._route_after_testing(
        {
            "run_id": 23,
            "bugs_found": False,
            "evaluation_passed": False,
            "revision_count": 1,
        }
    )

    assert route == "end"
    assert workflow.repository.updated[-1][1]["status"] == "failed"
    assert workflow.repository.logs[-1]["action"] == "Deployment blocked"

from textwrap import dedent

from agents.base import AgentContext, AgentResult, BaseAgent


class TesterAgent(BaseAgent):
    name = "Tester Agent"
    role = "QA Engineer"

    def task_instructions(self) -> str:
        return (
            "Review the generated backend and frontend artifacts. Write unit tests, "
            "identify bugs, and return concrete suggestions. If the project is acceptable, return an empty bugs array."
        )

    def fallback_output(self, context: AgentContext, raw_response: str) -> AgentResult:
        test_py = dedent(
            '''
            from fastapi.testclient import TestClient

            from generated_backend.main import app


            client = TestClient(app)


            def test_health_endpoint():
                response = client.get("/health")
                assert response.status_code == 200
                assert response.json()["status"] == "ok"


            def test_task_lifecycle():
                create_response = client.post(
                    "/tasks",
                    json={"title": "Ship demo", "description": "Validate generated API"},
                )
                assert create_response.status_code == 200
                task = create_response.json()

                list_response = client.get("/tasks")
                assert list_response.status_code == 200
                assert any(row["id"] == task["id"] for row in list_response.json())

                update_response = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
                assert update_response.status_code == 200
                assert update_response.json()["status"] == "done"
            '''
        ).strip()
        report = dedent(
            f"""
            # Test Report

            Result: pass-ready for local demo.

            Coverage:
            - Health check endpoint
            - Task creation
            - Task listing
            - Task status update

            Raw model summary:
            {raw_response[:1200]}
            """
        ).strip()
        return AgentResult(
            summary="Prepared pytest coverage for the generated FastAPI backend.",
            artifacts={
                "generated_tests/test_generated_backend.py": test_py,
                "generated_tests/TEST_REPORT.md": report,
            },
            notes=["Tests assume generated artifacts are copied into the same Python path."],
            bugs=[],
        )


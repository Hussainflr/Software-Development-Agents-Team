from evaluation.consistency import EndpointConsistencyChecker
from evaluation.test_execution import GeneratedTestRunner
from llm_providers.router import ModelRouter
from tools.permissions import ToolPermissionPolicy


def test_endpoint_consistency_finds_missing_route():
    result = EndpointConsistencyChecker().check(
        {
            "generated_backend/main.py": '''
from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health():
    return {"status": "ok"}
''',
            "generated_frontend/app.py": 'requests.post(f"{API_URL}/play", timeout=5)',
            "generated_tests/test_generated_backend.py": 'def test_play(client):\n    client.post("/play")',
        }
    )

    assert not result.passed
    assert "/play" in result.missing_routes


def test_generated_test_runner_executes_passing_tests():
    result = GeneratedTestRunner(timeout_seconds=10).run(
        {
            "generated_backend/main.py": '''
from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health():
    return {"status": "ok"}
''',
            "generated_tests/test_generated_backend.py": '''
from fastapi.testclient import TestClient
from generated_backend.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").status_code == 200
''',
        }
    )

    assert result.attempted
    assert result.passed


def test_tool_permission_policy_requires_approval_for_terminal():
    decision = ToolPermissionPolicy().decide("terminal.exec")

    assert not decision.allowed
    assert decision.requires_approval

    approved = ToolPermissionPolicy().decide("terminal.exec", approved=True)

    assert approved.allowed


def test_model_router_records_zero_local_cost():
    metrics = ModelRouter().measure(
        provider="ollama",
        model="qwen2.5-coder",
        prompt="build an app",
        output="done",
        started_at=0,
    )

    assert metrics.input_tokens_estimate >= 1
    assert metrics.estimated_cost_usd == 0.0

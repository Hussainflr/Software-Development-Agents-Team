from langchain_core.language_models.fake_chat_models import FakeListChatModel

from evaluation.scorer import EvaluationScorer


COMPLETE_ARTIFACTS = {
    "generated_backend/main.py": """
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    title: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tasks")
def create_task(task: Task):
    return {"id": "1", "title": task.title}
""",
    "generated_backend/README.md": "Run with uvicorn generated_backend.main:app --port 9000",
    "generated_frontend/app.py": """
import os
import requests
import streamlit as st

API_URL = os.getenv("GENERATED_API_URL", "http://localhost:9000")
st.title("Tasks")
response = requests.get(f"{API_URL}/health", timeout=5)
st.write(response.json())
""",
    "generated_frontend/README.md": "Run with streamlit run generated_frontend/app.py",
    "generated_tests/test_generated_backend.py": """
from fastapi.testclient import TestClient
from generated_backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
""",
    "generated_tests/TEST_REPORT.md": "Health endpoint and task creation are covered.",
}


def test_evaluation_passes_complete_bug_free_artifacts():
    score = EvaluationScorer().score(COMPLETE_ARTIFACTS, bugs=[])

    assert score.passed is True


def test_evaluation_fails_when_bugs_exist():
    score = EvaluationScorer().score({"generated_backend/main.py": "backend"}, bugs=["Missing frontend"])

    assert score.passed is False


def test_llm_judge_can_fail_hybrid_evaluation():
    judge = FakeListChatModel(
        responses=[
            '{"correctness": 5, "completeness": 5, "code_quality": 5, '
            '"passed": false, "summary": "Not enough game behavior.", '
            '"findings": ["Frontend does not implement the requested interaction."]}'
        ]
    )

    score = EvaluationScorer().score(COMPLETE_ARTIFACTS, bugs=[], requirement="Build a game", llm_judge=judge)

    assert score.passed is False
    assert score.correctness == 5
    assert "LLM judge" in score.summary


def test_llm_judge_failure_falls_back_to_deterministic_score():
    judge = FakeListChatModel(responses=["not json"])

    score = EvaluationScorer().score(COMPLETE_ARTIFACTS, bugs=[], requirement="Build a task tracker", llm_judge=judge)

    assert score.passed is True
    assert "LLM judge unavailable" in score.summary

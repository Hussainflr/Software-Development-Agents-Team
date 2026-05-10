import pytest
from fastapi import HTTPException

from backend.app import main as api
from backend.app.schemas import RunCreate
from guardrails import validate_requirement


def test_greeting_is_not_actionable_software_requirement():
    result = validate_requirement("hello")

    assert result.allowed is False
    assert result.category == "small_talk"


def test_valid_software_requirement_is_allowed():
    result = validate_requirement(
        "Build a FastAPI task tracker with a Streamlit dashboard, SQLite storage, tests, and Docker setup."
    )

    assert result.allowed is True


def test_create_run_rejects_small_talk_before_provider_resolution(monkeypatch):
    monkeypatch.setattr(api, "resolve_model", lambda *_args, **_kwargs: pytest.fail("provider resolution should not run"))

    with pytest.raises(HTTPException) as exc_info:
        api.create_run(RunCreate(requirement="hello", provider="ollama", model="auto"))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["category"] == "small_talk"

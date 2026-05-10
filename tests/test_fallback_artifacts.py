from skills.fallback_artifacts import backend_fallback, frontend_fallback, tester_fallback as build_tester_fallback


RPS_REQUIREMENT = "Build a Rock Paper Scissors game with FastAPI /play, Streamlit buttons, and tests."


def test_rock_paper_scissors_backend_fallback_matches_requirement():
    output = backend_fallback(RPS_REQUIREMENT, "invalid model output")
    backend = output.artifacts["generated_backend/main.py"]

    assert '"/play"' in backend
    assert "rock" in backend
    assert "paper" in backend
    assert "scissors" in backend
    compile(backend, "generated_backend/main.py", "exec")


def test_rock_paper_scissors_frontend_fallback_matches_requirement():
    output = frontend_fallback(RPS_REQUIREMENT, "invalid model output")
    frontend = output.artifacts["generated_frontend/app.py"]

    assert "/play" in frontend
    assert "rock" in frontend
    assert "paper" in frontend
    assert "scissors" in frontend
    assert "/tasks" not in frontend


def test_rock_paper_scissors_tester_fallback_matches_requirement():
    output = build_tester_fallback(RPS_REQUIREMENT, "invalid model output")
    tests = output.artifacts["generated_tests/test_generated_backend.py"]

    assert "/play" in tests
    assert "/tasks" not in tests
    compile(tests, "generated_tests/test_generated_backend.py", "exec")

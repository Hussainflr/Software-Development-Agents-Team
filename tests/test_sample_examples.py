from pathlib import Path


def test_rock_paper_scissors_prompt_sample_is_actionable():
    prompt = Path("samples/rock_paper_scissors_prompt.md").read_text(encoding="utf-8").lower()

    assert "rock paper scissors" in prompt
    assert "fastapi backend" in prompt
    assert "streamlit frontend" in prompt
    assert "tester writes api tests" in prompt


def test_rock_paper_scissors_backend_test_example_targets_play_endpoint():
    sample = Path("samples/rock_paper_scissors_backend_test.py").read_text(encoding="utf-8")

    assert 'client.post("/play"' in sample
    assert 'json={"move": "rock"}' in sample
    assert '"/tasks"' not in sample
    compile(sample, "samples/rock_paper_scissors_backend_test.py", "exec")

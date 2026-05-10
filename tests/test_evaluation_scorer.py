from evaluation.scorer import EvaluationScorer


def test_evaluation_passes_complete_bug_free_artifacts():
    score = EvaluationScorer().score(
        {
            "generated_backend/main.py": "backend",
            "generated_frontend/app.py": "frontend",
            "generated_tests/test_app.py": "tests",
        },
        bugs=[],
    )

    assert score.passed is True


def test_evaluation_fails_when_bugs_exist():
    score = EvaluationScorer().score({"generated_backend/main.py": "backend"}, bugs=["Missing frontend"])

    assert score.passed is False

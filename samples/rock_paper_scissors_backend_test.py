from fastapi.testclient import TestClient

from generated_backend.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_play_round_accepts_valid_move():
    response = client.post("/play", json={"move": "rock"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["player_move"] == "rock"
    assert payload["computer_move"] in {"rock", "paper", "scissors"}
    assert payload["winner"] in {"player", "computer", "tie"}


def test_play_round_rejects_invalid_move():
    response = client.post("/play", json={"move": "lizard"})

    assert response.status_code == 422


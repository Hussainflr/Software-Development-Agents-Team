from agents.base import parse_agent_json


def test_parse_agent_json_with_surrounding_text():
    result = parse_agent_json(
        'Here is the JSON: {"summary": "done", "artifacts": {"a.py": "print(1)"}, "notes": "ok", "bugs": []}'
    )

    assert result.summary == "done"
    assert result.artifacts == {"a.py": "print(1)"}
    assert result.notes == ["ok"]
    assert result.bugs == []


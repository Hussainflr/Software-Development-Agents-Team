from skills.registry import render_skill_registry


def test_skill_registry_loads_markdown_skill_files():
    rendered = render_skill_registry(["code_generation", "code_review"])

    assert "# Code Generation" in rendered
    assert "# Code Review" in rendered
    assert "Return full file contents" in rendered


from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    description: str


SKILLS = {
    "code_generation": SkillDefinition(
        name="code_generation",
        description="Generate complete, runnable application code artifacts.",
    ),
    "test_generation": SkillDefinition(
        name="test_generation",
        description="Generate focused tests and concise test reports.",
    ),
    "code_review": SkillDefinition(
        name="code_review",
        description="Review artifacts for bugs, missing behavior, and maintainability risks.",
    ),
    "dockerfile_generation": SkillDefinition(
        name="dockerfile_generation",
        description="Generate Dockerfile, Compose, and local run instructions.",
    ),
}


def render_skill_registry(skill_names: list[str]) -> str:
    rows = []
    for name in skill_names:
        skill = SKILLS[name]
        rows.append(f"- {skill.name}: {skill.description}")
    return "\n".join(rows)

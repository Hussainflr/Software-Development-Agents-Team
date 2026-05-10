from dataclasses import dataclass
from pathlib import Path


SKILLS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    file_name: str

    @property
    def content(self) -> str:
        return (SKILLS_DIR / self.file_name).read_text(encoding="utf-8").strip()


SKILLS = {
    "code_generation": SkillDefinition(
        name="code_generation",
        file_name="code_generation.md",
    ),
    "test_generation": SkillDefinition(
        name="test_generation",
        file_name="test_generation.md",
    ),
    "code_review": SkillDefinition(
        name="code_review",
        file_name="code_review.md",
    ),
    "dockerfile_generation": SkillDefinition(
        name="dockerfile_generation",
        file_name="dockerfile_generation.md",
    ),
}


def render_skill_registry(skill_names: list[str]) -> str:
    rows = []
    for name in skill_names:
        skill = SKILLS[name]
        rows.append(f"## {skill.name}\n{skill.content}")
    return "\n\n".join(rows)

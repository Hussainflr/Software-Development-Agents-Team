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
    "planning": SkillDefinition(
        name="planning",
        file_name="planning.md",
    ),
    "code_generation": SkillDefinition(
        name="code_generation",
        file_name="code_generation.md",
    ),
    "debugging": SkillDefinition(
        name="debugging",
        file_name="debugging.md",
    ),
    "testing": SkillDefinition(
        name="testing",
        file_name="testing.md",
    ),
    "evaluation": SkillDefinition(
        name="evaluation",
        file_name="evaluation.md",
    ),
    "deployment": SkillDefinition(
        name="deployment",
        file_name="deployment.md",
    ),
    "rag": SkillDefinition(
        name="rag",
        file_name="rag.md",
    ),
    "research": SkillDefinition(
        name="research",
        file_name="research.md",
    ),
    "security_review": SkillDefinition(
        name="security_review",
        file_name="security_review.md",
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

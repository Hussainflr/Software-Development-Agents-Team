from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class RequirementGuardrailResult:
    allowed: bool
    category: str
    reason: str
    guidance: str

    def model_dump(self) -> dict[str, str | bool]:
        return asdict(self)


GREETINGS = {
    "hello",
    "hi",
    "hey",
    "yo",
    "salam",
    "assalamualaikum",
    "thanks",
    "thank",
    "ok",
    "okay",
}

BUILD_ACTIONS = {
    "add",
    "build",
    "create",
    "debug",
    "deploy",
    "design",
    "develop",
    "fix",
    "generate",
    "implement",
    "make",
    "refactor",
    "scaffold",
    "setup",
    "test",
    "update",
    "write",
}

SOFTWARE_TERMS = {
    "agent",
    "api",
    "app",
    "application",
    "auth",
    "automation",
    "backend",
    "bot",
    "cli",
    "component",
    "crud",
    "dashboard",
    "database",
    "docker",
    "endpoint",
    "fastapi",
    "frontend",
    "game",
    "integration",
    "login",
    "page",
    "react",
    "service",
    "sqlite",
    "streamlit",
    "test",
    "tool",
    "ui",
    "website",
    "workflow",
}

SOFTWARE_PHRASES = (
    "user interface",
    "web app",
    "rest api",
    "unit test",
    "docker compose",
    "data model",
)


def validate_requirement(requirement: str) -> RequirementGuardrailResult:
    """Decide whether a manager input is actionable enough to start the team."""

    cleaned = " ".join((requirement or "").strip().split())
    normalized = cleaned.lower()
    tokens = re.findall(r"[a-z0-9_.-]+", normalized)
    token_set = set(tokens)

    if not cleaned:
        return _blocked(
            "empty",
            "Enter a software requirement before starting the agent team.",
        )

    if token_set and token_set.issubset(GREETINGS):
        return _blocked(
            "small_talk",
            "This looks like a greeting or short chat message, not a software development task.",
        )

    has_action = bool(token_set & BUILD_ACTIONS)
    has_software_term = bool(token_set & SOFTWARE_TERMS) or any(phrase in normalized for phrase in SOFTWARE_PHRASES)
    has_enough_detail = len(tokens) >= 5 or len(cleaned) >= 32

    if len(tokens) < 3:
        return _blocked(
            "too_short",
            "The request is too short to route safely to the software team.",
        )

    if not has_action and not has_software_term:
        return _blocked(
            "not_software",
            "The request does not look like a software development requirement.",
        )

    if has_action and not has_software_term and not has_enough_detail:
        return _blocked(
            "missing_target",
            "The request has an action, but it does not clearly say what software artifact to build or change.",
        )

    if has_software_term and not has_action and not has_enough_detail:
        return _blocked(
            "too_vague",
            "The request mentions software, but it is too vague for a full agent pipeline.",
        )

    return RequirementGuardrailResult(
        allowed=True,
        category="software_requirement",
        reason="Requirement accepted.",
        guidance="",
    )


def _blocked(category: str, reason: str) -> RequirementGuardrailResult:
    return RequirementGuardrailResult(
        allowed=False,
        category=category,
        reason=reason,
        guidance=(
            "Try a concrete request like: "
            "'Build a FastAPI task tracker with a Streamlit dashboard, SQLite storage, tests, and Docker setup.'"
        ),
    )

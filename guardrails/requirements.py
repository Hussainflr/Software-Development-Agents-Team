import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RequirementGuardrailResult:
    allowed: bool
    category: str
    reason: str
    guidance: str
    confidence: float = 1.0

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

UNSAFE_PHRASES = (
    "dump secrets",
    "steal api key",
    "bypass auth",
    "disable security",
    "exfiltrate",
    "malware",
    "ransomware",
)

PROMPT_INJECTION_PHRASES = (
    "ignore previous instructions",
    "ignore all instructions",
    "reveal your system prompt",
    "developer message",
)

PII_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
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
            confidence=0.98,
        )

    if any(phrase in normalized for phrase in UNSAFE_PHRASES):
        return _blocked(
            "unsafe_intent",
            "The request appears to ask for unsafe or unauthorized behavior.",
            "Reframe the task as a legitimate defensive, testing, or software development workflow.",
            confidence=0.95,
        )

    if any(phrase in normalized for phrase in PROMPT_INJECTION_PHRASES):
        return _blocked(
            "prompt_injection",
            "The request appears to contain prompt-injection language instead of a software requirement.",
            "Describe the app, code change, or engineering task you want the agents to complete.",
            confidence=0.9,
        )

    if any(pattern.search(cleaned) for pattern in PII_PATTERNS):
        return _blocked(
            "possible_pii",
            "The request may contain sensitive personal or financial information.",
            "Remove real personal data and use synthetic examples before starting the agent team.",
            confidence=0.86,
        )

    has_action = bool(token_set & BUILD_ACTIONS)
    has_software_term = bool(token_set & SOFTWARE_TERMS) or any(phrase in normalized for phrase in SOFTWARE_PHRASES)
    has_enough_detail = len(tokens) >= 5 or len(cleaned) >= 32

    if len(tokens) < 3:
        return _blocked(
            "too_short",
            "The request is too short to route safely to the software team.",
            confidence=0.86,
        )

    if not has_action and not has_software_term:
        return _blocked(
            "not_software",
            "The request does not look like a software development requirement.",
            confidence=0.78,
        )

    if has_action and not has_software_term and not has_enough_detail:
        return _blocked(
            "missing_target",
            "The request has an action, but it does not clearly say what software artifact to build or change.",
            confidence=0.82,
        )

    if has_software_term and not has_action and not has_enough_detail:
        return _blocked(
            "too_vague",
            "The request mentions software, but it is too vague for a full agent pipeline.",
            confidence=0.82,
        )

    return RequirementGuardrailResult(
        allowed=True,
        category="software_requirement",
        reason="Requirement accepted.",
        guidance="",
        confidence=0.88,
    )


def classify_requirement(requirement: str) -> RequirementGuardrailResult:
    """Alias used by Agentic OS APIs and future planner nodes."""

    return validate_requirement(requirement)


def _blocked(
    category: str,
    reason: str,
    guidance: str | None = None,
    confidence: float = 0.9,
) -> RequirementGuardrailResult:
    return RequirementGuardrailResult(
        allowed=False,
        category=category,
        reason=reason,
        guidance=guidance or (
            "Try a concrete request like: "
            "'Build a FastAPI task tracker with a Streamlit dashboard, SQLite storage, tests, and Docker setup.'"
        ),
        confidence=confidence,
    )

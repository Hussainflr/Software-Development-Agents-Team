from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentDefinition:
    """Declarative contract for Agentic OS agents."""

    key: str
    name: str
    role: str
    responsibilities: tuple[str, ...]
    default_skills: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    implemented: bool = False
    parallel_safe: bool = False


AGENT_CATALOG: dict[str, AgentDefinition] = {
    "planner": AgentDefinition(
        key="planner",
        name="Planner Agent",
        role="Breaks a user goal into an executable plan.",
        responsibilities=("intent classification", "task decomposition", "workflow routing"),
        default_skills=("planning",),
        allowed_tools=("memory.search",),
    ),
    "research": AgentDefinition(
        key="research",
        name="Research Agent",
        role="Collects project, repository, and documentation context.",
        responsibilities=("repo inspection", "documentation lookup", "source synthesis"),
        default_skills=("research", "rag"),
        allowed_tools=("filesystem.read", "web.search", "memory.search"),
        parallel_safe=True,
    ),
    "coder": AgentDefinition(
        key="coder",
        name="Coder Agent",
        role="Produces implementation changes across shared code.",
        responsibilities=("code generation", "refactoring", "integration"),
        default_skills=("code_generation",),
        allowed_tools=("filesystem.read", "filesystem.write", "python.exec"),
    ),
    "frontend": AgentDefinition(
        key="frontend",
        name="Frontend Agent",
        role="Builds UI and API integrations.",
        responsibilities=("UI generation", "component composition", "API wiring"),
        default_skills=("code_generation",),
        allowed_tools=("filesystem.read", "filesystem.write"),
        implemented=True,
        parallel_safe=True,
    ),
    "backend": AgentDefinition(
        key="backend",
        name="Backend Agent",
        role="Builds APIs, domain logic, and persistence boundaries.",
        responsibilities=("API design", "database schema", "service implementation"),
        default_skills=("code_generation",),
        allowed_tools=("filesystem.read", "filesystem.write"),
        implemented=True,
        parallel_safe=True,
    ),
    "debugger": AgentDefinition(
        key="debugger",
        name="Debugger Agent",
        role="Diagnoses runtime failures and proposes focused repairs.",
        responsibilities=("trace analysis", "root cause analysis", "repair planning"),
        default_skills=("debugging",),
        allowed_tools=("terminal.exec", "python.exec", "filesystem.read"),
    ),
    "tester": AgentDefinition(
        key="tester",
        name="Tester Agent",
        role="Creates tests and validates generated systems.",
        responsibilities=("unit tests", "integration tests", "test reporting"),
        default_skills=("testing", "code_review"),
        allowed_tools=("python.exec", "terminal.exec", "filesystem.read", "filesystem.write"),
        implemented=True,
        parallel_safe=True,
    ),
    "reviewer": AgentDefinition(
        key="reviewer",
        name="Reviewer Agent",
        role="Reviews maintainability, architecture, and delivery risk.",
        responsibilities=("code review", "architecture review", "risk assessment"),
        default_skills=("code_review", "evaluation"),
        allowed_tools=("filesystem.read",),
        parallel_safe=True,
    ),
    "security": AgentDefinition(
        key="security",
        name="Security Agent",
        role="Finds secrets, unsafe code paths, and permission risks.",
        responsibilities=("secret scanning", "security review", "unsafe action detection"),
        default_skills=("security_review",),
        allowed_tools=("filesystem.read", "terminal.exec"),
        parallel_safe=True,
    ),
    "deployment": AgentDefinition(
        key="deployment",
        name="Deployment Agent",
        role="Prepares local and container deployment artifacts.",
        responsibilities=("Dockerfiles", "compose files", "startup validation"),
        default_skills=("deployment", "dockerfile_generation"),
        allowed_tools=("filesystem.read", "filesystem.write", "docker.inspect"),
        implemented=True,
    ),
    "evaluator": AgentDefinition(
        key="evaluator",
        name="Evaluator Agent",
        role="Scores outputs and drives repair loops.",
        responsibilities=("requirement alignment", "quality scoring", "repair decisioning"),
        default_skills=("evaluation",),
        allowed_tools=("filesystem.read", "python.exec"),
    ),
    "memory": AgentDefinition(
        key="memory",
        name="Memory Agent",
        role="Stores and retrieves goals, decisions, traces, and artifacts.",
        responsibilities=("memory write policy", "memory retrieval", "summarization"),
        default_skills=("rag",),
        allowed_tools=("memory.search", "memory.write"),
        parallel_safe=True,
    ),
}


def list_agent_definitions() -> list[AgentDefinition]:
    return list(AGENT_CATALOG.values())


def implemented_agent_names() -> list[str]:
    return [agent.name for agent in AGENT_CATALOG.values() if agent.implemented]

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ToolRisk(str, Enum):
    READ = "read"
    WRITE = "write"
    NETWORK = "network"
    DESTRUCTIVE = "destructive"
    EXTERNAL = "external"


@dataclass(frozen=True)
class ToolDefinition:
    """Permissioned tool contract used by agents and future MCP adapters."""

    name: str
    description: str
    risk: ToolRisk
    requires_approval: bool = False
    timeout_seconds: int = 60
    mcp_compatible: bool = True


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "filesystem.read": ToolDefinition("filesystem.read", "Read project files.", ToolRisk.READ),
    "filesystem.write": ToolDefinition("filesystem.write", "Write generated artifacts.", ToolRisk.WRITE),
    "terminal.exec": ToolDefinition(
        "terminal.exec",
        "Run bounded shell commands for tests and diagnostics.",
        ToolRisk.WRITE,
        requires_approval=True,
        timeout_seconds=120,
    ),
    "python.exec": ToolDefinition(
        "python.exec",
        "Execute isolated Python checks.",
        ToolRisk.WRITE,
        requires_approval=True,
        timeout_seconds=120,
    ),
    "git.inspect": ToolDefinition("git.inspect", "Inspect git state and diffs.", ToolRisk.READ),
    "docker.inspect": ToolDefinition("docker.inspect", "Inspect Docker readiness.", ToolRisk.READ),
    "docker.run": ToolDefinition(
        "docker.run",
        "Run Docker build or compose commands.",
        ToolRisk.EXTERNAL,
        requires_approval=True,
        timeout_seconds=300,
    ),
    "web.search": ToolDefinition(
        "web.search",
        "Search the web for current external context.",
        ToolRisk.NETWORK,
        requires_approval=True,
    ),
    "vector.retrieve": ToolDefinition("vector.retrieve", "Retrieve semantic memory.", ToolRisk.READ),
    "document.read": ToolDefinition("document.read", "Read PDFs and documents.", ToolRisk.READ),
    "tabular.read": ToolDefinition("tabular.read", "Read CSV and Excel files.", ToolRisk.READ),
    "api.request": ToolDefinition(
        "api.request",
        "Call approved external APIs.",
        ToolRisk.EXTERNAL,
        requires_approval=True,
    ),
    "database.query": ToolDefinition("database.query", "Query application memory stores.", ToolRisk.READ),
    "memory.search": ToolDefinition("memory.search", "Search long-term memory.", ToolRisk.READ),
    "memory.write": ToolDefinition("memory.write", "Persist approved memory facts.", ToolRisk.WRITE),
}


def list_tools() -> list[ToolDefinition]:
    return list(TOOL_REGISTRY.values())


def allowed_tools(tool_names: tuple[str, ...] | list[str]) -> list[ToolDefinition]:
    return [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]

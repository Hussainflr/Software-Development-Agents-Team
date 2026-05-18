from __future__ import annotations

from dataclasses import asdict, dataclass

from tools.registry import ToolDefinition


@dataclass(frozen=True)
class MCPToolDescriptor:
    """MCP-compatible view of a local Agentic OS tool."""

    name: str
    description: str
    requires_approval: bool
    timeout_seconds: int
    metadata: dict[str, object]


def to_mcp_descriptor(tool: ToolDefinition) -> MCPToolDescriptor:
    return MCPToolDescriptor(
        name=tool.name,
        description=tool.description,
        requires_approval=tool.requires_approval,
        timeout_seconds=tool.timeout_seconds,
        metadata={
            "risk": tool.risk.value,
            "mcp_compatible": tool.mcp_compatible,
            "source": "agentic-os-local-tool-registry",
        },
    )


def render_mcp_manifest(tools: list[ToolDefinition]) -> dict[str, object]:
    return {
        "protocol": "mcp-compatible-tool-manifest",
        "tools": [asdict(to_mcp_descriptor(tool)) for tool in tools],
    }

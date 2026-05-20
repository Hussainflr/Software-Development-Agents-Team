from __future__ import annotations

from dataclasses import dataclass

from tools.registry import TOOL_REGISTRY, ToolDefinition


@dataclass(frozen=True)
class ToolPermissionDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    tool: ToolDefinition | None = None


class ToolPermissionPolicy:
    """Central permission gate for local and MCP-compatible tools."""

    def decide(self, tool_name: str, approved: bool = False) -> ToolPermissionDecision:
        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            return ToolPermissionDecision(
                allowed=False,
                requires_approval=False,
                reason=f"Unknown tool: {tool_name}",
            )
        if tool.requires_approval and not approved:
            return ToolPermissionDecision(
                allowed=False,
                requires_approval=True,
                reason=f"Tool {tool_name} requires human approval.",
                tool=tool,
            )
        return ToolPermissionDecision(
            allowed=True,
            requires_approval=tool.requires_approval,
            reason=f"Tool {tool_name} is allowed.",
            tool=tool,
        )

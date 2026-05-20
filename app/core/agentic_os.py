from __future__ import annotations

from dataclasses import asdict

from agents.catalog import list_agent_definitions
from app.core.control_loop import ControlLoopPolicy
from guardrails.requirements import classify_requirement
from llm_providers.catalog import list_model_provider_capabilities
from llm_providers.router import ModelRouter
from tools.mcp import render_mcp_manifest
from tools.permissions import ToolPermissionPolicy
from tools.registry import list_tools


class AgenticOSRuntime:
    """Read-only facade exposing platform capabilities to APIs and UI."""

    def __init__(self, control_policy: ControlLoopPolicy | None = None) -> None:
        self.control_policy = control_policy or ControlLoopPolicy()
        self.model_router = ModelRouter()
        self.tool_policy = ToolPermissionPolicy()

    def capabilities(self) -> dict[str, object]:
        tools = list_tools()
        return {
            "control_loop": asdict(self.control_policy),
            "agents": [asdict(agent) for agent in list_agent_definitions()],
            "tools": [asdict(tool) for tool in tools],
            "model_providers": [asdict(provider) for provider in list_model_provider_capabilities()],
            "memory_layers": ["short_term", "long_term", "session_planned", "artifact", "vector_planned"],
            "mcp": {
                "status": "adapter-ready",
                "manifest": render_mcp_manifest(tools),
            },
            "model_router": {
                "status": "metrics-ready",
                "features": ["fallback_route_contract", "token_estimates", "cost_estimates", "latency_metrics"],
            },
            "permissions": {
                "status": "policy-ready",
                "approval_required_tools": [tool.name for tool in tools if tool.requires_approval],
            },
        }

    def classify_goal(self, goal: str) -> dict[str, object]:
        return classify_requirement(goal).model_dump()

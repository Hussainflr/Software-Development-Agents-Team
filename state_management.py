"""
Production-ready state management for multi-agent workflows.

Uses TypedDict for type-safe, well-documented state management across agents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, TypedDict


# Type aliases for clarity
ArtifactPath = str
ArtifactContent = str
AgentName = str
MessageContent = str


class WorkflowState(TypedDict, total=False):
    """
    Main workflow state shared across all agents.
    
    This TypedDict defines the complete state object passed through the workflow.
    All fields are optional (total=False) to support gradual state building.
    """

    # Execution context
    run_id: int
    execution_id: str
    start_time: datetime
    current_stage: str

    # User requirement
    requirement: str
    requirement_parsed: dict[str, Any]

    # LLM configuration
    llm_provider: str
    llm_model: str
    temperature: float

    # Generated artifacts
    artifacts: dict[ArtifactPath, ArtifactContent]
    pending_artifacts: dict[ArtifactPath, ArtifactContent]

    # Execution history
    messages: list[str]
    agent_outputs: dict[AgentName, dict[str, Any]]
    agent_timings: dict[AgentName, float]

    # Testing results
    test_results: dict[str, Any]
    bugs_found: list[str]
    bug_report: str
    revision_count: int

    # Control flow
    approval_status: Literal["pending", "approved", "rejected"]
    deployment_approved: bool
    stop_requested: bool
    failed: bool
    failure_reason: str
    failure_agent: str

    # Metadata
    metadata: dict[str, Any]


@dataclass
class AgentExecutionContext:
    """
    Context provided to each agent during execution.
    
    Contains all necessary information for an agent to make decisions
    and generate artifacts.
    """

    run_id: int
    execution_id: str
    agent_name: str
    requirement: str
    artifacts: dict[ArtifactPath, ArtifactContent]
    messages: list[MessageContent]
    bug_report: str = ""
    revision: bool = False
    revision_count: int = 0
    parent_outputs: dict[AgentName, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "execution_id": self.execution_id,
            "agent_name": self.agent_name,
            "requirement": self.requirement,
            "artifact_paths": list(self.artifacts.keys()),
            "message_count": len(self.messages),
            "revision": self.revision,
            "revision_count": self.revision_count,
        }


@dataclass
class AgentExecutionResult:
    """
    Result returned by an agent after execution.
    
    Contains generated artifacts, summary, and any issues encountered.
    """

    agent_name: str
    success: bool
    summary: str
    artifacts: dict[ArtifactPath, ArtifactContent] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    bugs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    tokens_used: dict[str, int] = field(default_factory=dict)
    raw_response: str = ""
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging and serialization."""
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "summary": self.summary,
            "artifact_count": len(self.artifacts),
            "bug_count": len(self.bugs),
            "error_count": len(self.errors),
            "execution_time_seconds": self.execution_time_seconds,
            "tokens_used": self.tokens_used,
            "retry_count": self.retry_count,
        }


@dataclass
class WorkflowExecutionReport:
    """
    Final report of workflow execution.
    
    Provides comprehensive metrics and results for monitoring and analysis.
    """

    run_id: int
    execution_id: str
    status: Literal["completed", "failed", "stopped"]
    total_duration_seconds: float
    stages_executed: list[str]
    agent_results: dict[AgentName, AgentExecutionResult]
    final_artifacts: dict[ArtifactPath, ArtifactContent]
    errors_encountered: list[dict[str, Any]]
    revision_cycles: int
    total_tokens_used: int
    start_time: datetime
    end_time: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging and storage."""
        return {
            "run_id": self.run_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "total_duration_seconds": self.total_duration_seconds,
            "stages_executed": self.stages_executed,
            "agent_count": len(self.agent_results),
            "artifact_count": len(self.final_artifacts),
            "error_count": len(self.errors_encountered),
            "revision_cycles": self.revision_cycles,
            "total_tokens_used": self.total_tokens_used,
        }


# Helper functions for state operations
def init_workflow_state(
    run_id: int, execution_id: str, requirement: str, **kwargs: Any
) -> WorkflowState:
    """Initialize a new workflow state."""
    return WorkflowState(
        run_id=run_id,
        execution_id=execution_id,
        requirement=requirement,
        start_time=datetime.utcnow(),
        artifacts={},
        pending_artifacts={},
        messages=[],
        agent_outputs={},
        agent_timings={},
        test_results={},
        bugs_found=[],
        bug_report="",
        revision_count=0,
        approval_status="pending",
        deployment_approved=False,
        stop_requested=False,
        failed=False,
        metadata=kwargs,
    )


def add_agent_output(
    state: WorkflowState, agent_name: str, output: AgentExecutionResult
) -> WorkflowState:
    """Add agent output to state, merging artifacts."""
    state["agent_outputs"][agent_name] = output.to_dict()
    state["artifacts"] = {**state["artifacts"], **output.artifacts}
    state["messages"].append(f"{agent_name}: {output.summary}")

    if output.bugs:
        state["bugs_found"].extend(output.bugs)
        state["bug_report"] = "\n".join(output.bugs)

    return state

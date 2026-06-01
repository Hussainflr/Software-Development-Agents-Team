from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ControlPhase(str, Enum):
    """Standard execution phases for agentic work."""

    SENSE = "sense"
    PLAN = "plan"
    ACT = "act"
    EVALUATE = "evaluate"
    REFINE = "refine"
    RETRY = "retry"
    FINALIZE = "finalize"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class ControlLoopPolicy:
    """Runtime limits applied to every autonomous workflow."""

    max_refinements: int = 2
    max_retries_per_step: int = 2
    step_timeout_seconds: int = 180
    workflow_timeout_seconds: int = 1800
    require_human_approval_for_deployment: bool = True


@dataclass
class ControlLoopState:
    """Small state object shared by workflow nodes and observability."""

    run_id: int
    goal: str
    phase: ControlPhase = ControlPhase.SENSE
    current_agent: str | None = None
    refinements: int = 0
    retries: dict[str, int] = field(default_factory=dict)
    cancelled: bool = False
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(self, phase: ControlPhase, agent: str | None = None, **metadata: Any) -> None:
        self.phase = phase
        self.current_agent = agent
        if metadata:
            self.metadata.update(metadata)

    def retry_count(self, step_name: str) -> int:
        return self.retries.get(step_name, 0)

    def mark_retry(self, step_name: str) -> int:
        next_count = self.retry_count(step_name) + 1
        self.retries[step_name] = next_count
        self.phase = ControlPhase.RETRY
        return next_count

    def can_retry(self, step_name: str, policy: ControlLoopPolicy) -> bool:
        return self.retry_count(step_name) < policy.max_retries_per_step

    def can_refine(self, policy: ControlLoopPolicy) -> bool:
        return self.refinements < policy.max_refinements

    def mark_refinement(self) -> int:
        self.refinements += 1
        self.phase = ControlPhase.REFINE
        return self.refinements

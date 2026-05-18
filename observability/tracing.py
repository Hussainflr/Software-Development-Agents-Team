from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from database.repository import Repository


@dataclass(frozen=True)
class TraceEvent:
    run_id: int
    component: str
    event_type: str
    message: str
    status: str = "info"
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TraceRecorder:
    """Persists structured trace events through the existing log table."""

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def record(self, event: TraceEvent) -> None:
        payload = {
            "message": event.message,
            "event_type": event.event_type,
            "metadata": event.metadata,
            "timestamp": event.timestamp.isoformat(),
        }
        self.repository.add_log(
            event.run_id,
            event.component,
            event.event_type,
            json.dumps(payload),
            status=event.status,
        )

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

try:
    from pydantic import BaseModel, Field, validator
except ImportError:  # pragma: no cover - pydantic optional in some envs
    BaseModel = object  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore
    validator = lambda *_, **__: lambda x: x  # type: ignore


ISO = "%Y-%m-%dT%H:%M:%S"


class UsageMessage(BaseModel):  # type: ignore[misc]
    usage: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    content: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UsageEvent(BaseModel):  # type: ignore[misc]
    event_id: str | None = None
    time: datetime
    source: str
    environment: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    conversation_id: str | None = None
    route_id: str | None = None
    model_id: str | None = None
    provider: str | None = None
    account_id: str | None = None
    endpoint_id: str | None = None
    cwd: str | None = None
    agent: str | None = None
    message: UsageMessage
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("time", pre=True)
    def _parse_time(cls, value: Any) -> datetime:  # noqa: N805
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


class LabeledUsageEvent(BaseModel):  # type: ignore[misc]
    event: UsageEvent
    task_type: str | None = None
    domain: str | None = None
    complexity: str | None = None
    outcome: str | None = None
    quality_score: float | None = None
    regret: bool | None = None
    tags: list[str] = Field(default_factory=list)
    label_source: str = "heuristic"
    confidence: float | None = None


def from_ccusage_line(line: str, default_agent: str = "claude-code") -> UsageEvent:
    """Convert a ccusage JSONL line into a UsageEvent."""
    data = json.loads(line)
    msg = data.get("message", {})
    usage = msg.get("usage") or {}
    content = msg.get("content") or []
    return UsageEvent(
        time=data.get("timestamp") or datetime.utcnow(),
        source="ccusage",
        environment="ide",
        session_id=data.get("sessionId"),
        cwd=data.get("cwd"),
        agent=data.get("agent") or default_agent,
        message=UsageMessage(usage=usage, model=msg.get("model"), content=content),
        metadata={"raw": data},
    )


# Sentinel event primitives -------------------------------------------------

@dataclass(slots=True)
class SentinelSummary:
    run_id: str
    outcome: str
    errors: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    last_messages: list[str] = field(default_factory=list)
    source: str = "unknown"
    route_id: Optional[str] = None
    agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class SentinelDecision:
    action: str  # retry | followup | escalate | none
    reason: str
    confidence: float
    summary: SentinelSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "confidence": self.confidence,
            "summary": {
                "run_id": self.summary.run_id,
                "outcome": self.summary.outcome,
                "errors": self.summary.errors,
                "next_steps": self.summary.next_steps,
                "last_messages": self.summary.last_messages,
                "source": self.summary.source,
                "route_id": self.summary.route_id,
                "agent": self.summary.agent,
                "created_at": self.summary.created_at.isoformat(),
            },
        }

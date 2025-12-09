"""Neo4j storage adapter models and configuration."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class Neo4jConnectionState(str, Enum):
    """Connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    max_transaction_retry_time: float = 30.0
    encrypted: bool = True
    trust: str = "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES"


@dataclass
class Entity:
    """Graph entity (node) representation."""
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_neo4j_node(cls, node: Any) -> "Entity":
        """Create from Neo4j node object."""
        props = dict(node)
        return cls(
            id=props.pop("id", str(node.id)),
            labels=list(node.labels),
            properties=props,
            created_at=datetime.fromisoformat(props.pop("created_at", _utcnow().isoformat())),
            updated_at=datetime.fromisoformat(props.pop("updated_at", _utcnow().isoformat()))
        )


@dataclass
class Relationship:
    """Graph relationship (edge) representation."""
    id: str
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class QueryResult:
    """Result from Cypher query execution."""
    records: List[Dict[str, Any]]
    summary: Dict[str, Any]
    keys: List[str]
    execution_time_ms: float

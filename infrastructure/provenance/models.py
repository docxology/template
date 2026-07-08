"""Data models for the provenance DAG.

Nodes represent artifacts, pipeline runs, data sources, and scientific claims.
Edges encode directed relationships between nodes.  The DAG is content-addressed:
each node receives a SHA-256 ``node_id`` derived from its kind and payload.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeKind(str, Enum):
    """Classification of a provenance node."""

    artifact = "artifact"  # A file or dataset artifact
    run = "run"  # A pipeline run or script execution
    source = "source"  # An external data source or reference
    claim = "claim"  # A scientific claim or assertion


class EdgeRelation(str, Enum):
    """Directed relationship type between two provenance nodes."""

    derived_from = "derived_from"  # Target was derived from source
    produced_by = "produced_by"  # Target was produced by a run
    cites = "cites"  # Target cites a source
    supports = "supports"  # Source evidence supports a claim
    contradicts = "contradicts"  # Source evidence contradicts a claim
    depends_on = "depends_on"  # Target depends on source
    versioned_from = "versioned_from"  # Target is a new version of source


def _sha256_id(kind: str, payload: dict[str, Any]) -> str:
    """Derive a stable SHA-256 content-address from *kind* + *payload*."""
    canonical = json.dumps({"kind": kind, **payload}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


@dataclass
class NodeBase:
    """Common fields shared by all provenance nodes.

    Attributes:
        node_id: SHA-256 content address (first 32 hex chars).
        kind: Node classification.
        label: Human-readable display name.
        metadata: Free-form extra attributes.
        created_at: ISO-8601 timestamp string (supplied by the store).
    """

    node_id: str
    kind: NodeKind
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "node_id": self.node_id,
            "kind": self.kind.value,
            "label": self.label,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class ArtifactNode(NodeBase):
    """Provenance node for a file or dataset artifact.

    Attributes:
        path: Relative or absolute path to the artifact.
        content_hash: SHA-256 hash of the artifact's content, or ``None``.
        size_bytes: File size in bytes, or ``None``.
    """

    path: str = ""
    content_hash: str | None = None
    size_bytes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        d = super().to_dict()
        d.update({"path": self.path, "content_hash": self.content_hash, "size_bytes": self.size_bytes})
        return d

    @classmethod
    def create(
        cls,
        label: str,
        path: str,
        content_hash: str | None = None,
        size_bytes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ArtifactNode":
        """Process create."""
        node_id = _sha256_id(NodeKind.artifact.value, {"label": label, "path": path})
        return cls(
            node_id=node_id,
            kind=NodeKind.artifact,
            label=label,
            path=path,
            content_hash=content_hash,
            size_bytes=size_bytes,
            metadata=metadata or {},
        )


@dataclass
class RunNode(NodeBase):
    """Provenance node for a pipeline run or script execution.

    Attributes:
        command: The command or script that was executed.
        exit_code: Exit code, or ``None`` if still running.
        duration_seconds: Wall-clock duration, or ``None``.
    """

    command: str = ""
    exit_code: int | None = None
    duration_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        d = super().to_dict()
        d.update(
            {
                "command": self.command,
                "exit_code": self.exit_code,
                "duration_seconds": self.duration_seconds,
            }
        )
        return d

    @classmethod
    def create(
        cls,
        label: str,
        command: str,
        exit_code: int | None = None,
        duration_seconds: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "RunNode":
        """Process create."""
        node_id = _sha256_id(NodeKind.run.value, {"label": label, "command": command})
        return cls(
            node_id=node_id,
            kind=NodeKind.run,
            label=label,
            command=command,
            exit_code=exit_code,
            duration_seconds=duration_seconds,
            metadata=metadata or {},
        )


@dataclass
class SourceNode(NodeBase):
    """Provenance node for an external data source or reference.

    Attributes:
        uri: URI / DOI / URL of the source.
        source_type: Classification, e.g. ``"paper"``, ``"dataset"``, ``"url"``.
    """

    uri: str = ""
    source_type: str = "generic"

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        d = super().to_dict()
        d.update({"uri": self.uri, "source_type": self.source_type})
        return d

    @classmethod
    def create(
        cls,
        label: str,
        uri: str,
        source_type: str = "generic",
        metadata: dict[str, Any] | None = None,
    ) -> "SourceNode":
        """Process create."""
        node_id = _sha256_id(NodeKind.source.value, {"label": label, "uri": uri})
        return cls(
            node_id=node_id,
            kind=NodeKind.source,
            label=label,
            uri=uri,
            source_type=source_type,
            metadata=metadata or {},
        )


@dataclass
class ClaimNode(NodeBase):
    """Provenance node for a scientific claim or assertion.

    Attributes:
        claim_text: The verbatim claim.
        confidence: Confidence score in ``[0, 1]``.
    """

    claim_text: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        d = super().to_dict()
        d.update({"claim_text": self.claim_text, "confidence": self.confidence})
        return d

    @classmethod
    def create(
        cls,
        label: str,
        claim_text: str,
        confidence: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> "ClaimNode":
        """Process create."""
        node_id = _sha256_id(NodeKind.claim.value, {"label": label, "claim_text": claim_text})
        return cls(
            node_id=node_id,
            kind=NodeKind.claim,
            label=label,
            claim_text=claim_text,
            confidence=confidence,
            metadata=metadata or {},
        )


@dataclass(frozen=True)
class Edge:
    """A directed edge between two provenance nodes.

    Attributes:
        from_id: ``node_id`` of the source node.
        to_id: ``node_id`` of the target node.
        relation: Relationship type.
        metadata: Optional edge-level metadata.
    """

    from_id: str
    to_id: str
    relation: EdgeRelation
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation": self.relation.value,
            "metadata": dict(self.metadata),
        }


# Node type alias
ProvenanceNode = ArtifactNode | RunNode | SourceNode | ClaimNode

_KIND_MAP: dict[str, type[ProvenanceNode]] = {
    NodeKind.artifact.value: ArtifactNode,
    NodeKind.run.value: RunNode,
    NodeKind.source.value: SourceNode,
    NodeKind.claim.value: ClaimNode,
}


def node_from_dict(data: dict[str, Any]) -> ProvenanceNode:
    """Deserialise a node from a plain dictionary.

    Args:
        data: A mapping as returned by :meth:`NodeBase.to_dict`.

    Returns:
        The appropriate subclass instance.

    Raises:
        ValueError: For unknown ``kind`` values.
    """
    kind = data.get("kind", "")
    cls = _KIND_MAP.get(kind)
    if cls is None:
        raise ValueError(f"Unknown node kind: {kind!r}")

    common = {
        "node_id": data.get("node_id", ""),
        "kind": NodeKind(kind),
        "label": data.get("label", ""),
        "metadata": data.get("metadata") or {},
        "created_at": data.get("created_at", ""),
    }
    if cls is ArtifactNode:
        return ArtifactNode(
            **common,
            path=data.get("path", ""),
            content_hash=data.get("content_hash"),
            size_bytes=data.get("size_bytes"),
        )
    if cls is RunNode:
        return RunNode(
            **common,
            command=data.get("command", ""),
            exit_code=data.get("exit_code"),
            duration_seconds=data.get("duration_seconds"),
        )
    if cls is SourceNode:
        return SourceNode(
            **common,
            uri=data.get("uri", ""),
            source_type=data.get("source_type", "generic"),
        )
    # ClaimNode
    return ClaimNode(
        **common,
        claim_text=data.get("claim_text", ""),
        confidence=float(data.get("confidence", 0.0)),
    )


__all__ = [
    "ArtifactNode",
    "ClaimNode",
    "Edge",
    "EdgeRelation",
    "NodeBase",
    "NodeKind",
    "ProvenanceNode",
    "RunNode",
    "SourceNode",
    "node_from_dict",
]

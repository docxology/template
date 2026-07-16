"""Provenance DAG store with SHA-256 content addressing and atomic writes.

The store persists nodes and edges as a single JSON file under
``output/provenance/dag.json`` relative to the project directory.
All writes are atomic (write-then-rename) to avoid partial-state corruption.
"""

from __future__ import annotations

import datetime
import json
import tempfile
import typing
from contextlib import suppress
from pathlib import Path
from typing import Any, Iterator

from infrastructure.provenance.models import (
    Edge,
    EdgeRelation,
    NodeKind,
    ProvenanceNode,
    node_from_dict,
)

_DEFAULT_FILENAME = "dag.json"


class Provenance:
    """Persistent provenance DAG store.

    Args:
        path: Path to the JSON backing file.  The parent directory is created
            on first write.

    Usage::

        prov = Provenance.with_path(project_dir / "output" / "provenance")
        node = ArtifactNode.create("fig1.pdf", path="output/figures/fig1.pdf")
        prov.record(node)
        prov.link(run_node.node_id, node.node_id, EdgeRelation.produced_by)
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        if path.exists():
            self._load()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def with_path(cls, directory: Path | str, filename: str = _DEFAULT_FILENAME) -> "Provenance":
        """Create a :class:`Provenance` rooted at *directory*/*filename*.

        Args:
            directory: Directory that will hold the DAG JSON file.
            filename: JSON file name (default: ``dag.json``).
        """
        return cls(Path(directory) / filename)

    @property
    def path(self) -> Path:
        """Return the backing file path."""
        return self._path

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def record(self, node: ProvenanceNode) -> ProvenanceNode:
        """Record *node* in the DAG (idempotent by ``node_id``).

        Args:
            node: Any provenance node.  The ``created_at`` timestamp is set
                when the node is first recorded.

        Returns:
            The recorded node (with ``created_at`` filled in if newly created).
        """
        if node.node_id not in self._nodes:
            node.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self._nodes[node.node_id] = node.to_dict()
            self._save()
        return node

    def link(
        self,
        from_id: str,
        to_id: str,
        relation: EdgeRelation,
        metadata: dict[str, Any] | None = None,
    ) -> Edge:
        """Add a directed edge between two nodes (idempotent by key).

        Args:
            from_id: Source node id.
            to_id: Target node id.
            relation: Relationship type.
            metadata: Optional edge-level payload.

        Returns:
            The edge object.

        Raises:
            KeyError: When either *from_id* or *to_id* is not recorded.
        """
        if from_id not in self._nodes:
            raise KeyError(f"Node '{from_id}' not found in provenance store")
        if to_id not in self._nodes:
            raise KeyError(f"Node '{to_id}' not found in provenance store")

        edge = Edge(from_id=from_id, to_id=to_id, relation=relation, metadata=metadata or {})
        key = (from_id, to_id, relation.value)
        # Idempotent: only add if not already present
        existing_keys = {(e["from_id"], e["to_id"], e["relation"]) for e in self._edges}
        if key not in existing_keys:
            self._edges.append(edge.to_dict())
            self._save()
        return edge

    def clear(self) -> tuple[int, int]:
        """Remove all nodes and edges.

        Returns:
            A tuple ``(num_nodes, num_edges)`` indicating what was removed.
        """
        n_nodes, n_edges = len(self._nodes), len(self._edges)
        self._nodes.clear()
        self._edges.clear()
        self._save()
        return n_nodes, n_edges

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, node_id: str) -> ProvenanceNode | None:
        """Return the node with *node_id*, or ``None``."""
        data = self._nodes.get(node_id)
        return node_from_dict(data) if data else None

    def list(  # noqa: A003
        self,
        kind: NodeKind | None = None,
    ) -> list[ProvenanceNode]:
        """Return all nodes, optionally filtered by *kind*.

        Args:
            kind: When supplied, only nodes of this kind are returned.
        """
        nodes = [node_from_dict(d) for d in self._nodes.values()]
        if kind is not None:
            nodes = [n for n in nodes if n.kind == kind]
        return nodes

    def query(
        self,
        *,
        from_id: str | None = None,
        to_id: str | None = None,
        relation: EdgeRelation | None = None,
    ) -> typing.List[Edge]:
        """Return edges matching the supplied criteria.

        All supplied criteria are combined with AND.

        Args:
            from_id: Filter by source node id.
            to_id: Filter by target node id.
            relation: Filter by edge relation type.
        """
        results: list[Edge] = []
        for e in self._edges:
            if from_id is not None and e["from_id"] != from_id:
                continue
            if to_id is not None and e["to_id"] != to_id:
                continue
            if relation is not None and e["relation"] != relation.value:
                continue
            results.append(
                Edge(
                    from_id=e["from_id"],
                    to_id=e["to_id"],
                    relation=EdgeRelation(e["relation"]),
                    metadata=e.get("metadata") or {},
                )
            )
        return results

    def __len__(self) -> int:
        return len(self._nodes)

    def __iter__(self) -> Iterator[ProvenanceNode]:
        return iter(self.list())

    def __repr__(self) -> str:
        return f"Provenance(nodes={len(self._nodes)}, edges={len(self._edges)}, path={self._path})"

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load state from the backing file."""
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        self._nodes = {n["node_id"]: n for n in payload.get("nodes", []) if "node_id" in n}
        self._edges = payload.get("edges", [])

    def _save(self) -> None:
        """Atomically persist the current DAG to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": list(self._nodes.values()),
            "edges": self._edges,
        }
        # Atomic write: write to tmp then rename
        tmp_dir = self._path.parent
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=tmp_dir,
                delete=False,
                suffix=".tmp",
            ) as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
                tmp_path = Path(fh.name)
            tmp_path.replace(self._path)
        except OSError:
            if tmp_path is not None:
                with suppress(OSError):
                    tmp_path.unlink(missing_ok=True)
            raise


__all__ = ["Provenance"]

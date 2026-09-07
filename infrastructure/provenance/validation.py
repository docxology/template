"""Provenance DAG integrity and topological validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from infrastructure.provenance.models import Edge, NodeKind, ProvenanceNode
from infrastructure.provenance.store import Provenance


@dataclass(frozen=True)
class ProvenanceValidationFinding:
    """A single issue discovered during provenance DAG validation."""

    code: str
    severity: str  # "error", "warning", "info"
    message: str
    node_id: str | None = None
    edge: dict[str, Any] | None = None


@dataclass
class ProvenanceValidationReport:
    """Report detailing DAG structural and content integrity."""

    total_nodes: int = 0
    total_edges: int = 0
    findings: list[ProvenanceValidationFinding] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if there are no error-level findings."""
        return not any(f.severity == "error" for f in self.findings)

    @property
    def errors(self) -> list[ProvenanceValidationFinding]:
        """Return all error findings."""
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[ProvenanceValidationFinding]:
        """Return all warning findings."""
        return [f for f in self.findings if f.severity == "warning"]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "is_valid": self.is_valid,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "findings": [
                {
                    "code": f.code,
                    "severity": f.severity,
                    "message": f.message,
                    "node_id": f.node_id,
                    "edge": f.edge,
                }
                for f in self.findings
            ],
        }


def validate_provenance_dag(store: Provenance) -> ProvenanceValidationReport:
    """Validate graph structure, references, and acyclicity of a Provenance store."""
    findings: list[ProvenanceValidationFinding] = []

    nodes: list[ProvenanceNode] = store.list()
    edges: list[Edge] = store.query()
    node_map: dict[str, ProvenanceNode] = {n.node_id: n for n in nodes}

    # 1. Check for orphaned edges or dangling references
    for edge in edges:
        if edge.from_id not in node_map:
            findings.append(
                ProvenanceValidationFinding(
                    code="PROV_DANGLING_FROM",
                    severity="error",
                    message=f"Edge references non-existent source node '{edge.from_id}'",
                    edge=edge.to_dict(),
                )
            )
        if edge.to_id not in node_map:
            findings.append(
                ProvenanceValidationFinding(
                    code="PROV_DANGLING_TO",
                    severity="error",
                    message=f"Edge references non-existent target node '{edge.to_id}'",
                    edge=edge.to_dict(),
                )
            )

    # 2. Check for self-referential edges
    for edge in edges:
        if edge.from_id == edge.to_id:
            findings.append(
                ProvenanceValidationFinding(
                    code="PROV_SELF_LOOP",
                    severity="error",
                    message=f"Node '{edge.from_id}' has self-referential edge with relation '{edge.relation.value}'",
                    node_id=edge.from_id,
                    edge=edge.to_dict(),
                )
            )

    # 3. Detect cycles in derivation and dependency chains (topological sort)
    adjacency: dict[str, list[str]] = {n.node_id: [] for n in nodes}
    for edge in edges:
        if edge.from_id in adjacency and edge.to_id in adjacency:
            adjacency[edge.from_id].append(edge.to_id)

    visited: dict[str, int] = {}  # 0 = unvisited, 1 = visiting, 2 = visited

    def _dfs_cycle_check(node_id: str, path: list[str]) -> None:
        visited[node_id] = 1
        path.append(node_id)
        for neighbor in adjacency.get(node_id, []):
            if neighbor == node_id:
                # Trivial cycle already reported as PROV_SELF_LOOP above;
                # do not double-report the same defect as a full cycle.
                continue
            if visited.get(neighbor) == 1:
                cycle_str = " -> ".join(path[path.index(neighbor) :] + [neighbor])
                findings.append(
                    ProvenanceValidationFinding(
                        code="PROV_CYCLE_DETECTED",
                        severity="error",
                        message=f"Cycle detected in provenance DAG: {cycle_str}",
                        node_id=node_id,
                    )
                )
            elif neighbor not in visited:
                _dfs_cycle_check(neighbor, path)
        path.pop()
        visited[node_id] = 2

    for node_id in node_map:
        if node_id not in visited:
            _dfs_cycle_check(node_id, [])

    # 4. Check for unlinked / isolated claim or artifact nodes
    referenced_nodes = {e.from_id for e in edges} | {e.to_id for e in edges}
    for node in nodes:
        if node.kind in (NodeKind.claim, NodeKind.artifact) and node.node_id not in referenced_nodes:
            findings.append(
                ProvenanceValidationFinding(
                    code="PROV_ISOLATED_NODE",
                    severity="warning",
                    message=(
                        f"{node.kind.value.capitalize()} node '{node.label}' is completely "
                        "unlinked to any run or source"
                    ),
                    node_id=node.node_id,
                )
            )

    return ProvenanceValidationReport(
        total_nodes=len(nodes),
        total_edges=len(edges),
        findings=findings,
    )


__all__ = [
    "ProvenanceValidationFinding",
    "ProvenanceValidationReport",
    "validate_provenance_dag",
]

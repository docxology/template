"""ExperimentNode tree with frozen semantics (OpenResearch-style discipline).

An experiment tree is a small hierarchy of experiment nodes stored inside the
existing content-addressed provenance store (as ``run`` nodes carrying an
``experiment`` metadata block).  Tree discipline:

- ``answered`` nodes are immutable -- mutating one raises
  :class:`ProvenanceStoreError` with diagnostic ``EXPERIMENT.ANSWERED_IMMUTABLE``.
- every node in a tree must share one ``run_command`` (the "fixed run
  contract", diagnostic ``EXPERIMENT.RUN_COMMAND_MISMATCH``).
- the tree must stay acyclic (delegated to
  :func:`infrastructure.provenance.validation.validate_provenance_dag`).
- exactly one baseline root per tree (``EXPERIMENT.MULTIPLE_BASELINES``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List

from infrastructure.provenance.models import EdgeRelation, NodeKind, RunNode, _sha256_id
from infrastructure.provenance.store import Provenance, ProvenanceStoreError
from infrastructure.provenance.validation import (
    ProvenanceValidationFinding,
    ProvenanceValidationReport,
    validate_provenance_dag,
)

_EXPERIMENT_METADATA_KEY = "experiment"


class ExperimentCode:
    """Stable dotted diagnostic IDs for experiment-tree findings."""

    ANSWERED_IMMUTABLE = "EXPERIMENT.ANSWERED_IMMUTABLE"
    RUN_COMMAND_MISMATCH = "EXPERIMENT.RUN_COMMAND_MISMATCH"
    CYCLE_DETECTED = "EXPERIMENT.CYCLE_DETECTED"
    MULTIPLE_BASELINES = "EXPERIMENT.MULTIPLE_BASELINES"
    MISSING_PARENT = "EXPERIMENT.MISSING_PARENT"
    NOT_AN_EXPERIMENT = "EXPERIMENT.NOT_AN_EXPERIMENT"
    INVALID_STATE = "EXPERIMENT.INVALID_STATE"


class ExperimentKind(str, Enum):
    """Role of an experiment node within its tree."""

    baseline = "baseline"
    child = "child"


class ExperimentStatus(str, Enum):
    """Lifecycle status of an experiment node."""

    provisional = "provisional"
    frozen = "frozen"
    answered = "answered"


@dataclass
class ExperimentNode:
    """A node in an experiment tree, persisted in the provenance store.

    Attributes:
        experiment_id: SHA-256 content address (first 32 hex chars), derived
            with the package-wide ``_sha256_id`` convention.
        kind: ``baseline`` or ``child``.
        status: ``provisional``, ``frozen``, or ``answered``.
        run_command: The fixed run command shared by the whole tree.
        parent_id: ``experiment_id`` of the parent (empty for a baseline).
        payload: Free-form experiment payload (hypothesis, params, results).
    """

    experiment_id: str
    kind: ExperimentKind
    status: ExperimentStatus
    run_command: str
    parent_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain JSON-safe dict."""
        return {
            "experiment_id": self.experiment_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "run_command": self.run_command,
            "parent_id": self.parent_id,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentNode":
        """Deserialize from :meth:`to_dict` output.

        Raises:
            ProvenanceStoreError: When any field is missing or malformed.
        """
        experiment_id = data.get("experiment_id")
        if not isinstance(experiment_id, str) or not experiment_id:
            raise ProvenanceStoreError(f"Experiment node has no valid experiment_id: {data!r}")
        try:
            kind = ExperimentKind(data.get("kind", ""))
            status = ExperimentStatus(data.get("status", ""))
        except ValueError as exc:
            raise ProvenanceStoreError(f"Invalid experiment node state for {experiment_id}: {exc}") from exc
        run_command = data.get("run_command")
        if not isinstance(run_command, str) or not run_command:
            raise ProvenanceStoreError(f"Experiment node {experiment_id} has no valid run_command")
        parent_id = data.get("parent_id", "")
        if not isinstance(parent_id, str):
            raise ProvenanceStoreError(f"Experiment node {experiment_id} has invalid parent_id")
        payload = data.get("payload", {})
        if not isinstance(payload, dict):
            raise ProvenanceStoreError(f"Experiment node {experiment_id} has invalid payload")
        return cls(
            experiment_id=experiment_id,
            kind=kind,
            status=status,
            run_command=run_command,
            parent_id=parent_id,
            payload=payload,
        )


def _experiment_node_id(label: str, parent_id: str) -> str:
    """Derive a stable content address for an experiment node."""
    return _sha256_id("experiment", {"label": label, "parent_id": parent_id})


class ExperimentTree:
    """Experiment-tree discipline layered on an existing :class:`Provenance` store.

    Nodes are stored as ``run`` provenance nodes whose ``metadata`` carries an
    ``experiment`` block, so persistence, atomic writes, and validation all
    reuse the existing content-addressed store.
    """

    def __init__(self, store: Provenance) -> None:
        self._store = store

    @property
    def store(self) -> Provenance:
        """Return the backing provenance store."""
        return self._store

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_baseline(self, label: str, run_command: str, payload: dict[str, Any] | None = None) -> ExperimentNode:
        """Add a baseline (root) experiment node."""
        return self._add_node(
            label=label,
            kind=ExperimentKind.baseline,
            parent_id="",
            run_command=run_command,
            payload=payload,
        )

    def add_child(
        self,
        label: str,
        parent_id: str,
        run_command: str,
        payload: dict[str, Any] | None = None,
    ) -> ExperimentNode:
        """Add a child experiment node under *parent_id*.

        Raises:
            ProvenanceStoreError: When the parent does not exist or uses a
                different ``run_command``.
        """
        parent = self.get(parent_id)
        if parent is None:
            raise ProvenanceStoreError(f"{ExperimentCode.MISSING_PARENT}: parent experiment '{parent_id}' not found")
        if parent.run_command != run_command:
            raise ProvenanceStoreError(
                f"{ExperimentCode.RUN_COMMAND_MISMATCH}: run_command {run_command!r} does not "
                f"match tree contract {parent.run_command!r}"
            )
        return self._add_node(
            label=label,
            kind=ExperimentKind.child,
            parent_id=parent_id,
            run_command=run_command,
            payload=payload,
        )

    def _add_node(
        self,
        *,
        label: str,
        kind: ExperimentKind,
        parent_id: str,
        run_command: str,
        payload: dict[str, Any] | None,
    ) -> ExperimentNode:
        experiment_id = _experiment_node_id(label, parent_id)
        if self.get(experiment_id) is not None:
            raise ProvenanceStoreError(f"Experiment node '{experiment_id}' already exists")
        node = ExperimentNode(
            experiment_id=experiment_id,
            kind=kind,
            status=ExperimentStatus.provisional,
            run_command=run_command,
            parent_id=parent_id,
            payload=payload or {},
        )
        self._store.record(self._to_run_node(node))
        if parent_id:
            self._store.link(parent_id, node.experiment_id, EdgeRelation.depends_on)
        return node

    def update_node(
        self,
        experiment_id: str,
        *,
        status: ExperimentStatus | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ExperimentNode:
        """Update the status and/or payload of an experiment node.

        Raises:
            ProvenanceStoreError: When the node does not exist or is
                ``answered`` (immutable).
        """
        node = self.get(experiment_id)
        if node is None:
            raise ProvenanceStoreError(f"{ExperimentCode.NOT_AN_EXPERIMENT}: experiment '{experiment_id}' not found")
        if node.status is ExperimentStatus.answered:
            raise ProvenanceStoreError(
                f"{ExperimentCode.ANSWERED_IMMUTABLE}: experiment '{experiment_id}' is answered and cannot be mutated"
            )
        if status is not None:
            node.status = status
        if payload is not None:
            node.payload = dict(payload)
        self._store.update_node(self._to_run_node(node))
        return node

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, experiment_id: str) -> ExperimentNode | None:
        """Return the experiment node with *experiment_id*, or ``None``."""
        raw = self._store.get(experiment_id)
        if raw is None or _EXPERIMENT_METADATA_KEY not in raw.metadata:
            return None
        return ExperimentNode.from_dict(raw.metadata[_EXPERIMENT_METADATA_KEY])

    def list(self) -> List[ExperimentNode]:  # noqa: A003
        """Return all experiment nodes in the tree."""
        experiments: List[ExperimentNode] = []
        for raw in self._store.list():
            if _EXPERIMENT_METADATA_KEY in raw.metadata:
                experiments.append(ExperimentNode.from_dict(raw.metadata[_EXPERIMENT_METADATA_KEY]))
        return experiments

    def roots(self) -> List[ExperimentNode]:
        """Return baseline nodes (tree roots)."""
        return [n for n in self.list() if n.kind is ExperimentKind.baseline]

    def children_of(self, experiment_id: str) -> List[ExperimentNode]:
        """Return the child nodes of *experiment_id*."""
        return [n for n in self.list() if n.parent_id == experiment_id]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _to_run_node(node: ExperimentNode) -> RunNode:
        return RunNode(
            node_id=node.experiment_id,
            kind=NodeKind.run,
            label=node.experiment_id,
            command=node.run_command,
            metadata={_EXPERIMENT_METADATA_KEY: node.to_dict()},
        )


def validate_experiment_tree(tree: ExperimentTree) -> ProvenanceValidationReport:
    """Validate tree discipline: fixed run contract, acyclicity, single baseline.

    Acyclicity is delegated to :func:`validate_provenance_dag`; its cycle
    findings are re-emitted with ``EXPERIMENT.CYCLE_DETECTED``.
    """
    findings: list[ProvenanceValidationFinding] = []
    nodes = tree.list()
    node_map = {n.experiment_id: n for n in nodes}

    dag_report = validate_provenance_dag(tree.store)
    for finding in dag_report.findings:
        if finding.code == "PROV_CYCLE_DETECTED":
            findings.append(
                ProvenanceValidationFinding(
                    code=ExperimentCode.CYCLE_DETECTED,
                    severity="error",
                    message=finding.message,
                    node_id=finding.node_id,
                    edge=finding.edge,
                )
            )

    run_commands = {n.run_command for n in nodes}
    if len(run_commands) > 1:
        canonical = sorted(run_commands)[0]
        offenders = sorted(n.experiment_id for n in nodes if n.run_command != canonical)
        findings.append(
            ProvenanceValidationFinding(
                code=ExperimentCode.RUN_COMMAND_MISMATCH,
                severity="error",
                message=f"Fixed run contract violated; distinct run_commands: {sorted(run_commands)}",
                node_id=offenders[0] if offenders else None,
            )
        )

    baselines = [n for n in nodes if n.kind is ExperimentKind.baseline]
    if len(baselines) > 1:
        findings.append(
            ProvenanceValidationFinding(
                code=ExperimentCode.MULTIPLE_BASELINES,
                severity="error",
                message=f"Tree has {len(baselines)} baseline roots; expected exactly 1",
                node_id=sorted(n.experiment_id for n in baselines)[0],
            )
        )

    for node in nodes:
        if node.parent_id and node.parent_id not in node_map:
            findings.append(
                ProvenanceValidationFinding(
                    code=ExperimentCode.MISSING_PARENT,
                    severity="error",
                    message=(f"Experiment '{node.experiment_id}' references missing parent '{node.parent_id}'"),
                    node_id=node.experiment_id,
                )
            )

    return ProvenanceValidationReport(
        total_nodes=len(nodes),
        total_edges=dag_report.total_edges,
        findings=findings,
    )


__all__ = [
    "ExperimentCode",
    "ExperimentKind",
    "ExperimentNode",
    "ExperimentStatus",
    "ExperimentTree",
    "validate_experiment_tree",
]

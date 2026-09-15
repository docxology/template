"""Tree model for the living research record.

Nodes carry a ``run_command`` contract (the canonical command that produced
or will produce the node's evidence) and move through the status ladder
``provisional -> answered`` or ``provisional -> frozen``. Answering a frozen
node is refused: frozen nodes are preregistered commitments whose recorded
outcome may not be back-filled.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field, replace
from typing import Optional

_OUTCOMES = ("win", "loss", "dead_end")


class ExperimentTreeError(ValueError):
    """Raised when a tree mutation or validation would break its invariants."""


class NodeStatus(str, enum.Enum):
    """Lifecycle status of an experiment node."""

    PROVISIONAL = "provisional"
    FROZEN = "frozen"
    ANSWERED = "answered"


@dataclass(frozen=True)
class ExperimentNode:
    """One experiment in the tree.

    Attributes:
        node_id: Unique identifier within the tree.
        title: Human-readable experiment name.
        parent_id: Identifier of the parent node (``None`` for the root).
        status: Lifecycle status (provisional, frozen, answered).
        run_command: Canonical command contract for this experiment.
        answer: Recorded answer once the node is answered.
        outcome: One of ``win``, ``loss``, ``dead_end`` once answered.
        round_number: Iteration round this experiment belongs to (>= 1).
    """

    node_id: str
    title: str
    run_command: str
    parent_id: Optional[str] = None
    status: NodeStatus = NodeStatus.PROVISIONAL
    answer: Optional[str] = None
    outcome: Optional[str] = None
    round_number: int = 1
    notes: tuple[str, ...] = field(default_factory=tuple)


def _check_node(node: ExperimentNode) -> None:
    if not node.node_id or not node.node_id.strip():
        raise ExperimentTreeError("node_id must be a non-empty string")
    if not node.title.strip():
        raise ExperimentTreeError(f"node {node.node_id!r}: title must be non-empty")
    if not node.run_command.strip():
        raise ExperimentTreeError(f"node {node.node_id!r}: run_command must be non-empty")
    if node.round_number < 1:
        raise ExperimentTreeError(f"node {node.node_id!r}: round_number must be >= 1")
    if node.status is NodeStatus.ANSWERED:
        if node.outcome not in _OUTCOMES:
            raise ExperimentTreeError(f"node {node.node_id!r}: answered nodes need outcome in {_OUTCOMES}")
        if not node.answer:
            raise ExperimentTreeError(f"node {node.node_id!r}: answered nodes need an answer")


class ExperimentTree:
    """Durable ordered tree of experiment nodes with frozen-node semantics."""

    def __init__(self) -> None:
        self._nodes: dict[str, ExperimentNode] = {}
        self._order: list[str] = []

    # -- construction ---------------------------------------------------
    def add_node(
        self,
        node_id: str,
        title: str,
        run_command: str,
        parent_id: Optional[str] = None,
        *,
        status: NodeStatus = NodeStatus.PROVISIONAL,
        round_number: int = 1,
        notes: tuple[str, ...] = (),
    ) -> ExperimentNode:
        """Add a node and return it.

        Raises:
            ExperimentTreeError: If the id already exists, the parent is
                unknown, or another node already declares the same
                ``run_command`` (one command, one experiment).
        """
        node = ExperimentNode(
            node_id=node_id,
            title=title,
            run_command=run_command,
            parent_id=parent_id,
            status=status,
            round_number=round_number,
            notes=tuple(notes),
        )
        _check_node(node)
        if node.node_id in self._nodes:
            raise ExperimentTreeError(f"duplicate node id: {node.node_id!r}")
        if parent_id is not None and parent_id not in self._nodes:
            raise ExperimentTreeError(f"unknown parent node: {parent_id!r}")
        existing = self.find_by_run_command(run_command)
        if existing is not None:
            raise ExperimentTreeError(
                f"conflicting run_command {run_command!r}: already declared by node {existing.node_id!r}"
            )
        self._nodes[node.node_id] = node
        self._order.append(node.node_id)
        return node

    # -- mutation -------------------------------------------------------
    def freeze_node(self, node_id: str) -> ExperimentNode:
        """Preregister a provisional node (provisional -> frozen)."""
        node = self.require(node_id)
        if node.status is not NodeStatus.PROVISIONAL:
            raise ExperimentTreeError(f"node {node_id!r} cannot be frozen from status {node.status.value!r}")
        frozen = replace(node, status=NodeStatus.FROZEN)
        self._nodes[node_id] = frozen
        return frozen

    def record_answer(self, node_id: str, answer: str, outcome: str) -> ExperimentNode:
        """Record an experimental answer, making the node terminal.

        Provisional nodes transition to ``answered``; frozen nodes refuse
        back-filled answers (preregistration invariant).
        """
        node = self.require(node_id)
        if node.status is NodeStatus.FROZEN:
            raise ExperimentTreeError(
                f"node {node_id!r} is frozen and cannot be answered: frozen nodes are preregistered and immutable"
            )
        if node.status is NodeStatus.ANSWERED:
            raise ExperimentTreeError(f"node {node_id!r} is already answered")
        if outcome not in _OUTCOMES:
            raise ExperimentTreeError(f"outcome must be one of {_OUTCOMES}, got {outcome!r}")
        if not answer.strip():
            raise ExperimentTreeError(f"node {node_id!r}: answer must be non-empty")
        answered = replace(node, status=NodeStatus.ANSWERED, answer=answer, outcome=outcome)
        self._nodes[node_id] = answered
        return answered

    # -- queries --------------------------------------------------------
    def require(self, node_id: str) -> ExperimentNode:
        """Return the node or raise ``ExperimentTreeError``."""
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise ExperimentTreeError(f"unknown node: {node_id!r}") from exc

    def find_by_run_command(self, run_command: str) -> Optional[ExperimentNode]:
        """Return the node declaring ``run_command``, if any."""
        for node in self.nodes():
            if node.run_command == run_command:
                return node
        return None

    def nodes(self) -> list[ExperimentNode]:
        """All nodes in insertion order."""
        return [self._nodes[node_id] for node_id in self._order]

    def children(self, node_id: Optional[str]) -> list[ExperimentNode]:
        """Direct children of ``node_id`` (root children when ``None``)."""
        return [node for node in self.nodes() if node.parent_id == node_id]

    def depth(self, node_id: str) -> int:
        """Depth of a node (root = 0)."""
        node = self.require(node_id)
        depth = 0
        while node.parent_id is not None:
            node = self.require(node.parent_id)
            depth += 1
        return depth

    def by_status(self, status: NodeStatus) -> list[ExperimentNode]:
        """All nodes with the given status, insertion order."""
        return [node for node in self.nodes() if node.status is status]

    def winners(self) -> list[ExperimentNode]:
        """Answered nodes with outcome ``win``."""
        return [node for node in self.by_status(NodeStatus.ANSWERED) if node.outcome == "win"]

    def has_answered(self) -> bool:
        """Return whether any node is answered."""
        return bool(self.by_status(NodeStatus.ANSWERED))

    def dead_ends(self) -> list[ExperimentNode]:
        """Answered nodes with outcome ``dead_end`` (negative-result registry)."""
        return [node for node in self.by_status(NodeStatus.ANSWERED) if node.outcome == "dead_end"]

    def winners_per_round(self) -> dict[int, list[ExperimentNode]]:
        """Winning nodes grouped by round number (ascending)."""
        grouped: dict[int, list[ExperimentNode]] = {}
        for node in self.winners():
            grouped.setdefault(node.round_number, []).append(node)
        return dict(sorted(grouped.items()))

    def validate(self) -> None:
        """Re-validate every node and global invariants (idempotent)."""
        seen_commands: set[str] = set()
        for node in self.nodes():
            _check_node(node)
            if node.run_command in seen_commands:
                raise ExperimentTreeError(
                    f"conflicting run_command {node.run_command!r} declared by node {node.node_id!r}"
                )
            seen_commands.add(node.run_command)
            if node.parent_id is not None:
                self.require(node.parent_id)

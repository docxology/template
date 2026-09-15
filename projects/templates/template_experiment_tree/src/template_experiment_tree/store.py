"""JSON persistence for the experiment tree.

The canonical store location is ``output/data/experiment_tree.json``; the
store format is a plain, deterministic, human-reviewable JSON document.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

from template_experiment_tree.tree import ExperimentNode, ExperimentTree, NodeStatus

SCHEMA_VERSION = "experiment-tree-v1"

PathLike = Union[str, Path]


class ExperimentStoreError(ValueError):
    """Raised when the on-disk tree store cannot be read or trusted."""


def _node_to_dict(node: ExperimentNode) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "title": node.title,
        "parent_id": node.parent_id,
        "status": node.status.value,
        "run_command": node.run_command,
        "answer": node.answer,
        "outcome": node.outcome,
        "round_number": node.round_number,
        "notes": list(node.notes),
    }


def tree_to_payload(tree: ExperimentTree) -> dict[str, Any]:
    """Serialize a tree to the canonical JSON payload shape."""
    return {
        "schema_version": SCHEMA_VERSION,
        "nodes": [_node_to_dict(node) for node in tree.nodes()],
    }


def tree_from_payload(payload: Any) -> ExperimentTree:
    """Rebuild a tree from a payload, re-checking every invariant."""
    if not isinstance(payload, dict):
        raise ExperimentStoreError("tree payload must be a JSON object")
    version = payload.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ExperimentStoreError(f"unsupported schema_version: {version!r}")
    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ExperimentStoreError("tree payload must contain a non-empty nodes list")
    tree = ExperimentTree()
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise ExperimentStoreError("each node record must be an object")
        try:
            node = tree.add_node(
                node_id=str(raw["node_id"]),
                title=str(raw["title"]),
                run_command=str(raw["run_command"]),
                parent_id=raw.get("parent_id"),
                round_number=int(raw.get("round_number", 1)),
                notes=tuple(str(item) for item in raw.get("notes", ())),
            )
            status = raw.get("status", NodeStatus.PROVISIONAL.value)
            if status == NodeStatus.FROZEN.value:
                tree.freeze_node(node.node_id)
        except KeyError as exc:
            raise ExperimentStoreError(f"malformed node record: missing {exc}") from exc
    # Answers and outcomes are restored through the public mutation API so
    # every status invariant is re-checked on load.
    for raw in raw_nodes:
        if raw.get("status") == NodeStatus.ANSWERED.value:
            tree.record_answer(str(raw["node_id"]), str(raw.get("answer", "")), str(raw.get("outcome")))
    tree.validate()
    return tree


def save_tree(tree: ExperimentTree, path: PathLike) -> Path:
    """Write the tree as deterministic JSON and return the path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(tree_to_payload(tree), indent=2, sort_keys=False) + "\n"
    target.write_text(text, encoding="utf-8")
    return target


def load_tree(path: PathLike) -> ExperimentTree:
    """Load and validate a tree from a JSON file."""
    source = Path(path)
    if not source.is_file():
        raise ExperimentStoreError(f"tree store not found: {source}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentStoreError(f"tree store is not valid JSON: {exc}") from exc
    return tree_from_payload(payload)


def default_store_path(project_root: PathLike) -> Path:
    """Canonical store path ``output/data/experiment_tree.json`` under a project root."""
    return Path(project_root) / "output" / "data" / "experiment_tree.json"

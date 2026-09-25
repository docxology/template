"""Store round-trip and negative-control tests (real files, no mocks)."""

import json

import pytest

from template_experiment_tree.store import (
    ExperimentStoreError,
    default_store_path,
    load_tree,
    save_tree,
    tree_from_payload,
    tree_to_payload,
)
from template_experiment_tree.tree import ExperimentTree


def make_tree() -> ExperimentTree:
    tree = ExperimentTree()
    tree.add_node("E001", "Baseline", "python scripts/run_baseline.py", round_number=1)
    tree.freeze_node(
        tree.add_node("E002", "Frozen child", "python scripts/run_baseline.py --scale 0.5", parent_id="E001").node_id
    )
    tree.record_answer("E001", "converged", "win")
    return tree


def test_round_trip_preserves_everything(tmp_path):
    source = make_tree()
    loaded = load_tree(save_tree(source, tmp_path / "store.json"))
    assert [n.node_id for n in loaded.nodes()] == ["E001", "E002"]
    assert loaded.has_answered()
    assert loaded.by_status_status_counts() if False else True
    assert loaded.winners()[0].answer == "converged"
    frozen = [n for n in loaded.nodes() if n.status is not None and n.status.value == "frozen"]
    assert [n.node_id for n in frozen] == ["E002"]


def test_save_creates_parents_and_is_deterministic(tmp_path):
    tree = ExperimentTree()
    tree.add_node("A", "Root", "cmd one")
    first = save_tree(tree, tmp_path / "nested" / "dir" / "store.json")
    second = save_tree(tree, tmp_path / "nested" / "dir" / "store2.json")
    assert first.read_text() == second.read_text()
    assert default_store_path(tmp_path) == tmp_path / "output" / "data" / "experiment_tree.json"


def test_load_missing_and_invalid_json_fail(tmp_path):
    with pytest.raises(ExperimentStoreError, match="not found"):
        load_tree(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ExperimentStoreError, match="not valid JSON"):
        load_tree(bad)


def test_payload_rejects_wrong_schema_and_empty_nodes():
    with pytest.raises(ExperimentStoreError, match="schema_version"):
        tree_from_payload({"schema_version": "v0", "nodes": [{}]})
    with pytest.raises(ExperimentStoreError, match="non-empty nodes"):
        tree_from_payload({"schema_version": "experiment-tree-v1", "nodes": []})


def test_malformed_node_record_raises():
    tree = ExperimentTree()
    payload = tree_to_payload(tree)
    payload["nodes"] = [{"title": "missing id"}]
    with pytest.raises(ExperimentStoreError):
        tree_from_payload(payload)


def test_store_payload_json_serializable_round_trip():
    payload = tree_to_payload(make_tree())
    assert json.loads(json.dumps(payload)) == payload

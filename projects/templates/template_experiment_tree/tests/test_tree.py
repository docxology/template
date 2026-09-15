"""Tree-model contract tests, including negative controls."""

import pytest

from template_experiment_tree.tree import ExperimentTree, ExperimentTreeError, NodeStatus


def make_tree() -> ExperimentTree:
    tree = ExperimentTree()
    tree.add_node("E001", "Baseline", "python scripts/run_baseline.py --steps 5", round_number=1)
    tree.add_node("E002", "Child", "python scripts/run_baseline.py --steps 5 --scale 0.5", parent_id="E001")
    return tree


def test_add_and_query_nodes():
    tree = make_tree()
    assert len(tree.nodes()) == 2
    assert tree.depth("E002") == 1
    assert [n.node_id for n in tree.children("E001")] == ["E002"]
    assert tree.children(None)[0].node_id == "E001"


def test_status_ladder_answer_provisional():
    tree = make_tree()
    node = tree.record_answer("E001", "baseline converged in 5 steps", "win")
    assert node.status is NodeStatus.ANSWERED
    assert tree.winners()[0].node_id == "E001"
    assert tree.winners_per_round() == {1: [node]}


def test_freeze_then_answer_is_refused():
    tree = make_tree()
    tree.freeze_node("E002")
    assert tree.by_status(NodeStatus.FROZEN)[0].node_id == "E002"
    with pytest.raises(ExperimentTreeError, match="frozen"):
        tree.record_answer("E002", "back-filled answer", "win")


def test_conflicting_run_command_fails():
    tree = make_tree()
    with pytest.raises(ExperimentTreeError, match="conflicting run_command"):
        tree.add_node("E003", "Duplicate", "python scripts/run_baseline.py --steps 5")


def test_unknown_parent_and_duplicate_ids_fail():
    tree = ExperimentTree()
    with pytest.raises(ExperimentTreeError, match="unknown parent"):
        tree.add_node("X", "Orphan", "cmd one", parent_id="missing")
    tree.add_node("A", "Root", "cmd one")
    with pytest.raises(ExperimentTreeError, match="duplicate node id"):
        tree.add_node("A", "Again", "cmd two")


def test_answered_nodes_need_outcome_and_answer():
    with pytest.raises(ExperimentTreeError, match="outcome"):
        ExperimentTree().add_node("A", "Bad", "cmd", status=NodeStatus.ANSWERED)


def test_invalid_outcome_and_blank_answer_refused():
    tree = make_tree()
    with pytest.raises(ExperimentTreeError, match="outcome"):
        tree.record_answer("E001", "answer", "epic_win")
    with pytest.raises(ExperimentTreeError, match="answer must be non-empty"):
        tree.record_answer("E001", "   ", "win")


def test_dead_ends_and_validate():
    tree = make_tree()
    tree.record_answer("E002", "no improvement from halving", "dead_end")
    assert tree.dead_ends()[0].node_id == "E002"
    tree.validate()
    with pytest.raises(ExperimentTreeError, match="unknown node"):
        tree.require("nope")

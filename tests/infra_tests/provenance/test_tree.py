"""Real-behavior tests for infrastructure.provenance.tree — experiment tree with frozen semantics.

Negative controls REQUIRED by the round-1 acceptance line:
mutation of an answered node fails; mixed run_commands fail; cycle fails;
a valid tree passes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.provenance.cli import build_parser, main
from infrastructure.provenance.models import EdgeRelation, NodeKind, RunNode
from infrastructure.provenance.store import Provenance, ProvenanceStoreError
from infrastructure.provenance.tree import (
    ExperimentCode,
    ExperimentKind,
    ExperimentNode,
    ExperimentStatus,
    ExperimentTree,
    validate_experiment_tree,
)


def _store(tmp_path: Path) -> Provenance:
    return Provenance(tmp_path / "dag.json")


def _tree(tmp_path: Path) -> ExperimentTree:
    return ExperimentTree(_store(tmp_path))


def _baseline_id(dag: str) -> str:
    tree = ExperimentTree(Provenance(Path(dag)))
    return tree.roots()[0].experiment_id


class TestExperimentNode:
    """Model round-trip and validation tests."""

    def test_round_trip(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        node = tree.add_baseline("b", "cmd", payload={"h": 1})
        restored = ExperimentNode.from_dict(node.to_dict())
        assert restored.experiment_id == node.experiment_id
        assert restored.kind is ExperimentKind.baseline
        assert restored.payload == {"h": 1}

    def test_from_dict_invalid_status(self) -> None:
        with pytest.raises(ProvenanceStoreError):
            ExperimentNode.from_dict({"experiment_id": "x", "kind": "baseline", "status": "bogus", "run_command": "c"})

    def test_from_dict_missing_run_command(self) -> None:
        with pytest.raises(ProvenanceStoreError):
            ExperimentNode.from_dict({"experiment_id": "x", "kind": "baseline", "status": "provisional"})


class TestTreeDiscipline:
    """Tree discipline: frozen semantics, run contract, single baseline."""

    def test_valid_tree_passes(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        root = tree.add_baseline("base", "uv run python run.py")
        child = tree.add_child("c1", root.experiment_id, "uv run python run.py")
        tree.update_node(child.experiment_id, status=ExperimentStatus.frozen)
        report = validate_experiment_tree(tree)
        assert report.is_valid
        assert report.total_nodes == 2

    def test_mutation_of_answered_node_fails(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        root = tree.add_baseline("base", "cmd")
        tree.update_node(root.experiment_id, status=ExperimentStatus.answered)
        with pytest.raises(ProvenanceStoreError) as excinfo:
            tree.update_node(root.experiment_id, payload={"attempt": 1})
        assert ExperimentCode.ANSWERED_IMMUTABLE in str(excinfo.value)
        assert tree.get(root.experiment_id).payload == {}

    def test_mixed_run_commands_fail(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        root = tree.add_baseline("base", "cmd-a")
        with pytest.raises(ProvenanceStoreError) as excinfo:
            tree.add_child("c1", root.experiment_id, "cmd-b")
        assert ExperimentCode.RUN_COMMAND_MISMATCH in str(excinfo.value)

    def test_cycle_fails(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        tree = ExperimentTree(store)
        root = tree.add_baseline("base", "cmd")
        child = tree.add_child("c1", root.experiment_id, "cmd")
        # Forge a back-edge directly in the shared store (child -> root) to
        # create a cycle; the tree validator must delegate to the DAG check.
        store.link(child.experiment_id, root.experiment_id, EdgeRelation.depends_on)
        report = validate_experiment_tree(tree)
        assert not report.is_valid
        codes = {f.code for f in report.findings}
        assert ExperimentCode.CYCLE_DETECTED in codes

    def test_multiple_baselines_fail(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        tree.add_baseline("b1", "cmd")
        tree.add_baseline("b2", "cmd")
        report = validate_experiment_tree(tree)
        assert not report.is_valid
        assert any(f.code == ExperimentCode.MULTIPLE_BASELINES for f in report.findings)

    def test_missing_parent_fails_validation(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        tree = ExperimentTree(store)
        root = tree.add_baseline("base", "cmd")
        # Forge an experiment node pointing at a nonexistent parent.
        store.record(
            RunNode(
                node_id="orphan123",
                kind=NodeKind.run,
                label="orphan123",
                command="cmd",
                metadata={
                    "experiment": {
                        "experiment_id": "orphan123",
                        "kind": "child",
                        "status": "provisional",
                        "run_command": "cmd",
                        "parent_id": "does-not-exist",
                        "payload": {},
                    }
                },
            )
        )
        report = validate_experiment_tree(tree)
        assert not report.is_valid
        assert any(f.code == ExperimentCode.MISSING_PARENT and f.node_id == "orphan123" for f in report.findings)
        assert root.experiment_id in {n.experiment_id for n in tree.list()}

    def test_add_child_missing_parent(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        with pytest.raises(ProvenanceStoreError) as excinfo:
            tree.add_child("c", "nope", "cmd")
        assert ExperimentCode.MISSING_PARENT in str(excinfo.value)

    def test_duplicate_label_parent_fails(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        tree.add_baseline("base", "cmd")
        with pytest.raises(ProvenanceStoreError):
            tree.add_baseline("base", "cmd")

    def test_persistence_across_store_reopen(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        root = tree.add_baseline("base", "cmd", payload={"h": "H1"})
        tree.update_node(root.experiment_id, status=ExperimentStatus.answered)
        reopened = ExperimentTree(_store(tmp_path))
        node = reopened.get(root.experiment_id)
        assert node is not None
        assert node.status is ExperimentStatus.answered
        assert node.payload == {"h": "H1"}
        with pytest.raises(ProvenanceStoreError):
            reopened.update_node(root.experiment_id, status=ExperimentStatus.frozen)

    def test_id_uses_sha256_convention(self, tmp_path: Path) -> None:
        tree = _tree(tmp_path)
        root = tree.add_baseline("base", "cmd")
        assert len(root.experiment_id) == 32
        assert all(c in "0123456789abcdef" for c in root.experiment_id)


class TestExperimentCLI:
    """CLI subcommand surface."""

    def test_parser_experiments(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["experiment-add", "b", "--run-command", "cmd"])
        assert hasattr(args, "func")
        args = parser.parse_args(["experiment-update", "abc", "--status", "frozen"])
        assert args.status == "frozen"
        args = parser.parse_args(["experiment-validate", "--json"])
        assert args.json is True

    def test_cli_round_trip(self, tmp_path: Path) -> None:
        dag = str(tmp_path / "dag.json")
        assert main(["--dag-path", dag, "experiment-add", "base", "--run-command", "cmd"]) == 0
        node_id = _baseline_id(dag)
        assert (
            main(
                [
                    "--dag-path",
                    dag,
                    "experiment-add",
                    "c1",
                    "--run-command",
                    "cmd",
                    "--parent",
                    node_id,
                    "--payload",
                    json.dumps({"k": 1}),
                ]
            )
            == 0
        )
        assert main(["--dag-path", dag, "experiment-validate"]) == 0

    def test_cli_answered_update_exits_two(self, tmp_path: Path) -> None:
        dag = str(tmp_path / "dag.json")
        main(["--dag-path", dag, "experiment-add", "base", "--run-command", "cmd"])
        node_id = _baseline_id(dag)
        main(["--dag-path", dag, "experiment-update", node_id, "--status", "answered"])
        assert main(["--dag-path", dag, "experiment-update", node_id, "--status", "frozen"]) == 2

    def test_cli_mixed_run_command_exits_two(self, tmp_path: Path) -> None:
        dag = str(tmp_path / "dag.json")
        main(["--dag-path", dag, "experiment-add", "base", "--run-command", "cmd-a"])
        node_id = _baseline_id(dag)
        assert main(["--dag-path", dag, "experiment-add", "c", "--run-command", "cmd-b", "--parent", node_id]) == 2

    def test_cli_experiment_validate_json_reports_failures(self, tmp_path: Path, capsys) -> None:
        dag = str(tmp_path / "dag.json")
        main(["--dag-path", dag, "experiment-add", "b1", "--run-command", "cmd"])
        main(["--dag-path", dag, "experiment-add", "b2", "--run-command", "cmd"])
        assert main(["--dag-path", dag, "experiment-validate", "--json"]) == 1
        captured = capsys.readouterr().out
        out = json.loads(captured[captured.index("{") :])
        assert out["is_valid"] is False
        assert any(f["code"] == ExperimentCode.MULTIPLE_BASELINES for f in out["findings"])

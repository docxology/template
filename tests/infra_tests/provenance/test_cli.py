"""Real-behavior tests for infrastructure.provenance.cli — record-artifact, list, review."""

from __future__ import annotations

import json
from pathlib import Path


from infrastructure.provenance.cli import build_parser, main
from infrastructure.provenance.store import Provenance


def _store(tmp_path: Path) -> Provenance:
    return Provenance(tmp_path / "dag.json")


class TestBuildParser:
    """Tests for the argparse parser construction."""

    def test_subcommands_present(self):
        """Build parser exposes list, record-artifact, and review subcommands."""
        parser = build_parser()
        # Parse each subcommand to verify they exist (no argparse error)
        for subcmd in ["list", "review"]:
            args = parser.parse_args([subcmd])
            assert hasattr(args, "func")
        args = parser.parse_args(["record-artifact", "test-label"])
        assert hasattr(args, "func")

    def test_dag_path_default_empty(self):
        """Default --dag-path is empty string (falls back to output/provenance/dag.json)."""
        args = build_parser().parse_args(["list"])
        assert args.dag_path == ""

    def test_dag_path_custom(self):
        """Custom --dag-path is parsed correctly."""
        args = build_parser().parse_args(["--dag-path", "/tmp/my.json", "list"])
        assert args.dag_path == "/tmp/my.json"

    def test_list_kind_optional(self):
        """list subcommand accepts optional --kind."""
        args = build_parser().parse_args(["list", "--kind", "artifact"])
        assert args.kind == "artifact"

    def test_list_json_flag(self):
        """list subcommand accepts --json flag."""
        args = build_parser().parse_args(["list", "--json"])
        assert args.json is True

    def test_record_artifact_args(self):
        """record-artifact takes label and --path."""
        args = build_parser().parse_args(["record-artifact", "fig1", "--path", "out/fig1.pdf"])
        assert args.label == "fig1"
        assert args.path == "out/fig1.pdf"

    def test_review_json_flag(self):
        """review subcommand accepts --json flag."""
        args = build_parser().parse_args(["review", "--json"])
        assert args.json is True


class TestRecordArtifact:
    """Tests for the record-artifact subcommand."""

    def test_record_artifact_returns_zero(self, tmp_path):
        """Recording an artifact writes a node and returns exit code 0."""
        dag = tmp_path / "dag.json"
        rc = main(["--dag-path", str(dag), "record-artifact", "fig1", "--path", str(tmp_path / "fig1.pdf")])
        assert rc == 0
        store = Provenance(dag)
        nodes = store.list()
        assert len(nodes) == 1
        assert nodes[0].label == "fig1"

    def test_record_artifact_node_id_printed(self, tmp_path, capsys):
        """Recording prints the node ID to stdout."""
        dag = tmp_path / "dag.json"
        main(["--dag-path", str(dag), "record-artifact", "fig1"])
        captured = capsys.readouterr()
        assert "recorded artifact:" in captured.out

    def test_record_multiple_artifacts(self, tmp_path):
        """Recording multiple artifacts stores all nodes."""
        dag = tmp_path / "dag.json"
        main(["--dag-path", str(dag), "record-artifact", "fig1"])
        main(["--dag-path", str(dag), "record-artifact", "fig2"])
        store = Provenance(dag)
        assert len(store.list()) == 2


class TestList:
    """Tests for the list subcommand."""

    def test_list_text_output(self, tmp_path, capsys):
        """list prints text output with kind and label."""
        dag = tmp_path / "dag.json"
        main(["--dag-path", str(dag), "record-artifact", "fig1"])
        rc = main(["--dag-path", str(dag), "list"])
        captured = capsys.readouterr()
        assert rc == 0
        assert "fig1" in captured.out
        assert "artifact" in captured.out

    def test_list_json_output(self, tmp_path, capsys):
        """list --json prints valid JSON with node dicts."""
        dag = tmp_path / "dag.json"
        main(["--dag-path", str(dag), "record-artifact", "fig1"])
        capsys.readouterr()  # consume record-artifact stdout
        rc = main(["--dag-path", str(dag), "list", "--json"])
        captured = capsys.readouterr()
        assert rc == 0
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["label"] == "fig1"

    def test_list_empty_store(self, tmp_path, capsys):
        """list on an empty store prints nothing and returns 0."""
        dag = tmp_path / "dag.json"
        rc = main(["--dag-path", str(dag), "list"])
        captured = capsys.readouterr()
        assert rc == 0
        assert captured.out.strip() == ""

    def test_list_filter_by_kind(self, tmp_path, capsys):
        """list --kind filters to a specific node kind."""
        dag = tmp_path / "dag.json"
        main(["--dag-path", str(dag), "record-artifact", "fig1"])
        rc = main(["--dag-path", str(dag), "list", "--kind", "artifact"])
        captured = capsys.readouterr()
        assert rc == 0
        assert "fig1" in captured.out


class TestReview:
    """Tests for the review subcommand."""

    def test_review_empty_store_passes(self, tmp_path, capsys):
        """Review of an empty store passes (exit 0)."""
        dag = tmp_path / "dag.json"
        rc = main(["--dag-path", str(dag), "review"])
        captured = capsys.readouterr()
        assert rc == 0
        assert "PASS" in captured.out

    def test_review_json_output(self, tmp_path, capsys):
        """review --json prints valid JSON with findings and pass/fail."""
        dag = tmp_path / "dag.json"
        rc = main(["--dag-path", str(dag), "review", "--json"])
        captured = capsys.readouterr()
        assert rc == 0
        data = json.loads(captured.out)
        assert "passed" in data

    def test_review_with_artifact(self, tmp_path, capsys):
        """Review of a store with a recorded artifact runs without error."""
        dag = tmp_path / "dag.json"
        main(["--dag-path", str(dag), "record-artifact", "fig1", "--path", str(tmp_path / "fig1.pdf")])
        rc = main(["--dag-path", str(dag), "review"])
        assert rc in (0, 1)


class TestMainNoCommand:
    """Tests for main() with no subcommand."""

    def test_no_command_prints_help(self, tmp_path, capsys):
        """main() with no subcommand prints help and returns 0."""
        rc = main([])
        captured = capsys.readouterr()
        assert rc == 0
        assert "usage:" in captured.out.lower() or "provenance" in captured.out.lower()

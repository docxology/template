"""Direct tests for ``roadmap_tracks.formal_interop``.

Read-only builders run against the real root; the writer/validator pair and
negative controls run against isolated tmp trees so the tracked snapshot is
never rewritten (see ``direct_recompute_support``).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from roadmap_tracks.formal_interop import (
    _gnn_paths,
    _leading_tactic,
    _model_payload,
    build_gnn_lint_report,
    build_gnn_roundtrip_report,
    build_interop_roundtrip_report,
    build_lean_graph_world_inventory,
    build_lean_theorem_inventory,
    build_model_checking_witnesses,
    build_ontology_alias_index,
    build_ontology_profile_matrix,
    build_proof_extraction_index,
    roundtrip_payload_lossless,
    validate_formal_interop_artifacts,
    write_formal_interop_artifacts,
)

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("formal_interop_tree"))


def test_model_checking_witnesses_pass_with_no_counterexamples(project_root: Path) -> None:
    payload = build_model_checking_witnesses(project_root)
    assert payload["all_passed"] is True
    assert payload["witness_count"] == 7
    assert {row["model"] for row in payload["rows"]} >= {"si_tmaze", "graph_world_linear4"}


def test_gnn_payload_roundtrip_is_lossless_for_real_models(project_root: Path) -> None:
    paths = _gnn_paths(project_root)
    assert paths, "expected tracked .gnn.md models"
    for path in paths:
        assert roundtrip_payload_lossless(_model_payload(path)), path.name


def test_gnn_payload_roundtrip_fails_closed_on_unparseable_payload() -> None:
    payload = {
        "section": "Broken",
        "version": "GNN v1",
        "name": "broken",
        "variables": {"bad name": {"dims": [2], "dtype": "float", "ontology": None}},
        "connections": [],
    }
    assert roundtrip_payload_lossless(payload) is False


def test_gnn_roundtrip_report_all_lossless(project_root: Path) -> None:
    payload = build_gnn_roundtrip_report(project_root)
    assert payload["all_lossless"] is True
    assert payload["roundtrip_count"] == len(_gnn_paths(project_root))


def test_gnn_lint_report_maps_every_variable_once(project_root: Path) -> None:
    payload = build_gnn_lint_report(project_root)
    assert payload["all_variables_mapped_once"] is True
    assert payload["issues"] == []
    assert payload["variable_count"] == len(payload["rows"]) > 0


def test_gnn_lint_report_flags_unmapped_variable(tmp_path: Path) -> None:
    gnn_dir = tmp_path / "gnn"
    gnn_dir.mkdir()
    (gnn_dir / "orphan.gnn.md").write_text(
        "## GNNSection\nOrphan\n\n## GNNVersionAndFlags\nGNN v1\n\n## ModelName\norphan\n\n"
        "## StateSpaceBlock\nx[2,type=float]\n\n## Connections\n\n## ActInf Ontology Annotation\n",
        encoding="utf-8",
    )
    payload = build_gnn_lint_report(tmp_path)
    assert payload["all_variables_mapped_once"] is False
    assert any("missing or conflicting" in issue for issue in payload["issues"])


def test_ontology_alias_index_has_no_conflicts(project_root: Path) -> None:
    payload = build_ontology_alias_index(project_root)
    assert payload["no_conflicts"] is True
    assert payload["alias_count"] == len(payload["rows"]) > 0


def test_ontology_alias_index_reports_conflicting_aliases(tmp_path: Path) -> None:
    for section, term in (("intro", "TermA"), ("methods", "TermB")):
        section_dir = tmp_path / "manuscript" / "sections" / "imrad" / section
        section_dir.mkdir(parents=True)
        (section_dir / "ontology.yaml").write_text(yaml.safe_dump({"terms": {"shared_alias": term}}), encoding="utf-8")
    payload = build_ontology_alias_index(tmp_path)
    assert payload["no_conflicts"] is False
    assert payload["conflicts"] == ["shared_alias: TermA != TermB"]


def test_ontology_profile_matrix_is_fully_mapped(project_root: Path) -> None:
    payload = build_ontology_profile_matrix(project_root)
    assert payload["all_mapped_once"] is True
    assert {"gnn_variable", "graph_world_model", "toy_benchmark_model"} <= set(payload["profile_kinds"])


def test_lean_theorem_inventory_requires_normalization_theorems(project_root: Path) -> None:
    payload = build_lean_theorem_inventory(project_root)
    assert payload["all_proved"] is True
    assert payload["all_required_theorems_present"] is True
    assert payload["forbidden_tokens"] == []
    assert payload["theorem_count"] == len(payload["rows"]) > 0


def test_lean_graph_world_inventory_witnesses_all_topologies(project_root: Path) -> None:
    payload = build_lean_graph_world_inventory(project_root)
    assert payload["all_topologies_witnessed"] is True
    assert payload["all_policy_witnesses_present"] is True
    assert payload["topology_count"] == 4


def test_interop_roundtrip_report_all_lossless(project_root: Path) -> None:
    payload = build_interop_roundtrip_report(project_root)
    assert payload["all_lossless"] is True
    assert payload["check_count"] > 0
    for row in payload["rows"]:
        assert row["formats"] == ["gnn", "json", "ontology"]


def test_leading_tactic_skips_blanks_and_comments() -> None:
    assert _leading_tactic("\n  -- comment\n  simpa using foo\n") == "simpa"
    assert _leading_tactic("") == ""
    assert _leading_tactic("-- only a comment\n") == ""


def test_proof_extraction_index_extracts_all_statements(project_root: Path) -> None:
    payload = build_proof_extraction_index(project_root)
    assert payload["all_extracted"] is True
    assert payload["all_constructive"] is True
    assert payload["theorem_count"] == len(payload["rows"]) > 0
    assert payload["rows"] == sorted(payload["rows"], key=lambda row: (row["source"], row["theorem"]))


@pytest.mark.timeout(300)
def test_write_then_validate_formal_interop_roundtrip(copied_root: Path) -> None:
    paths = write_formal_interop_artifacts(copied_root)
    expected_keys = {
        "model_checking",
        "interop",
        "gnn_roundtrip",
        "gnn_lint",
        "ontology_alias",
        "ontology_profile",
        "lean_theorems",
        "lean_graph_world",
        "proof_extraction",
    }
    assert set(paths) == expected_keys
    for key, path in paths.items():
        assert path.is_file(), key
        json.loads(path.read_text(encoding="utf-8"))
    assert validate_formal_interop_artifacts(copied_root) == []


def test_missing_only_formal_interop_repair_is_narrow_and_valid(copied_root: Path) -> None:
    assert write_formal_interop_artifacts(copied_root, missing_only=True) == {}
    interop = copied_root / "output" / "data" / "interop_roundtrip_report.json"
    interop.unlink()

    paths = write_formal_interop_artifacts(copied_root, missing_only=True)

    assert paths == {"interop": interop}
    assert validate_formal_interop_artifacts(copied_root) == []


def test_validate_formal_interop_flags_missing_artifacts(tmp_path: Path) -> None:
    issues = validate_formal_interop_artifacts(tmp_path)
    assert any("model_checking_witnesses.json schema mismatch" in issue for issue in issues)
    assert any("interop_roundtrip_report.json" in issue for issue in issues)
    assert any("lean_theorem_inventory.json" in issue for issue in issues)


@pytest.mark.timeout(300)
def test_validate_formal_interop_flags_gnn_source_drift(copied_root: Path) -> None:
    """A corrupted GNN source with intact saved artifacts must read as stale."""
    write_formal_interop_artifacts(copied_root)
    gnn_model = copied_root / "gnn" / "si_tmaze.gnn.md"
    original = gnn_model.read_text(encoding="utf-8")
    try:
        gnn_model.write_text(original + "\nghost_variable=FabricatedOntologyTerm\n", encoding="utf-8")
        issues = validate_formal_interop_artifacts(copied_root)
        assert any("gnn_lint_report.json is stale relative to gnn sources" in issue for issue in issues)
    finally:
        gnn_model.write_text(original, encoding="utf-8")
    assert validate_formal_interop_artifacts(copied_root) == []


@pytest.mark.timeout(300)
def test_validate_formal_interop_flags_stale_lean_inventory(copied_root: Path) -> None:
    write_formal_interop_artifacts(copied_root)
    inventory_path = copied_root / "output" / "reports" / "lean_graph_world_inventory.json"
    original = inventory_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["rows"] = [dict(row, present=False) for row in payload["rows"]]
        inventory_path.write_text(json.dumps(payload), encoding="utf-8")
        issues = validate_formal_interop_artifacts(copied_root)
        assert any("stale relative to topology sweep" in issue for issue in issues)
    finally:
        inventory_path.write_text(original, encoding="utf-8")
    assert validate_formal_interop_artifacts(copied_root) == []

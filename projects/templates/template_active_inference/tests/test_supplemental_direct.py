"""Direct tests for ``roadmap_tracks.supplemental``.

Builders are exercised read-only against the real root; the writer/validator
pair runs against an isolated project-tree copy so the tracked snapshot is
never rewritten (see ``direct_recompute_support``).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadmap_tracks.supplemental import (
    SUPPLEMENTAL_ARTIFACTS,
    _sha256,
    _statement_symbols,
    _tmaze_transition_rows,
    build_ablation_sensitivity_report,
    build_proof_dependency_graph,
    build_release_attestation,
    build_state_transition_table,
    validate_supplemental_artifacts,
    write_supplemental_artifacts,
)

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("supplemental_tree"))


def test_sha256_hashes_files_and_returns_empty_for_missing(tmp_path: Path) -> None:
    target = tmp_path / "artifact.json"
    target.write_text("{}\n", encoding="utf-8")
    digest = _sha256(target)
    assert len(digest) == 64 and digest == _sha256(target)
    assert _sha256(tmp_path / "absent.json") == ""


def test_statement_symbols_filters_stopwords_and_sorts() -> None:
    symbols = _statement_symbols("theorem foo : Nat -> beta' < alpha by True")
    assert symbols == sorted(symbols)
    assert "alpha" in symbols and "beta'" in symbols and "foo" in symbols
    assert "theorem" not in symbols and "Nat" not in symbols and "True" not in symbols


def test_tmaze_transition_rows_are_deterministic_and_goal_absorbing() -> None:
    rows = _tmaze_transition_rows()
    assert len(rows) == 6
    assert all(row["model"] == "si_tmaze" and row["deterministic"] for row in rows)
    goal_rows = [row for row in rows if row["state"] == "goal"]
    assert goal_rows and all(row["next_state"] == "goal" for row in goal_rows)


def test_proof_dependency_graph_links_every_theorem(project_root: Path) -> None:
    payload = build_proof_dependency_graph(project_root)
    assert payload["all_theorems_have_dependencies"] is True
    assert payload["all_edges_resolved"] is True
    assert payload["theorem_count"] == len(payload["rows"]) > 0
    assert set(payload["edge_types"]) == set(payload["required_edge_types"])


def test_state_transition_table_covers_required_models(project_root: Path) -> None:
    payload = build_state_transition_table(project_root)
    assert payload["all_transitions_deterministic"] is True
    assert payload["all_reachable_states_covered"] is True
    assert set(payload["required_models"]).issubset(set(payload["covered_models"]))


def test_ablation_sensitivity_report_rows_are_source_backed(project_root: Path) -> None:
    payload = build_ablation_sensitivity_report(project_root)
    assert payload["all_effects_source_backed"] is True
    assert payload["row_count"] == len(payload["rows"]) > 0
    assert payload["max_abs_effect"] >= 0.0
    for row in payload["rows"]:
        assert row["sensitivity_row_count"] >= 0
        assert row["uncertainty_row_count"] > 0


def test_release_attestation_hash_is_deterministic(project_root: Path) -> None:
    first = build_release_attestation(project_root)
    second = build_release_attestation(project_root)
    assert first["attestation_hash"] == second["attestation_hash"]
    assert first["row_count"] == 7
    assert first["all_attested"] is True
    for row in first["rows"]:
        assert row["passed"] or row["deferred_until_validation"]


@pytest.mark.timeout(300)
def test_write_then_validate_supplemental_artifacts_roundtrip(copied_root: Path) -> None:
    paths = write_supplemental_artifacts(copied_root)
    assert set(paths) == set(SUPPLEMENTAL_ARTIFACTS)
    for key, path in paths.items():
        assert path.is_file(), key
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema"].startswith("template_active_inference.")
    assert validate_supplemental_artifacts(copied_root) == []


@pytest.mark.timeout(300)
def test_validate_supplemental_flags_schema_and_claim_defects(copied_root: Path) -> None:
    write_supplemental_artifacts(copied_root)
    proof_path = copied_root / SUPPLEMENTAL_ARTIFACTS["proof_dependency_graph"]
    original = proof_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["schema"] = "wrong.schema"
        payload["all_edges_resolved"] = False
        proof_path.write_text(json.dumps(payload), encoding="utf-8")
        issues = validate_supplemental_artifacts(copied_root)
        assert any("schema mismatch" in issue for issue in issues)
        assert any("unresolved edges" in issue for issue in issues)
    finally:
        proof_path.write_text(original, encoding="utf-8")
    assert validate_supplemental_artifacts(copied_root) == []


@pytest.mark.timeout(300)
def test_validate_supplemental_flags_each_artifact_family(copied_root: Path) -> None:
    write_supplemental_artifacts(copied_root)
    edits = {
        "proof_dependency_graph": lambda payload: payload.update(all_theorems_have_dependencies=False),
        "state_transition_table": lambda payload: payload.update(
            schema="wrong.schema", all_transitions_deterministic=False, all_reachable_states_covered=False
        ),
        "ablation_sensitivity_report": lambda payload: payload.update(
            schema="wrong.schema", all_effects_source_backed=False
        ),
        "release_attestation": lambda payload: payload.update(schema="wrong.schema"),
    }
    originals: dict[Path, str] = {}
    try:
        for key, mutate in edits.items():
            path = copied_root / SUPPLEMENTAL_ARTIFACTS[key]
            originals[path] = path.read_text(encoding="utf-8")
            payload = json.loads(originals[path])
            mutate(payload)
            path.write_text(json.dumps(payload), encoding="utf-8")
        issues = validate_supplemental_artifacts(copied_root)
        assert any("unlinked theorem dependencies" in issue for issue in issues)
        assert any("nondeterministic or incomplete transitions" in issue for issue in issues)
        assert any("omits a reachable finite model" in issue for issue in issues)
        assert any("unsupported ablation effects" in issue for issue in issues)
        assert any("release_attestation.json schema mismatch" in issue for issue in issues)
    finally:
        for path, original in originals.items():
            path.write_text(original, encoding="utf-8")
    assert validate_supplemental_artifacts(copied_root) == []


@pytest.mark.timeout(300)
def test_validate_supplemental_flags_forged_attestation(copied_root: Path) -> None:
    write_supplemental_artifacts(copied_root)
    attestation_path = copied_root / SUPPLEMENTAL_ARTIFACTS["release_attestation"]
    original = attestation_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        for row in payload["rows"]:
            row["passed"] = False
            row["deferred_until_validation"] = False
        # Keep the top-level claim True while every row fails: the validator must
        # catch the row/claim disagreement, not just trust the aggregate flag.
        payload["all_attested"] = True
        attestation_path.write_text(json.dumps(payload), encoding="utf-8")
        issues = validate_supplemental_artifacts(copied_root)
        assert any("claims a failed gate passed" in issue for issue in issues)
    finally:
        attestation_path.write_text(original, encoding="utf-8")

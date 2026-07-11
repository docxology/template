"""Direct tests for the semantic gluing certificate stack.

Covers three collaborating modules with deterministic, mostly copy-free inputs:

* ``semantic_restrictions`` -- the pure classification / lane / value-ok helpers
  and the tmp-fed restriction snapshots (missing-artifact defaults vs crafted
  agreement), each True aggregate paired with a forcing-false control.
* ``semantic_gluing_outputs`` -- the pure ``_stable_*`` projections and every
  arm of ``_semantic_lane_summary_issues`` (built from the real lane helpers so
  the clean payload genuinely round-trips to no issues).
* ``semantic_certificate`` -- a single build via ``write_semantic_gluing_certificate``
  with an explicit ``output_path`` (the light writer branch that skips the
  settle/refresh loop) against one isolated project-tree copy.

No tracked artifact is asserted current before an in-session write, and the one
project-tree copy is module-scoped and reused.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from manuscript.sheaf.semantic_certificate import write_semantic_gluing_certificate
from manuscript.sheaf.semantic_gluing_outputs import (
    _semantic_lane_summary_issues,
    _stable_artifact_graph,
    _stable_certificate_fields,
)
from manuscript.sheaf.semantic_maps import SEMANTIC_SCHEMA
from manuscript.sheaf.semantic_restrictions import (
    _animation_frame_count,
    _expected_symbol_gaps,
    _graph_world_restrictions,
    _lean_status,
    _policy_comparison_restrictions,
    _policy_posterior_restrictions,
    _proof_obligation_rows,
    _pymdp_hash_restrictions,
    _restriction_class,
    _restriction_lane,
    _restriction_lane_assignments,
    _restriction_lane_summaries,
    _restriction_value_ok,
    _runtime_diagnostics_restrictions,
)

from direct_recompute_support import copy_project_tree


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


# ---------------------------------------------------------------------------
# semantic_restrictions -- pure classifiers
# ---------------------------------------------------------------------------


def test_restriction_class_covers_every_arm() -> None:
    assert _restriction_class("security_posture_controls_ok") == "artifact_contract"
    assert _restriction_class("some_secret_finding") == "artifact_contract"
    assert _restriction_class("blocked_empirical_adapter") == "scope_boundary"
    assert _restriction_class("scope_boundary_toy_only") == "scope_boundary"
    assert _restriction_class("only_empirical_marker") == "scope_boundary"
    assert _restriction_class("lean_all_proved") == "formal_witness"
    assert _restriction_class("interop_all_lossless") == "formal_witness"
    assert _restriction_class("provenance_bundle_complete") == "artifact_contract"
    assert _restriction_class("validation_gate_index_count") == "artifact_contract"
    assert _restriction_class("animation_frame_count") == "rendered_artifact"
    assert _restriction_class("plain_semantic_flag") == "semantic_restriction"


def test_restriction_lane_covers_every_arm() -> None:
    assert _restriction_lane("security_posture_controls_ok") == "release"
    assert _restriction_lane("policy_posterior_normalized") == "pymdp"
    assert _restriction_lane("lean_all_proved") == "formal"
    assert _restriction_lane("figure_source_coverage") == "visualization"
    assert _restriction_lane("analytical_assumption_count") == "analytical"
    assert _restriction_lane("blocked_empirical_adapter") == "scope"
    assert _restriction_lane("no_versioned_live_tracks") == "scope"
    assert _restriction_lane("provenance_bundle_complete") == "release"
    assert _restriction_lane("plain_semantic_flag") == "semantic"


def test_restriction_value_ok_arms_with_forcing_false() -> None:
    assert _restriction_value_ok("anything_bool", True) is True
    assert _restriction_value_ok("anything_bool", False) is False
    assert _restriction_value_ok("coverage_missing", 0) is True
    assert _restriction_value_ok("coverage_missing", 2) is False  # forcing-false control
    assert _restriction_value_ok("adversarial_known_bad_passed", 1) is False
    assert _restriction_value_ok("policy_comparison_run_count", 5) is True  # _count -> >= 0
    assert _restriction_value_ok("claim_count", 0) is True
    assert _restriction_value_ok("free_form", "value") is True
    assert _restriction_value_ok("free_form", "") is False


def test_lane_assignments_and_summaries_with_forcing_false() -> None:
    restrictions_ok = {"lean_all_proved": True}
    lanes = _restriction_lane_assignments(restrictions_ok)
    assert lanes == {"lean_all_proved": "formal"}
    summaries = _restriction_lane_summaries(restrictions_ok, lanes)
    assert summaries["formal"]["all_ok"] is True
    assert summaries["formal"]["restrictions"] == ["lean_all_proved"]

    restrictions_bad = {"lean_all_proved": False}
    summaries_bad = _restriction_lane_summaries(restrictions_bad, {"lean_all_proved": "formal"})
    assert summaries_bad["formal"]["all_ok"] is False  # forcing-false control


def test_proof_obligation_rows_true_and_false() -> None:
    rows = {
        row["restriction"]: row for row in _proof_obligation_rows({"lean_all_proved": True, "coverage_missing": False})
    }
    assert rows["lean_all_proved"]["ok"] is True
    assert rows["lean_all_proved"]["obligation"] == "prove_lean_all_proved"
    assert rows["coverage_missing"]["ok"] is False


def test_expected_symbol_gaps_clean_and_defect() -> None:
    symbol_map = {"symbol_a": "var_a"}
    expected_terms = {"var_a": "ExpectedTerm"}
    clean = _expected_symbol_gaps(
        label="toy",
        gnn_symbols={"var_a": "ExpectedTerm"},
        section_symbols={"var_a": "ExpectedTerm"},
        symbol_map=symbol_map,
        expected_terms=expected_terms,
    )
    assert clean == []
    gaps = _expected_symbol_gaps(
        label="toy",
        gnn_symbols={"var_a": "WrongTerm"},
        section_symbols={"var_a": "ExpectedTerm"},
        symbol_map=symbol_map,
        expected_terms=expected_terms,
    )
    assert any("GNN variable 'var_a' annotated 'WrongTerm', expected 'ExpectedTerm'" in gap for gap in gaps)


# ---------------------------------------------------------------------------
# semantic_restrictions -- tmp-fed snapshots (missing defaults vs crafted)
# ---------------------------------------------------------------------------


def test_graph_world_restrictions_missing_then_matching(tmp_path: Path) -> None:
    missing = _graph_world_restrictions(tmp_path)
    assert missing["steps_match"] is False
    assert missing["goal_reached"] is False

    _write_json(tmp_path / "output" / "data" / "si_graph_world_summary.json", {"steps": 3, "goal_reached": True})
    _write_json(tmp_path / "output" / "data" / "si_graph_world_trace.json", {"steps": [0, 1, 2]})
    matched = _graph_world_restrictions(tmp_path)
    assert matched["steps_match"] is True  # 3 summary steps == 3 trace steps
    assert matched["goal_reached"] is True


def test_pymdp_hash_restrictions_missing_then_mismatch(tmp_path: Path) -> None:
    missing = _pymdp_hash_restrictions(tmp_path)
    assert missing["mode_match"] is True  # short-circuits on absent artifacts
    assert missing["config_hash_match"] is True

    _write_json(
        tmp_path / "output" / "data" / "si_tmaze_summary.json",
        {"mode": "policy_inference", "config_hash": "aaa"},
    )
    _write_json(
        tmp_path / "output" / "data" / "analysis_statistics.json",
        {"pymdp_mode": "state_inference", "pymdp_config_hash": "bbb"},
    )
    mismatch = _pymdp_hash_restrictions(tmp_path)
    assert mismatch["mode_match"] is False  # forcing-false control
    assert mismatch["config_hash_match"] is False


def test_restriction_snapshots_default_on_missing_artifacts(tmp_path: Path) -> None:
    assert _policy_comparison_restrictions(tmp_path)["run_count"] == 0
    assert _policy_comparison_restrictions(tmp_path)["complete_grid"] is False
    assert _policy_posterior_restrictions(tmp_path)["row_count"] == 0
    assert _policy_posterior_restrictions(tmp_path)["all_available_posteriors_normalized"] is False
    assert _runtime_diagnostics_restrictions(tmp_path)["ok"] is False
    assert _lean_status(tmp_path)["all_proved"] is False
    assert _animation_frame_count(tmp_path) == 0


# ---------------------------------------------------------------------------
# semantic_gluing_outputs -- pure projections and lane-summary arms
# ---------------------------------------------------------------------------


def test_stable_artifact_graph_filters_keys_and_non_dicts() -> None:
    payload = {
        "artifact_graph": {
            "output/data/a.json": {
                "producer": "p",
                "produced_by_configured_analysis": True,
                "consumers": ["s1"],
                "validation_gates": ["g1"],
                "claim_ids": ["c1"],
                "extra_field": "dropped",
            },
            "output/data/b.json": "not-a-dict",
        }
    }
    stable = _stable_artifact_graph(payload)
    assert set(stable) == {"output/data/a.json"}
    assert set(stable["output/data/a.json"]) == {
        "producer",
        "produced_by_configured_analysis",
        "consumers",
        "validation_gates",
        "claim_ids",
    }


def test_stable_certificate_fields_projects_expected_keys() -> None:
    payload = {
        "schema": "s",
        "tracks": [],
        "sections": [],
        "shared_symbols": {},
        "restrictions": {},
        "restriction_lanes": {},
        "lane_summaries": {},
        "artifact_graph": {},
        "ignored": "x",
    }
    fields = _stable_certificate_fields(payload)
    assert set(fields) == {
        "schema",
        "tracks",
        "sections",
        "shared_symbols",
        "restrictions",
        "restriction_lanes",
        "lane_summaries",
        "artifact_graph",
    }


def _clean_lane_payload() -> dict:
    restrictions = {"lean_all_proved": True, "coverage_missing": 0}
    lanes = _restriction_lane_assignments(restrictions)
    summaries = _restriction_lane_summaries(restrictions, lanes)
    all_ok = bool(summaries) and all(row["all_ok"] for row in summaries.values())
    return {
        "restrictions": restrictions,
        "restriction_lanes": lanes,
        "lane_summaries": summaries,
        "all_lane_summaries_ok": all_ok,
    }


def test_semantic_lane_summary_issues_clean_is_empty() -> None:
    assert _semantic_lane_summary_issues(_clean_lane_payload()) == []


def test_semantic_lane_summary_issues_incomplete_assignment() -> None:
    payload = _clean_lane_payload()
    payload["restriction_lanes"].pop("coverage_missing")
    assert "saved sheaf_gluing_certificate.json has incomplete restriction lane assignments" in (
        _semantic_lane_summary_issues(payload)
    )


def test_semantic_lane_summary_issues_unknown_lane() -> None:
    payload = _clean_lane_payload()
    payload["restriction_lanes"]["coverage_missing"] = "not_a_lane"
    assert "saved sheaf_gluing_certificate.json has unknown restriction lanes" in (
        _semantic_lane_summary_issues(payload)
    )


def test_semantic_lane_summary_issues_summaries_disagree() -> None:
    payload = _clean_lane_payload()
    payload["lane_summaries"] = {}
    assert "saved sheaf_gluing_certificate.json lane summaries disagree with restrictions" in (
        _semantic_lane_summary_issues(payload)
    )


def test_semantic_lane_summary_issues_all_ok_disagrees() -> None:
    payload = _clean_lane_payload()
    payload["all_lane_summaries_ok"] = not payload["all_lane_summaries_ok"]
    assert "saved sheaf_gluing_certificate.json all_lane_summaries_ok disagrees with lane summaries" in (
        _semantic_lane_summary_issues(payload)
    )


# ---------------------------------------------------------------------------
# semantic_certificate -- explicit-output_path build against a copy
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("semantic_certificate_tree"))


@pytest.mark.timeout(300)
def test_write_certificate_with_output_path_is_self_consistent(copied_root: Path, tmp_path: Path) -> None:
    """The output_path writer builds once and its ok field agrees with its issues."""
    out = tmp_path / "certificate.json"
    returned = write_semantic_gluing_certificate(copied_root, output_path=out)
    assert returned == out
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == SEMANTIC_SCHEMA
    assert isinstance(payload["restrictions"], dict)
    # restriction lanes cover exactly the restriction keys
    assert set(payload["restriction_lanes"]) == set(payload["restrictions"])
    # ok is the negation of the issue list, not an independent stored literal
    assert payload["ok"] == (not payload["issues"])
    assert payload["proof_obligations"]

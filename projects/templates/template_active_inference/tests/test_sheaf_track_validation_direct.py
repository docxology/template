"""Direct leg-deterministic tests for ``roadmap_tracks.sheaf_track_validation``.

The full ``validate_sheaf_track_artifacts`` gate reads ~30 canonical artifacts
and, on the tracked snapshot, returns no issues -- so its row-recompute helpers
and the source-contract registry checks only ran their FAILURE arms when a gate
rebuilt state. These tests exercise:

* the pure row/summary/coerce helpers (``_all_rows``, ``_all_rows_absent``,
  ``_append_schema_issue``, ``_append_summary_issue``, ``_coerce_int``,
  ``_semantic_restriction_value_ok``) with constructed payloads -- each with a
  positive case and a paired negative control; and
* ``validate_sheaf_track_source_contract`` against a bare / crafted skeleton so
  the registry-contract issue-append branches (missing canonical tracks, missing
  producer/claims, versioned-id rejection, empirical-adapter promotion) fire on
  real detected defects.

Building a full valid artifact set to drive the 30-artifact gate would require
regenerating the snapshot; per tests/AGENTS.md leg-safety the tracked tree must
not be rewritten, so the heavyweight gate arms are left to the gate suite and
these tests target the deterministically reachable branches instead. Nothing
here touches the git-tracked project tree.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from roadmap_tracks.sheaf_track_validation import (
    _all_rows,
    _all_rows_absent,
    _append_schema_issue,
    _append_summary_issue,
    _coerce_int,
    _semantic_restriction_value_ok,
    validate_sheaf_track_source_contract,
)


# ---------------------------------------------------------------------------
# _all_rows / _all_rows_absent
# ---------------------------------------------------------------------------


def test_all_rows_true_only_when_every_row_has_field() -> None:
    assert _all_rows({"rows": [{"matched": True}, {"matched": 1}]}, "matched") is True
    assert _all_rows({"rows": [{"matched": True}, {"matched": False}]}, "matched") is False
    assert _all_rows({"rows": []}, "matched") is False  # vacuous


def test_all_rows_absent_true_only_when_field_missing_everywhere() -> None:
    assert _all_rows_absent({"rows": [{"other": 1}, {}]}, "shape_diff") is True
    assert _all_rows_absent({"rows": [{"shape_diff": "x"}]}, "shape_diff") is False
    assert _all_rows_absent({"rows": []}, "shape_diff") is False  # needs rows


# ---------------------------------------------------------------------------
# _append_schema_issue / _append_summary_issue
# ---------------------------------------------------------------------------


def test_append_schema_issue_only_on_mismatch() -> None:
    issues: list[str] = []
    _append_schema_issue(issues, {"schema": "good"}, "good", "schema mismatch")
    assert issues == []
    _append_schema_issue(issues, {"schema": "wrong"}, "good", "schema mismatch")
    assert issues == ["schema mismatch"]
    _append_schema_issue(issues, {}, "good", "schema mismatch")  # missing schema
    assert issues == ["schema mismatch", "schema mismatch"]


def test_append_summary_issue_flags_flag_row_disagreement() -> None:
    ok: list[str] = []
    _append_summary_issue(ok, {"flag": True}, "flag", True, "disagreement")
    assert ok == []  # flag True and derived True -> silent

    forged: list[str] = []
    # flag stored True but the recomputed value is False: the row/claim forgery
    # a gate must catch.
    _append_summary_issue(forged, {"flag": True}, "flag", False, "disagreement")
    assert forged == ["disagreement"]

    not_true: list[str] = []
    _append_summary_issue(not_true, {"flag": False}, "flag", False, "disagreement")
    assert not_true == ["disagreement"]  # flag is not True at all

    missing: list[str] = []
    _append_summary_issue(missing, {}, "flag", True, "disagreement")
    assert missing == ["disagreement"]  # flag absent


# ---------------------------------------------------------------------------
# _coerce_int -- every type arm
# ---------------------------------------------------------------------------


def test_coerce_int_type_arms() -> None:
    assert _coerce_int(True) == 1
    assert _coerce_int(False) == 0
    assert _coerce_int(7) == 7
    assert _coerce_int(2.9) == 2
    assert _coerce_int("5") == 5
    assert _coerce_int(None) == 0  # unhandled type -> 0
    assert _coerce_int(["x"]) == 0  # unhandled type -> 0


# ---------------------------------------------------------------------------
# _semantic_restriction_value_ok -- bool / zero-set / count / default arms
# ---------------------------------------------------------------------------


def test_semantic_restriction_value_ok_bool_arm() -> None:
    assert _semantic_restriction_value_ok("anything", True) is True
    assert _semantic_restriction_value_ok("anything", False) is False


def test_semantic_restriction_value_ok_zero_required_arm() -> None:
    assert _semantic_restriction_value_ok("coverage_missing", 0) is True
    assert _semantic_restriction_value_ok("coverage_missing", 3) is False
    assert _semantic_restriction_value_ok("adversarial_known_bad_passed", "0") is True
    assert _semantic_restriction_value_ok("pymdp_runtime_unexpected_warning_count", "2") is False


def test_semantic_restriction_value_ok_count_arm() -> None:
    assert _semantic_restriction_value_ok("section_count", 0) is True
    assert _semantic_restriction_value_ok("track_count", 5) is True
    assert _semantic_restriction_value_ok("some_count", "4") is True
    assert _semantic_restriction_value_ok("some_count", -1) is False


def test_semantic_restriction_value_ok_default_arm() -> None:
    assert _semantic_restriction_value_ok("free_form", "non-empty") is True
    assert _semantic_restriction_value_ok("free_form", "") is False


# ---------------------------------------------------------------------------
# validate_sheaf_track_source_contract -- registry-contract failure arms
# ---------------------------------------------------------------------------


def test_source_contract_flags_bare_skeleton(tmp_path: Path) -> None:
    """An empty tree fails every source-side contract with specific messages."""
    issues = validate_sheaf_track_source_contract(tmp_path)
    assert any("missing canonical live tracks" in i for i in issues)
    assert any("canonical live tracks missing manuscript bindings" in i for i in issues)
    assert any(
        "producer_coverage_complete: generate_sheaf_tracks.py missing from analysis scripts" in i for i in issues
    )
    assert any("all_canonical_artifacts_have_claims" in i for i in issues)


def test_source_contract_flags_versioned_and_empirical_promotion(tmp_path: Path) -> None:
    """A crafted registry trips the versioned-id and empirical-adapter guards."""
    sheaf_dir = tmp_path / "manuscript" / "sheaf"
    sheaf_dir.mkdir(parents=True, exist_ok=True)
    (sheaf_dir / "tracks.yaml").write_text(
        yaml.safe_dump({"tracks": {"provenance_v2": {}, "empirical_adapter": {}}}),
        encoding="utf-8",
    )
    issues = validate_sheaf_track_source_contract(tmp_path)
    assert any("versioned live track ids are not allowed: provenance_v2" in i for i in issues)
    assert any("empirical_adapter blocked track was promoted live" in i for i in issues)

"""Direct leg-deterministic tests for ``gates.claim_ledger``.

The claim-ledger gate resolves every claim's typed evidence against its backing
artifact. On the tracked snapshot the ledger resolves cleanly, so the module's
FAILURE branches -- missing ledger / path / artifact, malformed evidence,
predicate failures, empty tracks, and the many evidence-predicate arms -- only
ran when a gate rebuilt state. These tests drive the pure predicate helpers with
constructed data and drive the row/issue resolvers against tmp-only ledgers and
artifacts. Nothing touches the git-tracked project tree.

Every positive assertion (a predicate/claim resolving True) is paired with a
negative control that forces the same path False.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from gates.claim_ledger import (
    _evidence_predicate_name,
    _evidence_spec_holds,
    _load_structured,
    _lookup_field,
    _numbers_equal,
    _predicate_holds,
    _set_equals,
    claim_evidence_status_rows,
    typed_claim_evidence_issues,
    validate_typed_claim_evidence,
)


def _ledger(tmp_path: Path, claims: list[dict[str, Any]]) -> Path:
    path = tmp_path / "claim_ledger.yaml"
    path.write_text(yaml.safe_dump({"claims": claims}), encoding="utf-8")
    return path


def _artifact(tmp_path: Path, rel: str, text: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# _load_structured -- suffix routing
# ---------------------------------------------------------------------------


def test_load_structured_json_yaml_and_text(tmp_path: Path) -> None:
    js = _artifact(tmp_path, "a.json", '{"k": 1}')
    jl = _artifact(tmp_path, "a.jsonl", '{"k": 2}')
    ya = _artifact(tmp_path, "a.yaml", "k: 3\n")
    yl = _artifact(tmp_path, "a.yml", "k: 4\n")
    tx = _artifact(tmp_path, "a.txt", "raw text")
    assert _load_structured(js) == {"k": 1}
    assert _load_structured(jl) == {"k": 2}
    assert _load_structured(ya) == {"k": 3}
    assert _load_structured(yl) == {"k": 4}
    assert _load_structured(tx) == "raw text"


# ---------------------------------------------------------------------------
# _lookup_field -- dict / list / scalar-raises
# ---------------------------------------------------------------------------


def test_lookup_field_traverses_dicts_and_lists() -> None:
    data = {"a": {"b": [10, 20, 30]}}
    assert _lookup_field(data, "a.b.1") == 20


def test_lookup_field_raises_keyerror_on_scalar() -> None:
    with pytest.raises(KeyError):
        _lookup_field(5, "a")


def test_lookup_field_raises_on_bad_list_index() -> None:
    with pytest.raises((ValueError, IndexError)):
        _lookup_field({"a": [1]}, "a.notint")


# ---------------------------------------------------------------------------
# _numbers_equal -- bool / numeric-tolerance / equality arms
# ---------------------------------------------------------------------------


def test_numbers_equal_bool_arm() -> None:
    assert _numbers_equal(True, 1, 0.0) is True
    assert _numbers_equal(True, False, 0.0) is False


def test_numbers_equal_numeric_tolerance_arm() -> None:
    assert _numbers_equal(1.0, 1.05, 0.1) is True
    assert _numbers_equal(1.0, 1.5, 0.1) is False


def test_numbers_equal_equality_arm() -> None:
    assert _numbers_equal("x", "x", 0.0) is True
    assert _numbers_equal("x", "y", 0.0) is False


# ---------------------------------------------------------------------------
# _predicate_holds -- every predicate arm plus the unknown fallthrough
# ---------------------------------------------------------------------------


def test_predicate_holds_all_arms() -> None:
    assert _predicate_holds(1, "exists") is True
    assert _predicate_holds(None, "exists") is False
    assert _predicate_holds(1, "file_exists") is True
    assert _predicate_holds(0, "file_exists") is False
    assert _predicate_holds("y", "truthy") is True
    assert _predicate_holds("", "truthy") is False
    assert _predicate_holds([1], "non_empty") is True
    assert _predicate_holds([], "non_empty") is False
    assert _predicate_holds(0, "zero") is True
    assert _predicate_holds(1, "zero") is False
    assert _predicate_holds(2, "positive") is True
    assert _predicate_holds(0, "positive") is False
    assert _predicate_holds({"a": True, "b": True}, "all_true") is True
    assert _predicate_holds({"a": True, "b": False}, "all_true") is False
    assert _predicate_holds([1, 2], "all_true") is True
    assert _predicate_holds([1, 0], "all_true") is False
    assert _predicate_holds("scalar", "all_true") is False  # neither dict nor list
    assert _predicate_holds(True, "is_true") is True
    assert _predicate_holds(1, "is_true") is False  # identity, not truthiness
    assert _predicate_holds("anything", "unknown_predicate") is False


# ---------------------------------------------------------------------------
# _set_equals -- non-list rejection and value equality
# ---------------------------------------------------------------------------


def test_set_equals_arms() -> None:
    assert _set_equals(["a", "b"], ["b", "a"]) is True
    assert _set_equals(["a"], ["a", "b"]) is False
    assert _set_equals("a", ["a"]) is False  # left not a list
    assert _set_equals(["a"], "a") is False  # right not a list


# ---------------------------------------------------------------------------
# _evidence_spec_holds -- each comparator branch, positive + negative
# ---------------------------------------------------------------------------


def test_evidence_spec_field_lookup_failure_is_false() -> None:
    assert _evidence_spec_holds({"a": 1}, {"field": "missing.deep"}) is False


def test_evidence_spec_equals_and_approx() -> None:
    assert _evidence_spec_holds(5, {"equals": 5}) is True
    assert _evidence_spec_holds(5, {"equals": 6}) is False
    assert _evidence_spec_holds(1.0, {"approx": 1.02, "tolerance": 0.1}) is True
    assert _evidence_spec_holds(1.0, {"approx": 2.0, "tolerance": 0.1}) is False


def test_evidence_spec_min_max() -> None:
    assert _evidence_spec_holds(5, {"min": 1, "max": 10}) is True
    assert _evidence_spec_holds(5, {"min": 6}) is False
    assert _evidence_spec_holds(5, {"max": 4}) is False


def test_evidence_spec_contains() -> None:
    assert _evidence_spec_holds(["a", "b"], {"contains": "a"}) is True
    assert _evidence_spec_holds(["a", "b"], {"contains": "z"}) is False


def test_evidence_spec_set_len_and_predicate() -> None:
    assert _evidence_spec_holds(["a", "b"], {"set_equals": ["b", "a"]}) is True
    assert _evidence_spec_holds(["a"], {"set_equals": ["b"]}) is False
    assert _evidence_spec_holds([1, 2, 3], {"len_equals": 3}) is True
    assert _evidence_spec_holds([1, 2], {"len_equals": 3}) is False
    assert _evidence_spec_holds([1, 2, 3], {"len_min": 2}) is True
    assert _evidence_spec_holds([1], {"len_min": 2}) is False
    assert _evidence_spec_holds(True, {"predicate": "is_true"}) is True
    assert _evidence_spec_holds(False, {"predicate": "is_true"}) is False


def test_evidence_spec_all_and_any_nested() -> None:
    rows = [{"ok": True}, {"ok": True}]
    assert _evidence_spec_holds(rows, {"all": {"field": "ok", "predicate": "is_true"}}) is True
    mixed = [{"ok": True}, {"ok": False}]
    assert _evidence_spec_holds(mixed, {"all": {"field": "ok", "predicate": "is_true"}}) is False
    assert _evidence_spec_holds(mixed, {"any": {"field": "ok", "predicate": "is_true"}}) is True
    assert _evidence_spec_holds([{"ok": False}], {"any": {"field": "ok", "predicate": "is_true"}}) is False
    # non-list value with an all/any spec is rejected
    assert _evidence_spec_holds({"ok": True}, {"all": {"predicate": "is_true"}}) is False


def test_evidence_predicate_name_precedence() -> None:
    assert _evidence_predicate_name({"predicate": "positive"}) == "positive"
    assert _evidence_predicate_name({"min": 1}) == "min"
    assert _evidence_predicate_name({"unrelated": 1}) == ""


# ---------------------------------------------------------------------------
# typed_claim_evidence_issues -- every failure arm
# ---------------------------------------------------------------------------


def test_typed_issues_missing_ledger(tmp_path: Path) -> None:
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=tmp_path / "nope.yaml")
    assert issues == [f"claim ledger missing: {tmp_path / 'nope.yaml'}"]


def test_typed_issues_missing_path(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path, [{"id": "c1"}])
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert "c1: missing path" in issues


def test_typed_issues_certificate_skipped_when_allowed(tmp_path: Path) -> None:
    ledger = _ledger(
        tmp_path,
        [{"id": "cert", "path": "output/data/sheaf_gluing_certificate.json"}],
    )
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger, allow_missing_certificate=True)
    assert issues == []


def test_typed_issues_missing_artifact(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path, [{"id": "c2", "path": "output/data/absent.json"}])
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert "c2: missing artifact output/data/absent.json" in issues


def test_typed_issues_cannot_load_malformed_evidence(tmp_path: Path) -> None:
    _artifact(tmp_path, "output/data/bad.json", "{oops not json")
    ledger = _ledger(
        tmp_path,
        [{"id": "c4", "path": "output/data/bad.json", "evidence": {"predicate": "truthy"}, "tracks": ["t"]}],
    )
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert any(i.startswith("c4: cannot load evidence from output/data/bad.json") for i in issues)


def test_typed_issues_predicate_failed(tmp_path: Path) -> None:
    _artifact(tmp_path, "output/data/ok.json", '{"ok": false}')
    ledger = _ledger(
        tmp_path,
        [
            {
                "id": "c5",
                "path": "output/data/ok.json",
                "evidence": {"field": "ok", "predicate": "is_true"},
                "tracks": ["t"],
            }
        ],
    )
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert "c5: evidence predicate failed for output/data/ok.json" in issues


def test_typed_issues_empty_tracks(tmp_path: Path) -> None:
    _artifact(tmp_path, "output/data/ok.json", '{"ok": true}')
    ledger = _ledger(tmp_path, [{"id": "c6", "path": "output/data/ok.json", "tracks": []}])
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert "c6: tracks must not be empty" in issues


def test_typed_issues_file_exists_predicate_holds(tmp_path: Path) -> None:
    _artifact(tmp_path, "output/data/present.json", "{}")
    ledger = _ledger(
        tmp_path,
        [
            {
                "id": "c7",
                "path": "output/data/present.json",
                "evidence": {"predicate": "file_exists"},
                "tracks": ["t"],
            }
        ],
    )
    assert typed_claim_evidence_issues(tmp_path, ledger_path=ledger) == []


def test_validate_typed_claim_evidence_bool(tmp_path: Path) -> None:
    _artifact(tmp_path, "output/data/ok.json", '{"ok": true}')
    good = _ledger(
        tmp_path,
        [
            {
                "id": "c8",
                "path": "output/data/ok.json",
                "evidence": {"field": "ok", "predicate": "is_true"},
                "tracks": ["t"],
            }
        ],
    )
    assert validate_typed_claim_evidence(tmp_path, ledger_path=good) is True
    bad = _ledger(tmp_path, [{"id": "c9", "path": "output/data/absent.json"}])
    assert validate_typed_claim_evidence(tmp_path, ledger_path=bad) is False


# ---------------------------------------------------------------------------
# claim_evidence_status_rows -- row-level status resolution
# ---------------------------------------------------------------------------


def test_status_rows_empty_when_ledger_absent(tmp_path: Path) -> None:
    assert claim_evidence_status_rows(tmp_path, ledger_path=tmp_path / "nope.yaml") == []


def test_status_rows_cover_every_resolution_arm(tmp_path: Path) -> None:
    _artifact(tmp_path, "output/data/good.json", '{"val": 5}')
    _artifact(tmp_path, "output/data/fails.json", '{"ok": false}')
    _artifact(tmp_path, "output/data/bad.json", "{oops")
    _artifact(tmp_path, "output/data/waived.json", "{}")
    _artifact(tmp_path, "output/data/noevidence.json", "{}")
    _artifact(tmp_path, "output/data/tracksless.json", '{"val": 5}')
    ledger = _ledger(
        tmp_path,
        [
            {"id": "no_path"},
            {
                "id": "complete",
                "path": "output/data/good.json",
                "evidence": {"field": "val", "min": 1, "predicate": "positive"},
                "tracks": ["t"],
            },
            {
                "id": "waived",
                "path": "output/data/waived.json",
                "evidence": {"waiver": "documented deferral"},
                "tracks": ["t"],
            },
            {
                "id": "claim_evidence_audit_typed",
                "path": "output/reports/claim_evidence_audit.json",
                "evidence": {"field": "all_complete", "predicate": "is_true"},
                "tracks": ["t"],
            },
            {
                "id": "deferred_cert",
                "path": "output/data/sheaf_gluing_certificate.json",
                "evidence": {"field": "ok", "predicate": "is_true"},
                "tracks": ["t"],
            },
            {"id": "missing_artifact", "path": "output/data/absent.json", "tracks": ["t"]},
            {"id": "no_evidence", "path": "output/data/noevidence.json", "tracks": ["t"]},
            {
                "id": "predicate_fail",
                "path": "output/data/fails.json",
                "evidence": {"field": "ok", "predicate": "is_true"},
                "tracks": ["t"],
            },
            {
                "id": "load_fail",
                "path": "output/data/bad.json",
                "evidence": {"predicate": "truthy"},
                "tracks": ["t"],
            },
            {
                "id": "empty_tracks",
                "path": "output/data/tracksless.json",
                "evidence": {"field": "val", "predicate": "positive"},
                "tracks": [],
            },
        ],
    )
    rows = claim_evidence_status_rows(tmp_path, ledger_path=ledger, allow_missing_certificate=True)
    by_id = {row["id"]: row for row in rows}

    assert by_id["no_path"]["failure_reason"] == "missing path"
    assert by_id["no_path"]["complete"] is False

    assert by_id["complete"]["complete"] is True
    assert by_id["complete"]["failure_reason"] == ""
    assert by_id["complete"]["evidence_holds"] is True

    assert by_id["waived"]["complete"] is True
    assert by_id["waived"]["waiver"] == "documented deferral"

    # self-referential audit resolves True even though the artifact is absent
    assert by_id["claim_evidence_audit_typed"]["self_referential_audit"] is True
    assert by_id["claim_evidence_audit_typed"]["complete"] is True

    # fixed-point certificate deferral resolves True with the flag set
    assert by_id["deferred_cert"]["fixed_point_deferred"] is True
    assert by_id["deferred_cert"]["complete"] is True

    assert by_id["missing_artifact"]["failure_reason"] == "missing artifact output/data/absent.json"
    assert by_id["missing_artifact"]["complete"] is False

    assert by_id["no_evidence"]["failure_reason"] == "missing evidence"
    assert by_id["no_evidence"]["complete"] is False

    assert by_id["predicate_fail"]["failure_reason"] == "evidence predicate failed for output/data/fails.json"
    assert by_id["predicate_fail"]["complete"] is False

    assert by_id["load_fail"]["failure_reason"].startswith("cannot load evidence from output/data/bad.json")
    assert by_id["load_fail"]["complete"] is False

    assert by_id["empty_tracks"]["has_tracks"] is False
    assert by_id["empty_tracks"]["failure_reason"] == "tracks must not be empty"
    assert by_id["empty_tracks"]["complete"] is False

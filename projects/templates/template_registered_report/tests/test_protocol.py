from __future__ import annotations

import copy
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import pytest

from registered_report import (
    build_deviation_ledger,
    build_publication_receipt,
    build_review_packet,
    compare_analysis_to_registration,
    freeze_registration,
    REGISTRATION_SCHEMA_VERSION,
    registration_hash,
    validate_sensitivity_table,
    validate_registration,
)
from registered_report.protocol import _verify_frozen_record_binding, persist_frozen_registration


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_registration() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((PROJECT_ROOT / "data" / "example_registration.json").read_text(encoding="utf-8")),
    )


def test_freeze_registration_adds_content_hash_without_mutating_source() -> None:
    registration = load_registration()

    frozen = freeze_registration(registration)

    assert "registration_hash" in frozen
    assert "registration_hash" not in registration
    unhashed = dict(frozen)
    supplied = unhashed.pop("registration_hash")
    assert supplied == registration_hash(unhashed)
    assert validate_registration(frozen) == ()
    assert frozen["schema_version"] == REGISTRATION_SCHEMA_VERSION


@pytest.mark.parametrize("schema", [None, "template-registered-report/1", "unsupported-future-schema"])
def test_new_drafts_require_explicit_current_schema(schema: str | None, tmp_path: Path) -> None:
    registration = load_registration()
    if schema is None:
        registration.pop("schema_version")
    else:
        registration["schema_version"] = schema
    original = copy.deepcopy(registration)
    path = tmp_path / "frozen_registration.json"

    with pytest.raises(ValueError, match="New registration drafts must declare"):
        freeze_registration(registration)
    with pytest.raises(ValueError, match="New registration drafts must declare"):
        persist_frozen_registration(path, registration)
    assert any(f.code == "unsupported_schema" for f in validate_registration(registration))
    assert registration == original
    assert not path.exists()


@pytest.mark.parametrize("schema", [None, "template-registered-report/1", REGISTRATION_SCHEMA_VERSION])
def test_frozen_records_preserve_original_schema_hash_and_nested_intent(schema: str | None) -> None:
    archived = load_registration()
    if schema is None:
        archived.pop("schema_version")
    else:
        archived["schema_version"] = schema
    archived["registration_hash"] = registration_hash(archived)
    original = copy.deepcopy(archived)

    preserved = freeze_registration(archived)
    assert preserved == original
    assert preserved is not archived
    assert validate_registration(preserved) == ()
    preserved["hypotheses"][0]["claim"] = "Changed outside the archived record"
    assert archived == original


@pytest.mark.parametrize("target", ["hypothesis", "outcome", "analysis"])
def test_changed_frozen_intent_cannot_be_recertified(target: str) -> None:
    frozen = freeze_registration(load_registration())
    if target == "hypothesis":
        frozen["hypotheses"][0]["claim"] = "A result-selected replacement hypothesis"
    elif target == "outcome":
        frozen["outcomes"][0]["name"] = "result_selected_outcome"
    else:
        frozen["analysis_plan"]["primary_model"] = "result_selected_model"
    supplied = copy.deepcopy(frozen)

    with pytest.raises(ValueError, match="Frozen registration hash"):
        freeze_registration(frozen)
    assert frozen == supplied


@pytest.mark.parametrize("supplied", [None, True, 0, "", "f" * 64])
def test_invalid_supplied_frozen_hash_is_not_replaced(supplied: Any) -> None:
    frozen = freeze_registration(load_registration())
    frozen["registration_hash"] = supplied
    original = copy.deepcopy(frozen)
    with pytest.raises(ValueError, match="Frozen registration hash"):
        freeze_registration(frozen)
    assert frozen == original


def test_stored_frozen_registration_keeps_exact_schema_hash_and_file_bytes() -> None:
    path = PROJECT_ROOT / "output" / "reports" / "frozen_registration.json"
    original_bytes = path.read_bytes()
    archived = json.loads(original_bytes)
    assert freeze_registration(archived) == archived
    assert path.read_bytes() == original_bytes


def test_hash_valid_unknown_frozen_schema_refuses_without_replacement() -> None:
    frozen = load_registration()
    frozen["schema_version"] = "unsupported-future-schema"
    frozen["registration_hash"] = registration_hash(frozen)
    original = copy.deepcopy(frozen)
    with pytest.raises(ValueError, match="Unsupported frozen registration schema"):
        freeze_registration(frozen)
    assert any(f.code == "unsupported_schema" for f in validate_registration(frozen))
    assert frozen == original


def test_bounded_frozen_record_rejects_oversized_new_intent_without_creating_a_file(tmp_path: Path) -> None:
    registration = load_registration()
    registration["title"] = "x" * (1024 * 1024)
    path = tmp_path / "frozen_registration.json"
    with pytest.raises(ValueError, match="bounded record size"):
        persist_frozen_registration(path, registration)
    assert not path.exists()


def test_frozen_record_destination_rejects_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="parent traversal"):
        persist_frozen_registration(tmp_path / ".." / "frozen_registration.json", load_registration())
    assert not (tmp_path.parent / "frozen_registration.json").exists()


def test_persistence_preserves_exact_existing_bytes_and_refuses_changed_intent(tmp_path: Path) -> None:
    path = tmp_path / "frozen_registration.json"
    archived = persist_frozen_registration(path, load_registration())
    original = (json.dumps(archived, indent=4) + "\n\n").encode("utf-8")
    path.write_bytes(original)
    assert persist_frozen_registration(path, archived) == archived
    assert path.read_bytes() == original
    changed = load_registration()
    changed["hypotheses"][0]["claim"] = "Different prospective intent"
    with pytest.raises(ValueError, match="new versioned output directory"):
        persist_frozen_registration(path, changed)
    assert path.read_bytes() == original


@pytest.mark.parametrize("replacement", ["leaf", "parent", "ancestor", "same_inode_content"])
def test_frozen_record_binding_refuses_real_named_replacements_without_touching_foreign_bytes(
    tmp_path: Path, replacement: str
) -> None:
    authority = tmp_path / "authority"
    reports = authority / "reports"
    reports.mkdir(parents=True)
    path = reports / "frozen_registration.json"
    persist_frozen_registration(path, load_registration())
    original = path.read_bytes()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(tmp_path, flags)
    authority_fd = os.open("authority", flags, dir_fd=root_fd)
    reports_fd = os.open("reports", flags, dir_fd=authority_fd)
    record_fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=reports_fd)
    expected = os.fstat(record_fd)
    bindings = [(root_fd, "authority", authority_fd), (authority_fd, "reports", reports_fd)]
    try:
        if replacement == "leaf":
            retained = reports / "retained-original.json"
            path.rename(retained)
        elif replacement == "parent":
            retained_parent = authority / "retained-reports"
            reports.rename(retained_parent)
            retained = retained_parent / path.name
            reports.mkdir()
        elif replacement == "ancestor":
            retained_ancestor = tmp_path / "retained-authority"
            authority.rename(retained_ancestor)
            retained = retained_ancestor / "reports" / path.name
            reports.mkdir(parents=True)
        else:
            retained = path
        path.write_bytes(b"foreign replacement must remain untouched")

        with pytest.raises(ValueError, match="new versioned output directory"):
            _verify_frozen_record_binding(reports_fd, path.name, record_fd, bindings, expected)

        if replacement != "same_inode_content":
            assert retained.read_bytes() == original
        assert path.read_bytes() == b"foreign replacement must remain untouched"
    finally:
        for descriptor in (record_fd, reports_fd, authority_fd, root_fd):
            os.close(descriptor)


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_PATH") or os.geteuid() == 0,
    reason="requires real nonroot search-only ancestor traversal",
)
def test_frozen_record_persistence_traverses_search_only_ancestors_without_following_links(tmp_path: Path) -> None:
    ancestor = tmp_path.resolve() / "search-only"
    reports = ancestor / "reports"
    reports.mkdir(parents=True)
    path = reports / "frozen_registration.json"
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"foreign bytes must remain untouched")
    ancestor.chmod(0o111)
    try:
        with pytest.raises(PermissionError):
            list(ancestor.iterdir())
        frozen = persist_frozen_registration(path, load_registration())
        original = (json.dumps(frozen, indent=4) + "\n\n").encode("utf-8")
        path.write_bytes(original)
        assert persist_frozen_registration(path, frozen) == frozen
        assert path.read_bytes() == original
        changed = load_registration()
        changed["hypotheses"][0]["claim"] = "Different prospective intent"
        with pytest.raises(ValueError, match="new versioned output directory"):
            persist_frozen_registration(path, changed)
        assert path.read_bytes() == original
        linked = reports / "linked.json"
        linked.symlink_to(outside)
        with pytest.raises(ValueError, match="new versioned output directory"):
            persist_frozen_registration(linked, load_registration())
        assert linked.is_symlink() and outside.read_bytes() == b"foreign bytes must remain untouched"
    finally:
        ancestor.chmod(0o700)


def test_publication_receipt_requires_owner_authority_and_matching_payload() -> None:
    with pytest.raises(ValueError, match="owner authority"):
        build_publication_receipt({}, artifact_digest="a" * 64)
    authority = {
        "status": "approved",
        "authority": "owner",
        "receipt_id": "receipt-1",
        "repository": "example/repo",
        "payload_digest": "a" * 64,
    }
    receipt = build_publication_receipt({}, artifact_digest="a" * 64, authority_receipt=authority)
    assert receipt["status"] == "approved"
    authority["payload_digest"] = "b" * 64
    with pytest.raises(ValueError, match="payload digest"):
        build_publication_receipt({}, artifact_digest="a" * 64, authority_receipt=authority)


def test_registered_execution_scores_as_valid() -> None:
    frozen = freeze_registration(load_registration())
    executed = {"outcomes": ["primary_score"], "primary_model": "permutation_test"}

    report = compare_analysis_to_registration(frozen, executed)

    assert report.valid is True
    assert report.integrity_score == 1.0
    assert report.findings == ()


def test_unregistered_outcome_and_model_change_require_deviation() -> None:
    frozen = freeze_registration(load_registration())
    executed = {"outcomes": ["primary_score", "secondary_score"], "primary_model": "linear_model"}

    report = compare_analysis_to_registration(frozen, executed)
    codes = {finding.code for finding in report.findings}

    assert report.valid is False
    assert "unregistered_outcome" in codes
    assert "model_deviation" in codes


def test_documented_model_deviation_is_warning_not_error() -> None:
    frozen = freeze_registration(load_registration())
    executed = {"outcomes": ["primary_score"], "primary_model": "linear_model"}
    deviations = [{"kind": "model", "target": "linear_model", "rationale": "robustness sensitivity"}]

    report = compare_analysis_to_registration(frozen, executed, deviations)

    assert report.valid is True
    assert report.integrity_score == 0.9
    assert [finding.severity for finding in report.findings] == ["warning"]


def test_deviation_ledger_and_review_packet_separate_confirmatory_from_exploratory() -> None:
    frozen = freeze_registration(load_registration())
    executed = {"outcomes": ["primary_score", "secondary_score"], "primary_model": "linear_model"}
    deviations = [
        {"kind": "outcome", "target": "secondary_score", "rationale": "exploratory robustness endpoint"},
        {"kind": "model", "target": "linear_model", "rationale": "robustness sensitivity"},
    ]

    ledger = build_deviation_ledger(frozen, executed, deviations)
    packet = build_review_packet(frozen, executed, deviations)

    assert {row.target: row.severity for row in ledger}["primary_score"] == "ok"
    assert {row.target: row.severity for row in ledger}["secondary_score"] == "warning"
    assert packet["valid"] is True
    assert packet["confirmatory_outcomes"] == ("primary_score",)
    assert packet["exploratory_outcomes"] == ("secondary_score",)
    assert packet["deviation_ledger"][1]["rationale"] == "exploratory robustness endpoint"


def test_sensitivity_table_validation_catches_bad_targets_and_decisions() -> None:
    frozen = freeze_registration(load_registration())

    findings = validate_sensitivity_table(
        frozen,
        [{"name": "bad", "target": "unregistered", "model": "linear_model", "decision": "maybe"}],
    )
    codes = {finding.code for finding in findings}

    assert "unregistered_sensitivity_target" in codes
    assert "bad_sensitivity_decision" in codes


def test_registration_validation_reports_structural_gaps() -> None:
    broken = {
        "title": "broken",
        "version": "0.1.0",
        "hypotheses": [{"id": "H1", "claim": "a"}, {"id": "H1", "claim": "b"}],
        "outcomes": [{"name": "primary_score"}],
        "exclusion_rules": [],
        "analysis_plan": {},
    }

    codes = {finding.code for finding in validate_registration(broken)}

    assert "duplicate_hypothesis" in codes
    assert "incomplete_outcome" in codes
    assert "missing_primary_model" in codes


def test_bad_hash_and_empty_deviation_are_caught() -> None:
    frozen = freeze_registration(load_registration())
    frozen["registration_hash"] = "bad"

    report = compare_analysis_to_registration(
        frozen,
        {"outcomes": ["secondary_score"], "primary_model": "permutation_test"},
        [{"kind": "outcome", "target": "secondary_score", "rationale": ""}],
    )
    codes = {finding.code for finding in report.findings}

    assert "hash_mismatch" in codes
    assert "unregistered_outcome" in codes
    assert "deviation_without_rationale" in codes


def test_registration_validation_covers_empty_and_malformed_sections() -> None:
    broken = {
        "title": "thin",
        "version": "0.1.0",
        "hypotheses": [],
        "outcomes": [],
        "exclusion_rules": [],
        "analysis_plan": {"primary_model": "permutation_test"},
    }
    malformed = {
        "title": "malformed",
        "version": "0.1.0",
        "hypotheses": ["not-a-mapping"],
        "outcomes": ["not-a-mapping"],
        "analysis_plan": {"primary_model": "permutation_test"},
    }

    missing_codes = {finding.code for finding in validate_registration({"title": "missing"})}
    empty_codes = {finding.code for finding in validate_registration(broken)}
    malformed_codes = {finding.code for finding in validate_registration(malformed)}

    assert "missing_section" in missing_codes
    assert "missing_hypotheses" in empty_codes
    assert "missing_outcomes" in empty_codes
    assert "missing_seed" in empty_codes
    assert "bad_hypothesis" in malformed_codes
    assert "bad_outcome" in malformed_codes


def test_sensitivity_table_prose_matches_registered_analyses() -> None:
    frozen = freeze_registration(load_registration())
    rows = cast("list[dict[str, Any]]", frozen.get("sensitivity_analyses", []))
    assert rows  # the fixture ships a registered sensitivity row

    findings = validate_sensitivity_table(frozen, rows)
    assert findings == ()

    text = (PROJECT_ROOT / "manuscript" / "04_results.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    for row in rows:
        assert str(row["name"]) in normalized
        assert str(row["target"]) in normalized
        assert str(row["model"]) in normalized
        assert str(row["decision"]) in normalized
    assert "no findings" in normalized


def test_deviation_ledger_prose_matches_live_ledger() -> None:
    frozen = freeze_registration(load_registration())
    executed = {"outcomes": ["primary_score", "secondary_score"], "primary_model": "linear_model"}
    deviations = [
        {"kind": "outcome", "target": "secondary_score", "rationale": "exploratory robustness endpoint"},
        {"kind": "model", "target": "linear_model", "rationale": "robustness sensitivity"},
    ]

    ledger = build_deviation_ledger(frozen, executed, deviations)
    report = compare_analysis_to_registration(frozen, executed, deviations)
    text = (PROJECT_ROOT / "manuscript" / "05_deviations.md").read_text(encoding="utf-8")

    assert f"{report.integrity_score:.1f}" in text
    assert f"{report.integrity_score:.1f}" == "0.9"
    for row in ledger:
        assert row.target in text
        assert row.severity in text


def test_review_artifacts_match_fresh_regeneration() -> None:
    """Committed review artifacts must equal a fresh deterministic regeneration.

    Mirrors ``scripts/generate_review_artifacts.py`` exactly so the committed
    packet, ledger, sensitivity findings, and adherence report cannot silently
    drift from the frozen registration and executed-analysis fixtures.
    """
    output_dir = PROJECT_ROOT / "output" / "reports"
    if not (output_dir / "frozen_registration.json").is_file():
        pytest.skip("review artifacts are disposable outputs; run scripts/generate_review_artifacts.py first")

    registration = load_registration()
    frozen = freeze_registration(registration)
    sensitivity_rows = cast("list[dict[str, Any]]", frozen.get("sensitivity_analyses", []))
    executed = {"outcomes": ["primary_score", "secondary_score"], "primary_model": "linear_model"}
    deviations = [
        {"kind": "outcome", "target": "secondary_score", "rationale": "exploratory robustness endpoint"},
        {"kind": "model", "target": "linear_model", "rationale": "robustness sensitivity"},
    ]
    adherence = compare_analysis_to_registration(frozen, executed, deviations)
    ledger = build_deviation_ledger(frozen, executed, deviations)
    sensitivity_findings = validate_sensitivity_table(frozen, sensitivity_rows)
    packet = build_review_packet(frozen, executed, deviations, sensitivity_rows)

    fresh = {
        "frozen_registration.json": frozen,
        "registered_report_review_packet.json": packet,
        "deviation_ledger.json": {
            "registration_hash": packet["registration_hash"],
            "rows": tuple(asdict(row) for row in ledger),
        },
        "sensitivity_findings.json": {
            "registration_hash": packet["registration_hash"],
            "findings": tuple(asdict(finding) for finding in sensitivity_findings),
        },
        "adherence_report.json": {
            **asdict(adherence),
            "findings": tuple(asdict(finding) for finding in adherence.findings),
        },
    }
    for filename, payload in fresh.items():
        stored = json.loads((output_dir / filename).read_text(encoding="utf-8"))
        normalized = json.loads(json.dumps(payload, sort_keys=True))
        assert stored == normalized, f"{filename} drifted from a fresh regeneration"

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import pytest

from registered_report import (
    build_deviation_ledger,
    build_review_packet,
    compare_analysis_to_registration,
    freeze_registration,
    registration_hash,
    validate_sensitivity_table,
    validate_registration,
)


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

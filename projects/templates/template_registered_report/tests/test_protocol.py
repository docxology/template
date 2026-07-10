from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

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

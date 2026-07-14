"""Tests for deterministic seed-sensitivity statistics."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from config import load_gold_refinement_config
from seed_sensitivity import (
    run_seed_sensitivity,
    validate_seed_sensitivity_payload,
    write_seed_sensitivity_report,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_declared_seed_study_reports_distribution_and_precision():
    config = load_gold_refinement_config(PROJECT_ROOT)
    report = run_seed_sensitivity(config)

    assert report.sample_size == 1024
    assert report.seed_start == 0
    assert report.seed_end == 1023
    assert report.token_count == config.total_token_count
    assert report.unique_plan_count == report.sample_size
    assert report.canonical_matches == 1
    assert report.inventory_coverage == 1.0
    assert report.agreement_interval[0] <= report.mean_agreement <= report.agreement_interval[1]
    assert report.hoeffding_radius <= report.precision_target
    assert report.meets_precision_target is True
    assert report.minimum_sample_size_for_precision_target == 738
    assert report.bootstrap_replicates == 2000
    assert report.bootstrap_mean_interval[0] <= report.mean_agreement <= report.bootstrap_mean_interval[1]
    assert all(len(record.plan_digest) == 64 for record in report.records)
    assert [row["sample_size"] for row in report.sample_size_ladder] == [16, 32, 64, 128, 256, 512, 1024]


def test_small_custom_seed_study_is_deterministic():
    config = load_gold_refinement_config(PROJECT_ROOT)
    config = replace(
        config,
        seed_sensitivity={
            "sample_size": 8,
            "seed_start": 10,
            "sample_size_ladder": [2, 4, 8],
            "agreement_threshold": 0.5,
        },
    )
    first = run_seed_sensitivity(config)
    second = run_seed_sensitivity(config)

    assert first.to_dict() == second.to_dict()
    assert len(first.records) == 8
    assert [row["sample_size"] for row in first.sample_size_ladder] == [2, 4, 8]


def test_invalid_seed_study_settings_raise():
    config = load_gold_refinement_config(PROJECT_ROOT)
    with pytest.raises(ValueError, match="sample_size"):
        run_seed_sensitivity(replace(config, seed_sensitivity={"sample_size": 0}))


def test_seed_report_writer_creates_auditable_json(tmp_path):
    config = load_gold_refinement_config(PROJECT_ROOT)
    report = run_seed_sensitivity(replace(config, seed_sensitivity={"sample_size": 4}))
    output_path = write_seed_sensitivity_report(report, tmp_path / "data" / "seed_sensitivity.json")

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "template-gold-refinement-seed-sensitivity-v1"
    assert payload["sample_size"] == 4
    assert len(payload["records"]) == 4


def test_seed_report_validator_rejects_tampered_generated_metric():
    config = load_gold_refinement_config(PROJECT_ROOT)
    report = run_seed_sensitivity(replace(config, seed_sensitivity={"sample_size": 8}))
    payload = report.to_dict()
    payload["mean_agreement"] = 1.0

    issues = validate_seed_sensitivity_payload(
        replace(config, seed_sensitivity={"sample_size": 8}),
        payload,
    )

    assert issues
    assert "mean_agreement" in issues[0]


def test_seed_report_validator_accepts_deterministic_payload():
    config = load_gold_refinement_config(PROJECT_ROOT)
    report = run_seed_sensitivity(replace(config, seed_sensitivity={"sample_size": 8}))

    assert (
        validate_seed_sensitivity_payload(config=replace(config, seed_sensitivity={"sample_size": 8}), payload=report)
        == ()
    )

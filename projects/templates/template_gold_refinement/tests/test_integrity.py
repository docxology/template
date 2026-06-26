from __future__ import annotations

import json
from pathlib import Path

from config import load_gold_refinement_config
from integrity import (
    build_evidence_tiers,
    build_integrity_dimensions,
    evidence_tier_records,
    evidence_tier_table_rows,
    integrity_dimension_table_rows,
    integrity_owner_table_rows,
    integrity_records,
    integrity_summary_line,
)


def test_integrity_dimensions_are_unique_and_source_owned():
    cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
    dimensions = build_integrity_dimensions(cfg)
    ids = [item.dimension_id for item in dimensions]
    assert len(dimensions) == 8
    assert len(ids) == len(set(ids))
    assert all(item.evidence_surface for item in dimensions)
    assert all(item.validator for item in dimensions)
    assert all(1 <= item.severity <= 5 for item in dimensions)
    assert all(1 <= item.detectability <= 5 for item in dimensions)


def test_integrity_tables_include_risk_and_owners():
    cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
    dimensions = build_integrity_dimensions(cfg)
    dimension_rows = integrity_dimension_table_rows(dimensions)
    owner_rows = integrity_owner_table_rows(dimensions)
    summary = integrity_summary_line(dimensions)
    assert "I4" in dimension_rows
    assert "Analogy boundary" in dimension_rows
    assert "claim ledger" in owner_rows
    assert "highest residual risk" in summary


def test_evidence_tiers_use_shared_registry_when_available():
    cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
    dimensions = build_integrity_dimensions(cfg)
    tiers = build_evidence_tiers(
        {
            "source_tiers": {
                "generated_metric": 3,
                "claim_ledger": 2,
            }
        },
        dimensions,
    )
    assert [tier.tier for tier in tiers] == ["generated_metric", "claim_ledger"]
    rows = evidence_tier_table_rows(tiers)
    assert "Numbers regenerated from project analysis" in rows


def test_integrity_records_are_json_serializable():
    cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
    dimensions = build_integrity_dimensions(cfg)
    tiers = build_evidence_tiers({}, dimensions)
    payload = json.dumps(
        {
            "dimensions": integrity_records(dimensions),
            "tiers": evidence_tier_records(tiers),
        }
    )
    assert "Monotone refinery" in payload

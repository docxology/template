from __future__ import annotations

import json
from pathlib import Path

from config import load_gold_refinement_config
from security_assay import (
    SecurityAssayRecord,
    build_security_assay,
    security_assay_records,
    security_assay_summary_line,
    security_assay_table_rows,
)


def test_security_assay_records_are_complete_and_unique():
    cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
    records = build_security_assay(cfg)
    assert len(records) == 5
    assert [item.assay_id for item in records] == ["S1", "S2", "S3", "S4", "S5"]
    assert all(item.threat for item in records)
    assert all(item.standard for item in records)
    assert all(item.evidence_surface for item in records)
    assert all(item.validator for item in records)
    assert all(item.claim_boundary for item in records)
    assert all(item.is_complete for item in records)


def test_security_assay_table_and_summary_bound_scan_claims():
    cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
    records = build_security_assay(cfg)
    rows = security_assay_table_rows(records)
    summary = security_assay_summary_line(records)
    assert "NIST SP 800-207" in rows
    assert "SLSA v1.2" in rows
    assert "MITRE ATT&CK" in rows
    assert "Codex Security" in rows
    assert "no real scan finding is claimed" in rows
    assert "5 adversarial assay rows" in summary
    assert "not completed scan findings" in summary


def test_security_assay_records_are_json_serializable():
    cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
    payload = json.dumps(security_assay_records(build_security_assay(cfg)))
    assert "secure-by-design overclaim" in payload


def test_security_assay_completeness_is_schema_level_only():
    incomplete = SecurityAssayRecord("S1", "threat", "standard", "", "validator", "boundary")
    assert not incomplete.is_complete

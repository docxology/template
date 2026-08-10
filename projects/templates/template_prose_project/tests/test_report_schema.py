"""Strict report-schema regression controls."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.pipeline import CheckResult, build_evidence_summary
from src.pipeline.report_schema import validate_evidence_summary


def _report() -> SimpleNamespace:
    metrics = SimpleNamespace(
        long_sentence_count=0,
        passive_count=0,
        hedge_count=0,
        citation_count=1,
    )
    structure = SimpleNamespace(has_h1=True, has_skipped_level=False, headings=["h1"])
    file_report = SimpleNamespace(quality=metrics, structure=structure)
    return SimpleNamespace(
        files=[file_report],
        total_words=10,
        avg_flesch_reading_ease=70.0,
        avg_flesch_kincaid_grade=11.0,
        avg_gunning_fog=9.0,
        citation_keys=["key"],
    )


def test_built_summary_matches_schema() -> None:
    summary = build_evidence_summary(
        _report(),
        [CheckResult("bibliography_consistency", True, details={"missing": [], "unused": []})],
    )
    validate_evidence_summary(summary)


def test_unknown_top_level_report_field_is_rejected() -> None:
    summary = build_evidence_summary(_report(), [CheckResult("x", True)])
    summary["stale_field"] = True
    with pytest.raises(ValueError, match="unknown"):
        validate_evidence_summary(summary)


def test_report_schema_drift_is_rejected() -> None:
    summary = build_evidence_summary(_report(), [CheckResult("x", True)])
    summary["schema_version"] = "template-prose/evidence-summary/0"
    with pytest.raises(ValueError, match="Unsupported"):
        validate_evidence_summary(summary)

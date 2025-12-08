"""Tests for infrastructure.reporting.error_aggregator."""

from __future__ import annotations

import json

from infrastructure.reporting.error_aggregator import (
    ErrorAggregator,
    get_error_aggregator,
    reset_error_aggregator,
)


def test_add_error_and_summary(tmp_path):
    agg = ErrorAggregator()
    agg.add_error("test_failure", "boom", stage="tests", file="f.py", line=12)
    agg.add_error("validation_error", "warn", severity="warning")

    summary = agg.get_summary()

    assert summary["total_errors"] == 1
    assert summary["total_warnings"] == 1
    assert summary["errors_by_type"]["test_failure"] == 1
    assert summary["warnings_by_type"]["validation_error"] == 1
    assert summary["errors"][0]["file"] == "f.py"


def test_actionable_fixes_priorities():
    agg = ErrorAggregator()
    agg.add_error("test_failure", "fail")
    agg.add_error("validation_error", "val")
    agg.add_error("stage_failure", "stage")
    agg.add_error("other", "misc", suggestions=["check"])

    fixes = agg.get_actionable_fixes()

    priorities = {fix["priority"] for fix in fixes}
    assert "high" in priorities
    assert any(fix["issue"] == "1 test failure(s)" for fix in fixes)
    assert any(
        fix["priority"] == "medium" and fix["issue"].endswith("other error(s)")
        for fix in fixes
    )


def test_save_report_creates_files(tmp_path):
    agg = ErrorAggregator()
    agg.add_error("test_failure", "fail message", stage="tests")

    json_path = agg.save_report(tmp_path)
    md_path = tmp_path / "error_summary.md"

    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text())
    assert data["total_errors"] == 1
    assert md_path.read_text().startswith("# Error Summary Report")


def test_global_aggregator_reset():
    first = get_error_aggregator()
    second = get_error_aggregator()
    assert first is second

    reset_error_aggregator()
    third = get_error_aggregator()
    assert third is not first



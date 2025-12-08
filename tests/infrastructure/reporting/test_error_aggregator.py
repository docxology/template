from __future__ import annotations

import json
from pathlib import Path

from infrastructure.reporting.error_aggregator import (
    ErrorAggregator,
    get_error_aggregator,
    reset_error_aggregator,
)


def test_error_aggregator_summary_and_actionable_fixes() -> None:
    reset_error_aggregator()
    aggregator = get_error_aggregator()

    aggregator.add_error(
        error_type="test_failure",
        message="Unit test failed",
        stage="tests",
        file="tests/test_example.py",
        severity="error",
        suggestions=["Review assertion", "Check fixtures"],
    )
    aggregator.add_error(
        error_type="validation_error",
        message="PDF validation failed",
        stage="validation",
        severity="error",
    )
    aggregator.add_error(
        error_type="stage_failure",
        message="Stage crashed",
        stage="analysis",
        severity="error",
    )
    aggregator.add_error(
        error_type="performance",
        message="Slow step",
        stage="analysis",
        severity="warning",
    )

    summary = aggregator.get_summary()
    assert summary["total_errors"] == 3
    assert summary["total_warnings"] == 1
    assert summary["errors_by_type"]["test_failure"] == 1
    assert summary["warnings_by_type"]["performance"] == 1

    fixes = aggregator.get_actionable_fixes()
    assert any(fix["issue"].startswith("1 test failure") for fix in fixes)
    assert any(fix["issue"].startswith("1 validation error") for fix in fixes)
    assert any(fix["issue"].startswith("1 stage failure") for fix in fixes)


def test_error_aggregator_save_report_creates_json_and_markdown(tmp_path: Path) -> None:
    aggregator = ErrorAggregator()
    aggregator.add_error("test_failure", "Test failed", stage="tests")
    aggregator.add_error("validation_error", "Validation failed", stage="validation")

    json_path = aggregator.save_report(tmp_path)
    md_path = tmp_path / "error_summary.md"

    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text())
    assert data["total_errors"] == 2
    assert data["actionable_fixes"]

    md_content = md_path.read_text()
    assert "Error Summary Report" in md_content
    assert "Actionable Fixes" in md_content


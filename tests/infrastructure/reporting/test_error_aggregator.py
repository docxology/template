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


def test_error_entry_to_dict() -> None:
    """Test ErrorEntry to_dict method."""
    from infrastructure.reporting.error_aggregator import ErrorEntry
    
    entry = ErrorEntry(
        type="test_failure",
        message="Test failed",
        stage="tests",
        file="test.py",
        line=42,
        severity="error",
        suggestions=["Fix it"],
        context={"key": "value"}
    )
    entry_dict = entry.to_dict()
    assert entry_dict["type"] == "test_failure"
    assert entry_dict["message"] == "Test failed"
    assert entry_dict["stage"] == "tests"
    assert entry_dict["file"] == "test.py"
    assert entry_dict["line"] == 42
    assert entry_dict["severity"] == "error"
    assert entry_dict["suggestions"] == ["Fix it"]
    assert entry_dict["context"] == {"key": "value"}


def test_error_aggregator_empty() -> None:
    """Test ErrorAggregator with no errors."""
    aggregator = ErrorAggregator()
    summary = aggregator.get_summary()
    assert summary["total_errors"] == 0
    assert summary["total_warnings"] == 0
    assert summary["errors_by_type"] == {}
    assert summary["warnings_by_type"] == {}
    
    fixes = aggregator.get_actionable_fixes()
    assert fixes == []


def test_error_aggregator_warning_severity() -> None:
    """Test ErrorAggregator categorizes warnings correctly."""
    aggregator = ErrorAggregator()
    aggregator.add_error("performance", "Slow", severity="warning")
    aggregator.add_error("info", "Info message", severity="info")
    
    summary = aggregator.get_summary()
    assert summary["total_errors"] == 0
    assert summary["total_warnings"] == 2
    assert "performance" in summary["warnings_by_type"]
    assert "info" in summary["warnings_by_type"]


def test_error_aggregator_get_actionable_fixes_generic() -> None:
    """Test ErrorAggregator generates generic fixes for unknown error types."""
    aggregator = ErrorAggregator()
    aggregator.add_error("unknown_error", "Something went wrong", suggestions=["Check logs"])
    
    fixes = aggregator.get_actionable_fixes()
    assert len(fixes) == 1
    assert fixes[0]["priority"] == "medium"
    assert "unknown_error" in fixes[0]["issue"]
    assert fixes[0]["actions"] == ["Check logs"]


def test_error_aggregator_get_actionable_fixes_no_suggestions() -> None:
    """Test ErrorAggregator handles errors without suggestions."""
    aggregator = ErrorAggregator()
    aggregator.add_error("unknown_error", "Something went wrong")
    
    fixes = aggregator.get_actionable_fixes()
    assert len(fixes) == 1
    assert "Review error messages" in fixes[0]["actions"]


def test_error_aggregator_multiple_same_type() -> None:
    """Test ErrorAggregator with multiple errors of same type."""
    aggregator = ErrorAggregator()
    aggregator.add_error("test_failure", "Test 1 failed")
    aggregator.add_error("test_failure", "Test 2 failed")
    aggregator.add_error("test_failure", "Test 3 failed")
    
    summary = aggregator.get_summary()
    assert summary["errors_by_type"]["test_failure"] == 3
    
    fixes = aggregator.get_actionable_fixes()
    test_fix = next(fix for fix in fixes if "test failure" in fix["issue"])
    assert "3 test failure" in test_fix["issue"]


def test_get_error_aggregator_singleton() -> None:
    """Test get_error_aggregator returns same instance."""
    reset_error_aggregator()
    aggregator1 = get_error_aggregator()
    aggregator2 = get_error_aggregator()
    assert aggregator1 is aggregator2


def test_reset_error_aggregator() -> None:
    """Test reset_error_aggregator creates new instance."""
    reset_error_aggregator()
    aggregator1 = get_error_aggregator()
    aggregator1.add_error("test", "error")
    
    reset_error_aggregator()
    aggregator2 = get_error_aggregator()
    assert aggregator2 is not aggregator1
    assert len(aggregator2.get_summary()["errors"]) == 0


def test_error_aggregator_markdown_truncation(tmp_path: Path) -> None:
    """Test ErrorAggregator markdown report truncates at 10 errors."""
    aggregator = ErrorAggregator()
    for i in range(15):
        aggregator.add_error("test_failure", f"Error {i}")
    
    aggregator.save_report(tmp_path)
    md_content = (tmp_path / "error_summary.md").read_text()
    assert "Error 1" in md_content
    assert "Error 10" in md_content
    assert "... and 5 more errors" in md_content












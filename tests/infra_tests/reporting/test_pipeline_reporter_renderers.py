"""Markdown/HTML renderer output tests (formerly part of test_pipeline_reporter.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.reporting.pipeline_html import generate_html_report
from infrastructure.reporting.pipeline_io import (
    generate_error_markdown,
    generate_validation_markdown,
)
from infrastructure.reporting.pipeline_markdown import _generate_pipeline_markdown
from infrastructure.reporting.pipeline_report_model import generate_pipeline_report

from ._pipeline_reporter_helpers import _stage_results


def test__generate_pipeline_markdown_includes_sections() -> None:
    report = generate_pipeline_report(
        stage_results=_stage_results(),
        total_duration=9.5,
        repo_root=Path("."),
        test_results={
            "summary": {
                "total_tests": 5,
                "total_passed": 4,
                "total_failed": 1,
                "total_skipped": 0,
                "infrastructure_coverage": 61.48,
                "project_coverage": 99.88,
            }
        },
        validation_results={"checks": {"pdf": True}},
        performance_metrics={"duration": 9.5},
        error_summary={"total_errors": 2},
        output_statistics={"pdf_files": 2, "figures": 1, "data_files": 3},
    )

    md_content = _generate_pipeline_markdown(report)
    assert "Test Results" in md_content
    assert "Validation Results" in md_content
    assert "Performance Metrics" in md_content
    assert "Error Summary" in md_content
    assert "Output Statistics" in md_content
    assert "Infrastructure Coverage" in md_content
    assert "Project Coverage" in md_content


def test_generate_html_report_includes_test_coverage() -> None:
    report = generate_pipeline_report(
        stage_results=_stage_results(),
        total_duration=5.0,
        repo_root=Path("."),
        test_results={
            "summary": {
                "total_tests": 3,
                "total_passed": 3,
                "total_failed": 0,
                "total_skipped": 0,
                "infrastructure_coverage": 70.0,
                "project_coverage": 99.0,
            }
        },
    )

    html = generate_html_report(report)
    assert "Pipeline Execution Report" in html
    assert "Infrastructure Coverage" in html
    assert "Project Coverage" in html


def test__generate_pipeline_markdown_empty_sections() -> None:
    """Test markdown report generation with no optional sections."""
    report = generate_pipeline_report(
        stage_results=[{"name": "setup", "exit_code": 0, "duration": 1.0}],
        total_duration=1.0,
        repo_root=Path("."),
    )
    md_content = _generate_pipeline_markdown(report)
    assert "Pipeline Execution Report" in md_content
    assert "Summary" in md_content
    assert "Stage Results" in md_content
    # Should not have optional sections
    assert "Test Results" not in md_content
    assert "Error Summary" not in md_content


def test_generate_html_report_all_stages_passed() -> None:
    """Test HTML report with all stages passed."""
    report = generate_pipeline_report(
        stage_results=[
            {"name": "setup", "exit_code": 0, "duration": 1.0},
            {"name": "tests", "exit_code": 0, "duration": 2.0},
        ],
        total_duration=3.0,
        repo_root=Path("."),
    )
    html = generate_html_report(report)
    assert "100.0%" in html  # Success rate
    assert "status-passed" in html


def test_generate_validation_markdown_empty_checks() -> None:
    """Test validation markdown with empty checks."""
    results = {"checks": {}}
    md = generate_validation_markdown(results)
    assert "Validation Report" in md
    assert "Validation Checks" in md


def test_generate_error_markdown_no_errors() -> None:
    """Test error markdown generation with no errors."""
    summary = {"total_errors": 0, "errors_by_type": {}, "errors": []}
    md = generate_error_markdown(summary)
    assert "Error Summary" in md
    assert "**Total Errors:** 0" in md


def test_generate_error_markdown_with_suggestions() -> None:
    """Test error markdown includes suggestions when present."""
    summary = {
        "total_errors": 1,
        "errors_by_type": {"test_failure": 1},
        "errors": [
            {
                "type": "test_failure",
                "message": "Test failed",
                "suggestions": ["Fix assertion", "Check data"],
            }
        ],
    }
    md = generate_error_markdown(summary)
    assert "Fix assertion" in md
    assert "Check data" in md


class TestValidationMarkdownEdgeCases:
    """Test edge cases in validation markdown generation."""

    def test_validation_markdown_no_checks_key(self) -> None:
        """Test validation markdown when no checks key present."""
        results = {}
        md = generate_validation_markdown(results)
        assert "Validation Report" in md
        # Should not have Validation Checks section
        assert "Validation Checks" not in md

    def test_validation_markdown_mixed_results(self) -> None:
        """Test validation markdown with mixed pass/fail results."""
        results = {
            "checks": {
                "pdf_valid": True,
                "markdown_valid": False,
                "links_valid": True,
            }
        }
        md = generate_validation_markdown(results)
        assert "✅ PASS: pdf_valid" in md
        assert "❌ FAIL: markdown_valid" in md
        assert "✅ PASS: links_valid" in md

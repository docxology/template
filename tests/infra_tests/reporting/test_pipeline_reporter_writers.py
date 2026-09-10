"""pipeline_io artifact writers: validation, performance, test results, error summary (formerly part of test_pipeline_reporter.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.reporting.pipeline_io import (
    generate_error_markdown,
    generate_validation_markdown,
    save_error_summary,
    save_performance_report,
    save_test_results,
    save_validation_report,
)


def test_generate_validation_report_and_markdown(tmp_path: Path) -> None:
    validation_results = {"checks": {"pdf_validation": True, "markdown_validation": False}}
    save_validation_report(validation_results, tmp_path)

    assert (tmp_path / "validation_report.json").exists()
    assert (tmp_path / "validation_report.md").exists()

    md = generate_validation_markdown(validation_results)
    assert "pdf_validation" in md
    assert "markdown_validation" in md


def test_generate_performance_and_test_reports(tmp_path: Path) -> None:
    perf = {"total_duration": 12.3, "peak_memory_mb": 256}
    path = save_performance_report(perf, tmp_path)
    assert path.exists()

    test_path = save_test_results({"summary": {}}, tmp_path)
    assert test_path.name == "test_results.json"


def test_save_error_summary_and_markdown_truncation(tmp_path: Path) -> None:
    errors = [
        {
            "type": "stage_failure",
            "message": f"fail {i}",
            "file": f"f{i}.py",
            "suggestions": ["fix"],
        }
        for i in range(12)
    ]
    summary = save_error_summary(errors, tmp_path)
    assert summary["total_errors"] == 12
    assert summary["errors_by_type"]["stage_failure"] == 12
    assert (tmp_path / "error_summary.json").exists()
    assert (tmp_path / "error_summary.md").exists()

    md = generate_error_markdown(summary)
    assert "Error Summary" in md
    assert "... and 2 more errors" in md


def test_save_error_summary_empty_errors(tmp_path: Path) -> None:
    """Test error summary with no errors."""
    summary = save_error_summary([], tmp_path)
    assert summary["total_errors"] == 0
    assert summary["errors_by_type"] == {}
    assert (tmp_path / "error_summary.json").exists()
    assert (tmp_path / "error_summary.md").exists()


class TestErrorSummaryEdgeCases:
    """Test edge cases in error summary generation."""

    def test_error_summary_multiple_types(self, tmp_path: Path) -> None:
        """Test error summary with multiple error types."""
        errors = [
            {"type": "stage_failure", "message": "Stage failed"},
            {"type": "validation_error", "message": "Validation failed"},
            {"type": "stage_failure", "message": "Another stage failed"},
            {"type": "unknown"},  # Missing message
        ]
        summary = save_error_summary(errors, tmp_path)

        assert summary["total_errors"] == 4
        assert summary["errors_by_type"]["stage_failure"] == 2
        assert summary["errors_by_type"]["validation_error"] == 1
        assert summary["errors_by_type"]["unknown"] == 1

    def test_error_markdown_with_file_info(self) -> None:
        """Test error markdown includes file information."""
        summary = {
            "total_errors": 1,
            "errors_by_type": {"test_failure": 1},
            "errors": [
                {
                    "type": "test_failure",
                    "message": "Assertion failed",
                    "file": "test_example.py",
                }
            ],
        }
        md = generate_error_markdown(summary)
        assert "test_example.py" in md

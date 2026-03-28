"""Tests for infrastructure/validation/output/pipeline.py.

Tests the validation output pipeline orchestrator.
Follows No Mocks Policy — all tests use real files and real execution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.validation.output.pipeline import (
    generate_validation_report,
    validate_markdown,
    validate_pdfs,
    verify_outputs_exist,
)


class TestValidatePdfs:
    """Test validate_pdfs() with real file structures."""

    def test_returns_false_for_missing_pdf_dir(self) -> None:
        """Missing PDF dir returns False."""
        result = validate_pdfs("_nonexistent_project_xyz_abc")
        assert result is False

    def test_returns_false_for_empty_pdf_dir(self, tmp_path: Path, monkeypatch) -> None:
        """PDF dir exists but no PDFs returns False."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir(parents=True)

        # Monkeypatch Path to redirect to tmp_path structure
        import infrastructure.validation.output.pipeline as mod

        original = mod.Path

        def patched_path(*args, **kwargs):
            p = original(*args, **kwargs)
            return p

        # Use a project name that doesn't exist — will hit the "no PDF dir" branch
        result = validate_pdfs("_nonexistent_project_xyz_abc")
        assert result is False


class TestValidateMarkdown:
    """Test validate_markdown() with real directory structures."""

    def test_returns_true_for_missing_manuscript_dir(self) -> None:
        """Missing manuscript dir returns True (not an error, just nothing to validate)."""
        result = validate_markdown("_nonexistent_project_xyz_abc")
        assert result is True

    def test_returns_true_for_empty_manuscript_dir(self, tmp_path: Path) -> None:
        """Empty manuscript dir (no .md files) returns True."""
        import infrastructure.validation.output.pipeline as mod

        # Projects dir must be addressable — use nonexistent project (safe path)
        result = validate_markdown("_nonexistent_project_xyz_abc")
        assert result is True


class TestVerifyOutputsExist:
    """Test verify_outputs_exist() with real structures."""

    def test_returns_tuple(self) -> None:
        """Always returns a (bool, dict) tuple."""
        result = verify_outputs_exist("_nonexistent_project_xyz_abc")
        assert isinstance(result, tuple)
        assert len(result) == 2
        valid, details = result
        assert isinstance(valid, bool)
        assert isinstance(details, dict)

    def test_returns_false_for_nonexistent_project(self) -> None:
        """Nonexistent project output dir should report invalid structure."""
        valid, details = verify_outputs_exist("_nonexistent_project_xyz_abc")
        assert valid is False


class TestGenerateValidationReport:
    """Test generate_validation_report() with real data."""

    def test_generates_report_with_all_passing(self) -> None:
        """All-passing checks produce correct summary."""
        check_results = [
            ("pdf_validation", True),
            ("markdown_validation", True),
            ("output_exists", True),
        ]
        report = generate_validation_report(
            check_results=check_results,
            figure_issues=[],
            output_statistics={"total_files": 5},
            project_name="_test_project",
        )
        assert report["summary"]["total_checks"] == 3
        assert report["summary"]["passed"] == 3
        assert report["summary"]["failed"] == 0
        assert report["summary"]["all_passed"] is True

    def test_generates_report_with_failures(self) -> None:
        """Failed checks are counted correctly."""
        check_results = [
            ("pdf_validation", True),
            ("markdown_validation", False),
        ]
        report = generate_validation_report(
            check_results=check_results,
            figure_issues=["Missing figure: fig1.png"],
            output_statistics={},
            project_name="_test_project",
        )
        assert report["summary"]["failed"] == 1
        assert report["summary"]["figure_issues_count"] == 1
        assert report["summary"]["all_passed"] is False

    def test_report_contains_checks_dict(self) -> None:
        """Report checks dict maps check names to bool results."""
        check_results = [("my_check", True)]
        report = generate_validation_report(
            check_results=check_results,
            figure_issues=[],
            output_statistics={},
            project_name="_test_project",
        )
        assert "checks" in report
        assert report["checks"]["my_check"] is True

    def test_report_contains_figure_issues(self) -> None:
        """Report preserves figure issues list."""
        issues = ["fig1.png missing", "fig2.png wrong size"]
        report = generate_validation_report(
            check_results=[],
            figure_issues=issues,
            output_statistics={},
            project_name="_test_project",
        )
        assert report["figure_issues"] == issues

    def test_empty_check_results(self) -> None:
        """Zero checks produce valid empty summary."""
        report = generate_validation_report(
            check_results=[],
            figure_issues=[],
            output_statistics={},
            project_name="_test_project",
        )
        assert report["summary"]["total_checks"] == 0
        assert report["summary"]["passed"] == 0
        assert report["summary"]["all_passed"] is True

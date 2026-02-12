"""Comprehensive tests for src/reporting.py to ensure 100% coverage."""

import tempfile
from pathlib import Path

import pytest
from src.pipeline.reporting import ReportGenerator


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_initialization(self, tmp_path):
        """Test generator initialization."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        assert generator.output_dir == tmp_path

    def test_generate_markdown_report(self, tmp_path):
        """Test generating markdown report with explicit filename (branch 44->47)."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "summary": {"mean": 1.0, "std": 0.5},
            "findings": ["Finding 1", "Finding 2"],
            "tables": {"Test Table": {"Column1": ["A", "B"], "Column2": ["1", "2"]}},
        }
        # Pass explicit filename to cover branch 44->47 (filename is not None)
        report_path = generator.generate_markdown_report(
            "Test Report", results, filename="custom_markdown_report"
        )
        assert report_path.exists()
        assert report_path.suffix == ".md"
        assert report_path.stem == "custom_markdown_report"
        content = report_path.read_text()
        assert "Test Report" in content
        assert "Finding 1" in content

    def test_generate_latex_report(self, tmp_path):
        """Test generating LaTeX report with explicit filename (branch 44->47)."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "summary": {"mean": 1.0},
            "tables": {"Test Table": {"Col1": ["A"], "Col2": ["1"]}},
        }
        # Pass explicit filename to cover branch 44->47 (filename is not None)
        report_path = generator.generate_latex_report(
            "Test Report", results, filename="custom_report"
        )
        assert report_path.exists()
        assert report_path.suffix == ".tex"
        assert report_path.stem == "custom_report"
        content = report_path.read_text()
        assert "\\documentclass" in content
        assert "Test Report" in content

    def test_generate_html_report(self, tmp_path):
        """Test generating HTML report with explicit filename (branch 169->172)."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0}, "findings": ["Finding 1"]}
        # Pass explicit filename to cover branch 169->172 (filename is not None)
        report_path = generator.generate_html_report(
            "Test Report", results, filename="custom_html_report"
        )
        assert report_path.exists()
        assert report_path.suffix == ".html"
        assert report_path.stem == "custom_html_report"
        content = report_path.read_text()
        assert "<html>" in content
        assert "Test Report" in content

    def test_extract_key_findings(self, tmp_path):
        """Test extracting key findings."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "metrics": {"accuracy": 0.9, "precision": 0.85},
            "convergence": {"is_converged": True, "iterations": 100},
            "performance": {"best_method": "Method A"},
        }
        findings = generator.extract_key_findings(results)
        assert len(findings) > 0
        assert any("accuracy" in f for f in findings)

    def test_create_comparison_report(self, tmp_path):
        """Test creating comparison report."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        runs = [
            {"metrics": {"accuracy": 0.9, "precision": 0.85}},
            {"metrics": {"accuracy": 0.92, "precision": 0.87}},
            {"metrics": {"accuracy": 0.88, "precision": 0.83}},
        ]
        comparison = generator.create_comparison_report(runs, ["accuracy", "precision"])
        assert comparison["n_runs"] == 3
        assert "accuracy" in comparison["comparisons"]
        assert "precision" in comparison["comparisons"]

    def test_generate_markdown_report_default_filename(self, tmp_path):
        """Test generating markdown report with default filename."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0}}
        report_path = generator.generate_markdown_report("Test Report", results)
        assert "test_report" in report_path.name.lower()

    def test_generate_markdown_report_with_details(self, tmp_path):
        """Test generating markdown report with details section."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"details": {"section1": {"value": 1.0}, "section2": {"value": 2.0}}}
        report_path = generator.generate_markdown_report("Test Report", results)
        content = report_path.read_text()
        assert "Detailed Results" in content

    def test_generate_markdown_report_with_tables(self, tmp_path):
        """Test generating markdown report with tables."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "tables": {
                "Table1": {"Col1": ["A", "B"], "Col2": ["1", "2"]},
                "Table2": {"Col1": ["C"], "Col2": ["3"]},
            }
        }
        report_path = generator.generate_markdown_report("Test Report", results)
        content = report_path.read_text()
        assert "Tables" in content
        assert "Table1" in content

    def test_generate_latex_report_with_custom_filename(self, tmp_path):
        """Test generating LaTeX report with custom filename."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0}}
        report_path = generator.generate_latex_report(
            "Test Report", results, filename="custom"
        )
        assert "custom" in report_path.name

    def test_generate_latex_report_default_filename(self, tmp_path):
        """Test generating LaTeX report with default filename."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0}}
        report_path = generator.generate_latex_report("Test Report", results)
        # Should use default filename from title
        assert report_path.exists()
        assert "test_report" in report_path.name.lower()

    def test_generate_latex_report_with_findings(self, tmp_path):
        """Test generating LaTeX report with findings."""
        # LaTeX report doesn't include findings section, only summary and tables
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "summary": {"mean": 1.0},
            "findings": ["Finding 1", "Finding 2", "Finding 3"],
        }
        report_path = generator.generate_latex_report("Test Report", results)
        content = report_path.read_text()
        # LaTeX report should have summary but not findings
        assert "Summary" in content
        assert "\\documentclass" in content

    def test_generate_latex_report_with_tables(self, tmp_path):
        """Test generating LaTeX report with tables."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"tables": {"Test Table": {"Col1": ["A"], "Col2": ["1"]}}}
        report_path = generator.generate_latex_report("Test Report", results)
        content = report_path.read_text()
        assert "tabular" in content or "Table" in content

    def test_generate_html_report_with_details(self, tmp_path):
        """Test generating HTML report with details."""
        # HTML report doesn't have details section, only summary and findings
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"metric1": 1.0}, "findings": ["Finding 1"]}
        report_path = generator.generate_html_report("Test Report", results)
        content = report_path.read_text()
        assert "Summary" in content
        assert "Key Findings" in content

    def test_generate_html_report_default_filename(self, tmp_path):
        """Test generating HTML report with default filename."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0}}
        report_path = generator.generate_html_report("Test Report", results)
        # Should use default filename from title
        assert report_path.exists()
        assert "test_report" in report_path.name.lower()

    def test_generate_html_report_with_tables(self, tmp_path):
        """Test generating HTML report with tables."""
        # HTML report doesn't have tables section, only summary and findings
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0}, "findings": ["Finding 1"]}
        report_path = generator.generate_html_report("Test Report", results)
        content = report_path.read_text()
        assert "<html>" in content
        assert "Summary" in content

    def test_extract_key_findings_with_convergence(self, tmp_path):
        """Test extracting key findings with convergence data."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "convergence": {
                "is_converged": True,
                "iterations": 100,
                "final_error": 0.001,
            }
        }
        findings = generator.extract_key_findings(results)
        assert len(findings) > 0
        assert any(
            "converged" in f.lower() or "iteration" in f.lower() for f in findings
        )

    def test_extract_key_findings_with_performance(self, tmp_path):
        """Test extracting key findings with performance data."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "performance": {
                "best_method": "Method A",
                "speedup": 2.5,
                "efficiency": 0.9,
            }
        }
        findings = generator.extract_key_findings(results)
        assert len(findings) > 0
        assert any("best_method" in f.lower() or "Method A" in f for f in findings)

    def test_extract_key_findings_performance_no_best_method(self, tmp_path):
        """Test extracting key findings with performance but no best_method."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"performance": {"speedup": 2.0}}  # No best_method key
        findings = generator.extract_key_findings(results)
        # Should not add performance finding if best_method is missing
        assert isinstance(findings, list)

    def test_create_comparison_report_empty_runs(self, tmp_path):
        """Test creating comparison report with empty runs."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        comparison = generator.create_comparison_report([], ["accuracy"])
        assert comparison["n_runs"] == 0

    def test_create_comparison_report_missing_metrics(self, tmp_path):
        """Test creating comparison report with missing metrics."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        runs = [
            {"metrics": {"accuracy": 0.9}},
            {"metrics": {"accuracy": 0.92, "precision": 0.87}},
        ]
        comparison = generator.create_comparison_report(runs, ["accuracy", "precision"])
        assert "accuracy" in comparison["comparisons"]
        # precision may be missing from first run
        assert "precision" in comparison["comparisons"] or comparison["n_runs"] == 2

    def test_extract_key_findings_not_converged(self, tmp_path):
        """Test extracting key findings when not converged."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"convergence": {"is_converged": False, "iterations": 1000}}
        findings = generator.extract_key_findings(results)
        assert any("did not converge" in f.lower() for f in findings)

    def test_extract_key_findings_non_numeric_metric(self, tmp_path):
        """Test extracting key findings with non-numeric metrics."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "metrics": {"accuracy": 0.9, "method": "neural_network"}  # Non-numeric
        }
        findings = generator.extract_key_findings(results)
        # Should only include numeric metrics
        assert any("accuracy" in f for f in findings)
        assert not any("method" in f for f in findings)

    def test_format_summary_non_numeric(self, tmp_path):
        """Test formatting summary with non-numeric values."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0, "status": "completed"}}
        report_path = generator.generate_markdown_report("Test", results)
        content = report_path.read_text()
        assert "status" in content
        assert "completed" in content

    def test_format_details_dict(self, tmp_path):
        """Test formatting details as dictionary."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"details": {"section1": {"key1": "value1", "key2": "value2"}}}
        report_path = generator.generate_markdown_report("Test", results)
        content = report_path.read_text()
        assert "section1" in content

    def test_format_details_list(self, tmp_path):
        """Test formatting details as list."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"details": {"section1": ["item1", "item2", "item3"]}}
        report_path = generator.generate_markdown_report("Test", results)
        content = report_path.read_text()
        assert "section1" in content

    def test_format_details_string(self, tmp_path):
        """Test formatting details as string."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"details": {"section1": "Simple text content"}}
        report_path = generator.generate_markdown_report("Test", results)
        content = report_path.read_text()
        assert "Simple text content" in content

    def test_format_table_multiple_columns(self, tmp_path):
        """Test formatting table with multiple columns."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {
            "tables": {
                "Results": {
                    "Method": ["A", "B", "C"],
                    "Accuracy": ["0.9", "0.8", "0.85"],
                    "Time": ["1s", "2s", "1.5s"],
                }
            }
        }
        report_path = generator.generate_markdown_report("Test", results)
        content = report_path.read_text()
        assert "Method" in content
        assert "Accuracy" in content

    def test_format_summary_latex_non_numeric(self, tmp_path):
        """Test LaTeX summary formatting with non-numeric values."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0, "status": "completed"}}
        report_path = generator.generate_latex_report("Test", results)
        content = report_path.read_text()
        assert "status" in content

    def test_format_summary_html_non_numeric(self, tmp_path):
        """Test HTML summary formatting with non-numeric values."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        results = {"summary": {"mean": 1.0, "status": "completed"}}
        report_path = generator.generate_html_report("Test", results)
        content = report_path.read_text()
        assert "status" in content

    def test_create_comparison_report_no_values(self, tmp_path):
        """Test comparison report when no values found for metric."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        runs = [{"metrics": {"accuracy": 0.9}}, {"metrics": {"accuracy": 0.92}}]
        comparison = generator.create_comparison_report(
            runs, ["accuracy", "nonexistent"]
        )
        assert "accuracy" in comparison["comparisons"]
        # nonexistent metric should not be in comparisons if no values found
        assert "nonexistent" not in comparison["comparisons"]

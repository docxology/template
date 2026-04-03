"""Tests for infrastructure.reporting.pipeline_markdown — comprehensive coverage."""

from infrastructure.core.runtime.checkpoint import StageResult
from infrastructure.reporting.pipeline_markdown import _generate_pipeline_markdown
from infrastructure.reporting.pipeline_report_model import PipelineReport


def _make_report(stages=None, **kwargs):
    if stages is None:
        stages = [
            StageResult(name="setup", exit_code=0, duration=5.0, status="passed"),
            StageResult(name="test", exit_code=0, duration=30.0, status="passed"),
            StageResult(name="render", exit_code=1, duration=10.0, status="failed"),
        ]
    return PipelineReport(
        timestamp="2026-01-15T10:30:00",
        total_duration=45.0,
        stages=stages,
        **kwargs,
    )


class TestGeneratePipelineMarkdown:
    def test_basic_structure(self):
        report = _make_report()
        md = _generate_pipeline_markdown(report)
        assert "# Pipeline Execution Report" in md
        assert "## Summary" in md
        assert "## Stage Results" in md
        assert "2026-01-15" in md

    def test_summary_counts(self):
        report = _make_report()
        md = _generate_pipeline_markdown(report)
        assert "**Stages Executed:** 3" in md
        assert "**Stages Passed:** 2" in md
        assert "**Stages Failed:** 1" in md

    def test_stage_table(self):
        report = _make_report()
        md = _generate_pipeline_markdown(report)
        assert "| setup |" in md
        assert "| test |" in md
        assert "| render |" in md
        assert "passed" in md
        assert "failed" in md

    def test_empty_stages(self):
        report = _make_report(stages=[])
        md = _generate_pipeline_markdown(report)
        assert "**Stages Executed:** 0" in md
        assert "0.0%" in md

    def test_test_results_section(self):
        report = _make_report(
            test_results={
                "summary": {
                    "total_tests": 100,
                    "total_passed": 95,
                    "total_failed": 5,
                    "total_skipped": 0,
                    "infrastructure_coverage": 82.5,
                    "project_coverage": 91.3,
                }
            }
        )
        md = _generate_pipeline_markdown(report)
        assert "## Test Results" in md
        assert "100" in md
        assert "82.5" in md

    def test_no_test_results(self):
        report = _make_report()
        md = _generate_pipeline_markdown(report)
        assert "## Test Results" not in md

    def test_validation_results_section(self):
        report = _make_report(validation_results={"pdf_valid": True, "links_ok": False})
        md = _generate_pipeline_markdown(report)
        assert "## Validation Results" in md
        assert "pdf_valid" in md

    def test_performance_metrics_section(self):
        report = _make_report(performance_metrics={"cpu_time": 10.5, "memory_mb": 256})
        md = _generate_pipeline_markdown(report)
        assert "## Performance Metrics" in md
        assert "10.50" in md
        assert "256" in md

    def test_error_summary_section(self):
        report = _make_report(
            error_summary={
                "total_errors": 2,
                "errors": ["Import failed", "Timeout exceeded"],
            }
        )
        md = _generate_pipeline_markdown(report)
        assert "## Error Summary" in md
        assert "Import failed" in md
        assert "Timeout exceeded" in md

    def test_error_summary_truncation(self):
        errors = [f"Error {i}" for i in range(10)]
        report = _make_report(error_summary={"total_errors": 10, "errors": errors})
        md = _generate_pipeline_markdown(report)
        assert "and 5 more" in md

    def test_no_error_summary_when_zero(self):
        report = _make_report(error_summary={"total_errors": 0})
        md = _generate_pipeline_markdown(report)
        assert "## Error Summary" not in md

    def test_output_statistics_section(self):
        report = _make_report(
            output_statistics={"pdf_files": 3, "figures": 5, "data_files": 2}
        )
        md = _generate_pipeline_markdown(report)
        assert "## Output Statistics" in md
        assert "3" in md
        assert "5" in md

    def test_all_sections_present(self):
        report = _make_report(
            test_results={"summary": {"total_tests": 50}},
            validation_results={"check": True},
            performance_metrics={"speed": 1.0},
            error_summary={"total_errors": 1, "errors": ["err"]},
            output_statistics={"pdf_files": 1},
        )
        md = _generate_pipeline_markdown(report)
        assert "## Test Results" in md
        assert "## Validation Results" in md
        assert "## Performance Metrics" in md
        assert "## Error Summary" in md
        assert "## Output Statistics" in md

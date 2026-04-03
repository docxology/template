"""Tests for infrastructure.reporting.pipeline_html — comprehensive coverage."""

from infrastructure.core.runtime.checkpoint import StageResult
from infrastructure.reporting.pipeline_html import generate_html_report
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


class TestGenerateHtmlReport:
    def test_basic_structure(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "<!DOCTYPE html>" in html
        assert "Pipeline Execution Report" in html
        assert "</html>" in html

    def test_summary_cards(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "Stages Executed" in html
        assert "Stages Passed" in html
        assert "Stages Failed" in html
        assert "Success Rate" in html

    def test_stage_rows(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "setup" in html
        assert "test" in html
        assert "render" in html
        assert "status-passed" in html
        assert "status-failed" in html

    def test_empty_stages(self):
        report = _make_report(stages=[])
        html = generate_html_report(report)
        assert "0" in html
        assert "0.0%" in html

    def test_test_results_section(self):
        report = _make_report(
            test_results={
                "summary": {
                    "total_tests": 200,
                    "total_passed": 190,
                    "total_failed": 10,
                    "total_skipped": 0,
                    "infrastructure_coverage": 80.5,
                    "project_coverage": 92.3,
                }
            }
        )
        html = generate_html_report(report)
        assert "Test Results" in html
        assert "200" in html
        assert "80.50%" in html
        assert "92.30%" in html

    def test_no_test_results(self):
        report = _make_report()
        html = generate_html_report(report)
        # Should not crash or include test results section
        assert "Test Results" not in html

    def test_timestamp_displayed(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "2026-01-15" in html

    def test_all_stages_passed(self):
        stages = [
            StageResult(name="a", exit_code=0, duration=1.0, status="passed"),
            StageResult(name="b", exit_code=0, duration=2.0, status="passed"),
        ]
        report = _make_report(stages=stages)
        html = generate_html_report(report)
        assert "100.0%" in html

"""Summary formatter and post-run report tests split from test_summary_reporting.py.

Exercises real code paths in:

* ``infrastructure.core.pipeline.summary_formatters`` — ``format_text_summary``,
  ``format_json_summary``, ``format_html_summary``.
* ``infrastructure.core.pipeline.post_run_reporting`` —
  ``write_pipeline_post_run_reports`` with and without a pipeline log file.
"""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryManager
from infrastructure.core.pipeline.post_run_reporting import write_pipeline_post_run_reports
from infrastructure.core.pipeline.summary import PipelineSummaryGenerator
from infrastructure.core.pipeline.summary_formatters import (
    format_html_summary,
    format_json_summary,
    format_text_summary,
)
from ._summary_reporting_helpers import _make_output_dir, _result


class TestFormatTextSummary:
    """Detailed tests for ``format_text_summary``."""

    def test_text_summary_includes_log_file_section(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        log_file = Path("projects/demo/output/logs/pipeline.log")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Full pipeline log:" in text
        assert str(log_file) in text
        assert "Pipeline Log:" in text
        assert "Current:" in text

    def test_text_summary_includes_final_log_path_note(self, tmp_path: Path) -> None:
        """When log path changes after copy, a 'Final' note is added."""
        output_dir = _make_output_dir(tmp_path)
        log_file = Path("projects/demo/output/logs/pipeline.log")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Will be available at:" in text
        assert "output/logs/pipeline.log" in text

    def test_text_summary_no_log_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Pipeline Log:" not in text

    def test_text_summary_with_inventory_and_project_name(self, tmp_path: Path) -> None:
        """Inventory with a ``projects/<name>/output/`` base_dir surfaces the project name note."""
        # Create real files under projects/.../output for project_name extraction
        project_output = tmp_path / "projects" / "demo" / "output"
        project_output.mkdir(parents=True)
        (project_output / "pdf").mkdir(parents=True)
        (project_output / "pdf" / "report.pdf").write_text("PDF", encoding="utf-8")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=project_output,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        # The note about project output should appear
        assert "Files are also available in projects/demo/output/" in text or "Files will be copied" in text

    def test_text_summary_performance_metrics(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=8.0),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=10.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        text = format_text_summary(summary, manager)
        assert "Performance Metrics:" in text
        assert "Total Execution Time: 10.0s" in text
        assert "Average Stage Time:" in text
        assert "Slowest Stage:" in text
        assert "Stage 2 - tests" in text
        assert "Fastest Stage:" in text


class TestFormatJsonSummary:
    """Detailed tests for ``format_json_summary``."""

    def test_json_summary_structure(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path, {"data/results.csv": "a,b\n1,2"})
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=3.0),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=5.0,
            output_dir=output_dir,
        )
        text = format_json_summary(summary)
        data = json.loads(text)
        assert data["total_duration"] == 5.0
        assert "total_duration_formatted" in data
        assert len(data["stages"]) == 2
        assert data["stages"][0]["stage_name"] == "setup"
        assert data["stages"][1]["stage_name"] == "tests"
        assert data["performance"]["slowest_stage"]["stage_name"] == "tests"
        # fastest_stage excludes stage 1 (setup), so tests is the fastest
        assert data["performance"]["fastest_stage"]["stage_name"] == "tests"
        assert data["performance"]["failed_stages"] == []
        assert data["files"]["count"] == 1
        assert data["files"]["inventory"][0]["category"] == "data"

    def test_json_summary_no_log_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        text = format_json_summary(summary)
        data = json.loads(text)
        assert "log_file" not in data
        assert "log_file_final" not in data

    def test_json_summary_with_failed_stages(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1, error_message="err"),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=3.0,
            output_dir=output_dir,
        )
        text = format_json_summary(summary)
        data = json.loads(text)
        assert len(data["performance"]["failed_stages"]) == 1
        assert data["performance"]["failed_stages"][0]["stage_name"] == "render"
        assert data["performance"]["slowest_stage"]["stage_name"] == "setup"


class TestFormatHtmlSummary:
    """Detailed tests for ``format_html_summary``."""

    def test_html_summary_basic_structure(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "<div class='pipeline-summary'>" in html
        assert "</div>" in html
        assert "All stages completed successfully!" in html

    def test_html_summary_with_failures(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=3.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Pipeline completed with failures: render" in html
        assert "class='error'" in html

    def test_html_summary_with_log_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        log_file = Path("projects/demo/output/logs/pipeline.log")
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
            log_file=log_file,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Log file:" in html
        assert str(log_file) in html
        assert "Will be available at:" in html

    def test_html_summary_performance_metrics(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=8.0),
        ]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=10.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Total Execution Time: 10.0s" in html
        assert "Average Stage Time:" in html
        assert "Slowest Stage:" in html
        assert "Fastest Stage:" in html

    def test_html_summary_with_inventory(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path, {"pdf/report.pdf": "PDF content"})
        results = [_result("setup", stage_num=1, success=True, duration=1.0)]
        generator = PipelineSummaryGenerator()
        summary = generator.generate_summary(
            stage_results=results,
            total_duration=1.0,
            output_dir=output_dir,
        )
        manager = FileInventoryManager()
        html = format_html_summary(summary, manager)
        assert "Generated Files" in html


class TestWritePipelinePostRunReports:
    """Tests for ``write_pipeline_post_run_reports``."""

    def test_creates_reports_dir_and_json_report(self, tmp_path: Path) -> None:
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [_result("setup"), _result("tests")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        assert reports_dir.is_dir()
        json_reports = list(reports_dir.glob("pipeline_report*.json"))
        assert json_reports, "expected JSON pipeline report"

    def test_creates_html_and_markdown_reports(self, tmp_path: Path) -> None:
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [_result("setup"), _result("tests")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        html_reports = list(reports_dir.glob("pipeline_report*.html"))
        md_reports = list(reports_dir.glob("pipeline_report*.md"))
        assert html_reports, "expected HTML pipeline report"
        assert md_reports, "expected Markdown pipeline report"

    def test_with_pipeline_log_file(self, tmp_path: Path) -> None:
        """A non-empty pipeline log triggers log summary generation."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(parents=True)
        log_file = logs_dir / "pipeline.log"
        log_file.write_text(
            "\n".join(
                [
                    "INFO setup started",
                    "WARNING deprecated config",
                    "ERROR something failed",
                    "DEBUG detail",
                ]
            ),
            encoding="utf-8",
        )
        results = [_result("setup")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        log_summary = reports_dir / "log_summary.txt"
        assert log_summary.is_file()
        content = log_summary.read_text(encoding="utf-8")
        assert "LOG ANALYSIS" in content
        assert "Total Lines: 4" in content
        assert "WARNING" in content
        assert "ERROR" in content

    def test_empty_log_file_still_generates_summary(self, tmp_path: Path) -> None:
        """An empty pipeline log still produces a log summary (the guard is existence, not size)."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "pipeline.log").write_text("", encoding="utf-8")
        results = [_result("setup")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        log_summary = reports_dir / "log_summary.txt"
        # The log_summary is generated because the file exists; content has 0 lines
        assert log_summary.is_file()
        content = log_summary.read_text(encoding="utf-8")
        assert "LOG ANALYSIS" in content
        assert "Total Lines: 0" in content

    def test_no_log_file(self, tmp_path: Path) -> None:
        """Missing pipeline log does not crash; reports are still generated."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [_result("setup")]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        assert reports_dir.is_dir()
        # JSON report should still be generated
        json_reports = list(reports_dir.glob("pipeline_report*.json"))
        assert json_reports

    def test_json_report_content_has_stages(self, tmp_path: Path) -> None:
        """The generated JSON report contains the stage data."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [
            _result("setup", stage_num=1, success=True, duration=2.0),
            _result("tests", stage_num=2, success=True, duration=5.0),
        ]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=True,
        )

        reports_dir = output_dir / "reports"
        json_file = reports_dir / "pipeline_report.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["total_duration"] == 7.0
        assert len(data["stages"]) == 2
        assert data["stages"][0]["name"] == "setup"
        assert data["stages"][1]["name"] == "tests"

    def test_with_failed_stage(self, tmp_path: Path) -> None:
        """Reports are still generated when a stage fails."""
        project = "demo"
        project_root = tmp_path / "projects" / project
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        results = [
            _result("setup", stage_num=1, success=True, duration=1.0),
            _result("render", stage_num=7, success=False, duration=2.0, exit_code=1),
        ]

        write_pipeline_post_run_reports(
            results=results,
            repo_root=tmp_path,
            project_name=project,
            skip_infra=False,
        )

        reports_dir = output_dir / "reports"
        json_file = reports_dir / "pipeline_report.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["total_duration"] == 3.0
        assert len(data["stages"]) == 2
        assert data["stages"][1]["exit_code"] == 1

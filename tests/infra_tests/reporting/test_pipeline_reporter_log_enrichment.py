"""Log-file enrichment of pipeline report output statistics (formerly part of test_pipeline_reporter.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.reporting.pipeline_report_model import generate_pipeline_report

from ._pipeline_reporter_helpers import _stage_results


class TestGeneratePipelineReportWithLogFile:
    """Test generate_pipeline_report with project_name for log file info."""

    def test_report_includes_log_file_info_when_exists(self, tmp_path: Path) -> None:
        """Test that log file info is added when project_name is provided."""
        # Create project structure with log file
        project_name = "test_project"
        log_dir = tmp_path / "projects" / project_name / "output" / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "pipeline.log"
        log_file.write_text("Log content here")

        report = generate_pipeline_report(
            stage_results=_stage_results(),
            total_duration=5.0,
            repo_root=tmp_path,
            project_name=project_name,
            output_statistics={"pdf_files": 1},
        )

        assert report.output_statistics is not None
        assert "log_file" in report.output_statistics
        assert report.output_statistics["log_file"]["exists"] is True
        assert report.output_statistics["log_file"]["size"] > 0

    def test_report_log_file_info_when_not_exists(self, tmp_path: Path) -> None:
        """Test log file info when log file doesn't exist."""
        project_name = "test_project"
        # Don't create the log file

        report = generate_pipeline_report(
            stage_results=_stage_results(),
            total_duration=5.0,
            repo_root=tmp_path,
            project_name=project_name,
            output_statistics={"pdf_files": 1},
        )

        assert report.output_statistics is not None
        assert "log_file" in report.output_statistics
        assert report.output_statistics["log_file"]["exists"] is False


def test_generate_pipeline_report_enriches_output_statistics_with_log_file(
    tmp_path: Path,
) -> None:
    """generate_pipeline_report with project_name + output_statistics adds log_file info."""
    project_name = "test_project"
    output_stats = {"pdf_files": 2}

    report = generate_pipeline_report(
        stage_results=[],
        total_duration=1.0,
        repo_root=tmp_path,
        project_name=project_name,
        output_statistics=output_stats,
    )

    assert report.output_statistics is not None
    assert "log_file" in report.output_statistics
    log_info = report.output_statistics["log_file"]
    assert "exists" in log_info
    assert "size" in log_info
    assert "path" in log_info
    assert str(tmp_path) not in log_info["path"]
    # Original stats should still be present
    assert report.output_statistics["pdf_files"] == 2

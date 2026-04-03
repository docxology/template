"""Tests for infrastructure.reporting.pipeline_report_model — comprehensive coverage."""


from infrastructure.reporting.pipeline_report_model import (
    PipelineReport,
    generate_pipeline_report,
)


class TestPipelineReport:
    def test_basic_construction(self):
        report = PipelineReport(
            timestamp="2026-01-01T00:00:00",
            total_duration=120.0,
            stages=[],
        )
        assert report.total_duration == 120.0
        assert report.stages == []
        assert report.test_results is None
        assert report.validation_results is None

    def test_with_optional_fields(self):
        report = PipelineReport(
            timestamp="2026-01-01T00:00:00",
            total_duration=60.0,
            stages=[],
            test_results={"passed": 10},
            validation_results={"valid": True},
            performance_metrics={"cpu": 50},
            error_summary={"errors": 0},
            output_statistics={"pdfs": 2},
        )
        assert report.test_results["passed"] == 10
        assert report.output_statistics["pdfs"] == 2


class TestGeneratePipelineReport:
    def test_basic_report(self, tmp_path):
        stage_results = [
            {"name": "setup", "exit_code": 0, "duration": 5.0},
            {"name": "test", "exit_code": 0, "duration": 30.0},
            {"name": "render", "exit_code": 1, "duration": 10.0},
        ]
        report = generate_pipeline_report(stage_results, 45.0, tmp_path)
        assert report.total_duration == 45.0
        assert len(report.stages) == 3
        assert report.stages[0].name == "setup"
        assert report.stages[0].status == "passed"
        assert report.stages[2].status == "failed"

    def test_with_test_results(self, tmp_path):
        stage_results = [{"name": "test", "exit_code": 0, "duration": 10.0}]
        report = generate_pipeline_report(
            stage_results, 10.0, tmp_path, test_results={"total": 50, "passed": 48}
        )
        assert report.test_results["total"] == 50

    def test_empty_stages(self, tmp_path):
        report = generate_pipeline_report([], 0.0, tmp_path)
        assert report.stages == []
        assert report.total_duration == 0.0

    def test_missing_fields_default(self, tmp_path):
        stage_results = [{"name": "build"}]  # Missing exit_code and duration
        report = generate_pipeline_report(stage_results, 0.0, tmp_path)
        assert report.stages[0].exit_code == 1  # Default
        assert report.stages[0].duration == 0.0  # Default
        assert report.stages[0].status == "failed"

    def test_with_project_name_and_output_stats(self, tmp_path):
        # Create project structure
        log_dir = tmp_path / "projects" / "myproj" / "output" / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "pipeline.log"
        log_file.write_text("log content")

        stage_results = [{"name": "setup", "exit_code": 0, "duration": 1.0}]
        report = generate_pipeline_report(
            stage_results,
            1.0,
            tmp_path,
            project_name="myproj",
            output_statistics={"pdfs": 2},
        )
        assert report.output_statistics is not None
        assert report.output_statistics["pdfs"] == 2
        assert report.output_statistics["log_file"]["exists"] is True
        assert report.output_statistics["log_file"]["size"] > 0

    def test_with_project_dir_override(self, tmp_path):
        custom_dir = tmp_path / "custom_project"
        log_dir = custom_dir / "output" / "logs"
        log_dir.mkdir(parents=True)
        (log_dir / "pipeline.log").write_text("custom log")

        stage_results = [{"name": "setup", "exit_code": 0, "duration": 1.0}]
        report = generate_pipeline_report(
            stage_results,
            1.0,
            tmp_path,
            project_name="myproj",
            project_dir=custom_dir,
            output_statistics={"pdfs": 1},
        )
        assert report.output_statistics["log_file"]["exists"] is True

    def test_project_name_without_output_stats(self, tmp_path):
        # output_statistics is None, so log_file enrichment is skipped
        stage_results = [{"name": "setup", "exit_code": 0, "duration": 1.0}]
        report = generate_pipeline_report(
            stage_results, 1.0, tmp_path, project_name="myproj"
        )
        assert report.output_statistics is None

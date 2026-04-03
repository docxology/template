"""Tests for infrastructure.reporting._executive_renderers — comprehensive coverage."""

import json

from infrastructure.reporting._executive_renderers import (
    generate_executive_summary,
    save_executive_summary,
)


def _setup_project(tmp_path, name="demo"):
    """Create a minimal project layout for generate_executive_summary."""
    proj = tmp_path / "projects" / name
    (proj / "manuscript").mkdir(parents=True)
    (proj / "manuscript" / "01_intro.md").write_text("Hello world")
    (proj / "src").mkdir()
    (proj / "src" / "core.py").write_text("x = 1\n")
    reports = proj / "output" / "reports"
    reports.mkdir(parents=True)
    test_report = {
        "project": {"total": 20, "passed": 20, "coverage_percent": 95.0},
        "summary": {},
    }
    (reports / "test_results.json").write_text(json.dumps(test_report))
    pipeline_report = {
        "total_duration": 30.0,
        "stages": [{"name": "test", "status": "passed", "duration": 30.0}],
    }
    (reports / "pipeline_report.json").write_text(json.dumps(pipeline_report))
    # Output dir for output metrics
    output = tmp_path / "output" / name
    (output / "pdf").mkdir(parents=True)
    (output / "pdf" / "paper.pdf").write_bytes(b"%PDF")


def _make_summary(tmp_path):
    """Create a proper ExecutiveSummary by using the real generation pipeline.

    Uses generate_executive_summary with a real project layout to ensure
    the aggregate_metrics structure is fully populated.
    """
    _setup_project(tmp_path, "test_proj")
    return generate_executive_summary(tmp_path, ["test_proj"])


class TestGenerateExecutiveSummary:
    def test_basic_generation(self, tmp_path):
        _setup_project(tmp_path, "alpha")
        summary = generate_executive_summary(tmp_path, ["alpha"])
        assert summary.total_projects == 1
        assert len(summary.project_metrics) == 1
        assert summary.project_metrics[0].name == "alpha"
        assert "alpha" in summary.health_scores
        assert isinstance(summary.recommendations, list)
        assert summary.timestamp is not None

    def test_multiple_projects(self, tmp_path):
        _setup_project(tmp_path, "proj_a")
        _setup_project(tmp_path, "proj_b")
        summary = generate_executive_summary(tmp_path, ["proj_a", "proj_b"])
        assert summary.total_projects == 2
        names = {pm.name for pm in summary.project_metrics}
        assert names == {"proj_a", "proj_b"}

    def test_missing_project_skipped(self, tmp_path):
        _setup_project(tmp_path, "good")
        # "missing" project doesn't exist but shouldn't crash
        summary = generate_executive_summary(tmp_path, ["good", "missing"])
        # Both collected (missing just has empty metrics)
        assert summary.total_projects == 2

    def test_single_project_no_outputs(self, tmp_path):
        """Test with a project that has minimal structure."""
        proj = tmp_path / "projects" / "minimal"
        (proj / "manuscript").mkdir(parents=True)
        (proj / "src").mkdir()
        summary = generate_executive_summary(tmp_path, ["minimal"])
        assert summary.total_projects == 1


class TestSaveExecutiveSummary:
    def test_saves_all_formats(self, tmp_path):
        summary = _make_summary(tmp_path)
        out = tmp_path / "report_out"
        saved = save_executive_summary(summary, out)
        assert "json" in saved
        assert "markdown" in saved
        assert "html" in saved
        assert saved["json"].exists()
        assert saved["markdown"].exists()
        assert saved["html"].exists()

    def test_json_is_valid(self, tmp_path):
        summary = _make_summary(tmp_path)
        out = tmp_path / "report_out"
        saved = save_executive_summary(summary, out)
        data = json.loads(saved["json"].read_text())
        assert data["total_projects"] == 1

    def test_markdown_has_content(self, tmp_path):
        summary = _make_summary(tmp_path)
        out = tmp_path / "report_out"
        saved = save_executive_summary(summary, out)
        md = saved["markdown"].read_text()
        assert len(md) > 100
        assert "test_proj" in md

    def test_html_has_content(self, tmp_path):
        summary = _make_summary(tmp_path)
        out = tmp_path / "report_out"
        saved = save_executive_summary(summary, out)
        html = saved["html"].read_text()
        assert "<!DOCTYPE html>" in html or "<html" in html

    def test_creates_output_dirs(self, tmp_path):
        summary = _make_summary(tmp_path)
        nested = tmp_path / "deep" / "nested"
        saved = save_executive_summary(summary, nested)
        assert saved["json"].exists()

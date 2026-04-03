"""Tests for infrastructure.reporting._executive_collectors — comprehensive coverage."""

import json

from infrastructure.reporting._executive_collectors import (
    collect_codebase_metrics,
    collect_manuscript_metrics,
    collect_output_metrics,
    collect_pipeline_metrics,
    collect_project_metrics,
    collect_test_metrics,
)


# ---------------------------------------------------------------------------
# collect_manuscript_metrics
# ---------------------------------------------------------------------------


class TestCollectManuscriptMetrics:
    def test_nonexistent_dir(self, tmp_path):
        m = collect_manuscript_metrics(tmp_path / "missing")
        assert m.sections == 0
        assert m.total_words == 0

    def test_empty_dir(self, tmp_path):
        m = collect_manuscript_metrics(tmp_path)
        assert m.sections == 0
        assert m.markdown_files == []

    def test_counts_sections_and_files(self, tmp_path):
        (tmp_path / "01_intro.md").write_text("Hello world")
        (tmp_path / "02_methods.md").write_text("Some methods here")
        m = collect_manuscript_metrics(tmp_path)
        assert m.sections == 2
        assert set(m.markdown_files) == {"01_intro.md", "02_methods.md"}

    def test_counts_words(self, tmp_path):
        (tmp_path / "doc.md").write_text("one two three four five")
        m = collect_manuscript_metrics(tmp_path)
        assert m.total_words == 5

    def test_counts_lines(self, tmp_path):
        (tmp_path / "doc.md").write_text("line1\nline2\nline3\n")
        m = collect_manuscript_metrics(tmp_path)
        assert m.total_lines == 3

    def test_counts_equations(self, tmp_path):
        content = "Text $$E=mc^2$$ more text $$F=ma$$ end"
        (tmp_path / "doc.md").write_text(content)
        m = collect_manuscript_metrics(tmp_path)
        assert m.equations == 2

    def test_counts_bracket_equations(self, tmp_path):
        content = "Text \\[x^2\\] end"
        (tmp_path / "doc.md").write_text(content)
        m = collect_manuscript_metrics(tmp_path)
        assert m.equations == 1

    def test_counts_figures(self, tmp_path):
        content = "![Fig 1](fig1.png)\n![Fig 2](fig2.pdf)"
        (tmp_path / "doc.md").write_text(content)
        m = collect_manuscript_metrics(tmp_path)
        assert m.figures == 2

    def test_counts_references(self, tmp_path):
        content = "See @smith2020 and \\cite{jones2021} for details."
        (tmp_path / "doc.md").write_text(content)
        m = collect_manuscript_metrics(tmp_path)
        assert m.references == 2

    def test_accumulates_across_files(self, tmp_path):
        (tmp_path / "a.md").write_text("word1 word2")
        (tmp_path / "b.md").write_text("word3 word4 word5")
        m = collect_manuscript_metrics(tmp_path)
        assert m.total_words == 5
        assert m.sections == 2

    def test_ignores_non_md_files(self, tmp_path):
        (tmp_path / "readme.txt").write_text("not a markdown file")
        (tmp_path / "doc.md").write_text("markdown")
        m = collect_manuscript_metrics(tmp_path)
        assert m.sections == 1


# ---------------------------------------------------------------------------
# collect_codebase_metrics
# ---------------------------------------------------------------------------


class TestCollectCodebaseMetrics:
    def test_nonexistent_src_dir(self, tmp_path):
        m = collect_codebase_metrics(tmp_path / "missing")
        assert m.source_files == 0
        assert m.source_lines == 0

    def test_counts_source_files(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.py").write_text("x = 1\ny = 2\n")
        (src / "util.py").write_text("z = 3\n")
        m = collect_codebase_metrics(src)
        assert m.source_files == 2

    def test_counts_source_lines_excluding_comments_and_blanks(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        content = "# comment\nx = 1\n\ny = 2\n# another\nz = 3\n"
        (src / "mod.py").write_text(content)
        m = collect_codebase_metrics(src)
        # Only x=1, y=2, z=3 are code lines (3)
        assert m.source_lines == 3

    def test_counts_functions_and_classes(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        content = (
            "class Foo:\n"
            "    def bar(self):\n"
            "        pass\n"
            "\n"
            "def baz():\n"
            "    pass\n"
        )
        (src / "mod.py").write_text(content)
        m = collect_codebase_metrics(src)
        assert m.classes == 1
        assert m.methods == 2  # bar + baz

    def test_recurses_subdirs(self, tmp_path):
        src = tmp_path / "src"
        sub = src / "sub"
        sub.mkdir(parents=True)
        (src / "a.py").write_text("x = 1\n")
        (sub / "b.py").write_text("y = 2\n")
        m = collect_codebase_metrics(src)
        assert m.source_files == 2

    def test_counts_scripts(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (src / "mod.py").write_text("x = 1\n")
        (scripts / "run.py").write_text("print('hello')\n")
        (scripts / "clean.py").write_text("# cleanup\nimport os\n")
        m = collect_codebase_metrics(src, scripts)
        assert m.scripts == 2
        assert m.script_lines > 0

    def test_no_scripts_dir(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.py").write_text("x = 1\n")
        m = collect_codebase_metrics(src, None)
        assert m.scripts == 0

    def test_syntax_error_in_file_still_counts_lines(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        # This is valid text but invalid Python AST
        (src / "bad.py").write_text("def (\n")
        m = collect_codebase_metrics(src)
        assert m.source_files == 1
        assert m.source_lines >= 1
        # classes and methods stay 0 due to SyntaxError
        assert m.classes == 0
        assert m.methods == 0


# ---------------------------------------------------------------------------
# collect_test_metrics
# ---------------------------------------------------------------------------


class TestCollectTestMetrics:
    def test_no_report_file(self, tmp_path):
        m = collect_test_metrics(tmp_path)
        # Special value -1 indicates unavailable
        assert m.total_tests == -1

    def test_valid_report(self, tmp_path):
        report = {
            "project": {
                "total": 50,
                "passed": 45,
                "failed": 3,
                "skipped": 2,
                "coverage_percent": 88.5,
            },
            "summary": {"total_execution_time": 12.3},
        }
        (tmp_path / "test_results.json").write_text(json.dumps(report))
        m = collect_test_metrics(tmp_path)
        assert m.total_tests == 50
        assert m.passed == 45
        assert m.failed == 3
        assert m.skipped == 2
        assert m.coverage_percent == 88.5
        assert m.execution_time == 12.3
        assert m.test_files >= 1

    def test_empty_report(self, tmp_path):
        report = {"project": {}, "summary": {}}
        (tmp_path / "test_results.json").write_text(json.dumps(report))
        m = collect_test_metrics(tmp_path)
        assert m.total_tests == 0
        assert m.passed == 0
        assert m.coverage_percent == 0.0

    def test_corrupt_json(self, tmp_path):
        (tmp_path / "test_results.json").write_text("{bad json!!!")
        m = collect_test_metrics(tmp_path)
        # Falls back to default values (0s)
        assert m.total_tests == 0

    def test_test_files_estimate(self, tmp_path):
        report = {"project": {"total": 100, "passed": 100}, "summary": {}}
        (tmp_path / "test_results.json").write_text(json.dumps(report))
        m = collect_test_metrics(tmp_path)
        assert m.test_files == 10  # 100 // 10


# ---------------------------------------------------------------------------
# collect_output_metrics
# ---------------------------------------------------------------------------


class TestCollectOutputMetrics:
    def test_nonexistent_dir(self, tmp_path):
        m = collect_output_metrics(tmp_path / "missing")
        assert m.total_outputs == 0

    def test_empty_dir(self, tmp_path):
        m = collect_output_metrics(tmp_path)
        assert m.total_outputs == 0

    def test_counts_pdfs(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF-1.4 fake content" * 100)
        (pdf_dir / "supplement.pdf").write_bytes(b"%PDF-1.4 more" * 50)
        m = collect_output_metrics(tmp_path)
        assert m.pdf_files == 2
        assert m.pdf_size_mb > 0

    def test_counts_figures(self, tmp_path):
        fig_dir = tmp_path / "figures"
        fig_dir.mkdir()
        (fig_dir / "fig1.png").write_bytes(b"PNG")
        (fig_dir / "fig2.png").write_bytes(b"PNG")
        (fig_dir / "fig3.pdf").write_bytes(b"PDF")
        m = collect_output_metrics(tmp_path)
        assert m.figures == 3

    def test_counts_data_files(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "results.csv").write_text("a,b\n1,2\n")
        (data_dir / "stats.json").write_text("{}")
        # Subdirectory should not count
        (data_dir / "subdir").mkdir()
        m = collect_output_metrics(tmp_path)
        assert m.data_files == 2

    def test_counts_slides(self, tmp_path):
        slides_dir = tmp_path / "slides"
        slides_dir.mkdir()
        (slides_dir / "presentation.pdf").write_bytes(b"PDF")
        m = collect_output_metrics(tmp_path)
        assert m.slides == 1

    def test_counts_web_outputs(self, tmp_path):
        web_dir = tmp_path / "web"
        web_dir.mkdir()
        (web_dir / "index.html").write_text("<html></html>")
        (web_dir / "about.html").write_text("<html></html>")
        m = collect_output_metrics(tmp_path)
        assert m.web_outputs == 2

    def test_total_outputs_sums_all(self, tmp_path):
        (tmp_path / "pdf").mkdir()
        (tmp_path / "pdf" / "a.pdf").write_bytes(b"P")
        (tmp_path / "figures").mkdir()
        (tmp_path / "figures" / "b.png").write_bytes(b"P")
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "c.csv").write_text("x")
        (tmp_path / "slides").mkdir()
        (tmp_path / "slides" / "d.pdf").write_bytes(b"P")
        (tmp_path / "web").mkdir()
        (tmp_path / "web" / "e.html").write_text("<h>")
        m = collect_output_metrics(tmp_path)
        assert m.total_outputs == 5


# ---------------------------------------------------------------------------
# collect_pipeline_metrics
# ---------------------------------------------------------------------------


class TestCollectPipelineMetrics:
    def test_no_report_file(self, tmp_path):
        m = collect_pipeline_metrics(tmp_path)
        assert m.total_duration == 0.0
        assert m.stages_passed == 0

    def test_valid_report(self, tmp_path):
        report = {
            "total_duration": 120.5,
            "stages": [
                {"name": "setup", "status": "passed", "duration": 10.0},
                {"name": "test", "status": "passed", "duration": 80.0},
                {"name": "render", "status": "failed", "duration": 30.5},
            ],
        }
        (tmp_path / "pipeline_report.json").write_text(json.dumps(report))
        m = collect_pipeline_metrics(tmp_path)
        assert m.total_duration == 120.5
        assert m.stages_passed == 2
        assert m.stages_failed == 1
        assert m.bottleneck_stage == "test"
        assert m.bottleneck_duration == 80.0
        assert abs(m.bottleneck_percent - (80.0 / 120.5 * 100)) < 0.1

    def test_empty_stages(self, tmp_path):
        report = {"total_duration": 0.0, "stages": []}
        (tmp_path / "pipeline_report.json").write_text(json.dumps(report))
        m = collect_pipeline_metrics(tmp_path)
        assert m.stages_passed == 0
        assert m.bottleneck_stage == ""

    def test_corrupt_json(self, tmp_path):
        (tmp_path / "pipeline_report.json").write_text("not json")
        m = collect_pipeline_metrics(tmp_path)
        assert m.total_duration == 0.0

    def test_single_stage(self, tmp_path):
        report = {
            "total_duration": 15.0,
            "stages": [{"name": "only", "status": "passed", "duration": 15.0}],
        }
        (tmp_path / "pipeline_report.json").write_text(json.dumps(report))
        m = collect_pipeline_metrics(tmp_path)
        assert m.bottleneck_stage == "only"
        assert m.bottleneck_percent == 100.0


# ---------------------------------------------------------------------------
# collect_project_metrics (orchestrator)
# ---------------------------------------------------------------------------


class TestCollectProjectMetrics:
    def _setup_project(self, tmp_path):
        """Create a minimal valid project layout."""
        proj = tmp_path / "projects" / "demo"
        (proj / "manuscript").mkdir(parents=True)
        (proj / "manuscript" / "01_intro.md").write_text("Hello world of science")
        (proj / "src").mkdir()
        (proj / "src" / "core.py").write_text("def compute():\n    return 42\n")
        (proj / "scripts").mkdir()
        (proj / "scripts" / "run.py").write_text("print('go')\n")

        reports = proj / "output" / "reports"
        reports.mkdir(parents=True)
        test_report = {
            "project": {"total": 20, "passed": 18, "failed": 2, "coverage_percent": 75.0},
            "summary": {"total_execution_time": 5.0},
        }
        (reports / "test_results.json").write_text(json.dumps(test_report))
        pipeline_report = {
            "total_duration": 30.0,
            "stages": [{"name": "test", "status": "passed", "duration": 30.0}],
        }
        (reports / "pipeline_report.json").write_text(json.dumps(pipeline_report))

        output = tmp_path / "output" / "demo"
        (output / "pdf").mkdir(parents=True)
        (output / "pdf" / "paper.pdf").write_bytes(b"%PDF")

        return proj

    def test_collects_all_metrics(self, tmp_path):
        self._setup_project(tmp_path)
        pm = collect_project_metrics(tmp_path, "demo")
        assert pm.name == "demo"
        assert pm.manuscript.sections == 1
        assert pm.codebase.source_files == 1
        assert pm.codebase.scripts == 1
        assert pm.tests.total_tests == 20
        assert pm.outputs.pdf_files == 1
        assert pm.pipeline.total_duration == 30.0

    def test_project_dir_override(self, tmp_path):
        proj = self._setup_project(tmp_path)
        # Use project_dir to point directly
        pm = collect_project_metrics(tmp_path, "demo", project_dir=proj)
        assert pm.name == "demo"
        assert pm.manuscript.sections == 1

    def test_missing_project_graceful(self, tmp_path):
        pm = collect_project_metrics(tmp_path, "nonexistent")
        assert pm.name == "nonexistent"
        assert pm.manuscript.sections == 0
        assert pm.codebase.source_files == 0
        assert pm.tests.total_tests == -1  # unavailable flag
        assert pm.outputs.total_outputs == 0
        assert pm.pipeline.total_duration == 0.0

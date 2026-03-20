"""Comprehensive tests for the template introspection module.

Tests every public function in ``template.introspection`` against the real
repository structure (Zero-Mock policy).
"""

from pathlib import Path


from template import (
    CoverageConfig,
    InfrastructureReport,
    ModuleInfo,
    PipelineStage,
    ProjectInfo,
    analyze_test_coverage_config,
    build_infrastructure_report,
    count_pipeline_stages,
    discover_infrastructure_modules,
    discover_projects,
    load_metrics,
    render_all_chapters,
    render_chapter,
)

# Repository root — two levels up from this test file
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# discover_infrastructure_modules
# ---------------------------------------------------------------------------

class TestDiscoverInfrastructureModules:
    """Tests for ``discover_infrastructure_modules``."""

    def test_returns_list_of_module_info(self):
        modules = discover_infrastructure_modules(REPO_ROOT)
        assert isinstance(modules, list)
        assert all(isinstance(m, ModuleInfo) for m in modules)

    def test_discovers_minimum_expected_modules(self):
        """Repository must have at least 8 infrastructure subpackages."""
        modules = discover_infrastructure_modules(REPO_ROOT)
        names = [m.name for m in modules]
        assert len(modules) >= 8, f"Expected ≥8 modules, got {len(modules)}: {names}"

    def test_core_module_present(self):
        modules = discover_infrastructure_modules(REPO_ROOT)
        names = [m.name for m in modules]
        assert "core" in names, f"'core' not found in {names}"

    def test_known_modules_present(self):
        """All known subpackages should be discovered."""
        modules = discover_infrastructure_modules(REPO_ROOT)
        names = {m.name for m in modules}
        expected = {"core", "rendering", "steganography", "validation", "reporting"}
        missing = expected - names
        assert not missing, f"Missing modules: {missing}"

    def test_most_modules_have_init(self):
        """Most infrastructure subpackages are Python packages; config/ may be YAML-only."""
        modules = discover_infrastructure_modules(REPO_ROOT)
        with_init = sum(1 for m in modules if m.has_init)
        assert with_init >= 8, f"Expected ≥8 modules with __init__.py, got {with_init}"

    def test_most_modules_have_python_files(self):
        """Most infrastructure subpackages contain Python code; config/ may be YAML-only."""
        modules = discover_infrastructure_modules(REPO_ROOT)
        with_py = sum(1 for m in modules if m.python_file_count > 0)
        assert with_py >= 8, f"Expected ≥8 modules with Python files, got {with_py}"

    def test_invalid_root_returns_empty(self):
        result = discover_infrastructure_modules(Path("/nonexistent/path"))
        assert result == []

    def test_modules_sorted_by_name(self):
        modules = discover_infrastructure_modules(REPO_ROOT)
        names = [m.name for m in modules]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# discover_projects
# ---------------------------------------------------------------------------

class TestDiscoverProjects:
    """Tests for ``discover_projects``."""

    def test_returns_list_of_project_info(self):
        projects = discover_projects(REPO_ROOT)
        assert isinstance(projects, list)
        assert all(isinstance(p, ProjectInfo) for p in projects)

    def test_discovers_two_projects(self):
        projects = discover_projects(REPO_ROOT)
        names = [p.name for p in projects]
        assert len(projects) >= 2, f"Expected ≥2 projects, got {len(projects)}: {names}"

    def test_known_projects_present(self):
        """code_project is the primary exemplar in projects/; template lives in projects_in_progress."""
        projects = discover_projects(REPO_ROOT)
        names = {p.name for p in projects}
        assert "code_project" in names, f"code_project not found in {names}"

    def test_each_project_has_manuscript(self):
        projects = discover_projects(REPO_ROOT)
        for proj in projects:
            assert proj.has_manuscript, f"Project {proj.name} has no manuscript"

    def test_each_project_has_chapters(self):
        projects = discover_projects(REPO_ROOT)
        for proj in projects:
            assert proj.chapter_count > 0, f"Project {proj.name} has 0 chapters"

    def test_each_project_has_config(self):
        projects = discover_projects(REPO_ROOT)
        for proj in projects:
            assert proj.config, f"Project {proj.name} has empty config"
            assert "paper" in proj.config, f"Project {proj.name} config missing 'paper'"

    def test_invalid_root_returns_empty(self):
        result = discover_projects(Path("/nonexistent/path"))
        assert result == []


# ---------------------------------------------------------------------------
# count_pipeline_stages
# ---------------------------------------------------------------------------

class TestCountPipelineStages:
    """Tests for ``count_pipeline_stages``."""

    def test_returns_list_of_stages(self):
        stages = count_pipeline_stages(REPO_ROOT / "scripts")
        assert isinstance(stages, list)
        assert all(isinstance(s, PipelineStage) for s in stages)

    def test_discovers_minimum_stages(self):
        """Pipeline must have at least 5 numbered stages."""
        stages = count_pipeline_stages(REPO_ROOT / "scripts")
        assert len(stages) >= 5, f"Expected ≥5 stages, got {len(stages)}"

    def test_stages_are_sequential(self):
        stages = count_pipeline_stages(REPO_ROOT / "scripts")
        numbers = [s.number for s in stages]
        for i in range(1, len(numbers)):
            assert numbers[i] > numbers[i - 1], f"Stages not sequential: {numbers}"

    def test_stage_zero_is_setup(self):
        stages = count_pipeline_stages(REPO_ROOT / "scripts")
        stage_map = {s.number: s for s in stages}
        assert 0 in stage_map, "Stage 0 (setup) not found"
        assert "setup" in stage_map[0].script_name.lower()

    def test_stage_one_is_tests(self):
        stages = count_pipeline_stages(REPO_ROOT / "scripts")
        stage_map = {s.number: s for s in stages}
        assert 1 in stage_map, "Stage 1 (tests) not found"
        assert "test" in stage_map[1].script_name.lower()

    def test_each_stage_has_script_path(self):
        stages = count_pipeline_stages(REPO_ROOT / "scripts")
        for stage in stages:
            assert stage.script_path.is_file(), (
                f"Stage {stage.number} script missing: {stage.script_path}"
            )

    def test_invalid_dir_returns_empty(self):
        result = count_pipeline_stages(Path("/nonexistent/path"))
        assert result == []


# ---------------------------------------------------------------------------
# analyze_test_coverage_config
# ---------------------------------------------------------------------------

class TestAnalyzeCoverageConfig:
    """Tests for ``analyze_test_coverage_config``."""

    def test_returns_coverage_config(self):
        config = analyze_test_coverage_config(PROJECT_DIR)
        assert isinstance(config, CoverageConfig)

    def test_project_name_matches(self):
        config = analyze_test_coverage_config(PROJECT_DIR)
        assert config.project_name == "template"

    def test_thresholds_are_nonnegative(self):
        config = analyze_test_coverage_config(PROJECT_DIR)
        assert config.max_test_failures >= 0
        assert config.max_infra_test_failures >= 0
        assert config.max_project_test_failures >= 0

    def test_template_has_strict_project_tolerance(self):
        """Template project enforces zero project test failures."""
        config = analyze_test_coverage_config(PROJECT_DIR)
        assert config.max_project_test_failures == 0

    def test_invalid_dir_returns_none(self):
        result = analyze_test_coverage_config(Path("/nonexistent/path"))
        assert result is None


# ---------------------------------------------------------------------------
# build_infrastructure_report
# ---------------------------------------------------------------------------

class TestBuildInfrastructureReport:
    """Tests for ``build_infrastructure_report``."""

    def test_returns_infrastructure_report(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert isinstance(report, InfrastructureReport)

    def test_report_has_modules(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.module_count >= 8

    def test_report_has_projects(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.project_count >= 2

    def test_report_has_stages(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.stage_count >= 5

    def test_report_has_python_files(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.total_python_files > 50, (
            f"Expected >50 Python files, got {report.total_python_files}"
        )

    def test_report_has_test_files(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.total_test_files > 5, (
            f"Expected >5 test files, got {report.total_test_files}"
        )

    def test_infrastructure_version_populated(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.infrastructure_version != "unknown"

    def test_repo_root_matches(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.repo_root == REPO_ROOT

    def test_computed_properties_match_lists(self):
        report = build_infrastructure_report(REPO_ROOT)
        assert report.module_count == len(report.modules)
        assert report.project_count == len(report.projects)
        assert report.stage_count == len(report.pipeline_stages)


# ---------------------------------------------------------------------------
# inject_metrics — load_metrics, render_chapter, render_all_chapters
# ---------------------------------------------------------------------------

class TestInjectMetrics:
    """Tests for the inject_metrics module (Zero-Mock policy)."""

    def _write_metrics(self, tmp_path, data: dict) -> "Path":
        """Write *data* as JSON to a temp metrics file and return its path."""
        import json
        metrics_file = tmp_path / "metrics.json"
        metrics_file.write_text(json.dumps(data), encoding="utf-8")
        return metrics_file

    # --- load_metrics ---

    def test_load_metrics_returns_flat_dict(self, tmp_path):
        """load_metrics flattens nested JSON into a str→str dict."""
        path = self._write_metrics(tmp_path, {"module_count": 12, "nested": {"val": 5}})
        result = load_metrics(path)
        assert isinstance(result, dict)
        assert result["module_count"] == "12"
        assert result["nested_val"] == "5"  # flattened key

    def test_load_metrics_all_values_are_strings(self, tmp_path):
        """Every value returned by load_metrics must be a str (for Template substitution)."""
        path = self._write_metrics(tmp_path, {"n": 42, "s": "hello", "f": 3.14, "b": True})
        result = load_metrics(path)
        for v in result.values():
            assert isinstance(v, str), f"Non-string value: {v!r}"

    def test_load_metrics_missing_file_raises(self, tmp_path):
        """load_metrics raises FileNotFoundError for a nonexistent path."""
        import pytest
        with pytest.raises(FileNotFoundError):
            load_metrics(tmp_path / "nonexistent.json")

    def test_load_metrics_invalid_json_raises(self, tmp_path):
        """load_metrics raises ValueError for invalid JSON."""
        import pytest
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json{{{", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_metrics(bad)

    # --- render_chapter ---

    def test_render_chapter_substitutes_known_token(self, tmp_path):
        """render_chapter replaces ${module_count} with the metric value."""
        src = tmp_path / "01_test.md"
        src.write_text("We have ${module_count} modules.", encoding="utf-8")
        result_path = render_chapter(src, {"module_count": "12"}, tmp_path / "out")
        assert result_path.read_text(encoding="utf-8") == "We have 12 modules."

    def test_render_chapter_leaves_unknown_token(self, tmp_path):
        """Unknown tokens are left unchanged (safe_substitute does not raise)."""
        src = tmp_path / "02_test.md"
        src.write_text("Count: ${unknown_var}.", encoding="utf-8")
        result_path = render_chapter(src, {}, tmp_path / "out")
        assert "${unknown_var}" in result_path.read_text(encoding="utf-8")

    def test_render_chapter_multiple_tokens(self, tmp_path):
        """Multiple tokens in the same file are all substituted."""
        src = tmp_path / "03_test.md"
        src.write_text("${a} + ${b} = ${c}", encoding="utf-8")
        result = render_chapter(src, {"a": "1", "b": "2", "c": "3"}, tmp_path / "out")
        assert result.read_text() == "1 + 2 = 3"

    def test_render_chapter_output_in_correct_dir(self, tmp_path):
        """render_chapter writes to the specified output directory."""
        src = tmp_path / "04_test.md"
        src.write_text("text", encoding="utf-8")
        out_dir = tmp_path / "rendered"
        result_path = render_chapter(src, {}, out_dir)
        assert result_path.parent == out_dir
        assert result_path.name == "04_test.md"

    def test_render_chapter_creates_output_dir(self, tmp_path):
        """render_chapter creates the output directory if it does not exist."""
        src = tmp_path / "05_test.md"
        src.write_text("text", encoding="utf-8")
        out_dir = tmp_path / "deep" / "nested" / "dir"
        render_chapter(src, {}, out_dir)
        assert out_dir.is_dir()

    # --- render_all_chapters ---

    def test_render_all_chapters_processes_numbered_files(self, tmp_path):
        """render_all_chapters processes all NN_*.md chapter files."""
        ms_dir = tmp_path / "manuscript"
        ms_dir.mkdir()
        for i in range(1, 4):
            (ms_dir / f"0{i}_chapter.md").write_text(f"Chapter {i}: ${{val}}", encoding="utf-8")
        out_dir = tmp_path / "out"
        written = render_all_chapters(ms_dir, {"val": "LIVE"}, out_dir)
        assert len(written) == 3
        for f in written:
            assert "LIVE" in f.read_text(encoding="utf-8")

    def test_render_all_chapters_copies_ancillary_files(self, tmp_path):
        """render_all_chapters copies non-chapter files (bib, yaml, tex) verbatim."""
        ms_dir = tmp_path / "manuscript"
        ms_dir.mkdir()
        (ms_dir / "01_chapter.md").write_text("text", encoding="utf-8")
        (ms_dir / "references.bib").write_text("@article{x}", encoding="utf-8")
        (ms_dir / "preamble.md").write_text("preamble", encoding="utf-8")
        out_dir = tmp_path / "out"
        written = render_all_chapters(ms_dir, {}, out_dir)
        names = {f.name for f in written}
        assert "references.bib" in names
        assert "preamble.md" in names

    def test_render_all_chapters_real_manuscript(self, tmp_path):
        """render_all_chapters works on the real template manuscript directory."""
        manuscript_dir = PROJECT_DIR / "manuscript"
        out_dir = tmp_path / "rendered"
        # Use minimal metrics so tokens resolve without running full analysis
        metrics = {
            "module_count": "12",
            "total_infra_python_files": "150",
            "stage_count": "8",
            "infra_test_count_approx": "~3,000",
            "infra_test_file_count": "160",
            "all_projects_test_count": "576",
            "project_code_project_test_count": "39",
            "project_act_inf_metaanalysis_test_count": "501",
            "project_template_test_count": "36",
            "infrastructure_version": "v2.0.0",
            "generated_at": "2026-03-19T00:00:00Z",
            "module_inventory_table": "| Module | Files |\n|--------|-------|\n| core | 28 |",
        }
        written = render_all_chapters(manuscript_dir, metrics, out_dir)
        assert len(written) > 0
        # All numbered chapter files must be present in output
        chapter_names = [
            f.name for f in manuscript_dir.iterdir()
            if f.is_file() and f.name[0].isdigit() and f.suffix == ".md"
        ]
        out_names = {f.name for f in written}
        for ch in chapter_names:
            assert ch in out_names, f"Chapter {ch} not in rendered output"

    def test_load_metrics_round_trip_with_generate_script(self, tmp_path):
        """generate_manuscript_metrics produces valid load_metrics input."""
        import json
        import sys
        # Import generate_manuscript_metrics as a module (real invocation)
        scripts_dir = str(PROJECT_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import importlib
        gm = importlib.import_module("generate_manuscript_metrics")
        metrics = gm.build_manuscript_metrics_dict(gm.REPO_ROOT)
        # Write and round-trip via load_metrics
        metrics_file = tmp_path / "metrics.json"
        metrics_file.write_text(json.dumps(metrics), encoding="utf-8")
        loaded = load_metrics(metrics_file)
        # Core computed keys must be present and non-zero
        assert int(loaded["module_count"]) >= 8
        assert int(loaded["stage_count"]) >= 5
        assert int(loaded["total_infra_python_files"]) >= 50
        assert loaded["infrastructure_version"] != "unknown"

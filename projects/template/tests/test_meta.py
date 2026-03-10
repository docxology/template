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

    def test_each_module_has_init(self):
        modules = discover_infrastructure_modules(REPO_ROOT)
        for mod in modules:
            assert mod.has_init, f"Module {mod.name} missing __init__.py"

    def test_each_module_has_python_files(self):
        modules = discover_infrastructure_modules(REPO_ROOT)
        for mod in modules:
            assert mod.python_file_count > 0, f"Module {mod.name} has 0 Python files"

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

    def test_discovers_three_projects(self):
        projects = discover_projects(REPO_ROOT)
        names = [p.name for p in projects]
        assert len(projects) >= 3, f"Expected ≥3 projects, got {len(projects)}: {names}"

    def test_known_projects_present(self):
        projects = discover_projects(REPO_ROOT)
        names = {p.name for p in projects}
        expected = {"code_project", "cognitive_case_diagrams", "template"}
        missing = expected - names
        assert not missing, f"Missing projects: {missing}"

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
        assert report.project_count >= 3

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

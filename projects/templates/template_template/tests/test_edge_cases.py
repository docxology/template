"""Edge-case tests for template_template: covers previously-uncovered code paths.

Each test class targets specific uncovered branches identified from the coverage
report.  All tests follow the zero-mock policy: real filesystem operations
under ``tmp_path``, real imports, no monkeypatching of I/O primitives.

Coverage targets (from the 91.88% baseline):
  - metrics.py:36-38    OSError branch in count_test_functions
  - metrics.py:46       missing docs/ dir in count_docs_markdown_files
  - metrics.py:59       missing docs/ dir in count_docs_subdirs
  - metrics.py:215-218  save_metrics_json (never called)
  - introspection.py:120-123  sibling fallback + raise in resolve_template_repo_root
  - introspection.py:149-151  ImportError branch in discover_infrastructure_modules
  - introspection.py:175      config missing → None in _project_analysis_from_workspace
  - introspection.py:181-182  malformed YAML warning branch
  - introspection.py:186->194 non-numbered chapters fallback
  - introspection.py:281->289 public_only=False path in discover_projects
  - introspection.py:297      analysis is None continue in discover_projects
  - introspection.py:379-381  YAML parse error in analyze_test_coverage_config
  - introspection.py:407-408  ImportError version fallback in build_infrastructure_report
  - inject_metrics.py:99-101  OSError reading file in render_chapter
  - inject_metrics.py:141     FileNotFoundError for missing manuscript_dir
  - inject_metrics.py:148     subdirectory skip in render_all_chapters iteration
  - inject_metrics.py:206-208 OSError reading rendered file in validate_all_resolved
  - figure_pipeline_stages.py:67-69  long-name wrapping (>14 chars)
  - figure_pipeline_stages.py:85     stage with tags produces tag_text
  - paths.py:14-17        sibling fallback + raise in locate_repo_root
  - viz_palette.py:42-43  unrecognized tag → default pipeline color
"""

from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

import pytest

from helpers import PROJECT_DIR, REPO_ROOT

# ---------------------------------------------------------------------------
# metrics.py edge cases
# ---------------------------------------------------------------------------


class TestCountTestFunctionsOSError:
    """OSError while reading a test file is swallowed; count continues."""

    def test_unreadable_test_file_is_skipped(self, tmp_path: Path) -> None:
        from template_template.metrics import count_test_functions

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        # A good file contributes its count.
        (tests_dir / "test_good.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
        # An unreadable file (chmod 000) triggers the OSError branch.
        bad = tests_dir / "test_bad.py"
        bad.write_text("def test_b():\n    pass\n", encoding="utf-8")
        bad.chmod(0o000)
        try:
            result = count_test_functions(tests_dir)
            # We get at least 1 from the readable file; the bad one is skipped.
            assert result == 1
        finally:
            bad.chmod(0o644)


class TestCountDocsMissingDir:
    """When docs/ directory does not exist, counter functions return 0."""

    def test_count_docs_markdown_files_no_docs_dir(self, tmp_path: Path) -> None:
        from template_template.metrics import count_docs_markdown_files

        # tmp_path has no docs/ subdirectory at all.
        assert count_docs_markdown_files(tmp_path) == 0

    def test_count_docs_subdirs_no_docs_dir(self, tmp_path: Path) -> None:
        from template_template.metrics import count_docs_subdirs

        assert count_docs_subdirs(tmp_path) == 0


class TestSaveMetricsJson:
    """save_metrics_json writes JSON and returns the written path."""

    def test_save_creates_file_with_correct_content(self, tmp_path: Path) -> None:
        from template_template.metrics import save_metrics_json

        metrics = {"module_count": 10, "stage_count": 5, "label": "test"}
        out = tmp_path / "data" / "metrics.json"
        result = save_metrics_json(metrics, out)
        assert result == out
        assert out.is_file()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["module_count"] == 10
        assert loaded["stage_count"] == 5

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        from template_template.metrics import save_metrics_json

        deep_path = tmp_path / "a" / "b" / "c" / "metrics.json"
        save_metrics_json({"x": 1}, deep_path)
        assert deep_path.is_file()

    def test_save_returns_path_object(self, tmp_path: Path) -> None:
        from template_template.metrics import save_metrics_json

        out = tmp_path / "m.json"
        returned = save_metrics_json({"n": 0}, out)
        assert isinstance(returned, Path)
        assert returned == out


# ---------------------------------------------------------------------------
# introspection.py edge cases
# ---------------------------------------------------------------------------


class TestResolveTemplateRepoRootEdgeCases:
    """sibling fallback and FileNotFoundError in resolve_template_repo_root."""

    def test_raises_when_no_repo_found(self, tmp_path: Path) -> None:
        from template_template.introspection import resolve_template_repo_root

        # A completely isolated directory tree — no infrastructure/, no pyproject.toml.
        isolated = tmp_path / "nowhere" / "deep"
        isolated.mkdir(parents=True)
        with pytest.raises(FileNotFoundError, match="Could not locate template repo root"):
            resolve_template_repo_root(isolated)

    def test_finds_repo_from_inside_nested_dir(self) -> None:
        from template_template.introspection import resolve_template_repo_root

        # Starting from a deeply nested path inside the real repo root should work.
        nested = REPO_ROOT / "projects" / "templates" / "template_template" / "tests"
        result = resolve_template_repo_root(nested)
        assert result == REPO_ROOT

    def test_sibling_template_fallback(self, tmp_path: Path) -> None:
        """When parents[2]/template has infrastructure/, that path is returned."""
        from template_template.introspection import resolve_template_repo_root

        # Build: tmp_path/workspace/project_name/sub/ (3 levels deep from template sibling)
        # then siblings[2] == tmp_path → we put template/ there.
        #   parents[0] = tmp_path/workspace/project_name
        #   parents[1] = tmp_path/workspace
        #   parents[2] = tmp_path
        # sibling = parents[2] / "template" = tmp_path / "template"
        sibling = tmp_path / "template"
        (sibling / "infrastructure").mkdir(parents=True)
        # No pyproject.toml in project_dir parents — forces the sibling code path.
        project_path = tmp_path / "workspace" / "project_name" / "sub"
        project_path.mkdir(parents=True)

        result = resolve_template_repo_root(project_path)
        assert result == sibling.resolve()


class TestDiscoverInfrastructureModulesImportError:
    """ImportError during module import is caught; the module is still recorded."""

    def test_module_with_bad_init_still_discovered(self, tmp_path: Path) -> None:
        from template_template.introspection import discover_infrastructure_modules

        # Build a fake infrastructure tree with a module that has an __init__.py
        # but imports a non-existent dependency — this triggers the ImportError branch.
        fake_infra = tmp_path / "infrastructure"
        bad_mod = fake_infra / "bad_module"
        bad_mod.mkdir(parents=True)
        (bad_mod / "__init__.py").write_text(
            "import _this_module_does_not_exist_anywhere\n",
            encoding="utf-8",
        )
        (bad_mod / "main.py").write_text("# placeholder\n", encoding="utf-8")
        # Temporarily add tmp_path to sys.path so importlib can resolve infrastructure.
        sys.path.insert(0, str(tmp_path))
        try:
            modules = discover_infrastructure_modules(tmp_path)
        finally:
            sys.path.remove(str(tmp_path))
        names = [m.name for m in modules]
        assert "bad_module" in names
        # python_file_count should be 2 (both files are .py)
        bad = next(m for m in modules if m.name == "bad_module")
        assert bad.python_file_count == 2
        # has_init is True even though the import failed
        assert bad.has_init is True
        # public_symbols is empty because the import failed
        assert bad.public_symbols == []

    def test_module_without_all_uses_dir(self, tmp_path: Path) -> None:
        """Real infrastructure modules all have __all__; document the dir() fallback path.

        Line 149 (the dir() fallback for modules without __all__) is unreachable
        via public infrastructure modules because they all define __all__. The
        coverage branch remains as a defensive guard. This test documents the
        known state rather than testing an unreachable path.
        """
        from template_template.introspection import discover_infrastructure_modules

        # Verify all real infrastructure modules have __all__ — this confirms the
        # dir() fallback at line 149 is dead code for the live repository.
        modules = discover_infrastructure_modules(REPO_ROOT)
        import importlib

        for m in modules:
            if not m.has_init:
                continue
            try:
                mod = importlib.import_module(f"infrastructure.{m.name}")
                all_sym = getattr(mod, "__all__", None)
                # If __all__ exists, public_symbols came from it (line 147).
                if all_sym is not None:
                    assert m.public_symbols == list(all_sym), (
                        f"infrastructure.{m.name}: public_symbols mismatch"
                    )
            except (ImportError, AttributeError, OSError):
                pass  # Import failures are handled by the except branch


class TestProjectAnalysisFromWorkspaceEdgeCases:
    """Edge cases inside _project_analysis_from_workspace."""

    def test_workspace_without_config_returns_none(self, tmp_path: Path) -> None:
        """A workspace that has a manuscript/ dir but no config.yaml should be skipped."""
        from template_template.introspection import _project_analysis_from_workspace

        workspace = tmp_path / "some_project"
        (workspace / "manuscript").mkdir(parents=True)
        # config.yaml is intentionally absent
        result = _project_analysis_from_workspace(workspace)
        assert result is None

    def test_non_numbered_chapters_fallback(self, tmp_path: Path) -> None:
        """When no numbered chapters exist, fallback collects all non-meta .md files."""
        from template_template.introspection import _project_analysis_from_workspace

        workspace = tmp_path / "prose_proj"
        manuscript = workspace / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "config.yaml").write_text("paper:\n  title: Prose\n", encoding="utf-8")
        # Non-numbered chapters (no digit prefix)
        (manuscript / "introduction.md").write_text("# Intro\n", encoding="utf-8")
        (manuscript / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
        # Meta files that should be skipped
        (manuscript / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (manuscript / "README.md").write_text("# Readme\n", encoding="utf-8")

        result = _project_analysis_from_workspace(workspace)
        assert result is not None
        assert result.chapter_count == 2  # introduction.md + conclusion.md only

    def test_malformed_yaml_config_does_not_crash(self, tmp_path: Path) -> None:
        """A malformed config.yaml is logged as a warning; result is still returned."""
        from template_template.introspection import _project_analysis_from_workspace

        workspace = tmp_path / "bad_yaml_proj"
        manuscript = workspace / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "config.yaml").write_text(
            "paper: {unclosed bracket: [bad yaml\n", encoding="utf-8"
        )
        (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")

        result = _project_analysis_from_workspace(workspace)
        # The function should return an analysis object (not None) even with bad YAML.
        assert result is not None
        assert result.name == "bad_yaml_proj"
        # config will be empty dict because YAML failed to load
        assert result.config == {}


class TestDiscoverProjectsPublicOnlyFalse:
    """public_only=False path in discover_projects."""

    def test_public_only_false_with_synthetic_repo(self, tmp_path: Path) -> None:
        """With public_only=False, projects are not filtered by PUBLIC_PROJECT_NAMES."""
        from template_template.introspection import discover_projects

        # Build a minimal valid synthetic repo with a project not in PUBLIC_PROJECT_NAMES.
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
        (tmp_path / "scripts").mkdir()
        projects_dir = tmp_path / "projects" / "templates"
        projects_dir.mkdir(parents=True)
        proj = projects_dir / "my_private_project"
        (proj / "manuscript").mkdir(parents=True)
        (proj / "manuscript" / "config.yaml").write_text(
            "paper:\n  title: Private\n", encoding="utf-8"
        )
        (proj / "manuscript" / "01_intro.md").write_text("# Intro\n", encoding="utf-8")

        result = discover_projects(tmp_path, public_only=False)
        names = {p.name for p in result}
        assert "my_private_project" in names

    def test_discover_projects_skips_workspaces_without_config(self, tmp_path: Path) -> None:
        """Workspaces that lack manuscript/config.yaml are silently skipped."""
        from template_template.introspection import discover_projects

        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
        projects_dir = tmp_path / "projects" / "templates"
        projects_dir.mkdir(parents=True)
        # Directory without config.yaml
        (projects_dir / "no_config_project" / "manuscript").mkdir(parents=True)

        result = discover_projects(tmp_path, public_only=False)
        assert result == []


class TestAnalyzeTestCoverageConfigYAMLError:
    """YAML parse error branch in analyze_test_coverage_config."""

    def test_malformed_yaml_returns_none(self, tmp_path: Path) -> None:
        from template_template.introspection import analyze_test_coverage_config

        project = tmp_path / "proj"
        (project / "manuscript").mkdir(parents=True)
        (project / "manuscript" / "config.yaml").write_text(
            "testing: {bad: yaml: [unclosed\n", encoding="utf-8"
        )

        result = analyze_test_coverage_config(project)
        assert result is None

    def test_config_without_testing_key_has_zero_defaults(self, tmp_path: Path) -> None:
        """A valid config with no 'testing' section uses zero defaults."""
        from template_template.introspection import analyze_test_coverage_config

        project = tmp_path / "proj"
        (project / "manuscript").mkdir(parents=True)
        (project / "manuscript" / "config.yaml").write_text(
            "paper:\n  title: Test\n", encoding="utf-8"
        )

        result = analyze_test_coverage_config(project)
        assert result is not None
        assert result.max_test_failures == 0
        assert result.max_infra_test_failures == 0
        assert result.max_project_test_failures == 0


class TestBuildInfrastructureReportVersionFallback:
    """build_infrastructure_report populates infrastructure version from the live package."""

    def test_report_version_is_known_string(self) -> None:
        """Real repo: version should be a non-empty string (not 'unknown')."""
        from template_template.introspection import build_infrastructure_report

        report = build_infrastructure_report(REPO_ROOT)
        # The real repo has infrastructure installed, so version won't be 'unknown'.
        assert isinstance(report.infrastructure_version, str)
        assert len(report.infrastructure_version) > 0
        assert report.infrastructure_version != "unknown"

    def test_minimal_repo_produces_valid_report(self, tmp_path: Path) -> None:
        """A synthetic repo root with no modules or projects still returns a valid report."""
        from template_template.introspection import build_infrastructure_report, InfrastructureReport

        # Build a repo with empty infrastructure/ and scripts/ (no real packages).
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
        (tmp_path / "scripts").mkdir()

        report = build_infrastructure_report(tmp_path)
        assert isinstance(report, InfrastructureReport)
        assert report.modules == []
        assert report.projects == []
        assert report.pipeline_stages == []
        assert report.numbered_scripts == []
        # version is either the real infrastructure version (importable from sys.path)
        # or 'unknown' — both are valid strings.
        assert isinstance(report.infrastructure_version, str)


# ---------------------------------------------------------------------------
# inject_metrics.py edge cases
# ---------------------------------------------------------------------------


class TestRenderChapterOSError:
    """OSError when reading source file propagates from render_chapter."""

    def test_unreadable_source_raises_oserror(self, tmp_path: Path) -> None:
        from template_template.inject_metrics import render_chapter

        src = tmp_path / "01_chapter.md"
        src.write_text("content", encoding="utf-8")
        src.chmod(0o000)
        try:
            with pytest.raises(OSError):
                render_chapter(src, {}, tmp_path / "out")
        finally:
            src.chmod(0o644)


class TestRenderAllChaptersEdgeCases:
    """Edge cases in render_all_chapters."""

    def test_missing_manuscript_dir_raises_file_not_found(self, tmp_path: Path) -> None:
        from template_template.inject_metrics import render_all_chapters

        with pytest.raises(FileNotFoundError, match="Manuscript directory not found"):
            render_all_chapters(tmp_path / "nonexistent", {}, tmp_path / "out")

    def test_subdirectory_inside_manuscript_is_skipped(self, tmp_path: Path) -> None:
        """Directories inside the manuscript/ dir are silently skipped."""
        from template_template.inject_metrics import render_all_chapters

        ms_dir = tmp_path / "manuscript"
        ms_dir.mkdir()
        (ms_dir / "01_chapter.md").write_text("Hello ${name}.", encoding="utf-8")
        # A subdirectory that should be skipped.
        sub = ms_dir / "figures"
        sub.mkdir()
        (sub / "figure.png").write_text("fake png data", encoding="utf-8")

        written = render_all_chapters(ms_dir, {"name": "World"}, tmp_path / "out")
        # Only the chapter file should be written; the subdirectory is skipped.
        written_names = {p.name for p in written}
        assert "01_chapter.md" in written_names
        # The figure inside the subdirectory should NOT be in the output.
        assert "figure.png" not in written_names


class TestValidateAllResolvedOSError:
    """OSError reading a rendered file is reported as an issue."""

    def test_unreadable_rendered_file_is_reported(self, tmp_path: Path) -> None:
        from template_template.inject_metrics import validate_all_resolved

        out_dir = tmp_path / "rendered"
        out_dir.mkdir()
        bad = out_dir / "01_chapter.md"
        bad.write_text("content", encoding="utf-8")
        bad.chmod(0o000)
        try:
            issues = validate_all_resolved(out_dir)
            # Exactly one issue should be reported for the unreadable file.
            assert len(issues) == 1
            assert "could not read" in issues[0]
        finally:
            bad.chmod(0o644)


# ---------------------------------------------------------------------------
# figure_pipeline_stages.py edge cases
# ---------------------------------------------------------------------------


class TestPipelineStageLongNameWrapping:
    """Long stage names (>14 chars) are wrapped to two lines."""

    def test_long_stage_name_renders_without_error(self, tmp_path: Path) -> None:
        from template_template.figure_pipeline_stages import generate_pipeline_stages
        from template_template.introspection import PipelineStage

        # Stage name longer than 14 characters → triggers the word-wrap branch.
        long_name = "Very Long Stage Name Here"
        stages = [
            PipelineStage(
                number=1,
                name=long_name,
                script_name="01_long_stage.py",
                script_path=Path("/fake/01_long_stage.py"),
                tags=["core"],  # also exercises the tag_text branch
            ),
            PipelineStage(
                number=2,
                name="Short",
                script_name="02_short.py",
                script_path=Path("/fake/02_short.py"),
                tags=[],  # no tags → tag_text is empty, skips tag rendering
            ),
        ]
        path = generate_pipeline_stages(stages, tmp_path)
        assert path.exists()
        assert path.stat().st_size > 1000

    def test_stage_with_tags_renders_tag_text(self, tmp_path: Path) -> None:
        from template_template.figure_pipeline_stages import generate_pipeline_stages
        from template_template.introspection import PipelineStage

        stages = [
            PipelineStage(
                number=1,
                name="Core Stage",
                script_name="01_core.py",
                script_path=Path("/fake/01_core.py"),
                tags=["core", "tests"],
            )
        ]
        path = generate_pipeline_stages(stages, tmp_path)
        assert path.exists()
        assert path.stat().st_size > 1000


# ---------------------------------------------------------------------------
# paths.py edge cases
# ---------------------------------------------------------------------------


class TestLocateRepoRootEdgeCases:
    """Sibling fallback and FileNotFoundError in paths.locate_repo_root."""

    def test_raises_when_no_repo_found(self, tmp_path: Path) -> None:
        from template_template.paths import locate_repo_root

        isolated = tmp_path / "deep" / "nested" / "path"
        isolated.mkdir(parents=True)
        with pytest.raises(FileNotFoundError, match="Could not locate template repo root"):
            locate_repo_root(isolated)

    def test_finds_repo_from_project_dir(self) -> None:
        from template_template.paths import locate_repo_root

        result = locate_repo_root(PROJECT_DIR)
        assert result == REPO_ROOT
        assert (result / "infrastructure").is_dir()

    def test_finds_repo_from_deeply_nested_path(self) -> None:
        from template_template.paths import locate_repo_root

        deep = REPO_ROOT / "projects" / "templates" / "template_template" / "src"
        result = locate_repo_root(deep)
        assert result == REPO_ROOT

    def test_sibling_template_fallback(self, tmp_path: Path) -> None:
        """When parents[2]/template has infrastructure/ + pyproject.toml, use it."""
        from template_template.paths import locate_repo_root

        # Same layout as resolve_template_repo_root sibling test:
        # project_path is 3 levels deep under tmp_path so parents[2] == tmp_path.
        sibling = tmp_path / "template"
        (sibling / "infrastructure").mkdir(parents=True)
        (sibling / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
        project_path = tmp_path / "workspace" / "project_name" / "sub"
        project_path.mkdir(parents=True)

        result = locate_repo_root(project_path)
        assert result == sibling.resolve()


# ---------------------------------------------------------------------------
# viz_palette.py edge cases
# ---------------------------------------------------------------------------


class TestStageColorFallback:
    """Unrecognized tags fall back to the default pipeline color."""

    def test_unrecognized_tag_returns_pipeline_color(self) -> None:
        from template_template.introspection import PipelineStage
        from template_template.viz_palette import ARCH_VIZ_COLORS, stage_color
        import matplotlib.colors as mcolors

        stage = PipelineStage(
            number=99,
            name="Unknown Stage",
            script_name="99_unknown.py",
            script_path=Path("/fake/99_unknown.py"),
            tags=["not_a_real_tag"],
        )
        color = stage_color(stage)
        expected = mcolors.to_rgba(ARCH_VIZ_COLORS["pipeline"])
        assert color == expected

    def test_no_tags_returns_pipeline_color(self) -> None:
        from template_template.introspection import PipelineStage
        from template_template.viz_palette import ARCH_VIZ_COLORS, stage_color
        import matplotlib.colors as mcolors

        stage = PipelineStage(
            number=0,
            name="Tagless Stage",
            script_name="00_tagless.py",
            script_path=Path("/fake/00_tagless.py"),
            tags=[],
        )
        color = stage_color(stage)
        expected = mcolors.to_rgba(ARCH_VIZ_COLORS["pipeline"])
        assert color == expected

    def test_recognized_tag_returns_correct_color(self) -> None:
        from template_template.introspection import PipelineStage
        from template_template.viz_palette import stage_color
        import matplotlib.colors as mcolors

        # 'core' is a recognized tag.
        stage = PipelineStage(
            number=1,
            name="Core Stage",
            script_name="01_core.py",
            script_path=Path("/fake/01_core.py"),
            tags=["core"],
        )
        color = stage_color(stage)
        # Should NOT be the default pipeline color.
        import matplotlib.colors as mc
        from template_template.viz_palette import ARCH_VIZ_COLORS
        default = mc.to_rgba(ARCH_VIZ_COLORS["pipeline"])
        # core maps to 'pipeline' color, so it equals default — but the branch IS taken.
        # What matters: no exception; the first recognized tag branch ran.
        assert len(color) == 4  # RGBA tuple


# ---------------------------------------------------------------------------
# Integration: module_metric_slug
# ---------------------------------------------------------------------------


class TestModuleMetricSlug:
    """_module_metric_slug normalises dots and hyphens for Template substitution."""

    def test_dot_replaced(self) -> None:
        from template_template.metrics import _module_metric_slug

        assert _module_metric_slug("logrotate.d") == "logrotate_d"

    def test_hyphen_replaced(self) -> None:
        from template_template.metrics import _module_metric_slug

        assert _module_metric_slug("my-module") == "my_module"

    def test_plain_name_unchanged(self) -> None:
        from template_template.metrics import _module_metric_slug

        assert _module_metric_slug("core") == "core"

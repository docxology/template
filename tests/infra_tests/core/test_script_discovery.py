"""Tests for infrastructure.core.script_discovery module.

Comprehensive tests for script discovery and output verification utilities.
"""

import os

import pytest

from infrastructure.core.exceptions import PipelineError
from infrastructure.core.script_discovery import (
    discover_analysis_scripts,
    discover_orchestrators,
    verify_analysis_outputs,
)


class TestDiscoverAnalysisScripts:
    """Test discover_analysis_scripts function."""

    def test_discover_analysis_scripts_finds_python_files(self, tmp_path):
        """Test discovering Python scripts in project/scripts/."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects" / "project" / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create some Python scripts
        (scripts_dir / "analysis1.py").write_text("# Script 1")
        (scripts_dir / "analysis2.py").write_text("# Script 2")
        (scripts_dir / "analysis3.py").write_text("# Script 3")

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        assert len(scripts) == 3
        assert all(s.suffix == ".py" for s in scripts)
        assert all(s.name in ["analysis1.py", "analysis2.py", "analysis3.py"] for s in scripts)

    def test_discover_analysis_scripts_ignores_hidden(self, tmp_path):
        """Test that hidden files (starting with _) are ignored."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects" / "project" / "scripts"
        scripts_dir.mkdir(parents=True)

        (scripts_dir / "public.py").write_text("# Public")
        (scripts_dir / "_private.py").write_text("# Private")
        (scripts_dir / "__init__.py").write_text("# Init")

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        assert len(scripts) == 1
        assert scripts[0].name == "public.py"

    def test_discover_analysis_scripts_ignores_setup_hook(self, tmp_path):
        """Setup hooks run in Stage 00, not as Stage 02 analysis scripts."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects" / "project" / "scripts"
        scripts_dir.mkdir(parents=True)

        (scripts_dir / "analysis.py").write_text("# analysis")
        (scripts_dir / "setup_hook.py").write_text("# setup")

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        assert [script.name for script in scripts] == ["analysis.py"]

    def test_discover_analysis_scripts_ignores_preflight(self, tmp_path):
        """Preflight scripts are aesthetic/manual; they must not gate Stage 02."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects" / "project" / "scripts"
        scripts_dir.mkdir(parents=True)

        (scripts_dir / "analysis.py").write_text("# analysis")
        (scripts_dir / "00_preflight.py").write_text("# preflight")

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        assert [script.name for script in scripts] == ["analysis.py"]

    def test_discover_analysis_scripts_sorted(self, tmp_path):
        """Test that scripts are returned in sorted order."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects" / "project" / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create scripts in non-alphabetical order
        (scripts_dir / "zebra.py").write_text("# Z")
        (scripts_dir / "alpha.py").write_text("# A")
        (scripts_dir / "beta.py").write_text("# B")

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        assert len(scripts) == 3
        assert scripts[0].name == "alpha.py"
        assert scripts[1].name == "beta.py"
        assert scripts[2].name == "zebra.py"

    def test_discover_analysis_scripts_respects_config_allowlist(self, tmp_path):
        """Configured projects run only build-producing scripts, in config order."""
        repo_root = tmp_path / "repo"
        project_dir = repo_root / "projects" / "project"
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        manuscript_dir = project_dir / "manuscript"
        manuscript_dir.mkdir()

        (scripts_dir / "biology_analysis.py").write_text("# analysis")
        (scripts_dir / "generate_figures.py").write_text("# figures")
        (scripts_dir / "maintenance_rewrite.py").write_text("# maintenance")
        (manuscript_dir / "config.yaml").write_text(
            "analysis:\n"
            "  scripts:\n"
            "    - generate_figures.py\n"
            "    - biology_analysis.py\n"
        )

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        assert [script.name for script in scripts] == ["generate_figures.py", "biology_analysis.py"]

    def test_discover_analysis_scripts_resolves_wip_project(self, tmp_path):
        """Stage 02 can run a project before promotion from projects_in_progress/."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects_in_progress" / "draft_project" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "analysis.py").write_text("# analysis")

        scripts = discover_analysis_scripts(repo_root, project_name="draft_project")

        assert [script.name for script in scripts] == ["analysis.py"]

    @pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
    def test_discover_analysis_scripts_handles_external_project_symlink(self, tmp_path):
        """Stage 02 discovery works when projects/<name> points outside the repo."""
        repo_root = tmp_path / "repo"
        projects_dir = repo_root / "projects"
        projects_dir.mkdir(parents=True)

        external = tmp_path / "private" / "active" / "linked_project"
        scripts_dir = external / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "analysis.py").write_text("# analysis")

        (projects_dir / "linked_project").symlink_to(external, target_is_directory=True)

        scripts = discover_analysis_scripts(repo_root, project_name="linked_project")

        assert [script.name for script in scripts] == ["analysis.py"]

    def test_discover_analysis_scripts_empty_directory(self, tmp_path):
        """Test discovering scripts in empty directory."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "project" / "scripts"
        scripts_dir.mkdir(parents=True)

        scripts = discover_analysis_scripts(repo_root)

        assert len(scripts) == 0
        assert isinstance(scripts, list)

    def test_discover_analysis_scripts_missing_directory(self, tmp_path):
        """Test behavior when project/scripts/ directory doesn't exist."""
        repo_root = tmp_path / "repo"
        # Don't create projects/project/scripts/

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        # Should return empty list instead of raising error (graceful degradation)
        assert scripts == []

    def test_discover_analysis_scripts_ignores_non_python(self, tmp_path):
        """Test that non-Python files are ignored."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects" / "project" / "scripts"
        scripts_dir.mkdir(parents=True)

        (scripts_dir / "script.py").write_text("# Python")
        (scripts_dir / "script.txt").write_text("Text file")
        (scripts_dir / "script.sh").write_text("# Shell")
        (scripts_dir / "README.md").write_text("# Readme")

        scripts = discover_analysis_scripts(repo_root, project_name="project")

        assert len(scripts) == 1
        assert scripts[0].name == "script.py"


class TestDiscoverOrchestrators:
    """Test discover_orchestrators function."""

    def test_discover_orchestrators_finds_all(self, tmp_path):
        """Test discovering all orchestrator scripts."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create all expected orchestrators
        orchestrator_names = [
            "00_setup_environment.py",
            "01_run_tests.py",
            "02_run_analysis.py",
            "03_render_pdf.py",
            "04_validate_output.py",
            "05_copy_outputs.py",
        ]

        for name in orchestrator_names:
            (scripts_dir / name).write_text(f"# {name}")

        orchestrators = discover_orchestrators(repo_root)

        assert len(orchestrators) == 6
        assert all(o.name in orchestrator_names for o in orchestrators)

    def test_discover_orchestrators_partial(self, tmp_path):
        """Test discovering when some orchestrators are missing."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create only some orchestrators
        (scripts_dir / "00_setup_environment.py").write_text("# Setup")
        (scripts_dir / "01_run_tests.py").write_text("# Tests")
        # Don't create the rest

        orchestrators = discover_orchestrators(repo_root)

        assert len(orchestrators) == 2
        assert all(o.exists() for o in orchestrators)

    def test_discover_orchestrators_missing_directory(self, tmp_path):
        """Test error when scripts/ directory doesn't exist."""
        repo_root = tmp_path / "repo"
        # Don't create scripts/

        with pytest.raises(PipelineError) as exc_info:
            discover_orchestrators(repo_root)

        assert "not found" in str(exc_info.value).lower()

    def test_discover_orchestrators_empty_directory(self, tmp_path):
        """Test discovering when scripts directory is empty."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "scripts"
        scripts_dir.mkdir(parents=True)
        # Don't create any orchestrator files

        orchestrators = discover_orchestrators(repo_root)

        assert len(orchestrators) == 0
        assert isinstance(orchestrators, list)

    def test_discover_orchestrators_returns_existing_only(self, tmp_path):
        """Test that only existing orchestrator files are returned."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create only first and last orchestrators
        (scripts_dir / "00_setup_environment.py").write_text("# Setup")
        (scripts_dir / "05_copy_outputs.py").write_text("# Copy")

        orchestrators = discover_orchestrators(repo_root)

        assert len(orchestrators) == 2
        assert orchestrators[0].name == "00_setup_environment.py"
        assert orchestrators[1].name == "05_copy_outputs.py"


class TestVerifyAnalysisOutputs:
    """Test verify_analysis_outputs function."""

    def test_verify_analysis_outputs_with_files(self, tmp_path):
        """Test verifying when output directories have files."""
        repo_root = tmp_path / "repo"

        figures_dir = repo_root / "project" / "output" / "figures"
        figures_dir.mkdir(parents=True)
        (figures_dir / "plot1.png").write_text("plot data")
        (figures_dir / "plot2.png").write_text("plot data")

        data_dir = repo_root / "project" / "output" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "results.csv").write_text("data")

        result = verify_analysis_outputs(repo_root)

        assert result is True

    def test_verify_analysis_outputs_empty_directories(self, tmp_path):
        """Test verifying when output directories are empty."""
        repo_root = tmp_path / "repo"

        figures_dir = repo_root / "project" / "output" / "figures"
        figures_dir.mkdir(parents=True)

        data_dir = repo_root / "project" / "output" / "data"
        data_dir.mkdir(parents=True)

        result = verify_analysis_outputs(repo_root)

        # Should still return True (empty is valid)
        assert result is True

    def test_verify_analysis_outputs_missing_directories(self, tmp_path):
        """Test verifying when output directories don't exist."""
        repo_root = tmp_path / "repo"
        # Don't create output directories

        result = verify_analysis_outputs(repo_root)

        # Should return True (missing directories are not an error)
        assert result is True

    def test_verify_analysis_outputs_partial(self, tmp_path):
        """Test verifying when only one output directory exists."""
        repo_root = tmp_path / "repo"

        figures_dir = repo_root / "project" / "output" / "figures"
        figures_dir.mkdir(parents=True)
        (figures_dir / "plot.png").write_text("plot")

        # Don't create data directory

        result = verify_analysis_outputs(repo_root)

        assert result is True

    @pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
    def test_verify_analysis_outputs_handles_external_project_symlink(self, tmp_path):
        """Stage 02 output checks work when projects/<name> points outside the repo."""
        repo_root = tmp_path / "repo"
        projects_dir = repo_root / "projects"
        projects_dir.mkdir(parents=True)

        external = tmp_path / "private" / "active" / "linked_project"
        (external / "scripts").mkdir(parents=True)
        (external / "scripts" / "analysis.py").write_text("# analysis")
        (external / "output" / "data").mkdir(parents=True)
        (external / "output" / "data" / "result.json").write_text("{}")

        (projects_dir / "linked_project").symlink_to(external, target_is_directory=True)

        assert verify_analysis_outputs(repo_root, "linked_project") is True

    def test_verify_analysis_outputs_nested_files(self, tmp_path):
        """Test verifying with nested file structure."""
        repo_root = tmp_path / "repo"

        figures_dir = repo_root / "project" / "output" / "figures"
        figures_dir.mkdir(parents=True)
        (figures_dir / "subdir").mkdir()
        (figures_dir / "subdir" / "nested.png").write_text("nested")
        (figures_dir / "top.png").write_text("top")

        result = verify_analysis_outputs(repo_root)

        assert result is True

    def test_verify_analysis_outputs_quiet_when_some_outputs_present(
        self, tmp_path, caplog
    ):
        """When ``figures/`` has files but ``data/`` is absent, the
        ``not yet created: data`` line should be logged at DEBUG (not INFO)
        so projects that legitimately produce only figures don't surface
        the empty-companion message as recurring noise on every run.
        """
        repo_root = tmp_path / "repo"
        project_dir = repo_root / "projects" / "figures_only"
        figures_dir = project_dir / "output" / "figures"
        figures_dir.mkdir(parents=True)
        (figures_dir / "plot.png").write_text("plot")

        with caplog.at_level("DEBUG", logger="infrastructure.core.script_discovery"):
            result = verify_analysis_outputs(
                repo_root, project_name="figures_only", project_dir=project_dir
            )

        assert result is True
        not_yet_records = [
            r for r in caplog.records if "not yet created: data" in r.message
        ]
        assert not_yet_records, (
            "Expected at least one log record about the missing data/ directory."
        )
        for rec in not_yet_records:
            assert rec.levelname == "DEBUG", (
                f"Expected DEBUG when figures/ has files, got {rec.levelname}: "
                f"{rec.message}"
            )
        # And no INFO-level companion noise should leak through.
        for rec in caplog.records:
            if "not yet created: data" in rec.message or "is empty: data" in rec.message:
                assert rec.levelname != "INFO"

    def test_verify_analysis_outputs_loud_when_all_dirs_empty(
        self, tmp_path, caplog
    ):
        """When analysis scripts exist but **no** expected output directory
        contains files, the legacy INFO-level "not yet created" line stays
        loud so genuine analysis failures remain visible.
        """
        repo_root = tmp_path / "repo"
        project_dir = repo_root / "projects" / "no_output"
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "run_analysis.py").write_text("# noop")

        with caplog.at_level("INFO", logger="infrastructure.core.script_discovery"):
            result = verify_analysis_outputs(
                repo_root, project_name="no_output", project_dir=project_dir
            )

        assert result is False  # scripts present but no outputs
        info_not_yet = [
            r
            for r in caplog.records
            if r.levelname == "INFO" and "not yet created" in r.message
        ]
        assert info_not_yet, (
            "Expected the absent-output INFO line when nothing was generated."
        )

    def test_verify_analysis_outputs_ignores_setup_hook_only_project(self, tmp_path):
        """A project with only setup_hook.py does not require analysis outputs."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "projects" / "setup_only" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "setup_hook.py").write_text("# setup")

        assert verify_analysis_outputs(repo_root, "setup_only") is True


class TestDiscoverAnalysisScriptsFromScriptDiscovery:
    """Test discover_analysis_scripts with real directories."""

    def test_discovers_scripts(self, tmp_path):
        """Should discover Python scripts in scripts/ directory."""
        project_dir = tmp_path / "projects" / "testproj"
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "01_analysis.py").write_text("print('hello')")
        (scripts_dir / "02_plots.py").write_text("print('plot')")

        result = discover_analysis_scripts(tmp_path, "testproj")
        assert len(result) == 2
        assert all(s.suffix == ".py" for s in result)

    def test_ignores_underscore_scripts(self, tmp_path):
        """Should ignore scripts starting with underscore."""
        project_dir = tmp_path / "projects" / "testproj"
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "01_analysis.py").write_text("x")
        (scripts_dir / "_helper.py").write_text("x")
        (scripts_dir / "__init__.py").write_text("")

        result = discover_analysis_scripts(tmp_path, "testproj")
        assert len(result) == 1
        assert result[0].name == "01_analysis.py"

    def test_no_scripts_dir(self, tmp_path):
        """Should return empty list when scripts dir doesn't exist."""
        (tmp_path / "projects" / "testproj").mkdir(parents=True)
        result = discover_analysis_scripts(tmp_path, "testproj")
        assert result == []

    def test_empty_scripts_dir(self, tmp_path):
        """Should return empty list when scripts dir is empty."""
        scripts_dir = tmp_path / "projects" / "testproj" / "scripts"
        scripts_dir.mkdir(parents=True)
        result = discover_analysis_scripts(tmp_path, "testproj")
        assert result == []

    def test_custom_project_dir(self, tmp_path):
        """Should use project_dir when provided."""
        custom_dir = tmp_path / "custom"
        scripts_dir = custom_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "run.py").write_text("x")

        result = discover_analysis_scripts(tmp_path, "unused", project_dir=custom_dir)
        assert len(result) == 1


class TestDiscoverOrchestratorsFromScriptDiscovery:
    """Test discover_orchestrators with real scripts."""

    def test_discovers_existing_scripts(self, tmp_path):
        """Should find existing orchestrator scripts."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "00_setup_environment.py").write_text("x")
        (scripts_dir / "01_run_tests.py").write_text("x")

        result = discover_orchestrators(tmp_path)
        assert len(result) == 2

    def test_raises_without_scripts_dir(self, tmp_path):
        """Should raise PipelineError if scripts dir doesn't exist."""
        with pytest.raises(PipelineError):
            discover_orchestrators(tmp_path)

    def test_warns_about_missing_scripts(self, tmp_path):
        """Should handle partial set of orchestrators."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "00_setup_environment.py").write_text("x")
        result = discover_orchestrators(tmp_path)
        assert len(result) == 1


class TestVerifyAnalysisOutputsFromScriptDiscovery:
    """Test verify_analysis_outputs with real file structures."""

    def test_no_scripts_returns_true(self, tmp_path):
        """Should return True when no scripts exist (nothing expected)."""
        project_dir = tmp_path / "projects" / "testproj"
        project_dir.mkdir(parents=True)
        assert verify_analysis_outputs(tmp_path, "testproj") is True

    def test_scripts_with_outputs_returns_true(self, tmp_path):
        """Should return True when scripts and outputs both exist."""
        project_dir = tmp_path / "projects" / "testproj"
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "analysis.py").write_text("x")

        figures_dir = project_dir / "output" / "figures"
        figures_dir.mkdir(parents=True)
        (figures_dir / "fig1.png").write_bytes(b"png")

        assert verify_analysis_outputs(tmp_path, "testproj") is True

    def test_scripts_without_outputs_returns_false(self, tmp_path):
        """Should return False when scripts exist but no outputs."""
        project_dir = tmp_path / "projects" / "testproj"
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "analysis.py").write_text("x")

        assert verify_analysis_outputs(tmp_path, "testproj") is False

    def test_custom_project_dir(self, tmp_path):
        """Should use project_dir when provided."""
        custom_dir = tmp_path / "custom"
        (custom_dir / "output" / "figures").mkdir(parents=True)
        (custom_dir / "output" / "figures" / "fig.png").write_bytes(b"x")

        assert verify_analysis_outputs(tmp_path, "unused", project_dir=custom_dir) is True

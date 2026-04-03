"""Tests for infrastructure/core/script_discovery.py.

Covers: discover_analysis_scripts, discover_orchestrators, verify_analysis_outputs.

No mocks used — all tests use real file structures.
"""

from __future__ import annotations


import pytest

from infrastructure.core.exceptions import PipelineError
from infrastructure.core.script_discovery import (
    discover_analysis_scripts,
    discover_orchestrators,
    verify_analysis_outputs,
)


class TestDiscoverAnalysisScripts:
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


class TestDiscoverOrchestrators:
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


class TestVerifyAnalysisOutputs:
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

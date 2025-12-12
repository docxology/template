"""Tests for infrastructure.core.script_discovery module.

Comprehensive tests for script discovery and output verification utilities.
"""

from pathlib import Path
import pytest
import tempfile

from infrastructure.core.script_discovery import (
    discover_analysis_scripts,
    discover_orchestrators,
    verify_analysis_outputs,
)
from infrastructure.core.exceptions import PipelineError


class TestDiscoverAnalysisScripts:
    """Test discover_analysis_scripts function."""

    def test_discover_analysis_scripts_finds_python_files(self, tmp_path):
        """Test discovering Python scripts in project/scripts/."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "project" / "scripts"
        scripts_dir.mkdir(parents=True)
        
        # Create some Python scripts
        (scripts_dir / "analysis1.py").write_text("# Script 1")
        (scripts_dir / "analysis2.py").write_text("# Script 2")
        (scripts_dir / "analysis3.py").write_text("# Script 3")
        
        scripts = discover_analysis_scripts(repo_root)
        
        assert len(scripts) == 3
        assert all(s.suffix == '.py' for s in scripts)
        assert all(s.name in ['analysis1.py', 'analysis2.py', 'analysis3.py'] for s in scripts)

    def test_discover_analysis_scripts_ignores_hidden(self, tmp_path):
        """Test that hidden files (starting with _) are ignored."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "project" / "scripts"
        scripts_dir.mkdir(parents=True)
        
        (scripts_dir / "public.py").write_text("# Public")
        (scripts_dir / "_private.py").write_text("# Private")
        (scripts_dir / "__init__.py").write_text("# Init")
        
        scripts = discover_analysis_scripts(repo_root)
        
        assert len(scripts) == 1
        assert scripts[0].name == "public.py"

    def test_discover_analysis_scripts_sorted(self, tmp_path):
        """Test that scripts are returned in sorted order."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "project" / "scripts"
        scripts_dir.mkdir(parents=True)
        
        # Create scripts in non-alphabetical order
        (scripts_dir / "zebra.py").write_text("# Z")
        (scripts_dir / "alpha.py").write_text("# A")
        (scripts_dir / "beta.py").write_text("# B")
        
        scripts = discover_analysis_scripts(repo_root)
        
        assert len(scripts) == 3
        assert scripts[0].name == "alpha.py"
        assert scripts[1].name == "beta.py"
        assert scripts[2].name == "zebra.py"

    def test_discover_analysis_scripts_empty_directory(self, tmp_path):
        """Test discovering scripts in empty directory."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "project" / "scripts"
        scripts_dir.mkdir(parents=True)
        
        scripts = discover_analysis_scripts(repo_root)
        
        assert len(scripts) == 0
        assert isinstance(scripts, list)

    def test_discover_analysis_scripts_missing_directory(self, tmp_path):
        """Test error when project/scripts/ directory doesn't exist."""
        repo_root = tmp_path / "repo"
        # Don't create project/scripts/
        
        with pytest.raises(PipelineError) as exc_info:
            discover_analysis_scripts(repo_root)
        
        assert "not found" in str(exc_info.value).lower()

    def test_discover_analysis_scripts_ignores_non_python(self, tmp_path):
        """Test that non-Python files are ignored."""
        repo_root = tmp_path / "repo"
        scripts_dir = repo_root / "project" / "scripts"
        scripts_dir.mkdir(parents=True)
        
        (scripts_dir / "script.py").write_text("# Python")
        (scripts_dir / "script.txt").write_text("Text file")
        (scripts_dir / "script.sh").write_text("# Shell")
        (scripts_dir / "README.md").write_text("# Readme")
        
        scripts = discover_analysis_scripts(repo_root)
        
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


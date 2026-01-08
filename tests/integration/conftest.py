"""Pytest configuration for integration tests.

Provides shared fixtures and utilities for integration testing across
the research project template. All fixtures use real implementations
following the 'no mocks' policy.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Repository root path
ROOT = Path(__file__).parent.parent.parent.resolve()
SRC = ROOT / "src"

# Add src/ to path so we can import infrastructure and scientific modules
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory.
    
    Returns:
        Path to the repository root (where pyproject.toml is located)
    """
    return ROOT


@pytest.fixture
def scripts_path(repo_root: Path) -> Path:
    """Get the scripts directory path.
    
    Returns:
        Path to the scripts/ directory
    """
    return repo_root / "scripts"


# =============================================================================
# Temporary Project Structure Fixtures
# =============================================================================

@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary project directory with standard structure.
    
    Creates:
        - src/ directory with __init__.py
        - tests/ directory with __init__.py
        - manuscript/ directory
        - output/ directory with subdirectories
    
    Yields:
        Path to the temporary project directory
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Create standard subdirectories
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "__init__.py").write_text("")
    (project_dir / "manuscript").mkdir()
    (project_dir / "output").mkdir()
    
    # Create output subdirectories
    for subdir in ["pdf", "figures", "data", "web", "slides", "reports", "logs"]:
        (project_dir / "output" / subdir).mkdir()
    
    yield project_dir


@pytest.fixture
def sample_project_structure(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a complete sample project structure for testing.
    
    Creates a full project layout with:
        - projects/ directory with sample projects
        - output/ directory with project outputs
        - Sample manuscript, source, and test files
    
    Yields:
        Path to the temporary repository root
    """
    # Create projects directory
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    
    # Create two sample projects
    for project_name in ["project1", "project2"]:
        project_root = projects_dir / project_name
        project_root.mkdir()
        
        # Create manuscript
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text(
            "# Introduction\n\nTest manuscript content for integration testing.\n"
        )
        (manuscript_dir / "config.yaml").write_text(
            "paper:\n  title: Test Paper\nauthors:\n  - name: Test Author\n"
        )
        
        # Create src
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        (src_dir / "test_module.py").write_text("def test_function():\n    pass\n")
        
        # Create tests
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_sample.py").write_text(
            "def test_example():\n    assert True\n"
        )
        
        # Create output structure
        output_dir = project_root / "output"
        for subdir in ["pdf", "figures", "data", "web", "slides", "reports", "logs"]:
            (output_dir / subdir).mkdir(parents=True)
        
        # Create sample reports
        reports_dir = output_dir / "reports"
        test_report = {
            "project_tests": {
                "total": 50, "passed": 50, "failed": 0, "skipped": 0,
                "coverage_percent": 95.0
            },
            "summary": {"total_execution_time": 5.0}
        }
        (reports_dir / "test_results.json").write_text(json.dumps(test_report))
        
        # Create top-level output directory
        top_output = tmp_path / "output" / project_name
        top_output.mkdir(parents=True)
        pdf_dir = top_output / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / f"{project_name}_combined.pdf").write_text("PDF content")
    
    yield tmp_path


@pytest.fixture
def sample_manuscript_files(temp_project_dir: Path) -> dict[str, Path]:
    """Create sample manuscript files in a temporary project.
    
    Creates standard manuscript sections with LaTeX-style content.
    
    Returns:
        Dictionary mapping section names to file paths
    """
    manuscript_dir = temp_project_dir / "manuscript"
    
    files = {}
    sections = [
        ("01_abstract", "# Abstract\n\nThis is a test abstract with sample content.\n"),
        ("02_introduction", "# Introduction\n\nTest introduction with \\cite{ref2024}.\n"),
        ("03_methodology", "# Methodology\n\n\\begin{equation}\\label{eq:test}\nx = y\n\\end{equation}\n"),
        ("04_results", "# Results\n\nSee Figure \\ref{fig:test} for results.\n"),
    ]
    
    for name, content in sections:
        file_path = manuscript_dir / f"{name}.md"
        file_path.write_text(content)
        files[name] = file_path
    
    return files


# =============================================================================
# Subprocess Helpers
# =============================================================================

@pytest.fixture
def run_bash_command():
    """Fixture providing a helper to run bash commands.
    
    Returns:
        Function that runs bash commands and returns CompletedProcess
    """
    def _run(command: str, cwd: Path | None = None, env: dict | None = None):
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        return subprocess.run(
            ["bash", "-c", command],
            cwd=str(cwd) if cwd else None,
            env=full_env,
            capture_output=True,
            text=True
        )
    
    return _run


@pytest.fixture
def run_python_script(repo_root: Path):
    """Fixture providing a helper to run Python scripts.
    
    Returns:
        Function that runs Python scripts and returns CompletedProcess
    """
    def _run(
        script_path: Path | str,
        args: list[str] | None = None,
        cwd: Path | None = None
    ):
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        return subprocess.run(
            cmd,
            cwd=str(cwd or repo_root),
            env=os.environ.copy(),
            capture_output=True,
            text=True
        )
    
    return _run


# =============================================================================
# Script Path Fixtures
# =============================================================================

@pytest.fixture
def bash_utils_path(repo_root: Path) -> Path:
    """Get the path to bash_utils.sh script."""
    return repo_root / "scripts" / "bash_utils.sh"


@pytest.fixture
def run_sh_path(repo_root: Path) -> Path:
    """Get the path to run.sh script."""
    return repo_root / "run.sh"


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture
def cleanup_temp_files(tmp_path: Path):
    """Fixture that provides cleanup helper and auto-cleans on teardown.
    
    Yields:
        Function to register additional paths for cleanup
    """
    paths_to_clean = []
    
    def _register(path: Path):
        paths_to_clean.append(path)
    
    yield _register
    
    # Cleanup registered paths
    for path in paths_to_clean:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

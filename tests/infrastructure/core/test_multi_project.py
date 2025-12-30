"""Tests for multi-project orchestration system."""
from __future__ import annotations

import pytest
from pathlib import Path
import tempfile
import time
from pathlib import Path

from infrastructure.core.multi_project import (
    MultiProjectConfig,
    MultiProjectResult,
    MultiProjectOrchestrator
)
from infrastructure.project.discovery import ProjectInfo


def _create_test_repo_structure(tmp_dir: Path, make_project2_fail: bool = False) -> Path:
    """Create a minimal test repository structure with scripts and projects."""
    repo_root = Path(tmp_dir) / "repo"
    repo_root.mkdir()

    # Create scripts directory with minimal script stubs
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir()

    # Create minimal script stubs that succeed
    script_files = [
        "00_setup_environment.py",
        "01_run_tests.py",
        "02_run_analysis.py",
        "03_render_pdf.py",
        "04_validate_output.py",
        "05_copy_outputs.py",
        "06_llm_review.py",
        "07_generate_executive_report.py"
    ]

    for script_file in script_files:
        script_path = scripts_dir / script_file
        if script_file == "02_run_analysis.py" and make_project2_fail:
            # Make analysis script fail for project2
            script_path.write_text("""
import sys
import time
time.sleep(0.01)  # Minimal delay to simulate work

# Check if this is for project2
project_name = None
for i, arg in enumerate(sys.argv):
    if arg == "--project" and i + 1 < len(sys.argv):
        project_name = sys.argv[i + 1]
        break

if project_name == "project2":
    print("Analysis failed for project2", file=sys.stderr)
    sys.exit(1)
else:
    print("Script executed successfully")
    sys.exit(0)
""")
        else:
            script_path.write_text("""
import sys
import time
time.sleep(0.01)  # Minimal delay to simulate work
print("Script executed successfully")
sys.exit(0)
""")

    # Create projects directory
    projects_dir = repo_root / "projects"
    projects_dir.mkdir()

    return repo_root


def _create_test_project(repo_root: Path, project_name: str) -> None:
    """Create a minimal test project structure."""
    project_dir = repo_root / "projects" / project_name
    project_dir.mkdir()

    # Create required directories
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "scripts").mkdir()
    (project_dir / "manuscript").mkdir()
    (project_dir / "output").mkdir()

    # Create minimal files
    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "tests" / "__init__.py").write_text("")
    (project_dir / "scripts" / "__init__.py").write_text("")
    (project_dir / "manuscript" / "config.yaml").write_text("""
paper:
  title: "Test Project"
authors:
  - name: "Test Author"
""")

    # Create a minimal analysis script
    analysis_script = project_dir / "scripts" / "analysis_pipeline.py"
    analysis_script.write_text("""
import sys
print("Analysis completed")
sys.exit(0)
""")


class TestMultiProjectConfig:
    """Test MultiProjectConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        projects = [ProjectInfo(name="test", path=Path("/tmp/test"), has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
        config = MultiProjectConfig(repo_root=Path("/tmp"), projects=projects)

        assert config.repo_root == Path("/tmp")
        assert config.projects == projects
        assert config.run_infra_tests is True
        assert config.run_llm is True
        assert config.run_executive_report is True

    def test_custom_values(self):
        """Test custom configuration values."""
        projects = [ProjectInfo(name="test", path=Path("/tmp/test"), has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
        config = MultiProjectConfig(
            repo_root=Path("/repo"),
            projects=projects,
            run_infra_tests=False,
            run_llm=False,
            run_executive_report=False
        )

        assert config.repo_root == Path("/repo")
        assert config.projects == projects
        assert config.run_infra_tests is False
        assert config.run_llm is False
        assert config.run_executive_report is False


class TestMultiProjectResult:
    """Test MultiProjectResult dataclass."""

    def test_result_creation(self):
        """Test result creation."""
        project_results = {"project1": [], "project2": []}

        result = MultiProjectResult(
            project_results=project_results,
            infra_test_duration=15.5,
            total_duration=120.3,
            successful_projects=2,
            failed_projects=0
        )

        assert result.project_results == project_results
        assert result.infra_test_duration == 15.5
        assert result.total_duration == 120.3
        assert result.successful_projects == 2
        assert result.failed_projects == 0


class TestMultiProjectOrchestrator:
    """Test MultiProjectOrchestrator class."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        projects = [ProjectInfo(name="test", path=Path("/tmp/test"), has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
        config = MultiProjectConfig(repo_root=Path("/tmp"), projects=projects)
        orchestrator = MultiProjectOrchestrator(config)

        assert orchestrator.config == config

    def test_execute_all_projects_full_success(self):
        """Test successful full pipeline execution for all projects."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure (no failures)
            repo_root = _create_test_repo_structure(Path(tmp_dir), make_project2_fail=False)

            # Create test projects
            _create_test_project(repo_root, "project1")
            _create_test_project(repo_root, "project2")

            # Setup projects
            projects = [
                ProjectInfo(name="project1", path=repo_root / "projects" / "project1", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={}),
                ProjectInfo(name="project2", path=repo_root / "projects" / "project2", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})
            ]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects_full()

            assert isinstance(result, MultiProjectResult)
            assert len(result.project_results) == 2
            assert result.successful_projects == 2
            assert result.failed_projects == 0
            assert result.infra_test_duration > 0  # Should have run infra tests
            assert result.total_duration > 0

            # Verify each project has results
            assert "project1" in result.project_results
            assert "project2" in result.project_results
            assert len(result.project_results["project1"]) > 0
            assert len(result.project_results["project2"]) > 0

    def test_execute_all_projects_core_success(self):
        """Test successful core pipeline execution for all projects."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Create test project
            _create_test_project(repo_root, "project1")

            # Setup projects
            projects = [ProjectInfo(name="project1", path=repo_root / "projects" / "project1", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects_core()

            assert isinstance(result, MultiProjectResult)
            assert len(result.project_results) == 1
            assert result.successful_projects == 1
            assert result.failed_projects == 0
            assert result.infra_test_duration > 0  # Should have run infra tests

            # Verify project has results
            assert "project1" in result.project_results
            assert len(result.project_results["project1"]) > 0

    def test_execute_all_projects_full_no_infra_success(self):
        """Test successful full pipeline execution without infrastructure tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Create test project
            _create_test_project(repo_root, "project1")

            # Setup projects with run_infra_tests=False
            projects = [ProjectInfo(name="project1", path=repo_root / "projects" / "project1", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects, run_infra_tests=False)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects_full_no_infra()

            assert isinstance(result, MultiProjectResult)
            assert len(result.project_results) == 1
            assert result.successful_projects == 1
            assert result.failed_projects == 0
            assert result.infra_test_duration == 0.0  # No infra tests run

            # Verify project has results
            assert "project1" in result.project_results
            assert len(result.project_results["project1"]) > 0

    def test_execute_all_projects_with_failure(self):
        """Test execution when some projects fail."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure (project2 will fail)
            repo_root = _create_test_repo_structure(Path(tmp_dir), make_project2_fail=True)

            # Create test projects
            _create_test_project(repo_root, "project1")
            # Create a failing project by making its analysis script fail
            _create_test_project(repo_root, "project2")
            # Make the analysis script fail for project2
            analysis_script = repo_root / "projects" / "project2" / "scripts" / "analysis_pipeline.py"
            analysis_script.write_text("""
import sys
print("Analysis failed", file=sys.stderr)
sys.exit(1)  # Fail the script
""")

            # Setup projects
            projects = [
                ProjectInfo(name="project1", path=repo_root / "projects" / "project1", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={}),
                ProjectInfo(name="project2", path=repo_root / "projects" / "project2", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})
            ]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects_full()

            assert result.successful_projects == 1
            assert result.failed_projects == 1
            assert len(result.project_results) == 2
            assert result.infra_test_duration > 0  # Should have run infra tests

    def test_run_infrastructure_tests_once_success(self):
        """Test successful infrastructure tests execution."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Create test project
            _create_test_project(repo_root, "test")

            projects = [ProjectInfo(name="test", path=repo_root / "projects" / "test", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator._run_infrastructure_tests_once()

            assert result is True

    def test_run_infrastructure_tests_once_failure(self):
        """Test failed infrastructure tests execution."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure with failing infra tests
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Make the infrastructure tests script fail
            infra_test_script = repo_root / "scripts" / "01_run_tests.py"
            infra_test_script.write_text("""
import sys
print("Infrastructure tests failed", file=sys.stderr)
sys.exit(1)
""")

            # Create test project
            _create_test_project(repo_root, "test")

            projects = [ProjectInfo(name="test", path=repo_root / "projects" / "test", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator._run_infrastructure_tests_once()

            assert result is False

    def test_run_executive_reporting_import_error(self):
        """Test executive reporting when import fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            projects = [ProjectInfo(name="test", path=repo_root / "test", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            # Should not raise exception even if import fails
            # (the executive reporting module doesn't exist in our test environment)
            result = orchestrator._run_executive_reporting({})
            assert result is None

    def test_run_executive_reporting_single_project(self):
        """Test executive reporting is skipped for single project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            projects = [ProjectInfo(name="test", path=repo_root / "test", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator._run_executive_reporting({"project1": []})
            assert result is None  # Should be None when import fails or single project

    def test_timing_measurement(self):
        """Test that timing is measured correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Create test project
            _create_test_project(repo_root, "test")

            projects = [ProjectInfo(name="test", path=repo_root / "projects" / "test", has_src=True, has_tests=True, has_scripts=True, has_manuscript=True, metadata={})]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            # Execute a real pipeline and verify timing
            start_time = time.time()
            result = orchestrator.execute_all_projects_core()
            end_time = time.time()

            # Verify timing measurements are reasonable
            assert result.total_duration > 0
            assert result.infra_test_duration > 0
            assert result.total_duration >= result.infra_test_duration
            assert end_time - start_time >= result.total_duration
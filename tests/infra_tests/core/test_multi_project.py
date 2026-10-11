"""Tests for multi-project orchestration system."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path


import pytest

from infrastructure.core.pipeline.multi_project import (
    MultiProjectConfig,
    MultiProjectOrchestrator,
    MultiProjectResult,
)
from infrastructure.project.project_info import ProjectInfo
from tests._support.projects import make_project


def _create_test_repo_structure(tmp_dir: Path, make_project2_fail: bool = False) -> Path:
    """Create a minimal test repository structure with scripts and projects."""
    repo_root = Path(tmp_dir).resolve() / "repo"
    repo_root.mkdir()

    # Create scripts directory with minimal script stubs
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir()

    # Create minimal script stubs that succeed
    script_files = [
        "pipeline/stage_00_setup.py",
        "pipeline/stage_01_test.py",
        "pipeline/stage_02_analysis.py",
        "pipeline/stage_03_render.py",
        "pipeline/stage_04_validate.py",
        "pipeline/stage_05_copy.py",
        "pipeline/stage_06_llm_review.py",
        "pipeline/stage_07_executive_report.py",
    ]

    for script_file in script_files:
        script_path = scripts_dir / script_file
        script_path.parent.mkdir(parents=True, exist_ok=True)
        if script_file == "pipeline/stage_02_analysis.py" and make_project2_fail:
            # Make analysis script fail for project2
            script_path.write_text(
                """
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
"""
            )
        else:
            script_path.write_text(
                """
import sys
import time
time.sleep(0.01)  # Minimal delay to simulate work
print("Script executed successfully")
sys.exit(0)
"""
            )

    # Explicit child-only fixture contract; these tests assert invocation and
    # isolation, and do not claim rendered/validated scientific deliverables.
    import yaml

    stages = [
        {
            "name": "Infrastructure Tests",
            "key": "infra_tests",
            "script": "scripts/pipeline/stage_01_test.py",
            "args": ["--infra-only"],
            "tags": ["core"],
        },
        {
            "name": "Project Analysis",
            "key": "analysis",
            "script": "scripts/pipeline/stage_02_analysis.py",
            "tags": ["core"],
        },
        {
            "name": "Live Review",
            "key": "llm_reviews",
            "script": "scripts/pipeline/stage_06_llm_review.py",
            "tags": ["llm", "live"],
        },
    ]
    for stage in stages:
        stage["contract"] = {
            "definition_of_done": "The real child exits zero and its invocation is logged.",
            "failure_code": "FIXTURE_CHILD_FAILED",
        }
    declaration = repo_root / "infrastructure/core/pipeline/pipeline.yaml"
    declaration.parent.mkdir(parents=True)
    declaration.write_text(yaml.safe_dump({"stages": stages, "telemetry": {"enabled": False}}))
    (repo_root / "projects").mkdir()
    return repo_root


def _create_test_project(repo_root: Path, project_name: str) -> None:
    """Create a minimal test project structure."""
    project_dir = make_project(
        repo_root,
        project_name,
        with_manuscript=True,
        with_scripts=True,
        with_output=True,
    )
    (project_dir / "manuscript" / "config.yaml").write_text(
        """
paper:
  title: "Test Project"
authors:
  - name: "Test Author"
"""
    )
    analysis_script = project_dir / "scripts" / "analysis_pipeline.py"
    analysis_script.write_text(
        """
import sys
print("Analysis completed")
sys.exit(0)
"""
    )


class TestMultiProjectConfig:
    """Test MultiProjectConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        projects = [
            ProjectInfo(
                name="test",
                path=Path("/tmp/test"),
                has_src=True,
                has_tests=True,
                has_scripts=True,
                has_manuscript=True,
                metadata={},
            )
        ]
        config = MultiProjectConfig(repo_root=Path("/tmp"), projects=projects)

        assert config.repo_root == Path("/tmp")
        assert config.projects == projects
        assert config.run_infra_tests is True
        assert config.mode == "core"

    def test_custom_values(self):
        """Test custom configuration values."""
        projects = [
            ProjectInfo(
                name="test",
                path=Path("/tmp/test"),
                has_src=True,
                has_tests=True,
                has_scripts=True,
                has_manuscript=True,
                metadata={},
            )
        ]
        config = MultiProjectConfig(
            repo_root=Path("/repo"),
            projects=projects,
            run_infra_tests=False,
            mode="core",
        )

        assert config.repo_root == Path("/repo")
        assert config.projects == projects
        assert config.run_infra_tests is False
        assert config.mode == "core"


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
            failed_projects=0,
        )

        assert result.project_results == project_results
        assert result.infra_test_duration == 15.5
        assert result.total_duration == 120.3
        assert result.successful_projects == 2
        assert result.failed_projects == 0


@pytest.mark.timeout(120)
class TestMultiProjectOrchestrator:
    """Test MultiProjectOrchestrator class."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        projects = [
            ProjectInfo(
                name="test",
                path=Path("/tmp/test"),
                has_src=True,
                has_tests=True,
                has_scripts=True,
                has_manuscript=True,
                metadata={},
            )
        ]
        config = MultiProjectConfig(repo_root=Path("/tmp"), projects=projects)
        orchestrator = MultiProjectOrchestrator(config)

        assert orchestrator.config == config

    @pytest.mark.slow
    def test_execute_live_projects_success(self):
        """Test successful full pipeline execution for all projects."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure (no failures)
            repo_root = _create_test_repo_structure(Path(tmp_dir), make_project2_fail=False)

            # Create test projects
            _create_test_project(repo_root, "project1")
            _create_test_project(repo_root, "project2")

            # Setup projects
            projects = [
                ProjectInfo(
                    name="project1",
                    path=repo_root / "projects" / "project1",
                    has_src=True,
                    has_tests=True,
                    has_scripts=True,
                    has_manuscript=True,
                    metadata={},
                ),
                ProjectInfo(
                    name="project2",
                    path=repo_root / "projects" / "project2",
                    has_src=True,
                    has_tests=True,
                    has_scripts=True,
                    has_manuscript=True,
                    metadata={},
                ),
            ]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects, mode="live")
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects()

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

    @pytest.mark.slow
    def test_execute_core_projects_success(self):
        """Test successful core pipeline execution for all projects."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Create test project
            _create_test_project(repo_root, "project1")

            # Setup projects
            projects = [
                ProjectInfo(
                    name="project1",
                    path=repo_root / "projects" / "project1",
                    has_src=True,
                    has_tests=True,
                    has_scripts=True,
                    has_manuscript=True,
                    metadata={},
                )
            ]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects()

            assert isinstance(result, MultiProjectResult)
            assert len(result.project_results) == 1
            assert result.successful_projects == 1
            assert result.failed_projects == 0
            assert result.infra_test_duration > 0  # Should have run infra tests

            # Verify project has results
            assert "project1" in result.project_results
            assert len(result.project_results["project1"]) > 0

    def test_execute_nested_project_uses_qualified_name_and_real_path(self):
        """Nested projects run with program/name while resolving under projects/."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = _create_test_repo_structure(Path(tmp_dir))
            qualified_name = "my_program/nested_project"
            _create_test_project(repo_root, qualified_name)

            args_log = repo_root / "stage_args.txt"
            for script_path in (repo_root / "scripts" / "pipeline").glob("*.py"):
                script_path.write_text(
                    """
import sys
from pathlib import Path

Path("stage_args.txt").open("a", encoding="utf-8").write(" ".join(sys.argv) + "\\n")
sys.exit(0)
"""
                )

            project = ProjectInfo(
                name="nested_project",
                path=repo_root / "projects" / qualified_name,
                has_src=True,
                has_tests=True,
                has_scripts=True,
                has_manuscript=True,
                metadata={},
                program="my_program",
            )
            config = MultiProjectConfig(
                repo_root=repo_root,
                projects=[project],
                run_infra_tests=False,
            )
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects()

            assert result.successful_projects == 1
            assert qualified_name in result.project_results
            assert (repo_root / "projects" / qualified_name / "output" / "logs").exists()
            assert result.run_results[qualified_name].expected_stage_keys == ("analysis",)
            assert args_log.exists()
            assert f"--project {qualified_name}" in args_log.read_text(encoding="utf-8")

    @pytest.mark.slow
    def test_execute_core_without_shared_infrastructure_success(self):
        """Test successful full pipeline execution without infrastructure tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Create test project
            _create_test_project(repo_root, "project1")

            # Setup projects with run_infra_tests=False
            projects = [
                ProjectInfo(
                    name="project1",
                    path=repo_root / "projects" / "project1",
                    has_src=True,
                    has_tests=True,
                    has_scripts=True,
                    has_manuscript=True,
                    metadata={},
                )
            ]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects, run_infra_tests=False)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects()

            assert isinstance(result, MultiProjectResult)
            assert len(result.project_results) == 1
            assert result.successful_projects == 1
            assert result.failed_projects == 0
            assert result.infra_test_duration == 0.0  # No infra tests run

            # Verify project has results
            assert "project1" in result.project_results
            assert len(result.project_results["project1"]) > 0

    @pytest.mark.slow
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
            analysis_script.write_text(
                """
import sys
print("Analysis failed", file=sys.stderr)
sys.exit(1)  # Fail the script
"""
            )

            # Setup projects
            projects = [
                ProjectInfo(
                    name="project1",
                    path=repo_root / "projects" / "project1",
                    has_src=True,
                    has_tests=True,
                    has_scripts=True,
                    has_manuscript=True,
                    metadata={},
                ),
                ProjectInfo(
                    name="project2",
                    path=repo_root / "projects" / "project2",
                    has_src=True,
                    has_tests=True,
                    has_scripts=True,
                    has_manuscript=True,
                    metadata={},
                ),
            ]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            result = orchestrator.execute_all_projects()

            assert result.successful_projects == 1
            assert result.failed_projects == 1
            assert len(result.project_results) == 2
            assert result.infra_test_duration > 0  # Should have run infra tests

    @pytest.mark.parametrize("infra_exit, expected_code", [(0, 0), (2, 1)])
    def test_shared_infrastructure_real_child(self, tmp_path: Path, infra_exit: int, expected_code: int):
        from infrastructure.core.pipeline.multi_project_support import run_shared_infrastructure
        from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

        scaffold_pipeline(tmp_path, ("templates/demo",), infra_exit=infra_exit)
        from infrastructure.core.pipeline.multi_project_runtime import freeze_project_plans, freeze_shared_plan

        specs = freeze_project_plans(("templates/demo",), tmp_path, mode="core", resume=False, timeout=90)
        shared = run_shared_infrastructure(freeze_shared_plan(specs), deadline=time.monotonic() + 90)
        assert shared.exit_code == expected_code
        assert shared.run_result.expected_stage_keys == ("infra_tests",)
        assert shared.run_result.outcomes[0].child_exit_code == infra_exit
        assert shared.stage_results[0].outcome == shared.run_result.outcomes[0]
        assert (tmp_path / "process_order.log").read_text().splitlines() == ["templates/demo:infra"]

    @pytest.mark.slow
    def test_timing_measurement(self):
        """Test that timing is measured correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create real test repository structure
            repo_root = _create_test_repo_structure(Path(tmp_dir))

            # Create test project
            _create_test_project(repo_root, "test")

            projects = [
                ProjectInfo(
                    name="test",
                    path=repo_root / "projects" / "test",
                    has_src=True,
                    has_tests=True,
                    has_scripts=True,
                    has_manuscript=True,
                    metadata={},
                )
            ]
            config = MultiProjectConfig(repo_root=repo_root, projects=projects)
            orchestrator = MultiProjectOrchestrator(config)

            # Execute a real pipeline and verify timing
            start_time = time.time()
            result = orchestrator.execute_all_projects()
            end_time = time.time()

            # Verify timing measurements are reasonable
            assert result.total_duration > 0
            assert result.infra_test_duration > 0
            assert result.total_duration >= result.infra_test_duration
            assert end_time - start_time >= result.total_duration


def test_public_result_refuses_contradictory_row_and_run_evidence() -> None:
    from infrastructure.core.pipeline.multi_project import format_multi_project_outcome_lines
    from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
    from infrastructure.core.pipeline.types import PipelineStageResult

    failed = StageOutcome("analysis", StageStatus.FAILED, 2, "actual child failed")
    row = PipelineStageResult(
        1, "Analysis", False, 0.1, 2, "actual child failed", stage_completed=False, stage_key="analysis", outcome=failed
    )
    result = MultiProjectResult(
        {"alpha": [row]},
        expected_projects=("alpha",),
        run_results={"alpha": RunResult(("analysis",), (StageOutcome("analysis", StageStatus.SUCCEEDED, 0),))},
    )
    project = ProjectInfo("alpha", Path("/tmp/alpha"), True, True, False, False)
    assert result.exit_code == 1
    text = "\n".join(format_multi_project_outcome_lines([project], result))
    assert "Succeeded:" not in text and "actual child failed" in text


@pytest.mark.parametrize(("shared", "expected"), [(False, 1), (True, 1), (2, 1), (7, 1), (75, 75), (0, 0)])
def test_public_shared_gate_code_cannot_grant_invalid_completion(shared: int, expected: int) -> None:
    from infrastructure.core.pipeline.outcomes import RunResult
    from infrastructure.core.pipeline.types import PipelineStageResult

    row = PipelineStageResult(1, "Analysis", True, 0.1, 0, stage_key="analysis")
    run = RunResult.from_results([row], ("analysis",))
    result = MultiProjectResult(
        {"templates/demo": [row]},
        expected_projects=("templates/demo",),
        run_results={"templates/demo": run},
        shared_infrastructure_exit_code=shared,
    )
    assert result.exit_code == expected

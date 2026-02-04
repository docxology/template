"""Tests for pipeline execution system."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from infrastructure.core.checkpoint import CheckpointManager
from infrastructure.core.pipeline import (PipelineConfig, PipelineExecutor,
                                          PipelineStageResult)


class TestPipelineConfig:
    """Test PipelineConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PipelineConfig(project_name="test_project", repo_root=Path("/tmp"))

        assert config.project_name == "test_project"
        assert config.repo_root == Path("/tmp")
        assert config.skip_infra is False
        assert config.skip_llm is False
        assert config.resume is False
        assert config.total_stages == 10

    def test_custom_values(self):
        """Test custom configuration values."""
        config = PipelineConfig(
            project_name="myproject",
            repo_root=Path("/repo"),
            skip_infra=True,
            skip_llm=True,
            resume=True,
            total_stages=7,
        )

        assert config.project_name == "myproject"
        assert config.repo_root == Path("/repo")
        assert config.skip_infra is True
        assert config.skip_llm is True
        assert config.resume is True
        assert config.total_stages == 7


class TestPipelineStageResult:
    """Test PipelineStageResult dataclass."""

    def test_success_result(self):
        """Test successful stage result."""
        result = PipelineStageResult(
            stage_num=1, stage_name="Test Stage", success=True, duration=5.2
        )

        assert result.stage_num == 1
        assert result.stage_name == "Test Stage"
        assert result.success is True
        assert result.duration == 5.2
        assert result.exit_code == 0
        assert result.error_message == ""

    def test_failure_result(self):
        """Test failed stage result."""
        result = PipelineStageResult(
            stage_num=2,
            stage_name="Failed Stage",
            success=False,
            duration=10.5,
            exit_code=1,
            error_message="Command failed",
        )

        assert result.stage_num == 2
        assert result.stage_name == "Failed Stage"
        assert result.success is False
        assert result.duration == 10.5
        assert result.exit_code == 1
        assert result.error_message == "Command failed"


class TestPipelineExecutor:
    """Test PipelineExecutor class."""

    def _create_fake_repo(
        self, repo_root: Path, project_name: str, include_llm: bool
    ) -> Path:
        """Create a minimal repo layout with scripts that always succeed.

        The pipeline executor runs scripts from `{repo_root}/scripts/*.py`. For tests we create
        minimal implementations that:
        - record their invocation to `{repo_root}/invocations.jsonl`
        - exit 0
        """
        scripts_dir = repo_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Minimal project structure so PYTHONPATH augmentation is stable
        (repo_root / "projects" / project_name / "src").mkdir(
            parents=True, exist_ok=True
        )
        (repo_root / "projects" / project_name / "output").mkdir(
            parents=True, exist_ok=True
        )

        common_script = """
import json
import os
import sys

log_path = os.path.join(os.getcwd(), "invocations.jsonl")
with open(log_path, "a", encoding="utf-8") as f:
    json.dump({"script": os.path.basename(__file__), "args": sys.argv[1:]}, f)
    f.write("\\n")

sys.exit(0)
"""

        scripts = [
            "00_setup_environment.py",
            "01_run_tests.py",
            "02_run_analysis.py",
            "03_render_pdf.py",
            "04_validate_output.py",
            "05_copy_outputs.py",
        ]
        if include_llm:
            scripts.append("06_llm_review.py")

        for name in scripts:
            (scripts_dir / name).write_text(common_script, encoding="utf-8")

        return repo_root

    def _make_executor(
        self,
        repo_root: Path,
        project_name: str,
        *,
        clean: bool,
        skip_infra: bool,
        skip_llm: bool,
        resume: bool,
    ) -> PipelineExecutor:
        """Create executor wired to a test-local checkpoint directory (no repo side effects)."""
        config = PipelineConfig(
            project_name=project_name,
            repo_root=repo_root,
            clean=clean,
            skip_infra=skip_infra,
            skip_llm=skip_llm,
            resume=resume,
        )
        executor = PipelineExecutor(config)

        # Ensure checkpoints are written under the temp repo, not the real repository root.
        checkpoint_dir = (
            repo_root / "projects" / project_name / "output" / ".checkpoints"
        )
        executor.checkpoint_manager = CheckpointManager(
            checkpoint_dir=checkpoint_dir, project_name=project_name
        )

        return executor

    def _read_invocations(self, repo_root: Path) -> list[dict]:
        inv_path = repo_root / "invocations.jsonl"
        if not inv_path.exists():
            return []
        lines = inv_path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def test_initialization(self):
        """Test executor initialization."""
        config = PipelineConfig(project_name="test", repo_root=Path("/tmp"))
        executor = PipelineExecutor(config)

        assert executor.config == config

    def test_run_script_success(self):
        """Test successful script execution."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a simple test script
            script_path = Path(tmp_dir) / "test_script.py"
            script_path.write_text(
                """
import sys
print("success")
sys.exit(0)
"""
            )

            config = PipelineConfig(project_name="test", repo_root=Path(tmp_dir))
            executor = PipelineExecutor(config)

            result = executor._run_script(str(script_path), "--arg", "value")

            assert result is True

    def test_run_script_failure(self):
        """Test failed script execution."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a script that fails
            script_path = Path(tmp_dir) / "failing_script.py"
            script_path.write_text(
                """
import sys
print("error", file=sys.stderr)
sys.exit(1)
"""
            )

            config = PipelineConfig(project_name="test", repo_root=Path(tmp_dir))
            executor = PipelineExecutor(config)

            result = executor._run_script(str(script_path))

            assert result is False

    def test_execute_stage_success(self):
        """Test successful stage execution."""
        config = PipelineConfig(project_name="test", repo_root=Path("/tmp"))
        executor = PipelineExecutor(config)

        def stage():
            return True

        result = executor._execute_stage(1, "Test Stage", stage)

        assert isinstance(result, PipelineStageResult)
        assert result.stage_num == 1
        assert result.stage_name == "Test Stage"
        assert result.success is True
        assert result.duration >= 0
        assert result.exit_code == 0
        assert result.error_message == ""

    def test_execute_stage_failure(self):
        """Test failed stage execution."""
        config = PipelineConfig(project_name="test", repo_root=Path("/tmp"))
        executor = PipelineExecutor(config)

        def stage():
            raise Exception("Test error")

        result = executor._execute_stage(2, "Failing Stage", stage)

        assert isinstance(result, PipelineStageResult)
        assert result.stage_num == 2
        assert result.stage_name == "Failing Stage"
        assert result.success is False
        assert result.duration >= 0
        assert result.exit_code == 1
        assert "Test error" in result.error_message

    def test_execute_full_pipeline_success(self, tmp_path: Path):
        """Test successful full pipeline execution."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=True)
        executor = self._make_executor(
            repo_root,
            "test",
            clean=False,
            skip_infra=False,
            skip_llm=False,
            resume=False,
        )

        results = executor.execute_full_pipeline()

        assert (
            len(results) == 9
        )  # setup, infra, project, analysis, pdf, validate, llm review, llm translations, copy
        assert all(r.success for r in results)
        assert all(r.stage_num == i + 1 for i, r in enumerate(results))

        # Verify stage names
        expected_names = [
            "Environment Setup",
            "Infrastructure Tests",
            "Project Tests",
            "Project Analysis",
            "PDF Rendering",
            "Output Validation",
            "LLM Scientific Review",
            "LLM Translations",
            "Copy Outputs",
        ]
        assert [r.stage_name for r in results] == expected_names

        invocations = self._read_invocations(repo_root)
        invoked_scripts = {i["script"] for i in invocations}
        assert "00_setup_environment.py" in invoked_scripts
        assert "01_run_tests.py" in invoked_scripts
        assert "02_run_analysis.py" in invoked_scripts
        assert "03_render_pdf.py" in invoked_scripts
        assert "04_validate_output.py" in invoked_scripts
        assert "06_llm_review.py" in invoked_scripts
        assert "05_copy_outputs.py" in invoked_scripts

    def test_execute_core_pipeline_success(self, tmp_path: Path):
        """Test successful core pipeline execution."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(
            repo_root,
            "test",
            clean=False,
            skip_infra=False,
            skip_llm=True,
            resume=False,
        )

        results = executor.execute_core_pipeline()

        assert len(results) == 7  # setup, infra, project, analysis, pdf, validate, copy
        assert all(r.success for r in results)

        # Verify stage names (no LLM stages)
        expected_names = [
            "Environment Setup",
            "Infrastructure Tests",
            "Project Tests",
            "Project Analysis",
            "PDF Rendering",
            "Output Validation",
            "Copy Outputs",
        ]
        assert [r.stage_name for r in results] == expected_names

    def test_skip_infra_execution(self, tmp_path: Path):
        """Test that infrastructure tests are skipped when configured."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(
            repo_root, "test", clean=False, skip_infra=True, skip_llm=True, resume=False
        )

        results = executor.execute_core_pipeline()
        assert all(r.success for r in results)

        invocations = self._read_invocations(repo_root)
        infra_calls = [
            i
            for i in invocations
            if i["script"] == "01_run_tests.py" and "--infra-only" in i["args"]
        ]
        assert infra_calls == []

    def test_skip_llm_execution(self, tmp_path: Path):
        """Test that LLM stages are skipped when configured."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(
            repo_root,
            "test",
            clean=False,
            skip_infra=False,
            skip_llm=True,
            resume=False,
        )

        results = executor.execute_full_pipeline()
        assert all(r.success for r in results)

        invocations = self._read_invocations(repo_root)
        llm_calls = [i for i in invocations if i["script"] == "06_llm_review.py"]
        assert llm_calls == []

    def test_resume_pipeline_missing_checkpoint_runs_fresh(self, tmp_path: Path):
        """If no valid checkpoint exists, resume falls back to a fresh run."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(
            repo_root, "test", clean=False, skip_infra=True, skip_llm=True, resume=True
        )

        results = executor._resume_pipeline()
        assert len(results) > 0
        assert all(isinstance(r, PipelineStageResult) for r in results)

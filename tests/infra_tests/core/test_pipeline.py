"""Tests for pipeline execution system."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


from infrastructure.core.runtime.checkpoint import CheckpointManager
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor, PipelineStageResult

_CANONICAL_PIPELINE_DECLARATION = Path(__file__).resolve().parents[3] / "infrastructure/core/pipeline/pipeline.yaml"
# Whole-pipeline fixtures run up to eight cold, source-verified children and a
# separate report worker. Keep their composition bounded without cutting off
# successful reporting; single-child and first-failure controls retain 60 seconds.
_PIPELINE_TEST_TIMEOUT_SECONDS = 120


class TestPipelineConfig:
    """Test PipelineConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PipelineConfig(project_name="test_project", repo_root=Path("/tmp"))

        assert config.project_name == "test_project"
        assert config.repo_root == Path("/tmp")
        assert config.skip_infra is False
        assert config.mode == "core"
        assert config.resume is False
        assert config.total_stages == 10

    def test_custom_values(self):
        """Test custom configuration values."""
        config = PipelineConfig(
            project_name="myproject",
            repo_root=Path("/repo"),
            skip_infra=True,
            resume=True,
            total_stages=7,
        )

        assert config.project_name == "myproject"
        assert config.repo_root == Path("/repo")
        assert config.skip_infra is True
        assert config.mode == "core"
        assert config.resume is True
        assert config.total_stages == 7


class TestPipelineStageResult:
    """Test PipelineStageResult dataclass."""

    def test_success_result(self):
        """Test successful stage result."""
        result = PipelineStageResult(stage_num=1, stage_name="Test Stage", success=True, duration=5.2)

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

    def _create_fake_repo(self, repo_root: Path, project_name: str, include_llm: bool) -> Path:
        """Create a minimal repo layout with scripts that always succeed.

        The pipeline executor runs canonical scripts from `{repo_root}/scripts/pipeline/*.py`.
        For tests we create
        minimal implementations that:
        - record their invocation to `{repo_root}/invocations.jsonl`
        - exit 0
        """
        scripts_dir = repo_root / "scripts" / "pipeline"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Minimal project structure so PYTHONPATH augmentation is stable
        (repo_root / "projects" / project_name / "src").mkdir(parents=True, exist_ok=True)
        (repo_root / "projects" / project_name / "output").mkdir(parents=True, exist_ok=True)

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
            "stage_00_setup.py",
            "stage_01_test.py",
            "stage_02_analysis.py",
            "stage_03_render.py",
            "stage_04_validate.py",
            "stage_05_copy.py",
        ]
        if include_llm:
            scripts.append("stage_06_llm_review.py")

        for name in scripts:
            (scripts_dir / name).write_text(common_script, encoding="utf-8")

        # Explicit child-only stage contracts admit the fixture's actual
        # inputs, without inheriting the publication pipeline's prerequisites.
        # The test-stage argv is taken from the canonical declaration so the
        # fixture exercises the scope the real pipeline forwards (for example
        # Stage 2's bounded ``--infra-scope pipeline-smoke`` lane).
        import yaml

        canonical = yaml.safe_load(_CANONICAL_PIPELINE_DECLARATION.read_text(encoding="utf-8"))
        canonical_args = {stage["key"]: list(stage.get("args") or []) for stage in canonical["stages"]}

        stages = []
        for label, key, script, args, tags in (
            ("Environment Setup", "setup", "stage_00_setup.py", [], ["core"]),
            ("Infrastructure Tests", "infra_tests", "stage_01_test.py", canonical_args["infra_tests"], ["core"]),
            ("Project Tests", "project_tests", "stage_01_test.py", canonical_args["project_tests"], ["core"]),
            ("Project Analysis", "analysis", "stage_02_analysis.py", [], ["core"]),
            ("PDF Rendering", "render_pdf", "stage_03_render.py", [], ["core"]),
            ("Output Validation", "validate", "stage_04_validate.py", [], ["core"]),
            ("Copy Outputs", "copy", "stage_05_copy.py", [], ["core"]),
            ("LLM Manuscript Review", "llm_reviews", "stage_06_llm_review.py", [], ["llm", "live"]),
        ):
            stages.append(
                {
                    "name": label,
                    "key": key,
                    "script": "scripts/pipeline/" + script,
                    "args": args,
                    "tags": tags,
                    "contract": {
                        "definition_of_done": "The actual child records its invocation and exits zero.",
                        "failure_code": "FIXTURE_CHILD_FAILED",
                    },
                }
            )
        declaration = repo_root / "infrastructure/core/pipeline/pipeline.yaml"
        declaration.parent.mkdir(parents=True, exist_ok=True)
        declaration.write_text(yaml.safe_dump({"stages": stages, "telemetry": {"enabled": False}}))
        return repo_root

    def _make_executor(
        self,
        repo_root: Path,
        project_name: str,
        *,
        clean: bool,
        skip_infra: bool,
        resume: bool,
        mode: str = "core",
    ) -> PipelineExecutor:
        """Create executor wired to a test-local checkpoint directory (no repo side effects)."""
        config = PipelineConfig(
            project_name=project_name,
            repo_root=repo_root,
            clean=clean,
            skip_infra=skip_infra,
            resume=resume,
            mode=mode,
        )
        executor = PipelineExecutor(config)

        # Ensure checkpoints are written under the temp repo, not the real repository root.
        checkpoint_dir = repo_root / "projects" / project_name / "output" / ".checkpoints"
        executor.checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir, project_name=project_name)

        return executor

    def _read_invocations(self, repo_root: Path) -> list[dict]:
        inv_path = repo_root / "invocations.jsonl"
        if not inv_path.exists():
            return []
        lines = inv_path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def test_initialization(self, tmp_path: Path):
        """Test executor initialization.

        The executor fingerprints its source boundary on construction and
        refuses symlinked ancestors by design, so fixtures use pytest's
        canonical ``tmp_path`` rather than platform aliases such as macOS's
        ``/tmp`` -> ``/private/tmp``.
        """
        config = PipelineConfig(project_name="test", repo_root=tmp_path)
        executor = PipelineExecutor(config)

        assert executor.config == config

    @pytest.mark.timeout(60)
    def test_run_script_success(self, tmp_path: Path):
        """Test successful script execution."""
        script_path = tmp_path / "scripts/test_script.py"
        script_path.parent.mkdir()
        script_path.write_text(
            """
import sys
print("success")
sys.exit(0)
"""
        )

        config = PipelineConfig(project_name="test", repo_root=tmp_path)
        executor = PipelineExecutor(config)

        result = executor._run_script("scripts/test_script.py", "--arg", "value")

        assert result.complete is True

    @pytest.mark.timeout(60)
    def test_run_script_failure(self, tmp_path: Path):
        """Test failed script execution."""
        script_path = tmp_path / "scripts/failing_script.py"
        script_path.parent.mkdir()
        script_path.write_text(
            """
import sys
print("error", file=sys.stderr)
sys.exit(1)
"""
        )

        config = PipelineConfig(project_name="test", repo_root=tmp_path)
        executor = PipelineExecutor(config)

        result = executor._run_script("scripts/failing_script.py")

        assert result.complete is False
        assert result.child_exit_code == 1

    def test_execute_stage_success(self, tmp_path: Path):
        """Test successful stage execution."""
        config = PipelineConfig(project_name="test", repo_root=tmp_path)
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

    def test_execute_stage_failure(self, tmp_path: Path):
        """Test failed stage execution."""
        config = PipelineConfig(project_name="test", repo_root=tmp_path)
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

    def test_execute_stage_failure_captures_exception_type(self, tmp_path: Path):
        """Exception type is recorded correctly for OSError and generic Exception."""
        config = PipelineConfig(project_name="test", repo_root=tmp_path)
        executor = PipelineExecutor(config)

        def os_error_stage():
            raise OSError("disk full")

        result = executor._execute_stage(3, "OS Error Stage", os_error_stage)
        assert result.success is False
        assert "disk full" in result.error_message

        def value_error_stage():
            raise ValueError("bad value")

        result2 = executor._execute_stage(4, "Value Error Stage", value_error_stage)
        assert result2.success is False
        assert "bad value" in result2.error_message

    @pytest.mark.timeout(_PIPELINE_TEST_TIMEOUT_SECONDS)
    def test_execute_full_pipeline_success(self, tmp_path: Path):
        """Test successful full pipeline execution."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=True)
        executor = self._make_executor(
            repo_root,
            "test",
            clean=False,
            skip_infra=False,
            resume=False,
            mode="live",
        )

        results = executor.execute_pipeline()

        assert all(r.success for r in results)

        # Check required stages are present (set membership, not order)
        stage_names = {r.stage_name for r in results}
        required_stages = {
            "Environment Setup",
            "Infrastructure Tests",
            "Project Tests",
            "Project Analysis",
            "PDF Rendering",
            "Output Validation",
            "Copy Outputs",
        }
        assert required_stages.issubset(stage_names)

        invocations = self._read_invocations(repo_root)
        invoked_scripts = {i["script"] for i in invocations}
        assert "stage_00_setup.py" in invoked_scripts
        assert "stage_01_test.py" in invoked_scripts
        assert "stage_02_analysis.py" in invoked_scripts
        assert "stage_03_render.py" in invoked_scripts
        assert "stage_04_validate.py" in invoked_scripts
        assert "stage_06_llm_review.py" in invoked_scripts
        assert "stage_05_copy.py" in invoked_scripts
        infra_invocations = [
            i for i in invocations if i["script"] == "stage_01_test.py" and "--infra-only" in i["args"]
        ]
        assert infra_invocations
        assert "--infra-scope" in infra_invocations[0]["args"]
        assert "pipeline-smoke" in infra_invocations[0]["args"]

    @pytest.mark.timeout(_PIPELINE_TEST_TIMEOUT_SECONDS)
    def test_execute_core_pipeline_success(self, tmp_path: Path):
        """Test successful core pipeline execution."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(
            repo_root,
            "test",
            clean=False,
            skip_infra=False,
            resume=False,
        )

        results = executor.execute_pipeline()

        assert all(r.success for r in results)

        # Check required core stages are present; no LLM stages
        stage_names = {r.stage_name for r in results}
        required_core_stages = {
            "Environment Setup",
            "Infrastructure Tests",
            "Project Tests",
            "Project Analysis",
            "PDF Rendering",
            "Output Validation",
            "Copy Outputs",
        }
        assert required_core_stages.issubset(stage_names)
        assert "LLM Manuscript Review" not in stage_names
        assert "LLM Translations" not in stage_names

    @pytest.mark.timeout(_PIPELINE_TEST_TIMEOUT_SECONDS)
    def test_skip_infra_execution(self, tmp_path: Path):
        """Test that infrastructure tests are skipped when configured."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(repo_root, "test", clean=False, skip_infra=True, resume=False)

        results = executor.execute_pipeline()
        assert all(r.success for r in results)

        invocations = self._read_invocations(repo_root)
        infra_calls = [i for i in invocations if i["script"] == "stage_01_test.py" and "--infra-only" in i["args"]]
        assert infra_calls == []

    @pytest.mark.timeout(_PIPELINE_TEST_TIMEOUT_SECONDS)
    def test_skip_llm_execution(self, tmp_path: Path):
        """Test that LLM stages are skipped when configured."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(
            repo_root,
            "test",
            clean=False,
            skip_infra=False,
            resume=False,
        )

        results = executor.execute_pipeline()
        assert all(r.success for r in results)

        invocations = self._read_invocations(repo_root)
        llm_calls = [i for i in invocations if i["script"] == "stage_06_llm_review.py"]
        assert llm_calls == []

    @pytest.mark.timeout(_PIPELINE_TEST_TIMEOUT_SECONDS)
    def test_resume_pipeline_missing_checkpoint_runs_fresh(self, tmp_path: Path):
        """If no valid checkpoint exists, resume falls back to a fresh run."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(repo_root, "test", clean=False, skip_infra=True, resume=True)

        results = executor._resume_pipeline()
        assert len(results) > 0
        assert all(isinstance(r, PipelineStageResult) for r in results)

    @pytest.mark.timeout(60)
    def test_execute_core_pipeline_aborts_on_first_failure(self, tmp_path: Path):
        """Pipeline stops after the first failing stage; subsequent scripts are never invoked."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=True)
        scripts_dir = repo_root / "scripts" / "pipeline"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (repo_root / "projects" / "test" / "src").mkdir(parents=True, exist_ok=True)
        (repo_root / "projects" / "test" / "output").mkdir(parents=True, exist_ok=True)

        # First script records its invocation then exits 1 (failure).
        failing_script = """
import json, os, sys
log_path = os.path.join(os.getcwd(), "invocations.jsonl")
with open(log_path, "a", encoding="utf-8") as f:
    json.dump({"script": os.path.basename(__file__)}, f)
    f.write("\\n")
sys.exit(1)
"""
        # Second script records its invocation then exits 0 (success).
        success_script = """
import json, os, sys
log_path = os.path.join(os.getcwd(), "invocations.jsonl")
with open(log_path, "a", encoding="utf-8") as f:
    json.dump({"script": os.path.basename(__file__)}, f)
    f.write("\\n")
sys.exit(0)
"""

        (scripts_dir / "stage_00_setup.py").write_text(failing_script, encoding="utf-8")
        (scripts_dir / "stage_01_test.py").write_text(success_script, encoding="utf-8")
        (scripts_dir / "stage_02_analysis.py").write_text(success_script, encoding="utf-8")
        (scripts_dir / "stage_03_render.py").write_text(success_script, encoding="utf-8")
        (scripts_dir / "stage_04_validate.py").write_text(success_script, encoding="utf-8")
        (scripts_dir / "stage_05_copy.py").write_text(success_script, encoding="utf-8")

        executor = self._make_executor(repo_root, "test", clean=False, skip_infra=True, resume=False)

        results = executor.execute_pipeline()

        # Only the failing stage result should be present.
        assert len(results) == 1
        assert results[0].success is False

        # No subsequent scripts should have been invoked.
        invocations = self._read_invocations(repo_root)
        invoked = {i["script"] for i in invocations}
        assert "stage_01_test.py" not in invoked
        assert "stage_02_analysis.py" not in invoked

    @pytest.mark.timeout(_PIPELINE_TEST_TIMEOUT_SECONDS)
    def test_llm_stage_exit_code_2_without_receipt_fails(self, tmp_path: Path):
        """An arbitrary child exit 2 cannot authorize a skip."""
        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=True)
        scripts_dir = repo_root / "scripts" / "pipeline"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (repo_root / "projects" / "test" / "src").mkdir(parents=True, exist_ok=True)
        (repo_root / "projects" / "test" / "output").mkdir(parents=True, exist_ok=True)

        skip_script = "import sys; sys.exit(2)\n"  # simulates Ollama unavailable
        success_script = "import sys; sys.exit(0)\n"

        for name in [
            "stage_00_setup.py",
            "stage_01_test.py",
            "stage_02_analysis.py",
            "stage_03_render.py",
            "stage_04_validate.py",
            "stage_05_copy.py",
        ]:
            (scripts_dir / name).write_text(success_script, encoding="utf-8")
        (scripts_dir / "stage_06_llm_review.py").write_text(skip_script, encoding="utf-8")

        executor = self._make_executor(repo_root, "test", clean=False, skip_infra=True, resume=False)
        executor.config.mode = "live"
        results = executor.execute_pipeline()

        assert results[-1].exit_code == 2
        assert executor.run_result(results).exit_code == 1

    @pytest.mark.timeout(_PIPELINE_TEST_TIMEOUT_SECONDS)
    def test_resume_pipeline_valid_checkpoint_skips_completed_stages(self, tmp_path: Path):
        """Resume with a valid checkpoint skips completed stages and runs remaining ones."""
        from infrastructure.core.runtime.checkpoint import StageResult

        repo_root = self._create_fake_repo(tmp_path / "repo", "test", include_llm=False)
        executor = self._make_executor(repo_root, "test", clean=False, skip_infra=True, resume=True)

        # Pre-populate checkpoint as if the first stage already completed
        executor.checkpoint_manager.save_checkpoint(
            pipeline_start_time=0.0,
            last_stage_completed=1,
            stage_results=[StageResult(name="Environment Setup", exit_code=0, duration=0.1, completed=True)],
            total_stages=executor.config.total_stages,
        )

        results = executor.execute_pipeline()

        # Results should include at least the resumed stages (checkpoint stage + new stages)
        assert len(results) > 0
        assert all(isinstance(r, PipelineStageResult) for r in results)


@pytest.mark.parametrize("projects_dir", ["projects/templates", "projects/working"])
def test_executor_checkpoint_uses_configured_project_directory(tmp_path: Path, projects_dir: str) -> None:
    """Alternate project collections keep logs, outputs, and checkpoints together."""
    config = PipelineConfig(project_name="demo", repo_root=tmp_path, projects_dir=projects_dir)
    executor = PipelineExecutor(config)
    assert executor.checkpoint_manager.checkpoint_dir == config.project_dir / "output/.checkpoints"
    assert executor.checkpoint_manager.save_checkpoint(1.0, 0, [], 3)
    assert (config.project_dir / "output/.checkpoints/pipeline_checkpoint.json").is_file()
    assert not (tmp_path / "projects/demo").exists()

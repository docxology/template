"""Individual pipeline stage runners.

Each method wraps a specific pipeline script invocation via subprocess.
Separated from executor.py for single-responsibility: this module handles
*what* each stage does, while executor.py handles *how* stages are orchestrated.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import os
import uuid
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.execution_boundary import validate_hook_root
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.files.cleanup import clean_output_directories
from infrastructure.core.files.secure_write import atomic_write_text_confined, unlink_confined
from infrastructure.core.runtime.environment import get_python_command, get_subprocess_env
from infrastructure.core.execution_policy import apply_execution_policy

if TYPE_CHECKING:
    from infrastructure.core.pipeline.types import PipelineConfig

from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint
from infrastructure.core.pipeline.stage_launch import launch_python_stage

logger = get_logger(__name__)
PIPELINE_STAGE_TIMEOUT_SECONDS = 7200.0


def _stage_launch_deadline(deadline: float) -> float:
    """Clamp directly to the original clock without renewing elapsed time."""
    return min(deadline, time.monotonic() + PIPELINE_STAGE_TIMEOUT_SECONDS)


def resolve_pipeline_script_path(repo_root: Path, script_name: str) -> Path:
    """Resolve explicit repository-relative scripts inside the public operating surface."""
    relative = Path(script_name)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) < 2
        or relative.parts[0] not in {"projects", "scripts"}
        or relative.suffix != ".py"
    ):
        raise ValueError("Stage scripts require an explicit repository-relative scripts/ or projects/ path")
    return validate_hook_root(repo_root / relative, hook_root=repo_root)


def build_stage_subprocess_env(repo_root: Path, project_dir: Path, *, mode: str | None = None) -> dict[str, str]:
    """Build the shared environment for full-pipeline and single-stage scripts."""
    env = get_subprocess_env()
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PROJECT_ROOT", str(repo_root))
    project_src = project_dir / "src"
    pythonpath_parts = [str(repo_root), str(repo_root / "infrastructure"), str(project_dir)]
    if project_src.exists():
        pythonpath_parts.append(str(project_src))
    existing = env.get("PYTHONPATH")
    if existing:
        pythonpath_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return apply_execution_policy(env, repo_root, mode=mode)


class PipelineStageMixin(ABC):
    """Mixin providing individual pipeline stage runner methods.

    Expects the host class to provide:
        - self.config: PipelineConfig (with repo_root, project_name, project_dir)
        - self.log_file: Path to the pipeline log file
        - self._setup_log_file_handler(): method to recreate log handler after clean
    """

    # Host-class contract: type-checker-visible declarations for duck-typed dependencies.
    # Concrete implementations are provided by PipelineExecutor via MRO.
    config: "PipelineConfig"
    log_file: Path

    @abstractmethod
    def _setup_log_file_handler(self) -> None: ...

    # -- Public stage methods ------------------------------------------------

    def run_infrastructure_tests(self) -> StageOutcome:
        """Public API used by multi-project orchestrator."""
        return self._run_script(
            "scripts/pipeline/stage_01_test.py",
            "--infra-only",
            "--verbose",
            "--infra-scope",
            "pipeline-smoke",
            "--project",
            self.config.project_name,
        )

    def run_project_tests(self) -> StageOutcome:
        """Run project test suite."""
        return self._run_script(
            "scripts/pipeline/stage_01_test.py",
            "--project-only",
            "--verbose",
            "--project",
            self.config.project_name,
        )

    # -- Built-in stage methods ----------------------------------------------

    def _run_clean_outputs(self) -> bool:
        """Clean output directories for a fresh run.

        After cleaning, recreates the log file handler since clean_output_directories
        may have deleted the log file.

        Returns:
            True if cleaning succeeded, False on error.
        """
        logger.info("Cleaning output directories...")
        try:
            clean_output_directories(self.config.repo_root, self.config.project_name)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to clean output directories: {e}")
            return False

        # Recreate log file handler after clean deleted the log directory
        self._setup_log_file_handler()
        logger.info(f"Recreated pipeline log file: {self.log_file}")
        return True

    # -- Subprocess execution ------------------------------------------------

    def _build_stage_env(self) -> dict[str, str]:
        """Return the subprocess environment for a stage script invocation.

        Extends the base uv-compatible env with project-specific PYTHONPATH entries
        so that stage scripts can import from infrastructure/ and project src/.
        """
        return build_stage_subprocess_env(self.config.repo_root, self.config.project_dir, mode=self.config.mode)

    def _run_script(self, script_name: str, *args: str, allow_skip_code: bool = False) -> StageOutcome:
        """Run a script with given arguments.

        Args:
            script_name: Explicit repository-relative scripts/ or projects/ path.
            *args: Arguments to pass to script
            allow_skip_code: Allow exit 2 only with a fresh, bound reason receipt.

        Returns:
            Typed outcome retaining the original child exit code and validated skip evidence.
        """
        script_path = resolve_pipeline_script_path(self.config.repo_root, script_name)

        cmd = get_python_command() + [str(script_path)] + list(args)
        logger.debug(f"Running: {' '.join(cmd)}")

        env = self._build_stage_env()
        stage_key = str(getattr(self, "_active_stage_key", "") or script_path.stem)
        run_id = str(getattr(self, "run_id", uuid.uuid4().hex))
        receipt_dir = self.config.runtime_output_dir / ".pipeline" / "skip_receipts" / run_id
        receipt_path = receipt_dir / f"{canonical_digest(stage_key)}.json"
        atomic_write_text_confined(self.config.repo_root, receipt_path, "", mode=0o600)
        unlink_confined(self.config.repo_root, receipt_path)
        env.update(
            {
                "PIPELINE_RUN_ID": run_id,
                "PIPELINE_STAGE_KEY": stage_key,
                "PIPELINE_COMMAND_DIGEST": canonical_digest(cmd),
                "PIPELINE_PLAN_DIGEST": str(getattr(self, "_plan_digest", "standalone")),
                "PIPELINE_SKIP_RECEIPT_PATH": str(receipt_path),
            }
        )
        deadline = float(getattr(self, "_stage_deadline", 0.0)) or time.monotonic() + PIPELINE_STAGE_TIMEOUT_SECONDS
        launch_deadline = _stage_launch_deadline(deadline)
        if launch_deadline <= time.monotonic():
            return StageOutcome(stage_key, StageStatus.TIMED_OUT, None, "Deadline expired before child launch")

        plan = getattr(self, "execution_plan", None)
        definition = self.config.repo_root / plan.provenance if plan is not None else None
        try:
            identity = (
                plan.source_identity
                if plan is not None
                else source_fingerprint(
                    self.config.repo_root,
                    self.config.project_dir,
                    definition_path=definition,
                )
            )
        except (OSError, ValueError) as exc:
            return StageOutcome(stage_key, StageStatus.BLOCKED, None, f"Stage source custody unavailable: {exc}")
        return launch_python_stage(
            repo=self.config.repo_root,
            project=self.config.project_dir,
            argv=cmd,
            env=env,
            deadline=launch_deadline,
            stage_key=stage_key,
            run_id=run_id,
            source_digest=identity,
            definition=definition,
            skip_path=receipt_path,
            allow_skip=allow_skip_code,
            stage_admission=getattr(self, "_active_stage_admission", None),
        )

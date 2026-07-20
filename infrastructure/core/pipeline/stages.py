"""Individual pipeline stage runners.

Each method wraps a specific pipeline script invocation via subprocess.
Separated from executor.py for single-responsibility: this module handles
*what* each stage does, while executor.py handles *how* stages are orchestrated.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.runtime.environment import get_python_command, get_subprocess_env
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.errors import SCRIPT_EXECUTION_FAILED
from infrastructure.core.files.cleanup import clean_output_directories

if TYPE_CHECKING:
    from infrastructure.core.pipeline.config import PipelineConfig

logger = get_logger(__name__)


def resolve_pipeline_script_path(repo_root: Path, script_name: str) -> Path:
    """Resolve canonical/project script paths and legacy bare filenames."""
    relative = Path(script_name)
    if relative.is_absolute():
        return relative
    if relative.parts and relative.parts[0] in {"projects", "scripts"}:
        return repo_root / relative
    return repo_root / "scripts" / relative


def build_stage_subprocess_env(repo_root: Path, project_dir: Path) -> dict[str, str]:
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
    return env


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

    def run_infrastructure_tests(self) -> bool:
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

    def run_project_tests(self) -> bool:
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
        return build_stage_subprocess_env(self.config.repo_root, self.config.project_dir)

    def _run_script(self, script_name: str, *args: str, allow_skip_code: bool = False) -> bool:
        """Run a script with given arguments.

        Args:
            script_name: Repository-relative script path. Bare filenames remain
                supported for project-specific legacy pipeline overrides.
            *args: Arguments to pass to script
            allow_skip_code: If True, treat exit code 2 as success (graceful skip)

        Returns:
            True if script succeeded (or skipped gracefully if allow_skip_code=True), False otherwise
        """
        script_path = resolve_pipeline_script_path(self.config.repo_root, script_name)

        cmd = get_python_command() + [str(script_path)] + list(args)
        logger.debug(f"Running: {' '.join(cmd)}")

        env = self._build_stage_env()

        try:
            # Stream subprocess output to console for long-running stages; still capture exit code.
            result = subprocess.run(  # nosec B603
                cmd, cwd=self.config.repo_root, env=env, check=False, timeout=7200
            )

            if result.returncode == 0:
                return True

            # Exit code 2 = graceful skip (e.g., Ollama not available)
            if allow_skip_code and result.returncode == 2:
                logger.info(f"Stage skipped gracefully (exit code 2): {script_name}")
                return True

            return False
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            logger.error(SCRIPT_EXECUTION_FAILED.format(script_name=script_name, error=e))
            return False

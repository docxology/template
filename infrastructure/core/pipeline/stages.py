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
from infrastructure.core.logging.utils import flush_file_handlers, get_logger
from infrastructure.core.errors import SCRIPT_EXECUTION_FAILED
from infrastructure.core.files.cleanup import clean_output_directories

if TYPE_CHECKING:
    from infrastructure.core.pipeline.config import PipelineConfig

logger = get_logger(__name__)


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
            "01_run_tests.py", "--infra-only", "--verbose", "--project", self.config.project_name
        )

    def run_project_tests(self) -> bool:
        """Run project test suite."""
        return self._run_script(
            "01_run_tests.py", "--project-only", "--verbose", "--project", self.config.project_name
        )

    # -- Internal stage methods ----------------------------------------------

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

    def _run_setup_environment(self) -> bool:
        return self._run_script("00_setup_environment.py", "--project", self.config.project_name)

    def _run_analysis(self) -> bool:
        return self._run_script("02_run_analysis.py", "--project", self.config.project_name)

    def _run_pdf_rendering(self) -> bool:
        return self._run_script("03_render_pdf.py", "--project", self.config.project_name)

    def _run_validation(self) -> bool:
        return self._run_script("04_validate_output.py", "--project", self.config.project_name)

    def _run_llm_review(self) -> bool:
        """Run LLM scientific review.

        Uses allow_skip_code=True to treat exit code 2 (Ollama not available) as success.
        """
        return self._run_script(
            "06_llm_review.py",
            "--reviews-only",
            "--project",
            self.config.project_name,
            allow_skip_code=True,
        )

    def _run_llm_translations(self) -> bool:
        """Run LLM translations.

        Uses allow_skip_code=True to treat exit code 2 (no languages configured or Ollama unavailable) as success.
        """
        return self._run_script(
            "06_llm_review.py",
            "--translations-only",
            "--project",
            self.config.project_name,
            allow_skip_code=True,
        )

    def _run_copy_outputs(self) -> bool:
        """Run output copying."""
        logger.info("Running output copying...")

        # Flush log handlers before copying to ensure log file is written
        flush_file_handlers()
        if not self._verify_log_file():
            logger.warning("Log file not verified before copy - may be missing or empty")

        return self._run_script("05_copy_outputs.py", "--project", self.config.project_name)

    def _verify_log_file(self) -> bool:
        """Check that the log file exists and has content.

        Returns:
            True if log file exists and has content, False otherwise
        """
        if self.log_file.exists():
            try:
                size = self.log_file.stat().st_size
                if size > 0:
                    logger.debug(f"Log file verified: {self.log_file} ({size:,} bytes)")
                    return True
                else:
                    logger.warning(f"Log file exists but is empty: {self.log_file}")
                    return False
            except OSError as e:
                logger.warning(f"Failed to verify log file: {e}")
                return False
        else:
            logger.warning(f"Log file not found: {self.log_file}")
            return False

    # -- Subprocess execution ------------------------------------------------

    def _build_stage_env(self) -> dict[str, str]:
        """Return the subprocess environment for a stage script invocation.

        Extends the base uv-compatible env with project-specific PYTHONPATH entries
        so that stage scripts can import from infrastructure/ and project src/.
        """
        env = get_subprocess_env()
        env.setdefault("MPLBACKEND", "Agg")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PROJECT_ROOT", str(self.config.repo_root))

        project_src = self.config.project_dir / "src"
        pythonpath_parts = [
            str(self.config.repo_root),
            str(self.config.repo_root / "infrastructure"),
        ]
        if project_src.exists():
            pythonpath_parts.append(str(project_src))
        existing = env.get("PYTHONPATH")
        if existing:
            pythonpath_parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
        return env

    def _run_script(self, script_name: str, *args: str, allow_skip_code: bool = False) -> bool:
        """Run a script with given arguments.

        Args:
            script_name: Name of script in scripts/ directory
            *args: Arguments to pass to script
            allow_skip_code: If True, treat exit code 2 as success (graceful skip)

        Returns:
            True if script succeeded (or skipped gracefully if allow_skip_code=True), False otherwise
        """
        script_path = self.config.repo_root / "scripts" / script_name

        cmd = get_python_command() + [str(script_path)] + list(args)
        logger.debug(f"Running: {' '.join(cmd)}")

        env = self._build_stage_env()

        try:
            # Stream subprocess output to console for long-running stages; still capture exit code.
            result = subprocess.run(  # nosec B603 — cmd is [python, known_script_path, validated_args]
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

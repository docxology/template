#!/usr/bin/env python3
"""Analysis and figure generation orchestrator script.

This thin orchestrator coordinates the analysis and figure generation stage:
1. Discovers all analysis scripts in project/scripts/
2. Executes them in order
3. Collects generated outputs from project/output/
4. Validates output quality

**Entry Point 2:** Generic orchestrator for template
- Works with any project by looking in project/scripts/
- Does NOT implement analysis logic
- Delegates to project-specific scripts

Stage 3 of the pipeline orchestration.

Architecture:
    This is a generic entry point (Layer 1 - Infrastructure).
    It discovers and executes project-specific scripts from project/scripts/
    without knowing their implementation details. Follows thin orchestrator pattern.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger,
    log_header,
    log_operation,
    log_success,
    format_error_with_suggestions,
)
from infrastructure.core.progress import SubStageProgress
from infrastructure.core.exceptions import ScriptExecutionError, PipelineError
from infrastructure.core.environment import get_python_command, get_subprocess_env
from infrastructure.core.script_discovery import (
    discover_analysis_scripts,
    verify_analysis_outputs,
)

# Set up logger for this module
logger = get_logger(__name__)


def run_analysis_script(script_path: Path, repo_root: Path, project_name: str = "project") -> int:
    """Execute a single analysis script.

    Args:
        script_path: Path to the script to execute
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        Exit code from script execution

    Raises:
        ScriptExecutionError: If script execution fails critically
    """
    logger.info(f"\n  Running: {project_name}/{script_path.name}")

    project_root = repo_root / "projects" / project_name

    # Detect project-local venv: if the project has its own .venv with optional
    # dependencies (e.g., discopy for cognitive_case_diagrams), use uv run
    # from the project directory so those dependencies are available.
    project_venv = project_root / ".venv"
    if project_venv.is_dir():
        import shutil

        uv_path = shutil.which("uv")
        if uv_path:
            cmd = [uv_path, "run", "--directory", str(project_root), "python", str(script_path)]
            logger.info(f"  Using project-local venv: {project_venv}")
        else:
            cmd = get_python_command() + [str(script_path)]
            logger.warning("  Project has local .venv but 'uv' not found; using root Python")
    else:
        cmd = get_python_command() + [str(script_path)]

    # Get clean environment dict with uv compatibility (handles VIRTUAL_ENV warnings)
    env = get_subprocess_env()
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

    # Set up Python path to include infrastructure and project modules
    pythonpath = os.pathsep.join(
        [
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(project_root / "src"),
        ]
    )
    env["PYTHONPATH"] = pythonpath

    # Set PROJECT_ROOT env var for scripts that need to find resources relative to project
    env["PROJECT_DIR"] = str(project_root)

    # Remove VIRTUAL_ENV to prevent uv from getting confused when switching venvs
    env.pop("VIRTUAL_ENV", None)

    try:
        with log_operation(f"Execute {script_path.name}", logger):
            # When using project-local venv, run from repo_root but let uv
            # handle the venv via --directory. Otherwise run from repo_root
            # as before.
            result = subprocess.run(
                cmd, cwd=str(repo_root), capture_output=False, check=False, env=env
            )

        if result.returncode != 0:
            logger.error(f"Script failed: {script_path.name} (exit code: {result.returncode})")
            logger.info("  Troubleshooting:")
            logger.info(f"    - Run script manually: python3 {script_path}")
            logger.info(f"    - Check script syntax: python3 -m py_compile {script_path}")
            logger.info(f"    - Verify dependencies: Check imports in {script_path.name}")
            logger.info("    - Review script logs above for specific error details")

        return result.returncode
    except Exception as e:
        raise ScriptExecutionError(
            f"Failed to execute {script_path.name}",
            context={"script": str(script_path), "error": str(e)},
        ) from e


def run_analysis_pipeline(scripts: list[Path], project_name: str = "project") -> int:
    """Execute all analysis scripts in sequence.

    Args:
        scripts: List of script paths to execute
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        Exit code (0=success, non-zero=at least one script failed)
    """
    logger.info("[STAGE-02] Executing analysis pipeline...")

    repo_root = Path(__file__).parent.parent

    if not scripts:
        logger.info("  No analysis scripts found - skipping stage")
        return 0

    successful_scripts = []
    failed_scripts = []

    # Use sub-stage progress tracking with EMA for better ETA
    progress = SubStageProgress(total=len(scripts), stage_name="Analysis Pipeline", use_ema=True)

    for i, script in enumerate(scripts, 1):
        progress.start_substage(i, f"{project_name}/{script.name}")
        exit_code = run_analysis_script(script, repo_root, project_name)
        progress.complete_substage()

        # Log progress with ETA every few scripts
        if i % 2 == 0 or i == len(scripts):
            progress.log_progress()

        if exit_code == 0:
            successful_scripts.append(script.name)
        else:
            failed_scripts.append(script.name)

    # Consolidated success message
    if successful_scripts:
        script_list_with_project = ", ".join(
            [f"{project_name}/{name}" for name in successful_scripts]
        )
        log_success(
            f"Analysis scripts completed: {len(successful_scripts)}/{len(scripts)} ({script_list_with_project})",  # noqa: E501
            logger,
        )

    if failed_scripts:
        logger.error(f"\n{len(failed_scripts)} script(s) failed:")
        for script_name in failed_scripts:
            logger.error(f"  Failed: {script_name}")
        logger.info("\n  Troubleshooting:")
        logger.info("    - Review error messages above for each failed script")
        logger.info("    - Run scripts individually to isolate issues")
        logger.info("    - Check script dependencies and imports")
        logger.info("    - Verify input data files exist if required")
        return 1

    return 0


def main() -> int:
    """Execute analysis orchestration.

    Returns:
        Exit code (0=success, 1=failure)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run analysis pipeline")
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    args = parser.parse_args()

    log_header(f"STAGE 02: Run Analysis (Project: {args.project})", logger)

    # Log resource usage at start
    from infrastructure.core.logging_utils import log_resource_usage

    log_resource_usage("Analysis stage start", logger)

    try:
        repo_root = Path(__file__).parent.parent

        # Discover scripts for the specified project
        scripts = discover_analysis_scripts(repo_root, args.project)

        if not scripts:
            logger.info("  No analysis scripts found - skipping stage")
            return 0

        # Run analysis pipeline
        exit_code = run_analysis_pipeline(scripts, args.project)

        if exit_code == 0:
            # Verify outputs
            outputs_valid = verify_analysis_outputs(repo_root, args.project)

            if outputs_valid:
                log_success("Analysis complete - ready for PDF rendering", logger)
            else:
                logger.warning("\nAnalysis complete but output verification failed")
        else:
            logger.error("\nAnalysis failed - fix issues and try again")

        # Log resource usage at end
        log_resource_usage("Analysis stage end", logger)

        return exit_code

    except (ScriptExecutionError, PipelineError) as e:
        logger.error(format_error_with_suggestions(e))
        log_resource_usage("Analysis stage end (error)", logger)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        log_resource_usage("Analysis stage end (error)", logger)
        return 1


if __name__ == "__main__":
    exit(main())

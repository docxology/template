"""Script discovery and execution utilities.

This module provides functions for discovering scripts in the project
and verifying their outputs.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.exceptions import PipelineError
from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def discover_analysis_scripts(repo_root: Path, project_name: str = "project") -> list[Path]:
    """Discover all analysis scripts in projects/{project_name}/scripts/ to execute.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        List of Python script paths from projects/{project_name}/scripts/ directory

    Raises:
        PipelineError: If project scripts directory not found

    Example:
        >>> scripts = discover_analysis_scripts(Path("."), "project")
        >>> all(s.suffix == '.py' for s in scripts)
        True
        >>> scripts = discover_analysis_scripts(Path("."), "myresearch")
        >>> # Discovers scripts in projects/myresearch/scripts/
    """
    logger.info(f"[STAGE-02] Discovering analysis scripts in projects/{project_name}/...")

    project_scripts_dir = repo_root / "projects" / project_name / "scripts"

    if not project_scripts_dir.exists():
        logger.info(
            f"[STAGE-02] No scripts directory found for '{project_name}' - analysis stage will be skipped"  # noqa: E501
        )
        return []

    # Find all Python scripts in projects/{project_name}/scripts/ except README files
    scripts = sorted(
        [f for f in project_scripts_dir.glob("*.py") if f.is_file() and not f.name.startswith("_")]
    )

    for script in scripts:
        log_success(f"Found: {script.name} (project: {project_name})", logger)

    return scripts


def discover_orchestrators(repo_root: Path) -> list[Path]:
    """Discover orchestrator scripts in scripts/ directory.

    Args:
        repo_root: Repository root directory

    Returns:
        List of available orchestrator script paths in execution order

    Raises:
        PipelineError: If scripts directory not found
    """
    scripts_dir = repo_root / "scripts"

    if not scripts_dir.exists():
        raise PipelineError(
            "Scripts directory not found", context={"expected_path": str(scripts_dir)}
        )

    orchestrators = [
        scripts_dir / "00_setup_environment.py",
        scripts_dir / "01_run_tests.py",
        scripts_dir / "02_run_analysis.py",
        scripts_dir / "03_render_pdf.py",
        scripts_dir / "04_validate_output.py",
        scripts_dir / "05_copy_outputs.py",
    ]

    available = [s for s in orchestrators if s.exists()]

    if len(available) < len(orchestrators):
        missing = [s.name for s in orchestrators if s not in available]
        logger.warning(f"Some orchestrators not found: {', '.join(missing)}")

    return available


def verify_analysis_outputs(repo_root: Path, project_name: str = "project") -> bool:
    """Verify that analysis generated expected outputs.

    Checks whether analysis scripts are present for this project and, if so,
    whether they produced output files in the expected directories.  Returns
    False only when scripts exist (output is expected) but all output
    directories are empty or absent.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        True if outputs are present or no scripts were expected to run,
        False if scripts exist but no output was generated.
    """
    logger.info(f"[STAGE-02] Verifying analysis outputs for projects/{project_name}/...")

    # Determine whether analysis scripts exist (so we know whether output is expected)
    scripts_dir = repo_root / "projects" / project_name / "scripts"
    scripts_exist = scripts_dir.exists() and any(
        f for f in scripts_dir.glob("*.py") if not f.name.startswith("_")
    )

    output_dirs = [
        repo_root / "projects" / project_name / "output" / "figures",
        repo_root / "projects" / project_name / "output" / "data",
    ]

    has_any_output = False
    for output_dir in output_dirs:
        if output_dir.exists():
            files = list(output_dir.glob("*"))
            if files:
                has_any_output = True
                log_success(
                    f"Output directory has {len(files)} file(s): {output_dir.name}",
                    logger,
                )
            else:
                logger.info(f"  ℹ️  Output directory is empty: {output_dir.name}")
        else:
            # Output directories may not exist yet, not an error on its own
            logger.info(f"  ℹ️  Output directory not yet created: {output_dir.name}")

    if scripts_exist and not has_any_output:
        logger.warning(
            f"[STAGE-02] Analysis scripts found for '{project_name}' but no output files detected. "
            "The analysis stage may have failed or produced no figures/data."
        )
        return False

    return True

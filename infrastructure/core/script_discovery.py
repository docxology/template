"""Script discovery and execution utilities.

This module provides functions for discovering scripts in the project
and verifying their outputs.

Stage 02 executes each discovered script under a subprocess timeout configured by
``ANALYSIS_SCRIPT_TIMEOUT_SEC`` (see :mod:`infrastructure.core.analysis_timeout`).
The default is **7200** seconds (2 hours) per script; set a higher value or
``0``/``unlimited`` for no limit on very long Hermes or Lean batches.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.exceptions import PipelineError
from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


def discover_analysis_scripts(
    repo_root: Path,
    project_name: str = "project",
    project_dir: Path | None = None,
) -> list[Path]:
    """Discover all analysis scripts for a project.

    Args:
        repo_root: Repository root directory.
        project_name: Name of project directory (default: "project").
        project_dir: Absolute path to the project directory. When provided,
            ``repo_root`` and ``project_name`` are only used for log messages.
            Defaults to ``repo_root / 'projects' / project_name``.

    Returns:
        List of Python script paths from the project's scripts/ directory.

    Raises:
        PipelineError: If project scripts directory not found.

    Example:
        >>> scripts = discover_analysis_scripts(Path("."), "project")
        >>> all(s.suffix == '.py' for s in scripts)
        True
        >>> scripts = discover_analysis_scripts(Path("."), "myresearch")
        >>> # Discovers scripts in projects/myresearch/scripts/
    """
    resolved_dir = project_dir if project_dir is not None else repo_root / "projects" / project_name
    logger.info(
        f"[STAGE-02] Discovering analysis scripts in {resolved_dir.relative_to(repo_root)}/..."
    )

    project_scripts_dir = resolved_dir / "scripts"

    if not project_scripts_dir.exists():
        logger.info(
            f"[STAGE-02] No scripts directory found for '{project_name}' - analysis stage will be skipped"  # noqa: E501
        )
        return []

    # Find all Python scripts in the scripts/ directory except private modules and
    # package markers (__init__.py) so ``scripts/`` may be a proper package.
    scripts = sorted(
        f
        for f in project_scripts_dir.glob("*.py")
        if f.is_file()
        and not f.name.startswith("_")
        and f.name != "__init__.py"
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


def verify_analysis_outputs(
    repo_root: Path,
    project_name: str = "project",
    project_dir: Path | None = None,
) -> bool:
    """Verify that analysis generated expected outputs.

    Checks whether analysis scripts are present for this project and, if so,
    whether they produced output files in the expected directories.  Returns
    False only when scripts exist (output is expected) but all output
    directories are empty or absent.

    Args:
        repo_root: Repository root directory.
        project_name: Name of project directory (default: "project").
        project_dir: Absolute path to the project directory. Defaults to
            ``repo_root / 'projects' / project_name``.

    Returns:
        True if outputs are present or no scripts were expected to run,
        False if scripts exist but no output was generated.
    """
    resolved_dir = project_dir if project_dir is not None else repo_root / "projects" / project_name
    logger.info(
        f"[STAGE-02] Verifying analysis outputs for {resolved_dir.relative_to(repo_root)}/..."
    )

    # Determine whether analysis scripts exist (so we know whether output is expected)
    scripts_dir = resolved_dir / "scripts"
    scripts_exist = scripts_dir.exists() and any(
        f for f in scripts_dir.glob("*.py") if not f.name.startswith("_")
    )

    output_dirs = [
        resolved_dir / "output" / "figures",
        resolved_dir / "output" / "data",
    ]

    # First pass: probe each expected output directory.
    statuses: list[tuple[Path, bool, int]] = []
    for output_dir in output_dirs:
        if output_dir.exists():
            files = list(output_dir.glob("*"))
            statuses.append((output_dir, True, len(files)))
        else:
            statuses.append((output_dir, False, 0))

    has_any_output = any(file_count > 0 for _, _, file_count in statuses)

    # Second pass: log. When at least one expected directory contains
    # files, "absent" or "empty" companions are downgraded from INFO to
    # DEBUG so that projects which legitimately produce only one output
    # kind (figures-only, data-only) do not surface as recurring noise.
    absent_or_empty_level = logger.debug if has_any_output else logger.info
    for output_dir, exists, file_count in statuses:
        if exists and file_count > 0:
            log_success(
                f"Output directory has {file_count} file(s): {output_dir.name}",
                logger,
            )
        elif exists:
            absent_or_empty_level(
                f"  ℹ️  Output directory is empty: {output_dir.name}"
            )
        else:
            # Output directories may not exist yet, not an error on its own.
            absent_or_empty_level(
                f"  ℹ️  Output directory not yet created: {output_dir.name}"
            )

    if scripts_exist and not has_any_output:
        logger.warning(
            f"[STAGE-02] Analysis scripts found for '{project_name}' but no output files detected. "
            "The analysis stage may have failed or produced no figures/data."
        )
        return False

    return True

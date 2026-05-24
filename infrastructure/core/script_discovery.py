"""Script discovery and execution utilities.

This module provides functions for discovering scripts in the project
and verifying their outputs.

Stage 02 executes each discovered script under a subprocess timeout configured by
``ANALYSIS_SCRIPT_TIMEOUT_SEC`` (see :mod:`infrastructure.core.analysis_timeout`).
The default is **7200** seconds (2 hours) per script; set a higher value or
``0``/``unlimited`` for no limit on very long Hermes or Lean batches.
"""

from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import PipelineError
from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.project.discovery import resolve_project_root

logger = get_logger(__name__)

_NON_ANALYSIS_SCRIPT_NAMES = frozenset({"__init__.py", "setup_hook.py", "00_preflight.py"})


def _display_project_path(resolved_dir: Path, repo_root: Path, project_name: str) -> Path:
    """Return a repo-relative path for logs without assuming symlink targets are in-repo."""
    if not resolved_dir.is_absolute():
        return resolved_dir
    try:
        return resolved_dir.relative_to(repo_root.resolve())
    except ValueError:
        return Path("projects") / project_name


def _is_analysis_script(path: Path) -> bool:
    """Return whether *path* should run in Stage 02 analysis discovery."""
    return (
        path.is_file()
        and path.suffix == ".py"
        and not path.name.startswith("_")
        and path.name not in _NON_ANALYSIS_SCRIPT_NAMES
    )


def _configured_analysis_scripts(project_dir: Path, project_scripts_dir: Path) -> list[Path] | None:
    """Return config-declared analysis scripts, or ``None`` when no allowlist exists."""
    config_path = project_dir / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return None

    try:
        import yaml

        loaded: Any = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - malformed optional config should fall back gracefully
        logger.warning("Could not read analysis script allowlist from %s: %s", config_path, exc)
        return None

    if not isinstance(loaded, dict):
        return None
    analysis = loaded.get("analysis")
    if not isinstance(analysis, dict) or "scripts" not in analysis:
        return None

    configured = analysis.get("scripts") or []
    if not isinstance(configured, list):
        logger.warning("Ignoring analysis.scripts in %s because it is not a list", config_path)
        return None

    scripts: list[Path] = []
    for item in configured:
        if not isinstance(item, str):
            logger.warning("Ignoring non-string analysis script entry in %s: %r", config_path, item)
            continue
        script = project_scripts_dir / item
        if _is_analysis_script(script):
            scripts.append(script)
        else:
            logger.warning("Configured analysis script not found or not runnable: %s", script)

    return scripts


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
    resolved_dir = project_dir if project_dir is not None else resolve_project_root(repo_root, project_name)
    display_dir = _display_project_path(resolved_dir, repo_root, project_name)
    logger.info(f"[STAGE-02] Discovering analysis scripts in {display_dir}/...")

    project_scripts_dir = resolved_dir / "scripts"

    if not project_scripts_dir.exists():
        logger.info(
            f"[STAGE-02] No scripts directory found for '{project_name}' - analysis stage will be skipped"  # noqa: E501
        )
        return []

    configured_scripts = _configured_analysis_scripts(resolved_dir, project_scripts_dir)
    if configured_scripts is not None:
        scripts = configured_scripts
        logger.info(
            "[STAGE-02] Using %d config-declared analysis script(s) from manuscript/config.yaml",
            len(scripts),
        )
    else:
        # Find all Python scripts in the scripts/ directory except private modules and
        # non-analysis hooks so ``scripts/`` may contain setup helpers.
        scripts = sorted(f for f in project_scripts_dir.glob("*.py") if _is_analysis_script(f))

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
        raise PipelineError("Scripts directory not found", context={"expected_path": str(scripts_dir)})

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
    resolved_dir = project_dir if project_dir is not None else resolve_project_root(repo_root, project_name)
    display_dir = _display_project_path(resolved_dir, repo_root, project_name)
    logger.info(f"[STAGE-02] Verifying analysis outputs for {display_dir}/...")

    # Determine whether analysis scripts exist (so we know whether output is expected)
    scripts_dir = resolved_dir / "scripts"
    configured_scripts = _configured_analysis_scripts(resolved_dir, scripts_dir) if scripts_dir.exists() else None
    if configured_scripts is not None:
        scripts_exist = bool(configured_scripts)
    else:
        scripts_exist = scripts_dir.exists() and any(_is_analysis_script(f) for f in scripts_dir.glob("*.py"))

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
            absent_or_empty_level(f"  ℹ️  Output directory is empty: {output_dir.name}")
        else:
            # Output directories may not exist yet, not an error on its own.
            absent_or_empty_level(f"  ℹ️  Output directory not yet created: {output_dir.name}")

    if scripts_exist and not has_any_output:
        logger.warning(
            f"[STAGE-02] Analysis scripts found for '{project_name}' but no output files detected. "
            "The analysis stage may have failed or produced no figures/data."
        )
        return False

    return True

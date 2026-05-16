"""Per-stage log-file setup.

Single source of truth for what ``setup_stage_logging`` did in ``run.sh``:
it appends a session-start banner to a deterministic log file path under
``output/<project>/logs/`` (or ``projects/<project>/output/logs/`` when
the per-project layout is requested) and returns the log path.

Idempotent: the directory is created with ``parents=True, exist_ok=True``
and prior log content is preserved (the function appends, never clobbers).
"""

from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_NAME = "pipeline.log"


def stage_log_path(
    repo_root: Path,
    project_name: str,
    *,
    log_name: str = DEFAULT_LOG_NAME,
    layout: str = "per_project",
) -> Path:
    """Return the canonical log file path for a project.

    Args:
        repo_root: Repository root.
        project_name: Project name or qualified ``program/name``.
        log_name: Log file basename. Defaults to ``pipeline.log``.
        layout: ``"per_project"`` (``projects/<name>/output/logs/<log_name>``)
            or ``"central"`` (``output/<name>/logs/<log_name>``). The
            per-project layout matches the legacy ``run.sh`` behavior.
    """
    if layout not in {"per_project", "central"}:
        raise ValueError(f"unknown layout: {layout!r}")
    if layout == "per_project":
        return repo_root / "projects" / project_name / "output" / "logs" / log_name
    return repo_root / "output" / project_name / "logs" / log_name


def setup_stage_log(
    repo_root: Path,
    project_name: str,
    stage_name: str,
    *,
    log_name: str = DEFAULT_LOG_NAME,
    layout: str = "per_project",
    now: datetime | None = None,
) -> Path:
    """Create the log directory and append a session-start banner.

    Args:
        repo_root: Repository root.
        project_name: Project to log under.
        stage_name: Human-readable stage name for the banner.
        log_name: Log file basename.
        layout: See :func:`stage_log_path`.
        now: Override timestamp (used by tests for determinism).

    Returns:
        Absolute path to the log file.
    """
    log_path = stage_log_path(repo_root, project_name, log_name=log_name, layout=layout)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")
    banner = "\n" + "=" * 70 + "\n" + f"[{timestamp}] Starting: {stage_name}\n" + "=" * 70 + "\n"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(banner)

    return log_path


def setup_multiproject_log(
    repo_root: Path,
    *,
    log_name: str = "multi_project_pipeline.log",
    now: datetime | None = None,
) -> Path:
    """Set up the consolidated multi-project log file."""
    log_path = repo_root / "output" / "multi_project_summary" / log_name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")
    banner = "\n" + "=" * 70 + "\n" + f"[{timestamp}] Multi-Project Pipeline Started\n" + "=" * 70 + "\n"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(banner)
    return log_path

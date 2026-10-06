"""Per-stage log-file setup.

Single source of truth for what ``setup_stage_logging`` did in ``run.sh``:
it appends a session-start banner to a deterministic log file path under
``output/<project>/logs/`` (or ``projects/<project>/output/logs/`` when
the per-project layout is requested) and returns the log path.

The confined append helper creates real directories under held ancestors and
preserves prior log content. Approved lifecycle project links resolve only the
project boundary; output and log directory links remain refused.
"""

from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.files.secure_write import append_text_confined
from infrastructure.core.logging.constants import PIPELINE_STAGE_WIDTH
from infrastructure.core.project_paths import NON_RENDERED_SUBDIRS, validate_project_name
from infrastructure.orchestration._stage_log_links import admitted_lifecycle_log_root

DEFAULT_LOG_NAME = "pipeline.log"


def _validate_log_name(log_name: str) -> None:
    if (
        not isinstance(log_name, str)
        or not log_name
        or "\0" in log_name
        or "\\" in log_name
        or Path(log_name).parts != (log_name,)
        or log_name in {".", ".."}
    ):
        raise ValueError("log_name must be a single filename without traversal")


def _append_project_banner(repo_root: Path, project: str, log_path: Path, banner: str) -> None:
    """Admit the supported project leaf link without resolving its output tree."""
    lexical = repo_root.absolute() / "projects" / project
    if project.split("/", 1)[0] not in NON_RENDERED_SUBDIRS | {"active"} or not lexical.is_symlink():
        append_text_confined(repo_root.absolute(), log_path.absolute(), banner)
        return
    with admitted_lifecycle_log_root(lexical) as (canonical, identity):
        append_text_confined(
            canonical, canonical / "output" / "logs" / log_path.name, banner, expected_root_identity=identity
        )


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
            per-project layout matches ``run.sh`` logging.
    """
    if layout not in {"per_project", "central"}:
        raise ValueError(f"unknown layout: {layout!r}")
    project_name = validate_project_name(project_name)
    _validate_log_name(log_name)
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
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")
    bar = "=" * PIPELINE_STAGE_WIDTH
    banner = f"\n{bar}\n[{timestamp}] Starting: {stage_name}\n{bar}\n"
    if layout == "per_project":
        _append_project_banner(repo_root, validate_project_name(project_name), log_path, banner)
    else:
        append_text_confined(repo_root.absolute(), log_path.absolute(), banner)

    return log_path


def setup_multiproject_log(
    repo_root: Path,
    *,
    log_name: str = "multi_project_pipeline.log",
    now: datetime | None = None,
) -> Path:
    """Set up the consolidated multi-project log file."""
    _validate_log_name(log_name)
    log_path = repo_root / "output" / "multi_project_summary" / log_name
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")
    bar = "=" * PIPELINE_STAGE_WIDTH
    banner = f"\n{bar}\n[{timestamp}] Multi-Project Pipeline Started\n{bar}\n"
    append_text_confined(repo_root.absolute(), log_path.absolute(), banner)
    return log_path

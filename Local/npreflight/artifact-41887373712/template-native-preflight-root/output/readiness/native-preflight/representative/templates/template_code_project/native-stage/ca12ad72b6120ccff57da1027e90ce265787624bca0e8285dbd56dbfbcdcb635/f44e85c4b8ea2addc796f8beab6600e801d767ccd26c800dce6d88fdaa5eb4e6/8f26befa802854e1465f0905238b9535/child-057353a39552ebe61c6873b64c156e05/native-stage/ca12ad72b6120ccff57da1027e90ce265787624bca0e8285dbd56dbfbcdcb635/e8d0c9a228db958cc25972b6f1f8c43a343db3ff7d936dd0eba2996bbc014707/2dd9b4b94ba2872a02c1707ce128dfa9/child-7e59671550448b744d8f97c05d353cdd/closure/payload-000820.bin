"""Stage orchestration for the optional docxplus export.

Mirrors ``ebook_stage``: resolve the project, read what the manuscript config
already knows about title and author, call the renderer, and report. The renderer
itself is in :mod:`infrastructure.rendering.docxplus_export`.

The stage returns 0 when it skips. A soft-fail, allow-skip stage that returned
nonzero because an *optional* dependency was absent would turn an opt-in feature
into a broken pipeline for everyone who never asked for it.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering.docxplus_export import export_project

logger = get_logger(__name__)


def _manuscript_identity(project_root: Path) -> tuple[str | None, str | None]:
    """Title and author from ``manuscript/config.yaml``, when it has them."""
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return None, None
    try:
        import yaml
    except ImportError:  # pragma: no cover - PyYAML is a core dependency
        return None, None
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        logger.debug("Could not read %s; exporting without title metadata", config_path)
        return None, None
    paper = data.get("paper") or {}
    authors = data.get("authors") or []
    author = authors[0].get("name") if authors and isinstance(authors[0], dict) else None
    return paper.get("title"), author


def run_docxplus_export(
    repo_root: Path,
    project: str,
    *,
    signing_key_path: str | None = None,
    password: str | None = None,
) -> int:
    """Execute the docxplus export for ``project``. Returns a process exit code."""
    log_header(f"STAGE 13: docxplus Export (Project: {project})", logger)

    project_root = resolve_project_root(repo_root, project)
    project_name = Path(project).name
    output_dir = project_root / "output" / "docxplus"

    signing_key_hex: str | None = None
    if signing_key_path:
        key_file = Path(signing_key_path)
        if not key_file.is_absolute():
            key_file = repo_root / key_file
        if key_file.is_file():
            signing_key_hex = key_file.read_text(encoding="utf-8").strip()
        else:
            logger.warning("Signing key not found: %s — exporting unsigned", key_file)

    title, author = _manuscript_identity(project_root)
    result = export_project(
        project_root,
        output_dir,
        project=project_name,
        title=title,
        author=author,
        signing_key_hex=signing_key_hex,
        password=password,
    )

    if not result.written:
        logger.info("docxplus export produced nothing: %s", result.skipped_reason)
        return 0

    log_success(
        f"docxplus export: {len(result.written)} file(s) carrying "
        f"{result.carried_files} project files"
        f"{' (signed)' if result.signed else ' (unsigned)'}",
        logger,
    )
    return 0

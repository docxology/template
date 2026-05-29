"""Pre-render validation leaf — pitfalls and citations without full markdown_validator surface."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging import DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.content.markdown_validator import (
    validate_citations,
    validate_pandoc_pitfalls,
)

logger = get_logger(__name__)


def prevalidate_for_render(
    source: Path | list[Path] | list[str],
    repo_root: Path | None = None,
    bib_file: str | Path | list[str | Path] | None = None,
) -> None:
    """Hard-gate combined-PDF render on source-markdown integrity.

    Runs pitfall and citation checks against the files about to be rendered.
    Raises :class:`RenderingError` when any blocker is found.
    """
    if isinstance(source, Path):
        if not source.exists():
            return
        paths: list[str] = [str(path) for path in discover_markdown_files(source, scope="tree")]
        anchor_dir = source
    else:
        paths = [str(p) for p in source]
        anchor_dir = Path(paths[0]).parent if paths else Path.cwd()

    if not paths:
        return

    if repo_root is None:
        repo_root = anchor_dir.parents[2] if len(anchor_dir.parents) >= 3 else anchor_dir

    problems = validate_pandoc_pitfalls(paths, repo_root) + validate_citations(paths, repo_root, bib_file=bib_file)
    if not problems:
        logger.debug("Pre-render validation passed for %d markdown file(s)", len(paths))
        return

    blockers = problems
    rendered = "\n".join(f"  [{p.file_path}] {p.message}" for p in blockers)
    by_severity = {
        DiagnosticSeverity.ERROR: sum(1 for p in blockers if p.severity == DiagnosticSeverity.ERROR),
        DiagnosticSeverity.WARNING: sum(1 for p in blockers if p.severity == DiagnosticSeverity.WARNING),
    }
    raise RenderingError(
        f"Pre-render validation failed with {len(blockers)} blocker(s) "
        f"({by_severity[DiagnosticSeverity.ERROR]} error / "
        f"{by_severity[DiagnosticSeverity.WARNING]} warning) before "
        f"Pandoc/xelatex runs:\n{rendered}\n"
        "Fix each occurrence in the listed source markdown file(s) and re-run."
    )


# Backward-compatible alias used by rendering and CLI docs.
prevalidate_source_markdown = prevalidate_for_render

__all__ = ["prevalidate_for_render", "prevalidate_source_markdown"]

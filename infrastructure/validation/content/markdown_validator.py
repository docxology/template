"""Markdown validation facade — orchestrates leaf validators.

Image, reference, math, Pandoc-pitfall, and citation checks live in sibling
``validator_*.py`` modules; this file keeps the public entry points stable.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from infrastructure.core.exceptions import FileNotFoundError
from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.rendering._bibliography import resolve_bibliography
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.content.symbols import collect_symbols
from infrastructure.validation.content.validator_citations import validate_citations
from infrastructure.validation.content.validator_images import validate_images
from infrastructure.validation.content.validator_math import validate_math
from infrastructure.validation.content.validator_pitfalls import validate_pandoc_pitfalls
from infrastructure.validation.content.validator_refs import validate_refs

__all__ = [
    "collect_symbols",
    "find_manuscript_directory",
    "validate_citations",
    "validate_images",
    "validate_markdown",
    "validate_math",
    "validate_pandoc_pitfalls",
    "validate_refs",
]


def validate_markdown(
    markdown_dir: str | Path,
    repo_root: str | Path,
    strict: bool = False,
    *,
    manuscript_files: Iterable[Path] | None = None,
    extra_search_dirs: list[str | Path] | None = None,
) -> tuple[list[DiagnosticEvent], int]:
    """Validate directory Markdown or a confined roster, with optional image roots."""
    markdown_dir = Path(markdown_dir)
    repo_root = Path(repo_root)

    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")

    paths: Iterable[Path]
    if manuscript_files is None:
        paths = discover_markdown_files(markdown_dir, scope="tree")
    else:
        paths = tuple(manuscript_files)
        for path in paths:
            path.resolve(strict=True).relative_to(markdown_dir.resolve(strict=True))
            if not path.is_file():
                raise ValueError(f"Manuscript input is not a file: {path}")
    md_paths = [str(path) for path in paths]
    if not md_paths:
        return ([], 0)

    labels, anchors = collect_symbols(md_paths)

    problems: list[DiagnosticEvent] = []
    problems += validate_images(md_paths, repo_root, extra_search_dirs=extra_search_dirs)
    problems += validate_refs(md_paths, repo_root, labels, anchors)
    problems += validate_math(md_paths, repo_root)
    include_documentation = manuscript_files is not None
    bibliography: list[str | Path] | None = list(resolve_bibliography(markdown_dir)) if include_documentation else None
    problems += validate_pandoc_pitfalls(md_paths, repo_root, include_documentation=include_documentation)
    problems += validate_citations(
        md_paths, repo_root, bib_file=bibliography, include_documentation=include_documentation
    )

    if problems:
        has_errors = any(p.severity == DiagnosticSeverity.ERROR for p in problems)
        exit_code = 1 if (strict and has_errors) else 0
        return (problems, exit_code)
    return ([], 0)


def find_manuscript_directory(repo_root: str | Path, project_name: str = "project") -> Path:
    """Find the manuscript directory for a discovered or qualified project name."""
    from infrastructure.project.discovery import discover_projects, resolve_project_root

    repo_root = Path(repo_root)
    project_root = resolve_project_root(repo_root, project_name)
    manuscript_dir = resolve_source_manuscript_dir(project_root)
    if manuscript_dir.exists() and manuscript_dir.is_dir():
        return manuscript_dir

    discovered = [p.qualified_name for p in discover_projects(repo_root)]
    hint = f" Discovered projects: {', '.join(discovered)}" if discovered else ""
    raise FileNotFoundError(f"Manuscript directory not found at expected location: {manuscript_dir}.{hint}")

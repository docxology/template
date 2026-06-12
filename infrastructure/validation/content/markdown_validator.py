"""Markdown validation facade — orchestrates leaf validators.

Image, reference, math, Pandoc-pitfall, and citation checks live in sibling
``validator_*.py`` modules; this file keeps the public entry points stable.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.exceptions import FileNotFoundError
from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
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
    markdown_dir: str | Path, repo_root: str | Path, strict: bool = False
) -> tuple[list[DiagnosticEvent], int]:
    """Validate all markdown files in a directory."""
    markdown_dir = Path(markdown_dir)
    repo_root = Path(repo_root)

    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")

    md_paths = [str(path) for path in discover_markdown_files(markdown_dir, scope="tree")]
    if not md_paths:
        return ([], 0)

    labels, anchors = collect_symbols(md_paths)

    problems: list[DiagnosticEvent] = []
    problems += validate_images(md_paths, repo_root)
    problems += validate_refs(md_paths, repo_root, labels, anchors)
    problems += validate_math(md_paths, repo_root)
    problems += validate_pandoc_pitfalls(md_paths, repo_root)
    problems += validate_citations(md_paths, repo_root)

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
    manuscript_dir = project_root / "manuscript"
    if manuscript_dir.exists() and manuscript_dir.is_dir():
        return manuscript_dir

    discovered = [p.qualified_name for p in discover_projects(repo_root)]
    hint = f" Discovered projects: {', '.join(discovered)}" if discovered else ""
    raise FileNotFoundError(f"Manuscript directory not found at expected location: {manuscript_dir}.{hint}")

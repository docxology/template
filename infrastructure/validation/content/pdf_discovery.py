"""Explicit combined-PDF discovery for canonical project names."""

from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def discover_combined_pdf(repo_root: Path, project_name: str | None = None) -> Path | None:
    """Locate a named delivery PDF; automatic selection covers public exemplars only."""
    names = (project_name,) if project_name else PUBLIC_PROJECT_NAMES
    found: list[Path] = []
    for name in names:
        parsed = Path(name)
        if parsed.is_absolute() or ".." in parsed.parts or not parsed.parts or "\\" in name:
            raise ValueError("PDF project names must be confined qualified names")
        path = repo_root / "output" / parsed / "pdf" / f"{parsed.name}_combined.pdf"
        current = repo_root
        for part in path.relative_to(repo_root).parts:
            current /= part
            if current.is_symlink():
                raise ValueError("Combined PDF discovery refuses symlink paths")
        if path.is_file():
            found.append(path)
    if len(found) > 1:
        raise ValueError("Multiple public combined PDFs exist; select --project or an explicit PDF path")
    return found[0] if found else None

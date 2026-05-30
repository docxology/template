"""Renderer for the generated public active-projects document."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from infrastructure.project.public_scope import public_project_names


def render_active_projects_doc(repo_root: Path, generated_at: datetime | None = None) -> str:
    """Render ``docs/_generated/active_projects.md`` content."""
    generated_at = generated_at or datetime.now(timezone.utc)
    names = public_project_names(repo_root)
    lines = [
        "# Public active projects",
        "",
        "This file is **generated**. Do not edit by hand.",
        "",
        "The names below are the public CI/documentation scope: tracked template "
        "projects under `projects/` that have both `src/` and `tests/`.",
        "",
        "Runtime discovery still uses "
        "`infrastructure.project.discovery.discover_projects()` and may include "
        "local-only private symlinked projects. Do not copy that local roster "
        "into public docs.",
        "",
        "Human-written documentation should **not** copy this list into RUN_GUIDE, "
        "PAI, or other guides; link here instead. For concrete paths, commands, and "
        "layout examples, default to the stable exemplar "
        "[`projects/templates/template_code_project/`](../../projects/templates/template_code_project/) unless a doc "
        "explicitly compares layouts.",
        "",
        f"Generated at (timezone.utc): `{generated_at.isoformat(timespec='seconds')}`",
        "",
        "Current entries:",
        "",
    ]
    for name in sorted(names):
        lines.append(f"- `{name}`")
    lines.extend(
        [
            "",
            "Regenerate after adding, removing, or renaming projects:",
            "",
            "```bash",
            "uv run python scripts/generate_active_projects_doc.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_active_projects_doc(repo_root: Path) -> Path:
    """Write the generated public active-projects document."""
    out_dir = repo_root / "docs" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "active_projects.md"
    out_path.write_text(render_active_projects_doc(repo_root), encoding="utf-8")
    return out_path

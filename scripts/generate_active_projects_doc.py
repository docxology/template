#!/usr/bin/env python3
"""Write docs/_generated/active_projects.md from discover_projects().

Run from repository root:

    uv run python scripts/generate_active_projects_doc.py
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from infrastructure.project.discovery import discover_projects


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "docs" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "active_projects.md"

    projects = discover_projects(repo_root)
    names = [p.qualified_name for p in projects]
    lines = [
        "# Active projects (`discover_projects`)",
        "",
        "This file is **generated**. Do not edit by hand.",
        "",
        "The names below are the single source of truth from "
        "`infrastructure.project.discovery.discover_projects()` for directories "
        "under `projects/` that have both `src/` and `tests/`.",
        "",
        "Human-written documentation should **not** copy this list into RUN_GUIDE, "
        "PAI, or other guides—link here instead. For concrete paths, commands, and "
        "layout examples, default to the stable exemplar "
        "[`projects/code_project/`](../../projects/code_project/) unless a doc "
        "explicitly compares layouts.",
        "",
        f"Generated at (UTC): `{datetime.now(UTC).isoformat(timespec='seconds')}`",
        "",
        "Current entries:",
        "",
    ]
    for n in sorted(names):
        lines.append(f"- `{n}`")
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
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path} ({len(names)} project(s))")


if __name__ == "__main__":
    main()

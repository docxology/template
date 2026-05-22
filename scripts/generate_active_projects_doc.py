#!/usr/bin/env python3
"""Write docs/_generated/active_projects.md for the public template scope.

Run from repository root:

    uv run python scripts/generate_active_projects_doc.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.project.public_scope import public_project_names

logger = get_logger(__name__)


def main() -> None:
    log_header("Generate Active Projects Documentation", logger)
    out_dir = REPO_ROOT / "docs" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "active_projects.md"

    names = public_project_names(REPO_ROOT)
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
        "PAI, or other guides—link here instead. For concrete paths, commands, and "
        "layout examples, default to the stable exemplar "
        "[`projects/template_code_project/`](../../projects/template_code_project/) unless a doc "
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
    log_success(f"Wrote {out_path} ({len(names)} project(s))", logger)


if __name__ == "__main__":
    main()

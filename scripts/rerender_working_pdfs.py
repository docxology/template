#!/usr/bin/env python3
"""Re-render combined PDFs for all ``projects/working/`` trees (author/metadata updates).

Thin orchestrator: stage 03 (render) + stage 05 (copy) with manuscript-variable
hydration skipped so long analysis rebuilds are not required for title-page edits.

Exit codes:
    0 — all projects rendered and copied successfully
    1 — one or more projects failed (see log)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.logging.utils import get_logger, log_header  # noqa: E402
from infrastructure.project.working_render import list_working_projects  # noqa: E402

logger = get_logger(__name__)


def _has_manuscript(project_dir: Path) -> bool:
    manuscript = project_dir / "manuscript"
    return manuscript.is_dir() and any(manuscript.glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-render working-project PDFs (skip variable hydration)",
    )
    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="Limit to one or more project names (repeatable)",
    )
    parser.add_argument(
        "--with-hydration",
        action="store_true",
        help="Run z_generate_manuscript_variables.py before render (slow)",
    )
    args = parser.parse_args()

    repo = repo_root
    names = args.projects if args.projects else list_working_projects(repo)
    names = [n for n in names if _has_manuscript(repo / "projects" / "working" / n)]

    if not names:
        logger.error("No working projects with manuscript/*.md found")
        return 1

    log_header(f"Working PDF re-render ({len(names)} projects)", logger)
    any_failed = False
    results: list[tuple[str, str, float]] = []

    for name in names:
        start = time.time()
        render_cmd = [
            sys.executable,
            str(repo / "scripts" / "03_render_pdf.py"),
            "--project",
            name,
        ]
        if not args.with_hydration:
            render_cmd.append("--skip-manuscript-hydration")

        logger.info("=== Render %s ===", name)
        render = subprocess.run(render_cmd, cwd=str(repo), check=False)  # nosec B603
        if render.returncode != 0:
            results.append((name, "FAIL — render", time.time() - start))
            any_failed = True
            logger.error("Render failed for %s (exit %s)", name, render.returncode)
            continue

        copy = subprocess.run(  # nosec B603
            [sys.executable, str(repo / "scripts" / "05_copy_outputs.py"), "--project", name],
            cwd=str(repo),
            check=False,
        )
        duration = time.time() - start
        if copy.returncode != 0:
            results.append((name, "PARTIAL — render ok, copy failed", duration))
            any_failed = True
            logger.warning("Copy failed for %s (exit %s)", name, copy.returncode)
        else:
            top = repo / "output" / name / f"{name}_combined.pdf"
            alt = repo / "output" / name / "pdf" / f"{name}_combined.pdf"
            if top.is_file() or alt.is_file():
                results.append((name, "PASS", duration))
            else:
                results.append((name, "PARTIAL — no top-level combined PDF", duration))
                any_failed = True

    logger.info("--- Summary ---")
    for name, status, duration in results:
        logger.info("  %s: %s (%.1fs)", name, status, duration)

    pass_n = sum(1 for _, status, _ in results if status == "PASS")
    logger.info("Complete: %d PASS, %d other (of %d)", pass_n, len(results) - pass_n, len(results))
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())

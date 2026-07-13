#!/usr/bin/env python3
"""Stage-02 analysis: render the newspaper PDF — the project's primary artifact.

Loads ``content/`` and renders the full edition to ``output/pdf/<basename>.pdf``,
then writes a machine-readable render report to ``output/data/render_report.json``
and a human summary to ``output/reports/render_summary.txt``. A non-empty overset
(content that did not fit a page) **fails the stage by default** so dropped copy
can never pass silently — this is the engine's core correctness contract. Pass
``--allow-overset`` to downgrade it to a warning. Output paths are printed to
stdout for pipeline manifest collection.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("newspaper.render")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project-root", default=str(project_root()))
    parser.add_argument(
        "--allow-overset",
        action="store_true",
        help="Downgrade over-set pages from a hard failure to a warning (default fails closed).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="(deprecated; over-set now fails by default) accepted for backward compatibility.",
    )
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    from newspaper.engine import build_and_render

    result = build_and_render(root)
    logger.info("Rendered %d pages → %s", result.page_count, result.output_path)

    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "render_report.json").write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    reports_dir = root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary = [
        "The Triplicate — render summary",
        "=" * 40,
        f"pages:        {result.page_count}",
        f"all_pages_fit: {result.all_pages_fit}",
        f"output:       {result.output_path}",
    ]
    if result.oversets:
        summary.append("OVERSET PAGES (content did not fit):")
        for page, n in sorted(result.oversets.items()):
            summary.append(f"  page {page}: {n} flowable(s) dropped")
    (reports_dir / "render_summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")

    # Print output paths to stdout for pipeline manifest collection.
    print(result.output_path)
    print(data_dir / "render_report.json")
    print(reports_dir / "render_summary.txt")

    if result.page_count == 0:
        logger.error("No pages rendered.")
        return 1
    if result.oversets:
        logger.warning("Over-set pages: %s", result.oversets)
        if not args.allow_overset:
            logger.error(
                "Over-set pages present — failing closed so dropped copy cannot ship "
                "silently. Re-run with --allow-overset to override."
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

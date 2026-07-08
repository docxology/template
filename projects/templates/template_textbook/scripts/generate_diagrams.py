"""Thin orchestrator: render every Mermaid diagram (PNG, or .mmd fallback).

Delegates to ``src/mermaid/diagrams.py``. Default output:
``<project_root>/output/figures/mermaid/``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import PROJECT as PROJECT_DIR, ensure_project_paths

ensure_project_paths()


def main() -> int:
    """CLI entry point."""
    from textbook_logging import get_logger
    from mermaid.diagrams import generate_all_diagrams

    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Render all template_textbook Mermaid diagrams")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "output" / "figures" / "mermaid")
    args = parser.parse_args()

    results = generate_all_diagrams(args.output_dir)
    for result in results:
        marker = "✓ png" if result.rendered_png else "· mmd"
        print(f"  {marker} {result.path}")
    rendered = sum(1 for r in results if r.rendered_png)
    logger.info("Rendered %d/%d diagrams as PNG → %s", rendered, len(results), args.output_dir)
    print(f"[generate_diagrams] {len(results)} diagrams ({rendered} png) → {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

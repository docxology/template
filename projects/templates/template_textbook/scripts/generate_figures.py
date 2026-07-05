"""Thin orchestrator: generate matplotlib figures the manuscript references.

Delegates chapter plots to ``visualization.plots.generate_all_figures``, the
optional format gallery to ``visualization.gallery.generate_gallery_figures``,
and registry emission to ``visualization.registry.write_figure_registry``.
Default output: ``<project_root>/output/figures/``. Prints each path for
manifest collection by the pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import PROJECT as PROJECT_DIR, ensure_project_paths

ensure_project_paths()


def main() -> int:
    from textbook_logging import get_logger
    from visualization.gallery import generate_gallery_figures
    from visualization.plots import generate_all_figures
    from visualization.registry import write_figure_registry

    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Generate all template_textbook figures")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "output" / "figures")
    parser.add_argument(
        "--no-gallery",
        action="store_true",
        help="Skip the plot-type gallery (figures/gallery/).",
    )
    args = parser.parse_args()

    paths = generate_all_figures(args.output_dir)
    for path in paths:
        print(f"  ✓ {path}")
    if not args.no_gallery:
        gallery_paths = generate_gallery_figures(args.output_dir / "gallery")
        for path in gallery_paths:
            print(f"  ✓ {path}")
        paths += gallery_paths
    registry_path = write_figure_registry(PROJECT_DIR / "manuscript", args.output_dir)
    print(f"  ✓ {registry_path}")
    paths.append(registry_path)
    logger.info("Generated %d figures → %s", len(paths), args.output_dir)
    print(f"[generate_figures] {len(paths)} figures → {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

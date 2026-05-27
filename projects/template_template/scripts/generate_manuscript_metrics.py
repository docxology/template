#!/usr/bin/env python3
"""Generate manuscript metrics JSON and inject variables — Thin Orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _locate_repo_root(project_dir: Path) -> Path:
    resolved = project_dir.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "infrastructure").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    sibling = resolved.parents[2] / "template"
    if (sibling / "infrastructure").is_dir():
        return sibling.resolve()
    raise FileNotFoundError(f"Could not locate template repo root from {project_dir}")


PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
REPO_ROOT = _locate_repo_root(PROJECT_DIR)
SRC_DIR = PROJECT_DIR / "src"
for _p in (str(REPO_ROOT), str(SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from template_template import (  # noqa: E402  (path setup must precede import)
    build_manuscript_metrics_dict,
    load_metrics,
    render_all_chapters,
    save_metrics_json,
)
from infrastructure.core.logging.utils import get_logger  # noqa: E402

logger = get_logger(__name__)

MANUSCRIPT_DIR = PROJECT_DIR / "manuscript"
OUTPUT_DATA_DIR = PROJECT_DIR / "output" / "data"
OUTPUT_MANUSCRIPT_DIR = PROJECT_DIR / "output" / "manuscript"


def main() -> int:
    """Generate metrics.json and inject variables into manuscript chapters."""
    logger.info("=== generate_manuscript_metrics: Stage 02 analysis ===")

    # Step 1: Compute metrics
    metrics = build_manuscript_metrics_dict(REPO_ROOT)

    # Step 2: Write metrics.json
    metrics_path = OUTPUT_DATA_DIR / "metrics.json"
    save_metrics_json(metrics, metrics_path)
    logger.info(f"Wrote metrics to {metrics_path} ({metrics_path.stat().st_size} bytes)")

    # Step 3: Verify round-trip (real load via inject_metrics.load_metrics)
    loaded = load_metrics(metrics_path)
    logger.info(f"Verified: round-trip load gives {len(loaded)} flat variables")

    # Step 4: Render chapters into output/manuscript/
    written = render_all_chapters(MANUSCRIPT_DIR, loaded, OUTPUT_MANUSCRIPT_DIR)
    logger.info(
        f"Rendered {len(written)} files into {OUTPUT_MANUSCRIPT_DIR.relative_to(PROJECT_DIR)}"
    )

    logger.info("=== generate_manuscript_metrics: complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

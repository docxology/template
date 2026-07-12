#!/usr/bin/env python3
"""Generate manuscript metrics JSON and inject variables — Thin Orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# The package initializer imports shared infrastructure, so the repository root
# must be available before importing even the package's path helper.
_explicit_repo_root = os.environ.get("TEMPLATE_REPO_ROOT", "").strip()
BOOTSTRAP_REPO_ROOT = (
    Path(_explicit_repo_root).resolve()
    if _explicit_repo_root
    else next(
        (candidate for candidate in (PROJECT_DIR, *PROJECT_DIR.parents) if (candidate / "infrastructure").is_dir()),
        None,
    )
)
if BOOTSTRAP_REPO_ROOT is None:
    raise RuntimeError(f"Could not locate repository root above {PROJECT_DIR}")
if str(BOOTSTRAP_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(BOOTSTRAP_REPO_ROOT))

from template_template.paths import locate_repo_root  # noqa: E402

REPO_ROOT = locate_repo_root(BOOTSTRAP_REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
    logger.info(f"Rendered {len(written)} files into {OUTPUT_MANUSCRIPT_DIR.relative_to(PROJECT_DIR)}")

    logger.info("=== generate_manuscript_metrics: complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

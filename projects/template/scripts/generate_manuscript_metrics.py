#!/usr/bin/env python3
"""Generate manuscript metrics JSON and inject variables — Thin Orchestrator.

This is the primary Stage 02 analysis script for the ``template/`` project.
It performs two sequential operations:

1. **Metrics generation**: Calls ``build_infrastructure_report()`` to compute
   real, validated metrics from the live repository structure, then serialises
   them to ``output/data/metrics.json`` together with per-project test counts
   computed by scanning real test files.

2. **Variable injection**: Calls ``render_all_chapters()`` to substitute all
   ``${variable}`` tokens in the manuscript chapter files, writing the
   rendered versions to ``output/manuscript/``.

The render hook in ``scripts/03_render_pdf.py`` (lines 56-62) automatically
detects ``output/manuscript/`` and uses it in preference to ``manuscript/``,
so Stage 03 receives fully populated chapters with no manual intervention.

Output files::

    projects/template/output/data/metrics.json
    projects/template/output/manuscript/01_abstract.md
    projects/template/output/manuscript/02_introduction.md
    ...
    projects/template/output/manuscript/references.bib
    projects/template/output/manuscript/preamble.md
    projects/template/output/manuscript/config.yaml
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup: project in projects_in_progress/ or projects/
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
REPO_ROOT = PROJECT_DIR.parent.parent
SRC_DIR = PROJECT_DIR / "src"
for _p in (str(REPO_ROOT), str(SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from template import (  # noqa: E402  (path setup must precede import)
    build_manuscript_metrics_dict,
    load_metrics,
    render_all_chapters,
    save_metrics_json,
)
from infrastructure.core.logging_utils import get_logger  # noqa: E402

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

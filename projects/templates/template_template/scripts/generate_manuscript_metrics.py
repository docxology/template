#!/usr/bin/env python3
"""Generate manuscript metrics JSON and inject variables — Thin Orchestrator."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
_BOOTSTRAP_SPEC = importlib.util.spec_from_file_location(
    "template_script_bootstrap", Path(__file__).resolve().parent / "_bootstrap.py"
)
if _BOOTSTRAP_SPEC is None or _BOOTSTRAP_SPEC.loader is None:
    raise ImportError("actual own project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_BOOTSTRAP_SPEC)
_BOOTSTRAP_SPEC.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(PROJECT_DIR)

from template_template.core.paths import data_repo_root, verify_reference_inputs  # noqa: E402 - selected SDK and own namespace precede imports

# Complete public SOURCE DATA is a separate input, never an SDK import path.
_explicit_repo_root = os.environ.get("TEMPLATE_REPO_ROOT", "").strip()
REPO_ROOT = data_repo_root(
    PROJECT_DIR, explicit_root=Path(_explicit_repo_root).absolute() if _explicit_repo_root else None
)

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

    verify_reference_inputs()
    logger.info("=== generate_manuscript_metrics: complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

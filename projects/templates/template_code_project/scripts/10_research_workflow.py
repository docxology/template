#!/usr/bin/env python3
"""Research workflow dispatch stage.

Reads the ``research_workflow:`` block from ``manuscript/config.yaml`` and,
when enabled, dispatches the 7-stage research workflow using the configured
stage overrides.

Consumed by: config.yaml ``research_workflow:`` block.
See: infrastructure/research/config.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from infrastructure.research.config import load_research_workflow_config  # noqa: E402

logger = get_logger(__name__)

# Canonical 7-stage research workflow names
_DEFAULT_STAGES = [
    "question_refinement",
    "background_review",
    "hypothesis_generation",
    "methodology_design",
    "gap_analysis",
    "synthesis",
    "reporting",
]


def _run_stage(stage_name: str) -> bool:
    """Execute a single research workflow stage.

    Args:
        stage_name: Canonical stage identifier.

    Returns:
        True on success.
    """
    logger.info(f"  [run] stage '{stage_name}'")
    # Infrastructure hook: LLM prompt dispatch would be wired here once
    # infrastructure.research.workflow is implemented.
    return True


def main() -> int:
    cfg = load_research_workflow_config(PROJECT_DIR)

    if not cfg.enabled:
        logger.info(
            "[skip] research_workflow disabled in config — "
            "set research_workflow.enabled: true to run"
        )
        return 0

    logger.info(f"Running research workflow ({len(_DEFAULT_STAGES)} stages)")
    failed = False
    for stage_name in _DEFAULT_STAGES:
        if stage_name in cfg.skip_stages:
            logger.info(f"  [skip] stage '{stage_name}' disabled in config")
            continue
        ok = _run_stage(stage_name)
        if not ok:
            logger.error(f"  [fail] stage '{stage_name}' failed")
            failed = True

    if failed:
        return 1
    logger.info("Research workflow complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

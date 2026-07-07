#!/usr/bin/env python3
"""Provenance DAG recording stage.

Reads the ``provenance:`` block from ``manuscript/config.yaml`` and, when
enabled, records a provenance node for the current pipeline run to the
content-addressed DAG store via the shared ``infrastructure.provenance``
store — the same store class every other provenance-recording surface in
this repo uses, so all projects' DAG files share one on-disk schema.

Consumed by: config.yaml ``provenance:`` block.
See: infrastructure/provenance/config.py, infrastructure/provenance/store.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from infrastructure.provenance import Provenance, RunNode  # noqa: E402
from infrastructure.provenance.config import load_provenance_config  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    cfg = load_provenance_config(PROJECT_DIR)

    if not cfg.enabled:
        logger.info("[skip] provenance disabled in config — set provenance.enabled: true to record")
        return 0

    store_path = cfg.dag_path(PROJECT_DIR)
    store = Provenance.with_path(store_path.parent, filename=store_path.name)
    run = store.record(RunNode.create(label="Pipeline Run", command="pipeline_run"))
    logger.info(f"Provenance node recorded: {run.node_id[:12]}… → {store_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

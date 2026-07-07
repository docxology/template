#!/usr/bin/env python3
"""Provenance DAG recording stage.

Reads the ``provenance:`` block from ``manuscript/config.yaml`` and, when
enabled, records a provenance node for the current pipeline run to the
content-addressed DAG store.

Consumed by: config.yaml ``provenance:`` block.
See: infrastructure/provenance/config.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from infrastructure.provenance.config import load_provenance_config  # noqa: E402

logger = get_logger(__name__)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record_node(
    store_path: Path,
    stage: str,
    label: str,
    parent_hashes: list[str] | None = None,
) -> str:
    """Append a provenance node to the DAG store.

    Returns the SHA-256 content address of the new node.
    """
    node: dict = {
        "stage": stage,
        "label": label,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "parents": parent_hashes or [],
    }
    node_bytes = json.dumps(node, sort_keys=True).encode("utf-8")
    node_hash = _sha256(node_bytes)
    node["hash"] = node_hash

    # Load existing graph
    store_path.parent.mkdir(parents=True, exist_ok=True)
    if store_path.exists():
        with open(store_path, "r", encoding="utf-8") as fh:
            graph: dict = json.load(fh)
    else:
        graph = {"nodes": {}, "heads": []}

    graph["nodes"][node_hash] = node
    # Update heads: remove parents from heads, add new node
    heads: list[str] = graph.get("heads", [])
    for ph in (parent_hashes or []):
        if ph in heads:
            heads.remove(ph)
    heads.append(node_hash)
    graph["heads"] = heads

    with open(store_path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=2)

    return node_hash


def main() -> int:
    cfg = load_provenance_config(PROJECT_DIR)

    if not cfg.enabled:
        logger.info("[skip] provenance disabled in config — set provenance.enabled: true to record")
        return 0

    store_path = cfg.dag_path(PROJECT_DIR)

    # Record a node for this pipeline invocation
    stage_key = "pipeline_run"
    label = "Pipeline Run"
    node_hash = _record_node(store_path, stage=stage_key, label=label)
    logger.info(f"Provenance node recorded: {node_hash[:12]}… → {store_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

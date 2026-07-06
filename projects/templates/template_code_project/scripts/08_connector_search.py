#!/usr/bin/env python3
"""Connector search pipeline stage.

Reads the ``connector_search:`` block from ``manuscript/config.yaml`` and,
when enabled, runs queries across the configured scientific-database
connectors, writing results to ``output/data/connector_search/``.

Consumed by: config.yaml ``connector_search:`` block.
See: infrastructure/search/connectors/config.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from infrastructure.search.connectors.config import load_connector_search_config  # noqa: E402
from infrastructure.search.connectors import search_connector  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    cfg = load_connector_search_config(PROJECT_DIR)

    if not cfg.enabled:
        logger.info("[skip] connector_search disabled in config — set connector_search.enabled: true to run")
        return 0

    if not cfg.connectors:
        logger.warning("[skip] connector_search.connectors is empty — no queries configured")
        return 0

    output_dir = PROJECT_DIR / cfg.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[dict]] = {}
    for connector_id, queries in cfg.connectors.items():
        logger.info(f"Running connector '{connector_id}' with {len(queries)} queries")
        connector_results: list[dict] = []
        for query in queries:
            try:
                hits = search_connector(
                    query,
                    connector_id=connector_id,
                    max_results=cfg.max_results,
                )
                for hit in hits:
                    connector_results.append({
                        "id": hit.id,
                        "title": hit.title,
                        "url": hit.url,
                        "year": hit.year,
                        "authors": hit.authors,
                        "abstract": hit.abstract,
                        "query": query,
                        "source": hit.source,
                    })
                logger.info(f"  '{query}' → {len(hits)} hits")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"  '{query}' via '{connector_id}' failed: {exc}")
        all_results[connector_id] = connector_results

    output_path = output_dir / "results.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(all_results, fh, indent=2)
    logger.info(f"Connector search results written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

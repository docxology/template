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

import yaml  # noqa: E402

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from infrastructure.search.connectors.config import load_connector_search_config  # noqa: E402
from infrastructure.search.connectors import list_connectors, search_connector  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    connector_search_config_path = PROJECT_DIR / "connector_search.yaml"
    if not connector_search_config_path.exists():
        logger.info("[skip] no connector_search.yaml — connector search not configured for this project")
        return 0

    cfg = load_connector_search_config(PROJECT_DIR)
    connector_ids = cfg.enabled_connectors or [entry.name for entry in list_connectors()]

    manuscript_config_path = PROJECT_DIR / "manuscript" / "config.yaml"
    queries: list[str] = []
    if manuscript_config_path.exists():
        manuscript_cfg = yaml.safe_load(manuscript_config_path.read_text(encoding="utf-8")) or {}
        queries = [str(k) for k in manuscript_cfg.get("keywords", [])]

    if not queries:
        logger.warning("[skip] manuscript/config.yaml has no keywords — no queries to run")
        return 0

    output_dir = PROJECT_DIR / "output" / "data" / "connector_search"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[dict]] = {}
    for connector_id in connector_ids:
        logger.info(f"Running connector '{connector_id}' with {len(queries)} queries")
        connector_results: list[dict] = []
        for query in queries:
            try:
                hits = search_connector(
                    connector_id,
                    query,
                    max_results=cfg.default_max_results,
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

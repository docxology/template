#!/usr/bin/env python3
"""Connector Search stage orchestrator (opt-in via [science] tag).

Thin dispatcher for scientific database connector searches. Reads query
configuration from the project's ``config.yaml`` ``connector_search:`` block
and runs searches against configured databases.

Usage::

    uv run python scripts/pipeline/stage_08_connector_search.py --project <name>
    uv run python scripts/pipeline/stage_08_connector_search.py --project <name> --connector arxiv --query "active inference"

Exit codes:
    0: All searches completed successfully.
    1: An unrecoverable error occurred.
    2: Graceful skip — no connectors configured or project not found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.search.connectors import (  # noqa: E402
    list_connectors,
    search_connector,
)

logger = get_logger(__name__)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Connector Search Stage")
    parser.add_argument("--project", default="project", help="Project name in projects/")
    parser.add_argument("--connector", default=None, help="Override connector ID")
    parser.add_argument("--query", default=None, help="Override search query")
    parser.add_argument("--output", default=None, help="Output JSON path")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Max results per query"
    )
    args = parser.parse_args()

    log_header(f"STAGE 08: Connector Search (Project: {args.project})", logger)

    # Resolve project dir
    project_dir = Path.cwd() / "projects" / args.project
    if not project_dir.is_dir():
        logger.warning(f"Project directory not found: {project_dir}")
        return 2

    # Load config
    config_path = project_dir / "manuscript" / "config.yaml"
    queries: list[tuple[str, str]] = []

    if args.connector and args.query:
        queries = [(args.connector, args.query)]
    elif config_path.exists():
        import yaml
        try:
            cfg = yaml.safe_load(config_path.read_text()) or {}
            cs = cfg.get("connector_search", {})
            if not cs.get("enabled", False):
                logger.info("connector_search not enabled in config — skipping")
                return 2
            for connector_id, connector_queries in cs.get("connectors", {}).items():
                for q in connector_queries:
                    queries.append((connector_id, q))
            # Override max_results from config if set
            args.max_results = cs.get("max_results", args.max_results)
        except Exception as exc:
            logger.error(f"Failed to load config: {exc}")
            return 1
    else:
        logger.info("No connector_search config found — skipping")
        return 2

    if not queries:
        logger.info("No queries configured — skipping")
        return 2

    # Run searches
    all_results: dict[str, list[dict]] = {}
    success = True
    for db_id, query in queries:
        logger.info(f"Searching {db_id}: {query}")
        try:
            hits = search_connector(db_id, query, limit=args.max_results)
            all_results[f"{db_id}:{query}"] = [
                {
                    "id": h.id,
                    "title": h.title,
                    "summary": h.summary or "",
                    "url": h.url or "",
                    "score": h.score,
                }
                for h in hits
            ]
            logger.info(f"  → {len(hits)} results")
        except Exception as exc:
            logger.error(f"  → Failed: {exc}")
            all_results[f"{db_id}:{query}"] = []
            success = False

    # Write output
    output_path = Path(args.output or project_dir / "output" / "data" / "connector_search.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_results, indent=2, default=str))
    logger.info(f"Results written to {output_path}")

    if success:
        log_success("Connector search complete")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
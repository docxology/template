#!/usr/bin/env python3
"""Provenance Record stage orchestrator (opt-in via [provenance] tag).

Thin dispatcher that records pipeline stage artifacts as provenance nodes
in the content-addressed provenance DAG.

Usage::

    uv run python scripts/pipeline/stage_09_provenance_record.py --project <name> --stage "Connector Search"

Exit codes:
    0: Provenance recording completed successfully.
    1: An unrecoverable error occurred.
    2: Graceful skip — provenance not configured or project not found.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.provenance import (  # noqa: E402
    Provenance,
    RunNode,
    ArtifactNode,
    EdgeRelation,
)

logger = get_logger(__name__)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Provenance Record Stage")
    parser.add_argument("--project", default="project", help="Project name in projects/")
    parser.add_argument("--stage", required=True, help="Pipeline stage name")
    parser.add_argument("--label", default=None, help="Human label for the run node")
    parser.add_argument("--inputs", default=None, help="Glob pattern for input files")
    parser.add_argument("--outputs", default=None, help="Glob pattern for output files")
    parser.add_argument("--store-path", default=None, help="Provenance store path")
    args = parser.parse_args()

    log_header(f"STAGE 09: Provenance Record (Project: {args.project})", logger)

    # Resolve project dir
    project_dir = Path.cwd() / "projects" / args.project
    if not project_dir.is_dir():
        logger.warning(f"Project directory not found: {project_dir}")
        return 2

    # Load config
    config_path = project_dir / "manuscript" / "config.yaml"
    store_path = args.store_path
    auto_record = True

    if config_path.exists():
        import yaml
        try:
            cfg = yaml.safe_load(config_path.read_text()) or {}
            pc = cfg.get("provenance", {})
            if not pc.get("enabled", True):
                logger.info("Provenance not enabled in config — skipping")
                return 2
            auto_record = pc.get("auto_record", True)
            if not store_path:
                store_path = str(project_dir / pc.get("store_path", ".provenance/graph.json"))
        except Exception as exc:
            logger.error(f"Failed to load config: {exc}")
            return 1

    if not auto_record:
        logger.info("auto_record is disabled — skipping")
        return 2

    if not store_path:
        store_path = str(project_dir / ".provenance" / "graph.json")

    # Record the run node
    store = Provenance.with_path(Path(store_path).parent, filename=Path(store_path).name)
    run = store.record(
        RunNode.create(
            label=args.label or f"Pipeline: {args.stage}",
            command=args.stage,
            metadata={"project": args.project},
        )
    )
    logger.info(f"Recorded run node: {run.node_id}")

    # Record outputs if glob given
    if args.outputs:
        import glob as glob_mod
        for path_str in glob_mod.glob(str(project_dir / args.outputs), recursive=True):
            p = Path(path_str)
            if p.is_file():
                art = store.record(
                    ArtifactNode.create(
                        label=p.name,
                        path=str(p.relative_to(project_dir)),
                        size_bytes=p.stat().st_size,
                    )
                )
                store.link(run.node_id, art.node_id, EdgeRelation.produced_by)
                logger.info(f"  Produced: {p.name} ({art.node_id})")

    log_success(f"Provenance recorded for stage: {args.stage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
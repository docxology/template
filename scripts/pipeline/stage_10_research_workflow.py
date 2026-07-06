#!/usr/bin/env python3
"""Research Workflow dispatch orchestrator (thin dispatcher).

Validates and reports on the 7-stage research workflow configuration
for a project. Can print the full workflow description or dispatch
a specific stage.

Usage::

    uv run python scripts/pipeline/stage_10_research_workflow.py --project <name> --describe
    uv run python scripts/pipeline/stage_10_research_workflow.py --project <name> --stage SCOPE

Exit codes:
    0: Workflow description or stage validation completed.
    1: An unrecoverable error occurred.
    2: Graceful skip — research workflow not configured.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.research import ResearchWorkflow, WORKFLOW_STAGES  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Research Workflow Stage")
    parser.add_argument("--project", default="project", help="Project name in projects/")
    parser.add_argument("--describe", action="store_true", help="Print full workflow description")
    parser.add_argument("--stage", default=None, help="Workflow stage name (SCOPE, LITERATURE, etc.)")
    args = parser.parse_args()

    log_header(f"STAGE 10: Research Workflow (Project: {args.project})", logger)

    # Check if research workflow is configured
    project_dir = Path.cwd() / "projects" / args.project
    config_path = project_dir / "manuscript" / "config.yaml"
    workflow_enabled = False

    if config_path.exists():
        import yaml
        try:
            cfg = yaml.safe_load(config_path.read_text()) or {}
            rw = cfg.get("research_workflow", {})
            workflow_enabled = rw.get("enabled", False)
        except Exception:
            pass

    if not workflow_enabled and not args.describe:
        logger.info("research_workflow not enabled in config — skipping")
        return 2

    if args.describe:
        description = ResearchWorkflow.describe()
        print(description)
        log_success("Workflow description printed")
        return 0

    if args.stage:
        stage = ResearchWorkflow.stage(args.stage.upper())
        if stage is None:
            valid = ", ".join(s.name for s in WORKFLOW_STAGES)
            logger.error(f"Unknown stage '{args.stage}'. Valid: {valid}")
            return 1
        logger.info(f"Stage {stage.order}: {stage.name}")
        logger.info(f"  Required: {stage.required}")
        logger.info(f"  Sub-agent: {stage.subagent or 'none'}")
        logger.info(f"  Parallel sub-agents: {stage.parallel_subagents}")
        logger.info(f"  Outputs: {', '.join(stage.outputs)}")
        if stage.template_commands:
            logger.info("  Template commands:")
            for cmd in stage.template_commands:
                logger.info(f"    $ {cmd}")
        log_success(f"Stage {stage.name} details")
        return 0

    # Default: show summary
    logger.info(f"Research workflow has {len(WORKFLOW_STAGES)} stages")
    for s in WORKFLOW_STAGES:
        required = "required" if s.required else "optional"
        logger.info(f"  {s.order}. {s.name} ({required})")
    log_success("Workflow summary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
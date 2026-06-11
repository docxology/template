#!/usr/bin/env python3
"""Execute research project pipeline stages.

Thin orchestrator over PipelineExecutor, post-run reporting, and HITL CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.hitl_cli import PipelineArgs, handle_hitl_command
from infrastructure.core.pipeline.incremental import IncrementalConfig
from infrastructure.core.pipeline.single_stage import execute_single_stage
from infrastructure.core.pipeline.stage_registry import known_stage_keys
from infrastructure.core.runtime.environment import validate_interpreter

# Re-export for tests importing from scripts.execute_pipeline
__all__ = ["PipelineArgs", "handle_hitl_command", "execute_pipeline", "execute_single_stage", "main"]

logger = get_logger(__name__)


def execute_pipeline(
    project_name: str,
    repo_root: Path,
    skip_infra: bool = False,
    skip_llm: bool = False,
    resume: bool = False,
    core_only: bool = False,
    hitl_mode: str = "full-auto",
    incremental: bool = False,
) -> int:
    """Execute pipeline for a single project."""
    try:
        validate_interpreter()
        config = PipelineConfig(
            project_name=project_name,
            repo_root=repo_root,
            skip_infra=skip_infra,
            skip_llm=skip_llm,
            resume=resume,
            hitl_mode=hitl_mode,
            incremental=IncrementalConfig(enabled=incremental),
        )
        executor = PipelineExecutor(config)
        results = executor.execute_core_pipeline() if core_only else executor.execute_full_pipeline()
        from infrastructure.core.pipeline.post_run_reporting import write_pipeline_post_run_reports

        write_pipeline_post_run_reports(
            results=results,
            repo_root=repo_root,
            project_name=project_name,
            skip_infra=skip_infra,
        )
        return 0 if all(r.success for r in results) else 1
    except Exception as exc:
        logger.error("Pipeline execution failed: %s", exc)
        return 1


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Execute research project pipeline")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--skip-infra", action="store_true", help="Skip infrastructure tests")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM stages")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--core-only", action="store_true", help="Run core pipeline only (no LLM)")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Enable incremental stage skipping when stage inputs/outputs are unchanged (opt-in; default off)",
    )
    parser.add_argument(
        "--hitl-mode",
        default="full-auto",
        choices=["full-auto", "gate-only", "checkpoint", "custom"],
        help="Human-in-the-loop pause policy",
    )
    parser.add_argument(
        "--hitl-command",
        choices=[
            "status",
            "history",
            "context",
            "validate-response",
            "respond",
            "approve",
            "reject",
            "guide",
            "resume",
        ],
        help="Run a non-interactive HITL command and exit",
    )
    parser.add_argument("--hitl-stage", type=int, help="Stage number for HITL guide commands")
    parser.add_argument("--response-file", help="Detached HITL response JSON path")
    parser.add_argument("--message", default="", help="Message for HITL approve/reject/guide/resume commands")
    parser.add_argument(
        "--stage",
        # Derived from the registry so this help and the dispatch table cannot diverge.
        help="Run a single stage and exit (%s)" % ", ".join(sorted(known_stage_keys())),
    )

    raw_args = parser.parse_args()
    args = PipelineArgs(
        project=raw_args.project,
        skip_infra=raw_args.skip_infra,
        skip_llm=raw_args.skip_llm,
        resume=raw_args.resume,
        core_only=raw_args.core_only,
        incremental=raw_args.incremental,
        stage=raw_args.stage,
        hitl_mode=raw_args.hitl_mode,
        hitl_command=raw_args.hitl_command,
        hitl_stage=raw_args.hitl_stage,
        response_file=raw_args.response_file,
        message=raw_args.message,
    )

    log_header(f"Pipeline: {args.project}", logger)
    if args.stage:
        return execute_single_stage(args.stage, args.project, repo_root)
    if args.hitl_command:
        return handle_hitl_command(args, repo_root)

    result = execute_pipeline(
        project_name=args.project,
        repo_root=repo_root,
        skip_infra=args.skip_infra,
        skip_llm=args.skip_llm,
        resume=args.resume,
        core_only=args.core_only,
        hitl_mode=args.hitl_mode,
        incremental=args.incremental,
    )
    if result == 0:
        log_success(f"Pipeline complete: {args.project}", logger)
    return result


if __name__ == "__main__":
    sys.exit(main())

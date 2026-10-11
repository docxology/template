#!/usr/bin/env python3
"""Execute research project pipeline stages.

Thin orchestrator over PipelineExecutor, post-run reporting, and HITL CLI.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.hitl_cli import PipelineArgs, handle_hitl_command
from infrastructure.core.pipeline.incremental import IncrementalConfig
from infrastructure.core.pipeline.single_stage import execute_single_stage
from infrastructure.core.pipeline.stage_registry import known_stage_keys
from infrastructure.core.runtime.environment import validate_interpreter
from infrastructure.orchestration.discovery import validate_project_slug

# Public imports for callers using the canonical runner module.
__all__ = ["PipelineArgs", "handle_hitl_command", "execute_pipeline", "execute_single_stage", "main"]

logger = get_logger(__name__)


def execute_pipeline(
    project_name: str,
    repo_root: Path,
    skip_infra: bool = False,
    resume: bool = False,
    mode: str = "core",
    hitl_mode: str = "full-auto",
    incremental: bool = False,
    *,
    pipeline_path: Path | None = None,
) -> int:
    """Execute pipeline for a single project."""
    execution_started = False
    try:
        if not isinstance(mode, str) or mode not in {"core", "live"}:
            raise ValueError(f"Invalid execution mode: {mode}")
        project_name = validate_project_slug(project_name, repo_root)
        validate_interpreter()
        config = PipelineConfig(
            project_name=project_name,
            repo_root=repo_root,
            skip_infra=skip_infra,
            mode=mode,
            resume=resume,
            hitl_mode=hitl_mode,
            incremental=IncrementalConfig(enabled=incremental),
            pipeline_path=pipeline_path,
        )
        deadline = time.monotonic() + config.run_timeout_seconds
        plan = compile_execution_plan(config)
        if time.monotonic() >= deadline:
            raise TimeoutError("Pipeline deadline expired during plan preflight")
        executor = PipelineExecutor(config)
        execution_started = True
        results = executor.execute_plan(plan, deadline_monotonic=deadline)
        if not results:
            logger.error("Pipeline produced no stage results; refusing an empty success")
            return 1
        return int(executor.run_result(results).exit_code)
    except KeyboardInterrupt:
        return 130
    except TimeoutError as exc:
        logger.error("Pipeline deadline expired: %s", exc)
        return 124
    except ValueError as exc:
        logger.error("Invalid pipeline invocation: %s", exc)
        return 1 if execution_started else 2
    except Exception as exc:
        logger.error("Pipeline execution failed: %s", exc)
        return 1


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Execute research project pipeline")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--skip-infra", action="store_true", help="Skip infrastructure tests")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument(
        "--mode", choices=("core", "live"), default="core", help="Core local stages or explicit live stages"
    )
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
    parser.add_argument(
        "--pipeline-yaml",
        type=Path,
        help="Explicit pipeline definition; takes precedence over project and repository defaults.",
    )

    raw_args = parser.parse_args()
    args = PipelineArgs(
        project=raw_args.project,
        skip_infra=raw_args.skip_infra,
        resume=raw_args.resume,
        mode=raw_args.mode,
        incremental=raw_args.incremental,
        pipeline_path=str(raw_args.pipeline_yaml) if raw_args.pipeline_yaml is not None else None,
        stage=raw_args.stage,
        hitl_mode=raw_args.hitl_mode,
        hitl_command=raw_args.hitl_command,
        hitl_stage=raw_args.hitl_stage,
        response_file=raw_args.response_file,
        message=raw_args.message,
    )

    log_header(f"Pipeline: {args.project}", logger)
    if args.stage:
        return execute_single_stage(
            args.stage,
            args.project,
            repo_root,
            pipeline_path=args.pipeline_path,
            mode=args.mode,
        )
    if args.hitl_command:
        return handle_hitl_command(args, repo_root)

    result = execute_pipeline(
        project_name=args.project,
        repo_root=repo_root,
        skip_infra=args.skip_infra,
        resume=args.resume,
        mode=args.mode,
        hitl_mode=args.hitl_mode,
        incremental=args.incremental,
        pipeline_path=Path(args.pipeline_path) if args.pipeline_path is not None else None,
    )
    if result == 0:
        log_success(f"Pipeline complete: {args.project}", logger)
    return result


if __name__ == "__main__":
    sys.exit(main())

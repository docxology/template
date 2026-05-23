#!/usr/bin/env python3
"""Execute research project pipeline stages.

This script provides pipeline execution functionality extracted from run.sh
into testable Python code following the thin orchestrator pattern.
"""

from __future__ import annotations

import sys
import json
from dataclasses import dataclass
from pathlib import Path

# Bootstrap: put repo root on sys.path so `infrastructure` is importable when
# this script is invoked directly (`python scripts/execute_pipeline.py`). The
# equivalent idempotent helper `scripts.ensure_repo_root_on_path()` is available
# to callers that already have the `scripts` package on sys.path.
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.runtime.environment import get_python_command, validate_interpreter

logger = get_logger(__name__)

_STAGE_TO_SCRIPT: dict[str, list[str]] = {
    "clean": [
        "scripts/00_setup_environment.py"
    ],  # setup script also validates dirs; clean is handled in PipelineExecutor
    "setup": ["scripts/00_setup_environment.py"],
    "infra_tests": ["scripts/01_run_tests.py", "--infra-only", "--verbose", "--infra-scope", "pipeline-smoke"],
    "project_tests": ["scripts/01_run_tests.py", "--project-only", "--verbose"],
    "tests": ["scripts/01_run_tests.py", "--verbose", "--infra-scope", "pipeline-smoke"],
    "analysis": ["scripts/02_run_analysis.py"],
    "render_pdf": ["scripts/03_render_pdf.py"],
    "validate": ["scripts/04_validate_output.py"],
    "copy": ["scripts/05_copy_outputs.py"],
    "llm_reviews": ["scripts/06_llm_review.py", "--reviews-only"],
    "llm_translations": ["scripts/06_llm_review.py", "--translations-only"],
    "executive_report": ["scripts/07_generate_executive_report.py"],
}


def execute_single_stage(stage: str, project_name: str, repo_root: Path) -> int:
    """Execute a single stage script in a subprocess.

    This is intentionally a thin wrapper around existing stage entry points.
    """
    stage_key = stage.strip().lower()
    if stage_key not in _STAGE_TO_SCRIPT:
        valid = ", ".join(sorted(_STAGE_TO_SCRIPT.keys()))
        raise SystemExit(f"Unknown stage '{stage}'. Valid: {valid}")

    script_and_args = _STAGE_TO_SCRIPT[stage_key]
    script_rel = script_and_args[0]
    extra_args = script_and_args[1:]

    # Most scripts support --project; executive report ignores it but accepts it.
    cmd = get_python_command() + [str(repo_root / script_rel)] + extra_args + ["--project", project_name]
    logger.info(f"Executing stage '{stage_key}' for project '{project_name}': {' '.join(cmd)}")

    import subprocess

    # Outer safety cap for the whole stage process (30 min). Per-script limits inside
    # scripts/02_run_analysis.py use ANALYSIS_SCRIPT_TIMEOUT_SEC / analysis_timeout
    # (default 7200 s per discovered script) — a different layer.
    result = subprocess.run(cmd, cwd=str(repo_root), check=False, timeout=1800)
    return result.returncode


def execute_pipeline(
    project_name: str,
    repo_root: Path,
    skip_infra: bool = False,
    skip_llm: bool = False,
    resume: bool = False,
    core_only: bool = False,
    hitl_mode: str = "full-auto",
) -> int:
    """Execute pipeline for a single project.

    Args:
        project_name: Name of the project to execute
        repo_root: Repository root path
        skip_infra: Whether to skip infrastructure tests
        skip_llm: Whether to skip LLM stages
        resume: Whether to resume from checkpoint
        core_only: Whether to run core pipeline only (no LLM)
        hitl_mode: Lightweight HITL policy (full-auto, gate-only, checkpoint, custom)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Validate interpreter hermeticity
        validate_interpreter()

        # Create pipeline configuration
        config = PipelineConfig(
            project_name=project_name,
            repo_root=repo_root,
            skip_infra=skip_infra,
            skip_llm=skip_llm,
            resume=resume,
            hitl_mode=hitl_mode,
        )

        # Execute pipeline
        executor = PipelineExecutor(config)

        if core_only:
            results = executor.execute_core_pipeline()
        else:
            results = executor.execute_full_pipeline()

        # Generate comprehensive pipeline report
        from infrastructure.core.pipeline.post_run_reporting import write_pipeline_post_run_reports

        write_pipeline_post_run_reports(
            results=results,
            repo_root=repo_root,
            project_name=project_name,
            skip_infra=skip_infra,
        )

        # Return appropriate exit code
        success = all(r.success for r in results)
        return 0 if success else 1

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return 1


@dataclass(frozen=True)
class PipelineArgs:
    """Frozen, typed CLI arguments for pipeline execution."""

    project: str
    skip_infra: bool = False
    skip_llm: bool = False
    resume: bool = False
    core_only: bool = False
    stage: str | None = None
    hitl_mode: str = "full-auto"
    hitl_command: str | None = None
    hitl_stage: int | None = None
    response_file: str | None = None
    message: str = ""


def handle_hitl_command(args: PipelineArgs, repo_root: Path) -> int:
    """Handle non-interactive HITL commands for a project output directory."""
    output_dir = repo_root / "projects" / args.project / "output"
    from infrastructure.core.pipeline.control import load_pipeline_control_config

    default_yaml = repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    project_yaml = repo_root / "projects" / args.project / "pipeline.yaml"
    control = load_pipeline_control_config(
        default_yaml if default_yaml.exists() else None,
        project_yaml=project_yaml if project_yaml.exists() else None,
        cli_hitl_mode=args.hitl_mode,
    )
    controller = HitlController(project_output_dir=output_dir, control=control)

    if args.hitl_command == "status":
        print(json.dumps(controller.status(), indent=2, sort_keys=True))
        return 0
    if args.hitl_command == "history":
        print(json.dumps(controller.history(), indent=2, sort_keys=True))
        return 0
    if args.hitl_command == "context":
        print(json.dumps(controller.agent_context(), indent=2, sort_keys=True))
        return 0
    if args.hitl_command == "validate-response":
        if args.response_file is None:
            raise SystemExit("--response-file is required for --hitl-command validate-response")
        from infrastructure.core.pipeline.hitl import validate_agent_response_file

        validation = validate_agent_response_file(Path(args.response_file))
        print(
            json.dumps(
                {"valid": validation.valid, "issues": list(validation.issues), "payload": validation.payload},
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if validation.valid else 1
    if args.hitl_command == "respond":
        if args.response_file is None:
            raise SystemExit("--response-file is required for --hitl-command respond")
        print(json.dumps(controller.respond_from_file(Path(args.response_file)), indent=2, sort_keys=True))
        return 0
    if args.hitl_command == "approve":
        controller.approve(message=args.message)
        return 0
    if args.hitl_command == "reject":
        controller.reject(message=args.message)
        return 0
    if args.hitl_command == "resume":
        controller.resume(message=args.message)
        return 0
    if args.hitl_command == "guide":
        if args.hitl_stage is None:
            raise SystemExit("--hitl-stage is required for --hitl-command guide")
        if not args.message:
            raise SystemExit("--message is required for --hitl-command guide")
        controller.guide(stage_num=args.hitl_stage, message=args.message)
        return 0
    raise SystemExit(f"Unknown HITL command: {args.hitl_command}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Execute research project pipeline")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--skip-infra", action="store_true", help="Skip infrastructure tests")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM stages")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--core-only", action="store_true", help="Run core pipeline only (no LLM)")
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
        help="Run a single stage and exit (setup, infra_tests, project_tests, analysis, render_pdf, validate, copy, llm_reviews, llm_translations, executive_report)",  # noqa: E501
    )

    raw_args = parser.parse_args()
    args = PipelineArgs(
        project=raw_args.project,
        skip_infra=raw_args.skip_infra,
        skip_llm=raw_args.skip_llm,
        resume=raw_args.resume,
        core_only=raw_args.core_only,
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
    )
    if result == 0:
        log_success(f"Pipeline complete: {args.project}", logger)
    return result


if __name__ == "__main__":
    sys.exit(main())

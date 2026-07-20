"""Non-interactive HITL CLI for pipeline execution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source


@dataclass(frozen=True)
class PipelineArgs:
    """Frozen, typed CLI arguments for pipeline execution."""

    project: str
    skip_infra: bool = False
    skip_llm: bool = False
    resume: bool = False
    core_only: bool = False
    incremental: bool = False
    pipeline_path: str | None = None
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

    default_yaml = resolve_pipeline_source(
        repo_root,
        explicit_path=args.pipeline_path,
        purpose=PipelinePurpose.EXECUTION,
    ).path
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

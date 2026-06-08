"""Ordered phase helpers for the AutoResearch loop orchestrator."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.autoresearch import AutoResearchPlan
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    write_evidence_registry_report,
)

from .config import AutoResearchLoopConfig
from .diagnostics import diagnostic_bundle
from .manuscript_variables import write_manuscript_hydration_artifacts
from .ml.task import MLTaskResult
from .models import AutoResearchLoopResult
from .writers import (
    refresh_loop_payloads,
    write_artifact_manifest,
    write_autoresearch_phase_ledger,
    write_final_visual_artifacts,
    write_loop_bound_figures,
    write_research_object_manifest,
    write_schema_manifest,
)
from .security import write_security_artifacts


@dataclass(frozen=True)
class LoopRunContext:
    """Mutable loop state shared across phase handlers."""

    project_root: Path
    repo_root: Path
    project_name: str
    plan: AutoResearchPlan
    config: AutoResearchLoopConfig
    stage_results: tuple[Any, ...]
    generated_at: str
    ml_result: MLTaskResult
    output_paths: list[Path]
    diagnostics: dict[str, Any]
    readiness_valid: bool = False


def append_paths(ctx: LoopRunContext, paths: list[Path] | Path) -> None:
    """Append one path or a list of paths to the context's running output list."""
    if isinstance(paths, Path):
        ctx.output_paths.append(paths)
        return
    ctx.output_paths.extend(paths)


def run_provisional_payload_phase(ctx: LoopRunContext, result: AutoResearchLoopResult) -> None:
    """Write the provisional loop payloads from the current (pre-readiness) result."""
    append_paths(ctx, refresh_loop_payloads(ctx.project_root, result))


def run_pre_readiness_visual_phase(ctx: LoopRunContext, result: AutoResearchLoopResult) -> None:
    """Emit loop-bound figures, optional security artifacts, and best-effort hydration."""
    append_paths(
        ctx,
        write_loop_bound_figures(
            ctx.project_root,
            result,
            ctx.ml_result,
            diagnostics=ctx.diagnostics,
        ),
    )
    if ctx.config.security_profile.enabled:
        append_paths(
            ctx,
            write_security_artifacts(
                ctx.project_root,
                ctx.config,
                ctx.output_paths,
                generated_at=ctx.generated_at,
                ml_result=ctx.ml_result,
            ),
        )
    append_paths(ctx, write_manuscript_hydration_artifacts(ctx.project_root, require_valid=False))


def run_final_payload_and_visual_phase(ctx: LoopRunContext, result: AutoResearchLoopResult) -> None:
    """Rewrite payloads, final figures, the evidence registry, and validated hydration."""
    append_paths(ctx, refresh_loop_payloads(ctx.project_root, result))
    append_paths(
        ctx,
        write_final_visual_artifacts(
            ctx.project_root,
            result,
            ctx.ml_result,
            diagnostics=ctx.diagnostics,
        ),
    )
    append_paths(
        ctx,
        write_evidence_registry_report(
            ctx.project_root / "output",
            build_project_evidence_registry(ctx.project_root),
        ),
    )
    append_paths(ctx, write_manuscript_hydration_artifacts(ctx.project_root, require_valid=True))


def run_settlement_manifest_phase(
    ctx: LoopRunContext,
    result: AutoResearchLoopResult,
    *,
    settlement_pass_count: int,
    write_final_manifest: bool,
) -> None:
    """Write the phase ledger, schema and research-object manifests, and final manifest."""
    append_paths(
        ctx,
        write_autoresearch_phase_ledger(
            ctx.project_root,
            result,
            ctx.output_paths,
            generated_at=ctx.generated_at,
            settlement_pass_count=settlement_pass_count,
        ),
    )
    append_paths(
        ctx,
        write_schema_manifest(ctx.project_root, ctx.output_paths, generated_at=ctx.generated_at),
    )
    append_paths(
        ctx,
        write_research_object_manifest(ctx.project_root, ctx.output_paths, generated_at=ctx.generated_at),
    )
    if write_final_manifest:
        append_paths(ctx, write_artifact_manifest(ctx.project_root, ctx.output_paths))


def build_loop_context(
    project_root: Path,
    repo_root: Path,
    project_name: str,
    plan: AutoResearchPlan,
    config: AutoResearchLoopConfig,
    stage_results: tuple[Any, ...],
    generated_at: str,
    ml_result: MLTaskResult,
    output_paths: list[Path],
) -> LoopRunContext:
    """Assemble the shared loop context, computing the diagnostic bundle once."""
    return LoopRunContext(
        project_root=project_root,
        repo_root=repo_root,
        project_name=project_name,
        plan=plan,
        config=config,
        stage_results=stage_results,
        generated_at=generated_at,
        ml_result=ml_result,
        output_paths=output_paths,
        diagnostics=diagnostic_bundle(project_root, ml_result),
    )


PhaseHandler = Callable[[LoopRunContext, AutoResearchLoopResult], None]

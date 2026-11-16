"""Ordered phase helpers for the AutoResearch loop orchestrator."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.autoresearch import AutoResearchPlan, AutoResearchReport, validate_autoresearch_plan
from infrastructure.core.files.portability import sanitize_machine_local_paths
from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory, output_inventory_mode_for_project
from infrastructure.autoresearch.models import AutoResearchIssue
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    write_evidence_registry_report,
)

from .config import AutoResearchLoopConfig
from ..diagnostics import diagnostic_bundle
from ..manuscript.manuscript_variables import write_manuscript_hydration_artifacts
from ..ml.task import MLTaskResult
from .models import AutoResearchLoopResult
from ..writers import (
    refresh_loop_payloads,
    relative_path,
    write_artifact_manifest,
    write_autoresearch_phase_ledger,
    write_final_visual_artifacts,
    write_method_contract_artifacts,
    write_research_object_manifest,
    write_schema_manifest,
)
from ..security import write_security_artifacts


@dataclass(frozen=True)
class LoopRunContext:
    """Mutable loop state shared across ordered phase handlers.

    The context is frozen so no phase can accidentally replace top-level
    fields; mutable state is limited to ``output_paths`` (a list) which
    phases append to as they produce artifacts.

    ``diagnostics`` is computed once by :func:`build_loop_context` from the
    deterministic ML result and reused by all figure-writing phases to avoid
    redundant computation.
    """

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


PhaseHandler = Callable[[LoopRunContext, AutoResearchLoopResult], None]


def append_paths(ctx: LoopRunContext, paths: list[Path] | Path) -> None:
    """Append one path or a list of paths to the context's running output list.

    Accepts both a single :class:`~pathlib.Path` and a ``list[Path]`` so
    phase handlers can forward the return value of any writer without an
    ``isinstance`` check at every call site.
    """
    if isinstance(paths, Path):
        ctx.output_paths.append(paths)
        return
    ctx.output_paths.extend(paths)


def final_output_path_payload(
    project_root: Path, output_paths: list[Path], required_artifacts: tuple[str, ...]
) -> tuple[str, ...]:
    """Return stable output paths for the JSON loop payload."""
    return tuple(
        dict.fromkeys(
            (
                *(relative_path(project_root, path) for path in output_paths),
                *(artifact for artifact in required_artifacts if (project_root / artifact).is_file()),
            )
        )
    )


def combine_readiness_reports(
    readiness_pre: AutoResearchReport,
    readiness_post: AutoResearchReport,
    project_name: str,
) -> AutoResearchReport:
    """Process combine readiness reports."""
    issues: list[AutoResearchIssue] = [*readiness_pre.issues, *readiness_post.issues]
    valid = readiness_pre.valid and readiness_post.valid
    plan = readiness_post.plan or readiness_pre.plan
    return AutoResearchReport(
        project_name=project_name,
        valid=valid,
        issues=tuple(issues),
        plan=plan,
    )


def write_readiness_manifest(project_root: Path, repo_root: Path) -> Path:
    """Refresh the exact lifecycle-aware manifest after artifacts settle."""
    return write_artifact_manifest(project_root, repo_root=repo_root)


def run_provisional_payload_phase(ctx: LoopRunContext, result: AutoResearchLoopResult) -> None:
    """Write the provisional loop payloads from the current (pre-readiness) result."""
    append_paths(ctx, refresh_loop_payloads(ctx.project_root, result))


def run_method_contract_phase(ctx: LoopRunContext) -> None:
    """Write research-program, idea ledger, run ledger, and benchmark artifacts."""
    append_paths(
        ctx,
        write_method_contract_artifacts(
            ctx.project_root,
            ctx.config,
            generated_at=ctx.generated_at,
            ml_result=ctx.ml_result,
        ),
    )


def run_pre_readiness_visual_phase(ctx: LoopRunContext, result: AutoResearchLoopResult) -> None:
    """Emit loop-bound figures, optional security artifacts, and best-effort hydration."""
    sanitize_machine_local_paths(ctx.project_root / "output")
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
    append_paths(
        ctx,
        write_final_visual_artifacts(
            ctx.project_root, result, ctx.ml_result, diagnostics=ctx.diagnostics,
        ),
    )
    append_paths(ctx, write_manuscript_hydration_artifacts(ctx.project_root, require_valid=False))


def run_pre_readiness_settlement_phase(ctx: LoopRunContext, result: AutoResearchLoopResult) -> None:
    """Close membership and materialize provisional catalogs before preflight."""
    close_output_membership(ctx)
    run_settlement_manifest_phase(ctx, result, settlement_pass_count=1, write_final_manifest=False)
    append_paths(ctx, write_readiness_manifest(ctx.project_root, ctx.repo_root))


def resolve_extrinsic_readiness(
    plan: AutoResearchPlan,
    project_root: Path,
    ctx: LoopRunContext,
    readiness_pre: AutoResearchReport,
) -> tuple[bool, AutoResearchReport]:
    """Read the genuine preflight verdict without checksum retry or error suppression."""
    readiness_post = validate_autoresearch_plan(plan, project_root, phase="extrinsic")
    readiness_valid = readiness_pre.valid and readiness_post.valid
    readiness_report = combine_readiness_reports(readiness_pre, readiness_post, plan.project_name)
    return readiness_valid, readiness_report


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
        write_research_object_manifest(ctx.project_root, ctx.output_paths, generated_at=ctx.generated_at),
    )
    append_paths(
        ctx,
        write_schema_manifest(ctx.project_root, ctx.output_paths, generated_at=ctx.generated_at),
    )
    if write_final_manifest:
        append_paths(ctx, write_artifact_manifest(ctx.project_root, repo_root=ctx.repo_root))


def run_post_readiness_final_phases(ctx: LoopRunContext, final: AutoResearchLoopResult) -> None:
    """Materialize the candidate once, then take the sole complete byte snapshot last."""
    run_final_payload_and_visual_phase(ctx, final)
    run_settlement_manifest_phase(ctx, final, settlement_pass_count=2, write_final_manifest=False)
    append_paths(ctx, write_manuscript_hydration_artifacts(ctx.project_root, require_valid=final.readiness_valid))
    append_paths(ctx, write_artifact_manifest(ctx.project_root, repo_root=ctx.repo_root))


def close_output_membership(ctx: LoopRunContext) -> None:
    """Freeze unique intended paths, including inherited evidence and later catalogs."""
    mode = output_inventory_mode_for_project(ctx.repo_root, ctx.project_root)
    inventory = collect_stable_output_inventory(ctx.project_root / "output", inventory_mode=mode)
    planned = (
        "output/data/autoresearch_phase_ledger.json",
        "output/data/autoresearch_schema_manifest.json",
        "output/data/research_object_manifest.json",
        "output/reports/artifact_manifest.json",
        "output/reports/autoresearch_readiness.json",
        "output/reports/autoresearch_readiness.md",
    )
    ctx.output_paths[:] = sorted({
        *(path.resolve() for path in ctx.output_paths),
        *inventory.files,
        *(ctx.project_root / name for name in planned),
    })


def run_pre_extrinsic_phases(ctx: LoopRunContext, pre_readiness: AutoResearchLoopResult) -> None:
    """Execute the ordered pre-extrinsic phase sequence."""
    for handler in PRE_EXTRINSIC_PHASES:
        handler(ctx, pre_readiness)


PRE_EXTRINSIC_PHASES: tuple[PhaseHandler, ...] = (
    run_provisional_payload_phase,
    run_pre_readiness_visual_phase,
    run_pre_readiness_settlement_phase,
)


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

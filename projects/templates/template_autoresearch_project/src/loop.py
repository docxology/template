"""Deterministic AutoResearch loop orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from infrastructure.autoresearch import (
    AutoResearchReport,
    build_autoresearch_plan,
    validate_autoresearch_plan,
    write_autoresearch_report,
)
from infrastructure.autoresearch.models import AutoResearchIssue
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    write_evidence_registry_report,
)

from .artifact_content import is_substantive_artifact
from .config import AutoResearchLoopConfig, build_loop_config, load_human_review, load_manuscript_loop_settings
from .loop_phases import (
    build_loop_context,
    run_final_payload_and_visual_phase,
    run_pre_readiness_visual_phase,
    run_provisional_payload_phase,
    run_settlement_manifest_phase,
)
from .ml.task import MLTaskResult, run_bounded_ml_task
from .models import AutoResearchClaim, AutoResearchLoopResult, LoopStageResult
from .writers import (
    relative_path,
    write_artifact_manifest,
    write_core_loop_artifacts,
    write_method_contract_artifacts,
    write_ml_task_artifacts,
    write_research_object_manifest,
    write_schema_manifest,
)

__all__ = [
    "AutoResearchClaim",
    "AutoResearchLoopResult",
    "LoopStageResult",
    "build_claims",
    "build_stage_results",
    "run_autoresearch_loop",
]


def run_autoresearch_loop(project_root: Path, repo_root: Path | None = None) -> AutoResearchLoopResult:
    """Run the full deterministic AutoResearch loop for this exemplar.

    Args:
        project_root: Path to the project directory whose loop is executed.
        repo_root: Optional repository root; defaults to the project's third parent.

    Returns:
        AutoResearchLoopResult snapshot of the completed loop (stages, claims,
        readiness verdict, and existence-filtered output paths).
    """
    project_root = project_root.resolve()
    repo_root = (repo_root or project_root.parents[2]).resolve()
    project_name = project_root.name
    plan = build_autoresearch_plan(repo_root, project_name)
    settings = load_manuscript_loop_settings(project_root)
    human_review = load_human_review(project_root / "human_review.yaml")
    config = build_loop_config(plan, settings, human_review=human_review)
    readiness_pre = validate_autoresearch_plan(plan, project_root, phase="intrinsic")
    stage_results = build_stage_results(config, plan_stage_count=len(plan.stages))
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    output_paths: list[Path] = []
    output_paths.extend(
        write_core_loop_artifacts(
            project_root,
            plan.to_dict(),
            config,
            stage_results,
            generated_at,
            project_name,
        )
    )
    output_paths.append(
        write_evidence_registry_report(
            project_root / "output",
            build_project_evidence_registry(project_root),
        )
    )
    ml_result = run_bounded_ml_task(project_root, config.budget_policy)
    output_paths.extend(write_ml_task_artifacts(project_root, ml_result, generated_at=generated_at))

    ctx = build_loop_context(
        project_root,
        repo_root,
        project_name,
        plan,
        config,
        stage_results,
        generated_at,
        ml_result,
        output_paths,
    )

    claims = build_claims(config, project_root)
    provisional = _loop_result(
        project_name,
        generated_at,
        config,
        stage_results,
        claims,
        readiness_valid=False,
        output_paths=(),
        ml_result=ml_result,
    )
    run_provisional_payload_phase(ctx, provisional)
    ctx.output_paths.extend(
        write_method_contract_artifacts(project_root, config, generated_at=generated_at, ml_result=ml_result)
    )

    pre_readiness = _loop_result(
        project_name,
        generated_at,
        config,
        stage_results,
        claims,
        readiness_valid=False,
        output_paths=_final_output_path_payload(project_root, ctx.output_paths, config.required_artifacts),
        ml_result=ml_result,
    )
    run_provisional_payload_phase(ctx, pre_readiness)
    run_pre_readiness_visual_phase(ctx, pre_readiness)
    ctx.output_paths.append(_write_readiness_manifest(project_root, ctx.output_paths))
    ctx.output_paths.append(write_schema_manifest(project_root, ctx.output_paths, generated_at=generated_at))
    ctx.output_paths.append(write_research_object_manifest(project_root, ctx.output_paths, generated_at=generated_at))
    run_settlement_manifest_phase(ctx, pre_readiness, settlement_pass_count=2, write_final_manifest=False)
    ctx.output_paths.append(_write_readiness_manifest(project_root, ctx.output_paths))

    readiness_post = validate_autoresearch_plan(plan, project_root, phase="extrinsic")
    if _only_changed_artifact_manifest_issues(readiness_post):
        ctx.output_paths.append(_write_readiness_manifest(project_root, ctx.output_paths))
        readiness_post = validate_autoresearch_plan(plan, project_root, phase="extrinsic")
    readiness_valid = readiness_pre.valid and readiness_post.valid
    readiness_report = _combine_readiness_reports(readiness_pre, readiness_post, plan.project_name)
    ctx.output_paths.extend(write_autoresearch_report(project_root, readiness_report))
    claims = build_claims(config, project_root)

    final = _loop_result(
        project_name,
        generated_at,
        config,
        stage_results,
        claims,
        readiness_valid=readiness_valid,
        output_paths=_final_output_path_payload(project_root, ctx.output_paths, config.required_artifacts),
        ml_result=ml_result,
    )
    run_final_payload_and_visual_phase(ctx, final)
    run_settlement_manifest_phase(ctx, final, settlement_pass_count=3, write_final_manifest=True)

    return _loop_result(
        project_name,
        generated_at,
        config,
        stage_results,
        claims,
        readiness_valid=readiness_valid,
        output_paths=tuple(dict.fromkeys(relative_path(project_root, path) for path in ctx.output_paths)),
        ml_result=ml_result,
    )


def _loop_result(
    project_name: str,
    generated_at: str,
    config: AutoResearchLoopConfig,
    stage_results: tuple[LoopStageResult, ...],
    claims: tuple[AutoResearchClaim, ...],
    *,
    readiness_valid: bool,
    output_paths: tuple[str, ...] | tuple[()],
    ml_result: MLTaskResult,
) -> AutoResearchLoopResult:
    """Assemble an AutoResearchLoopResult snapshot from the supplied loop state."""
    return AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=claims,
        readiness_valid=readiness_valid,
        output_paths=output_paths,
        ml_task=ml_result.to_summary_dict(),
    )


def build_stage_results(config: AutoResearchLoopConfig, *, plan_stage_count: int) -> tuple[LoopStageResult, ...]:
    """Declare deterministic loop stages without claiming pipeline execution."""
    stage_actions = {
        "plan": f"Declared {plan_stage_count} pipeline stage contract(s).",
        "gate": "Declared exact stage-gate names from autoresearch.yaml.",
        "experiment": "Ran the fixed-seed bounded ML-loop candidate evaluation.",
        "evidence": "Declared local domain, experiment, pipeline, and output evidence targets.",
        "claims": "Mapped configured questions to on-disk evidence paths.",
        "artifacts": "Declared machine-readable data and human-readable report outputs.",
        "readiness": "Scheduled intrinsic and extrinsic AutoResearch readiness checks.",
    }
    results: list[LoopStageResult] = []
    for stage in config.loop_stages:
        results.append(
            LoopStageResult(
                name=stage,
                status="declared",
                evidence=stage_actions.get(stage, "Declared deterministic loop stage."),
                suggested_action="review generated reports",
            )
        )
    return tuple(results)


def build_claims(config: AutoResearchLoopConfig, project_root: Path) -> tuple[AutoResearchClaim, ...]:
    """Build claims supported only by evidence files that carry real content."""
    claims: list[AutoResearchClaim] = []
    for question in config.research_questions:
        evidence_path = question.expected_evidence
        claims.append(
            AutoResearchClaim(
                identifier=question.identifier,
                statement=f"{question.question} Evidence is grounded in `{evidence_path}`.",
                evidence_path=evidence_path,
                supported=is_substantive_artifact(project_root / evidence_path),
            )
        )
    return tuple(claims)


def _final_output_path_payload(
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


def _combine_readiness_reports(
    readiness_pre: AutoResearchReport,
    readiness_post: AutoResearchReport,
    project_name: str,
) -> AutoResearchReport:
    issues: list[AutoResearchIssue] = [*readiness_pre.issues, *readiness_post.issues]
    valid = readiness_pre.valid and readiness_post.valid
    plan = readiness_post.plan or readiness_pre.plan
    return AutoResearchReport(
        project_name=project_name,
        valid=valid,
        issues=tuple(issues),
        plan=plan,
    )


def _only_changed_artifact_manifest_issues(report: AutoResearchReport) -> bool:
    """Return true when readiness only needs a manifest checksum refresh."""
    if report.valid or not report.issues:
        return False
    return all(
        issue.code == "AUTORESEARCH.ARTIFACT_MANIFEST_ISSUE" and issue.message.startswith("changed artifact:")
        for issue in report.issues
    )


def _write_readiness_manifest(project_root: Path, output_paths: list[Path]) -> Path:
    """Refresh the pre-readiness manifest after generated artifacts settle."""
    manifest_path = write_artifact_manifest(project_root, output_paths, exclude_volatile=True)
    return write_artifact_manifest(project_root, [*output_paths, manifest_path], exclude_volatile=True)

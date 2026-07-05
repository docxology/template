"""Deterministic AutoResearch loop orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from infrastructure.autoresearch import (
    build_autoresearch_plan,
    validate_autoresearch_plan,
    write_autoresearch_report,
)
from infrastructure.core.determinism import resolve_source_date_epoch
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    write_evidence_registry_report,
)

from .artifact_content import is_substantive_artifact
from .config import AutoResearchLoopConfig, build_loop_config, load_human_review, load_manuscript_loop_settings
from .loop_phases import (
    build_loop_context,
    final_output_path_payload as _final_output_path_payload,
    resolve_extrinsic_readiness,
    run_method_contract_phase,
    run_post_readiness_final_phases,
    run_pre_extrinsic_phases,
    run_provisional_payload_phase,
)
from .ml.task import MLTaskResult, run_bounded_ml_task
from .models import AutoResearchClaim, AutoResearchLoopResult, LoopStageResult
from .writers import (
    relative_path,
    write_core_loop_artifacts,
    write_ml_task_artifacts,
)

# Re-export phase helpers for tests and gate negative controls.

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
    # Deterministic (HEAD commit time) in TEMPLATE_DETERMINISTIC / SOURCE_DATE_EPOCH
    # mode so the emitted artifacts are byte-stable across runs; wall-clock otherwise.
    # Keep the historical +00:00 isoformat (timespec=seconds) shape the writers expect.
    _epoch = resolve_source_date_epoch(repo_root=project_root)
    _moment = datetime.fromtimestamp(_epoch, tz=timezone.utc) if _epoch is not None else datetime.now(timezone.utc)
    generated_at = _moment.isoformat(timespec="seconds")

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
    run_method_contract_phase(ctx)

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
    run_pre_extrinsic_phases(ctx, pre_readiness)

    readiness_valid, readiness_report = resolve_extrinsic_readiness(plan, project_root, ctx, readiness_pre)
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
    run_post_readiness_final_phases(ctx, final)

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
    # WHY: status is always "declared" — the loop records intent-based stage contracts,
    # not pipeline execution proof.  Live pipeline steps produce their own artifacts.
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
    """Build claims supported only by evidence files that carry real content.

    A claim is ``supported=True`` only when its configured ``expected_evidence``
    path points to a file with substantive, parseable content (non-empty, non-null
    JSON, or non-empty CSV with data rows).  An empty file, ``{}``, ``[]``, a
    header-only CSV, or an unparseable artifact does NOT support the claim.

    This binding is shared with the figure-quality and benchmark gates via
    :func:`src.artifact_content.is_substantive_artifact` and is locked by
    negative-control tests in ``tests/test_gate_negative_controls.py``.
    """
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

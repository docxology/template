"""Deterministic AutoResearch loop orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
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

from .config import AutoResearchLoopConfig, build_loop_config, load_manuscript_loop_settings
from .ml_task import run_bounded_ml_task
from .models import AutoResearchClaim, AutoResearchLoopResult, LoopStageResult
from .writers import (
    finalize_loop_payloads,
    relative_path,
    update_result_payloads,
    write_artifact_manifest,
    write_core_loop_artifacts,
    write_ml_task_artifacts,
    write_method_contract_artifacts,
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
    """Run the full deterministic AutoResearch loop for this exemplar."""
    project_root = project_root.resolve()
    repo_root = (repo_root or project_root.parents[1]).resolve()
    project_name = project_root.name
    plan = build_autoresearch_plan(repo_root, project_name)
    settings = load_manuscript_loop_settings(project_root)
    config = build_loop_config(plan, settings)
    readiness_pre = validate_autoresearch_plan(plan, project_root, phase="intrinsic")
    stage_results = build_stage_results(config, plan_stage_count=len(plan.stages))
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")

    output_paths = write_core_loop_artifacts(
        project_root,
        plan.to_dict(),
        config,
        stage_results,
        generated_at,
        project_name,
    )
    output_paths.append(
        write_evidence_registry_report(
            project_root / "output",
            build_project_evidence_registry(project_root),
        )
    )
    ml_result = run_bounded_ml_task(project_root, config.budget_policy)
    output_paths.extend(write_ml_task_artifacts(project_root, ml_result, generated_at=generated_at))

    claims = build_claims(config, project_root)
    provisional = AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=claims,
        readiness_valid=False,
        output_paths=(),
        ml_task=ml_result.to_summary_dict(),
    )
    output_paths.extend(finalize_loop_payloads(project_root, provisional))
    output_paths.extend(
        write_method_contract_artifacts(project_root, config, generated_at=generated_at, ml_result=ml_result)
    )

    final_paths = _final_output_path_payload(project_root, output_paths)
    final = AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=claims,
        readiness_valid=False,
        output_paths=final_paths,
        ml_task=ml_result.to_summary_dict(),
    )
    output_paths.extend(update_result_payloads(project_root, final))
    output_paths.append(write_artifact_manifest(project_root, output_paths))

    readiness_post = validate_autoresearch_plan(plan, project_root, phase="extrinsic")
    readiness_valid = readiness_pre.valid and readiness_post.valid
    readiness_report = _combine_readiness_reports(readiness_pre, readiness_post, plan.project_name)
    output_paths.extend(write_autoresearch_report(project_root, readiness_report))
    claims = build_claims(config, project_root)

    final_paths = _final_output_path_payload(project_root, output_paths)
    final = AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=claims,
        readiness_valid=readiness_valid,
        output_paths=final_paths,
        ml_task=ml_result.to_summary_dict(),
    )
    output_paths.extend(update_result_payloads(project_root, final))
    output_paths.append(
        write_evidence_registry_report(
            project_root / "output",
            build_project_evidence_registry(project_root),
        )
    )
    output_paths.append(write_artifact_manifest(project_root, output_paths))
    return AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=claims,
        readiness_valid=readiness_valid,
        output_paths=tuple(dict.fromkeys(relative_path(project_root, path) for path in output_paths)),
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
    """Build claims supported only by files that exist on disk."""
    claims: list[AutoResearchClaim] = []
    for question in config.research_questions:
        evidence_path = question.expected_evidence
        claims.append(
            AutoResearchClaim(
                identifier=question.identifier,
                statement=f"{question.question} Evidence is grounded in `{evidence_path}`.",
                evidence_path=evidence_path,
                supported=(project_root / evidence_path).exists(),
            )
        )
    return tuple(claims)


def _final_output_path_payload(project_root: Path, output_paths: list[Path]) -> tuple[str, ...]:
    """Return stable output paths for the JSON loop payload."""
    expected_final_paths = (
        "output/data/autoresearch_loop.json",
        "output/data/autoresearch_claims.json",
        "output/data/autoresearch_review_packet.json",
        "output/data/research_program.json",
        "output/data/idea_ledger.json",
        "output/data/run_ledger.json",
        "output/data/review_decisions.json",
        "output/data/benchmark_scores.json",
        "output/data/ml_task_results.json",
        "output/data/ml_candidate_ledger.json",
        "output/data/manuscript_variables.json",
        "output/reports/autoresearch_loop.json",
        "output/reports/autoresearch_loop.md",
        "output/reports/autoresearch_readiness.json",
        "output/reports/autoresearch_readiness.md",
        "output/reports/autoresearch_review_packet.md",
        "output/reports/autoresearch_summary.md",
        "output/reports/artifact_manifest.json",
        "output/reports/evidence_registry.json",
        "output/reports/benchmark_readiness_smoke.json",
        "output/reports/ml_experiment_report.md",
        "output/reports/ml_benchmark_score.json",
        "output/figures/ml_candidate_scores.png",
    )
    return tuple(
        dict.fromkeys(
            (
                *(relative_path(project_root, path) for path in output_paths),
                *expected_final_paths,
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

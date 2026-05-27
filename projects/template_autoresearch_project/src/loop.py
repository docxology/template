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

from .artifact_content import is_substantive_artifact
from .config import AutoResearchLoopConfig, build_loop_config, load_human_review, load_manuscript_loop_settings
from .manuscript_variables import write_manuscript_hydration_artifacts
from .ml_task import run_bounded_ml_task
from .models import AutoResearchClaim, AutoResearchLoopResult, LoopStageResult
from .writers import (
    finalize_loop_payloads,
    relative_path,
    update_result_payloads,
    write_autoresearch_phase_ledger,
    write_artifact_manifest,
    write_core_loop_artifacts,
    write_final_visual_artifacts,
    write_ml_task_artifacts,
    write_method_contract_artifacts,
    write_research_object_manifest,
    write_schema_manifest,
)
from .security import write_security_artifacts

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
    human_review = load_human_review(project_root / "human_review.yaml")
    config = build_loop_config(plan, settings, human_review=human_review)
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

    final_paths = _final_output_path_payload(project_root, output_paths, config.required_artifacts)
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
    if config.security_profile.enabled:
        output_paths.extend(write_security_artifacts(project_root, config, output_paths, generated_at=generated_at))
    output_paths.extend(write_final_visual_artifacts(project_root, final, ml_result))
    output_paths.extend(write_manuscript_hydration_artifacts(project_root, require_valid=False))
    output_paths.append(_write_readiness_manifest(project_root, output_paths))
    if config.security_profile.enabled:
        output_paths.extend(write_security_artifacts(project_root, config, output_paths, generated_at=generated_at))
    output_paths.append(write_schema_manifest(project_root, output_paths, generated_at=generated_at))
    output_paths.append(write_research_object_manifest(project_root, output_paths, generated_at=generated_at))
    output_paths.append(
        write_autoresearch_phase_ledger(
            project_root,
            final,
            output_paths,
            generated_at=generated_at,
            settlement_pass_count=2,
        )
    )
    output_paths.append(_write_readiness_manifest(project_root, output_paths))

    readiness_post = validate_autoresearch_plan(plan, project_root, phase="extrinsic")
    if _only_changed_artifact_manifest_issues(readiness_post):
        output_paths.append(_write_readiness_manifest(project_root, output_paths))
        readiness_post = validate_autoresearch_plan(plan, project_root, phase="extrinsic")
    readiness_valid = readiness_pre.valid and readiness_post.valid
    readiness_report = _combine_readiness_reports(readiness_pre, readiness_post, plan.project_name)
    output_paths.extend(write_autoresearch_report(project_root, readiness_report))
    claims = build_claims(config, project_root)

    final_paths = _final_output_path_payload(project_root, output_paths, config.required_artifacts)
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
    output_paths.extend(write_final_visual_artifacts(project_root, final, ml_result))
    output_paths.append(
        write_evidence_registry_report(
            project_root / "output",
            build_project_evidence_registry(project_root),
        )
    )
    output_paths.extend(write_manuscript_hydration_artifacts(project_root, require_valid=True))
    if config.security_profile.enabled:
        output_paths.extend(write_security_artifacts(project_root, config, output_paths, generated_at=generated_at))
    output_paths.append(
        write_autoresearch_phase_ledger(
            project_root,
            final,
            output_paths,
            generated_at=generated_at,
            settlement_pass_count=3,
        )
    )
    output_paths.append(write_schema_manifest(project_root, output_paths, generated_at=generated_at))
    output_paths.append(write_research_object_manifest(project_root, output_paths, generated_at=generated_at))
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
    """Build claims supported only by evidence files that carry real content.

    Support is bound to substance, not existence: an empty, header-only, or
    unparseable evidence file does not support its claim (see
    ``is_substantive_artifact``). This closes the prior fail-open where any
    present file — even a 0-byte placeholder — marked a research question
    "supported".
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


def _final_output_path_payload(
    project_root: Path, output_paths: list[Path], required_artifacts: tuple[str, ...]
) -> tuple[str, ...]:
    """Return stable output paths for the JSON loop payload.

    The expected set is derived from the project's declared ``required_artifacts``
    contract (``autoresearch.yaml``) — the single source of truth — rather than a
    hand-maintained tuple. This eliminates the drift class where the loop's
    self-reported paths silently diverged from what validation actually requires.

    Contract artifacts are included only if they actually exist on disk, so the
    self-report cannot overclaim a required artifact that was never written; a
    genuinely-missing artifact is therefore absent here (and still independently
    caught by the readiness gate and manifest consumers that re-check existence).
    """
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

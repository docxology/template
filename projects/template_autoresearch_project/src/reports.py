"""Markdown and structured report renderers for the AutoResearch loop."""

from __future__ import annotations

import csv
import io

from .ml_task import MLTaskResult
from .models import AutoResearchLoopResult


def render_loop_markdown(result: AutoResearchLoopResult) -> str:
    """Render the human-readable loop report."""
    lines = [
        "# AutoResearch Loop Report",
        "",
        f"- Project: `{result.project_name}`",
        f"- Topic: {result.config.topic}",
        f"- Readiness valid: `{str(result.readiness_valid).lower()}`",
        f"- Supported claims: {result.supported_claim_count}",
        "",
    ]
    if result.ml_task:
        lines.extend(
            [
                "## ML Task",
                "",
                f"- Accepted candidate: `{result.ml_task.get('accepted_candidate_id', 'N/A')}`",
                f"- Baseline accuracy: {result.ml_task.get('baseline_accuracy', 'N/A')}",
                f"- Best accuracy: {result.ml_task.get('best_accuracy', 'N/A')}",
                f"- Accuracy delta: {result.ml_task.get('accuracy_delta', 'N/A')}",
                "",
            ]
        )
    lines.extend(["## Stages", ""])
    for stage in result.stage_results:
        lines.append(f"- `{stage.name}`: {stage.status} - {stage.evidence}")
    lines.extend(["", "## Claims", ""])
    for claim in result.claims:
        status = "supported" if claim.supported else "unsupported"
        lines.append(f"- `{claim.identifier}` ({status}): {claim.statement}")
    lines.append("")
    return "\n".join(lines)


def render_stage_matrix_csv(result: AutoResearchLoopResult) -> str:
    """Render the stage matrix as CSV."""
    stream = io.StringIO()
    writer = csv.DictWriter(
        stream,
        fieldnames=("stage", "status", "evidence", "suggested_action"),
        lineterminator="\n",
    )
    writer.writeheader()
    for stage in result.stage_results:
        writer.writerow(
            {
                "stage": stage.name,
                "status": stage.status,
                "evidence": stage.evidence,
                "suggested_action": stage.suggested_action,
            }
        )
    return stream.getvalue()


def build_review_packet(result: AutoResearchLoopResult) -> dict[str, object]:
    """Build the machine-readable human review packet."""
    all_claims_supported = all(claim.supported for claim in result.claims)
    return {
        "project_name": result.project_name,
        "generated_at": result.generated_at,
        "topic": result.config.topic,
        "human_review": {
            "policy": result.config.review_policy,
            "ready_for_review": result.readiness_valid and all_claims_supported,
            "required_review_decision": "approve, revise, or block before publication",
        },
        "configuration": result.config.to_dict(),
        "stage_results": [stage.to_dict() for stage in result.stage_results],
        "claims": [claim.to_dict() for claim in result.claims],
        "metrics": {
            "stage_count": len(result.stage_results),
            "supported_claim_count": result.supported_claim_count,
            "readiness_valid": result.readiness_valid,
        },
        "next_actions": review_next_actions(result),
        "output_paths": list(result.output_paths),
    }


def review_next_actions(result: AutoResearchLoopResult) -> list[str]:
    """Return required human review actions."""
    if result.readiness_valid and result.supported_claim_count == len(result.claims):
        return [
            "Review the evidence registry against manuscript claims.",
            "Inspect the artifact manifest before copying final outputs.",
            "Record the human review decision outside generated artifacts.",
        ]
    return [
        "Resolve AutoResearch readiness issues.",
        "Regenerate the loop outputs.",
        "Repeat human review after readiness passes.",
    ]


def render_review_packet_markdown(result: AutoResearchLoopResult) -> str:
    """Render the human review packet."""
    packet = build_review_packet(result)
    human_review = packet["human_review"]
    assert isinstance(human_review, dict)
    lines = [
        "# AutoResearch Human Review Packet",
        "",
        f"- Project: `{result.project_name}`",
        f"- Topic: {result.config.topic}",
        f"- Policy: `{human_review['policy']}`",
        f"- Ready for review: `{str(human_review['ready_for_review']).lower()}`",
        "",
        "## Review Questions",
        "",
    ]
    for claim in result.claims:
        status = "supported" if claim.supported else "unsupported"
        lines.append(f"- `{claim.identifier}` ({status}) -> `{claim.evidence_path}`")
    lines.extend(["", "## Required Actions", ""])
    for action in review_next_actions(result):
        lines.append(f"- {action}")
    lines.append("")
    return "\n".join(lines)


def render_summary_markdown(result: AutoResearchLoopResult) -> str:
    """Render the short project summary."""
    lines = [
        "# AutoResearch Summary",
        "",
        f"`{result.project_name}` declared {len(result.stage_results)} AutoResearch loop stages.",
        f"Readiness status: `{str(result.readiness_valid).lower()}`.",
        f"Supported claims: {result.supported_claim_count} of {len(result.claims)}.",
        f"Required artifacts: {len(result.config.required_artifacts)}.",
    ]
    if result.ml_task:
        lines.extend(
            [
                f"Accepted ML-loop candidate: `{result.ml_task.get('accepted_candidate_id', 'N/A')}`.",
                f"Accuracy delta over baseline: `{result.ml_task.get('accuracy_delta', 'N/A')}`.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def render_ml_experiment_report(result: MLTaskResult) -> str:
    """Render the deterministic ML-loop experiment report."""
    lines = [
        "# Deterministic ML-Loop Experiment",
        "",
        f"- Task: {result.task_name}",
        f"- Seed: {result.dataset.seed}",
        f"- Train/test size: {result.dataset.train_size}/{result.dataset.test_size}",
        f"- Baseline accuracy: {result.baseline.accuracy:.3f}",
        f"- Accepted candidate: `{result.accepted_candidate_id}`",
        f"- Best accuracy: {result.best_accuracy:.3f}",
        f"- Accuracy delta: {result.accuracy_delta:.3f}",
        f"- Candidate budget exhausted: `{str(result.budget_exhausted).lower()}`",
        f"- LLM calls used: {result.llm_calls_used}",
        f"- Cost used: {result.cost_usd_used:.2f}",
        "",
        "## Candidate Ledger",
        "",
        "| Candidate | Status | Feature map | Alpha | Accuracy | Delta |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for candidate in result.candidates:
        accuracy = "N/A" if candidate.accuracy is None else f"{candidate.accuracy:.3f}"
        delta = "N/A" if candidate.accuracy_delta_vs_baseline is None else f"{candidate.accuracy_delta_vs_baseline:.3f}"
        lines.append(
            f"| `{candidate.identifier}` | {candidate.status} | {candidate.feature_map} | "
            f"{candidate.alpha:g} | {accuracy} | {delta} |"
        )
    lines.extend(
        [
            "",
            "This report is generated from deterministic local data. It does not call an external model, "
            "execute generated code, or approve the manuscript.",
            "",
        ]
    )
    return "\n".join(lines)

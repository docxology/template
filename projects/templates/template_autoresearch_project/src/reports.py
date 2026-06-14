"""Markdown and structured report renderers for the AutoResearch loop."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .ml.task import MLTaskResult
from .models import AutoResearchLoopResult
from .source_ledger import (
    load_source_ledger,
    source_age_summary,
    source_tier_counts,
    validate_source_ledger_contract,
)

_BENCHMARK_BOUNDARY_SCHEMA = "template-autoresearch-benchmark-boundary-v1"


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
    human_review_state = result.config.human_review
    return {
        "schema": "template-autoresearch-review-packet-v1",
        "project_name": result.project_name,
        "generated_at": result.generated_at,
        "topic": result.config.topic,
        "human_review": {
            "policy": result.config.review_policy,
            "ready_for_review": result.readiness_valid and all_claims_supported,
            "publication_approved": human_review_state.publication_approved,
            "decision_source": human_review_state.source_path,
            "decision_source_exists": human_review_state.source_exists,
            "reviewer": human_review_state.reviewer,
            "reviewed_at": human_review_state.reviewed_at,
            "required_review_decision": "approve, defer, or reject before publication",
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
        f"- Publication approved: `{str(human_review['publication_approved']).lower()}`",
        f"- Decision source: `{human_review['decision_source']}`",
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


def build_evidence_overview(project_root: Path, result: AutoResearchLoopResult) -> dict[str, object]:
    """Build a reviewer-facing evidence overview without granting approval."""
    packet = build_review_packet(result)
    human_review = packet["human_review"]
    assert isinstance(human_review, dict)
    ledger_path = project_root / "manuscript" / "source_ledger.yaml"
    if ledger_path.is_file():
        entries = load_source_ledger(ledger_path)
        ledger_issues = validate_source_ledger_contract(project_root)
    else:
        entries = ()
        ledger_issues = ["missing manuscript/source_ledger.yaml"]
    benchmark_boundary_path = project_root / "output" / "data" / "benchmark_boundary.json"
    benchmark_boundary = _load_json(benchmark_boundary_path)
    benchmark_boundary_issues = _benchmark_boundary_issues(benchmark_boundary_path, benchmark_boundary)
    review_decisions = _load_json(project_root / "output" / "data" / "review_decisions.json")
    file_publication_approved = bool(review_decisions.get("publication_approved", False))
    file_review_source_exists = bool(review_decisions.get("human_review_source_exists", False))
    config_publication_approved = result.config.human_review.publication_approved
    config_review_source_exists = result.config.human_review.source_exists
    security_threat_model = _load_json(project_root / "output" / "data" / "security_threat_model.json")
    security_inventory = _load_json(project_root / "output" / "data" / "security_artifact_inventory.json")
    return {
        "schema": "template-autoresearch-evidence-overview-v1",
        "project_name": result.project_name,
        "generated_at": result.generated_at,
        "review_state": {
            "ready_for_review": human_review["ready_for_review"],
            "publication_approved": human_review["publication_approved"],
            "approval_boundary": "generated outputs can be ready for review but cannot self-approve publication",
            "decision_source": human_review["decision_source"],
        },
        "claims": [
            {
                "id": claim.identifier,
                "supported": claim.supported,
                "evidence_path": claim.evidence_path,
                "statement": claim.statement,
            }
            for claim in result.claims
        ],
        "source_ledger": {
            "path": "manuscript/source_ledger.yaml",
            "entry_count": len(entries),
            "tier_counts": source_tier_counts(entries),
            "checked_age_buckets": source_age_summary(entries),
            "issues": ledger_issues,
            "offline_only": True,
        },
        "benchmark_boundary": {
            "path": "output/data/benchmark_boundary.json",
            "schema": benchmark_boundary.get("schema", ""),
            "metric": benchmark_boundary.get("metric", {}),
            "fixture_scope": benchmark_boundary.get("fixture_scope", {}),
            "statistical_methods": benchmark_boundary.get("statistical_methods", []),
            "non_claims": benchmark_boundary.get("non_claims", []),
            "issues": benchmark_boundary_issues,
        },
        "security_integrity": {
            "review_decisions_schema": review_decisions.get("schema", ""),
            "generated_self_approval": (file_publication_approved and not file_review_source_exists)
            or (config_publication_approved and not config_review_source_exists),
            "threat_model_schema": security_threat_model.get("schema", ""),
            "artifact_inventory_schema": security_inventory.get("schema", ""),
            "offline_only": True,
        },
    }


def render_evidence_overview_markdown(project_root: Path, result: AutoResearchLoopResult) -> str:
    """Render the reviewer evidence overview."""
    overview = build_evidence_overview(project_root, result)
    review_state = overview["review_state"]
    source_ledger = overview["source_ledger"]
    benchmark = overview["benchmark_boundary"]
    security = overview["security_integrity"]
    assert isinstance(review_state, dict)
    assert isinstance(source_ledger, dict)
    assert isinstance(benchmark, dict)
    assert isinstance(security, dict)
    lines = [
        "# AutoResearch Evidence Overview",
        "",
        f"- Ready for review: `{str(review_state['ready_for_review']).lower()}`",
        f"- Publication approved: `{str(review_state['publication_approved']).lower()}`",
        f"- Approval boundary: {review_state['approval_boundary']}",
        "",
        "## Claims",
        "",
    ]
    claims = overview["claims"]
    assert isinstance(claims, list)
    for claim in claims:
        assert isinstance(claim, dict)
        status = "supported" if claim["supported"] else "unsupported"
        lines.append(f"- `{claim['id']}` ({status}) -> `{claim['evidence_path']}`")
    lines.extend(
        [
            "",
            "## Source Ledger",
            "",
            f"- Entries: {source_ledger['entry_count']}",
            f"- Tiers: `{json.dumps(source_ledger['tier_counts'], sort_keys=True)}`",
            f"- Checked-age buckets: `{json.dumps(source_ledger['checked_age_buckets'], sort_keys=True)}`",
            f"- Issues: `{len(source_ledger['issues'])}`",
            "",
            "## Benchmark Boundary",
            "",
            f"- Path: `{benchmark['path']}`",
            f"- Metric: `{json.dumps(benchmark['metric'], sort_keys=True)}`",
            f"- Statistical methods: `{len(benchmark['statistical_methods'])}`",
            f"- Non-claims: `{len(benchmark['non_claims'])}`",
            f"- Issues: `{len(benchmark['issues'])}`",
            "",
            "## Security And Integrity",
            "",
            f"- Generated self-approval: `{str(security['generated_self_approval']).lower()}`",
            f"- Offline only: `{str(security['offline_only']).lower()}`",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _benchmark_boundary_issues(path: Path, payload: dict[str, object]) -> list[str]:
    issues: list[str] = []
    if not path.is_file():
        issues.append("missing output/data/benchmark_boundary.json")
    if payload.get("schema") != _BENCHMARK_BOUNDARY_SCHEMA:
        issues.append("benchmark_boundary.json schema mismatch")
    fixture_scope = payload.get("fixture_scope")
    if not isinstance(fixture_scope, dict):
        issues.append("benchmark_boundary.json fixture_scope is missing")
    else:
        if fixture_scope.get("offline_only") is not True:
            issues.append("benchmark_boundary.json does not assert offline_only=true")
        if fixture_scope.get("network_access") is not False:
            issues.append("benchmark_boundary.json does not assert network_access=false")
    if not isinstance(payload.get("non_claims"), list) or not payload.get("non_claims"):
        issues.append("benchmark_boundary.json lacks explicit non_claims")
    if not isinstance(payload.get("statistical_methods"), list) or not payload.get("statistical_methods"):
        issues.append("benchmark_boundary.json lacks statistical_methods")
    return issues


def render_ml_experiment_report(result: MLTaskResult) -> str:
    """Render the deterministic ML-loop experiment report."""
    lines = [
        "# Deterministic ML-Loop Experiment",
        "",
        f"- Task: {result.task_config.name}",
        f"- Seed: {result.task_config.seed}",
        f"- Train/test size: {result.dataset.train_size}/{result.dataset.test_size}",
        f"- Baseline accuracy: {result.baseline.test_accuracy:.3f}",
        f"- Accepted candidate: `{result.accepted_candidate_id}`",
        f"- Best accuracy: {result.best_accuracy:.3f}",
        f"- Accuracy delta: {result.accuracy_delta:.3f}",
        f"- Candidate budget exhausted: `{str(result.budget_exhausted).lower()}`",
        f"- LLM calls used: {result.llm_calls_used}",
        f"- Cost used: {result.cost_usd_used:.2f}",
        "",
        "## Candidate Ledger",
        "",
        "| Candidate | Status | Model | Parameters | Accuracy | Delta |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for candidate in result.candidates:
        accuracy = "N/A" if candidate.test_accuracy is None else f"{candidate.test_accuracy:.3f}"
        delta = "N/A" if candidate.accuracy_delta_vs_baseline is None else f"{candidate.accuracy_delta_vs_baseline:.3f}"
        lines.append(
            f"| `{candidate.identifier}` | {candidate.status} | {candidate.model_type} | "
            f"{candidate.parameter_count} | {accuracy} | {delta} |"
        )
    lines.extend(
        [
            "",
            "## Training Diagnostics",
            "",
            "Epoch-level metrics are written to `output/data/ml_training_history.csv`; training summaries "
            "are written to `output/data/ml_training_diagnostics.json`; accepted-candidate error examples "
            "are written to `output/data/ml_error_examples.json`. Probability records, "
            "classification diagnostics, calibration bins, and robustness smoke-test rows are written to "
            "`output/data/ml_prediction_records.json`, `output/data/ml_classification_diagnostics.json`, "
            "`output/data/ml_calibration_report.json`, `output/data/ml_robustness_report.json`, "
            "`output/data/ml_probability_diagnostics.json`, `output/data/ml_bootstrap_intervals.json`, and "
            "`output/data/ml_paired_comparison.json`, plus `output/data/ml_statistical_summary.json`.",
            "",
            "This report is generated from deterministic local data. It does not call an external model, "
            "execute generated code, or approve the manuscript.",
            "",
        ]
    )
    return "\n".join(lines)

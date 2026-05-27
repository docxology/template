"""Diagnostic bundle, boundary, selection-audit, and JSON writer units."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .diagnostics_intervals import (
    bootstrap_intervals,
    candidate_accuracy_intervals,
    candidate_rank_stability,
    paired_comparison_report,
)
from .diagnostics_metrics import (
    calibration_bin_intervals,
    calibration_report,
    class_balance_report,
    classification_diagnostics,
    probability_diagnostics,
    robustness_report,
    statistical_summary,
    training_diagnostics,
)
from .diagnostics_records import _evaluated_candidates, prediction_records
from .ml_task import MLTaskResult


def candidate_selection_audit(
    project_root: Path,
    result: MLTaskResult,
    *,
    statistical: dict[str, object] | None = None,
    intervals: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return ranking and tie-break evidence for evaluated candidate selection."""
    intervals = intervals or candidate_accuracy_intervals(result)
    statistical_payload = statistical or statistical_summary(project_root, result)
    interval_by_id = {
        str(row.get("candidate_id", "")): row for row in _mapping_list(intervals.get("rows")) if row.get("candidate_id")
    }
    quality_by_id = {
        str(row.get("candidate_id", "")): row
        for row in _mapping_list(statistical_payload.get("candidate_probability_quality"))
        if row.get("candidate_id")
    }
    ranked = sorted(
        _evaluated_candidates(result),
        key=lambda candidate: (
            -float(candidate.test_accuracy or 0.0),
            candidate.parameter_count,
            candidate.identifier,
        ),
    )
    rows: list[dict[str, object]] = []
    for rank, candidate in enumerate(ranked, start=1):
        interval = _mapping(interval_by_id.get(candidate.identifier))
        quality = _mapping(quality_by_id.get(candidate.identifier))
        rows.append(
            {
                "rank": rank,
                "candidate_id": candidate.identifier,
                "status": candidate.status,
                "objective_metric": result.task_config.metric_name,
                "test_accuracy": round(float(candidate.test_accuracy or 0.0), 6),
                "wilson_ci_low": _float_value(interval.get("ci_low")),
                "wilson_ci_high": _float_value(interval.get("ci_high")),
                "brier_score": _float_value(quality.get("brier_score")),
                "negative_log_likelihood": _float_value(quality.get("negative_log_likelihood")),
                "parameter_count": candidate.parameter_count,
                "tie_break_key": f"{candidate.parameter_count}:{candidate.identifier}",
                "accepted": candidate.identifier == result.accepted_candidate_id,
            }
        )
    return {
        "schema": "template-autoresearch-candidate-selection-audit-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "metric": result.task_config.metric_name,
        "direction": result.task_config.metric_direction,
        "rank_stability_source": "output/data/ml_candidate_rank_stability.json",
        "tie_break_order": ["metric", "lower_parameter_count", "candidate_id"],
        "rows": rows,
        "claim_boundary": "Selection is based on the configured objective metric; diagnostics are audit context.",
    }


def diagnostic_bundle(
    project_root: Path, result: MLTaskResult, *, resamples: int | None = None
) -> dict[str, dict[str, object]]:
    """Return all deterministic diagnostic payloads for a single ML task result."""
    predictions = prediction_records(project_root, result)
    classification = classification_diagnostics(result)
    intervals = candidate_accuracy_intervals(result)
    class_balance = class_balance_report(project_root, result)
    calibration = calibration_report(project_root, result, records_payload=predictions)
    calibration_intervals = calibration_bin_intervals(project_root, result, calibration=calibration)
    robustness = robustness_report(result)
    probability = probability_diagnostics(project_root, result, records_payload=predictions)
    bootstrap = bootstrap_intervals(project_root, result, resamples=resamples)
    paired = paired_comparison_report(project_root, result)
    statistical = statistical_summary(
        project_root,
        result,
        resamples=resamples,
        records_payload=predictions,
        classification=classification,
        calibration=calibration,
        bootstrap=bootstrap,
        paired=paired,
    )
    training = training_diagnostics(result)
    rank_stability = candidate_rank_stability(project_root, result, resamples=resamples)
    selection = candidate_selection_audit(project_root, result, statistical=statistical, intervals=intervals)
    boundary = diagnostic_boundary_report(result)
    return {
        "prediction_records": predictions,
        "classification_diagnostics": classification,
        "candidate_intervals": intervals,
        "class_balance": class_balance,
        "calibration_report": calibration,
        "calibration_bin_intervals": calibration_intervals,
        "robustness_report": robustness,
        "probability_diagnostics": probability,
        "bootstrap_intervals": bootstrap,
        "paired_comparison": paired,
        "statistical_summary": statistical,
        "training_diagnostics": training,
        "candidate_rank_stability": rank_stability,
        "candidate_selection_audit": selection,
        "diagnostic_boundary": boundary,
    }


def diagnostic_boundary_report(result: MLTaskResult) -> dict[str, object]:
    """Return claim-boundary rows separating selection, diagnostics, robustness, and non-claims."""
    rows = [
        {
            "surface": "objective_selection",
            "source_artifact": "output/data/ml_task_results.json",
            "method": "rank evaluated candidates by configured held-out metric and deterministic tie-breaks",
            "supports": "accepted-candidate selection within this fixed local task",
            "does_not_support": "full MNIST state-of-the-art, external benchmark leadership, or universal model quality",
        },
        {
            "surface": "descriptive_diagnostics",
            "source_artifact": "output/data/ml_classification_diagnostics.json",
            "method": "per-class metrics, calibration, probability quality, and paired comparison",
            "supports": "local error analysis and uncertainty description",
            "does_not_support": "population-level certification or deployment readiness",
        },
        {
            "surface": "robustness_smoke_test",
            "source_artifact": "output/data/ml_robustness_report.json",
            "method": "deterministic no-retrain transforms applied to the fixed test split",
            "supports": "small perturbation smoke-test evidence",
            "does_not_support": "adversarial robustness or distribution-shift robustness",
        },
        {
            "surface": "artifact_integrity",
            "source_artifact": "output/data/autoresearch_integrity_attestation.json",
            "method": "local SHA-256 checks over declared inputs and generated artifacts",
            "supports": "local artifact integrity evidence for the run",
            "does_not_support": "external signing, production SLSA compliance, or runtime intrusion detection",
        },
        {
            "surface": "review_governance",
            "source_artifact": "output/data/review_decisions.json",
            "method": "deferred generated review decisions with human review required",
            "supports": "readiness for human review",
            "does_not_support": "machine self-approval or publication acceptance",
        },
    ]
    return {
        "schema": "template-autoresearch-diagnostic-boundary-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "rows": rows,
        "claim_boundary": "Each diagnostic surface declares what it can and cannot support.",
    }


def write_prediction_records_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write probability-aware prediction records."""
    return _write_json(path, prediction_records(project_root, result))


def write_classification_diagnostics_json(path: Path, result: MLTaskResult) -> Path:
    """Write classification diagnostics."""
    return _write_json(path, classification_diagnostics(result))


def write_candidate_accuracy_intervals_json(path: Path, result: MLTaskResult) -> Path:
    """Write candidate accuracy Wilson intervals."""
    return _write_json(path, candidate_accuracy_intervals(result))


def write_class_balance_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write local fixture class-balance diagnostics."""
    return _write_json(path, class_balance_report(project_root, result))


def write_calibration_report_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write accepted-candidate calibration diagnostics."""
    return _write_json(path, calibration_report(project_root, result))


def write_calibration_bin_intervals_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write calibration-bin Wilson intervals."""
    return _write_json(path, calibration_bin_intervals(project_root, result))


def write_robustness_report_json(path: Path, result: MLTaskResult) -> Path:
    """Write deterministic robustness smoke-test metrics."""
    return _write_json(path, robustness_report(result))


def write_probability_diagnostics_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write accepted-candidate probability diagnostics."""
    return _write_json(path, probability_diagnostics(project_root, result))


def write_bootstrap_intervals_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write deterministic bootstrap intervals."""
    return _write_json(path, bootstrap_intervals(project_root, result))


def write_paired_comparison_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write matched baseline-vs-accepted comparison diagnostics."""
    return _write_json(path, paired_comparison_report(project_root, result))


def write_statistical_summary_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write run-level statistical summary diagnostics."""
    return _write_json(path, statistical_summary(project_root, result))


def write_training_diagnostics_json(path: Path, result: MLTaskResult) -> Path:
    """Write configured-training dynamics."""
    return _write_json(path, training_diagnostics(result))


def write_candidate_rank_stability_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write deterministic candidate rank-stability diagnostics."""
    return _write_json(path, candidate_rank_stability(project_root, result))


def write_candidate_selection_audit_json(path: Path, project_root: Path, result: MLTaskResult) -> Path:
    """Write candidate-selection audit context."""
    return _write_json(path, candidate_selection_audit(project_root, result))


def write_diagnostic_boundary_json(path: Path, result: MLTaskResult) -> Path:
    """Write diagnostic claim-boundary rows."""
    return _write_json(path, diagnostic_boundary_report(result))


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _float_value(value: object) -> float:
    return float(value) if isinstance(value, int | float | str) else 0.0


__all__ = [
    "candidate_selection_audit",
    "diagnostic_bundle",
    "diagnostic_boundary_report",
    "write_prediction_records_json",
    "write_classification_diagnostics_json",
    "write_candidate_accuracy_intervals_json",
    "write_class_balance_json",
    "write_calibration_report_json",
    "write_calibration_bin_intervals_json",
    "write_robustness_report_json",
    "write_probability_diagnostics_json",
    "write_bootstrap_intervals_json",
    "write_paired_comparison_json",
    "write_statistical_summary_json",
    "write_training_diagnostics_json",
    "write_candidate_rank_stability_json",
    "write_candidate_selection_audit_json",
    "write_diagnostic_boundary_json",
    "_write_json",
    "_mapping_list",
    "_mapping",
    "_float_value",
]

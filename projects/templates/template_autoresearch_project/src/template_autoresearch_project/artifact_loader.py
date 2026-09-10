"""Load loop output artifacts once for manuscript hydration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .json_coerce import mapping


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return mapping(json.loads(path.read_text(encoding="utf-8")))


def _load_optional_json(path: Path) -> dict[str, Any]:
    return _load_json(path)


@dataclass(frozen=True)
class LoopArtifacts:
    """In-memory bundle of loop JSON artifacts under ``output/``."""

    loop: dict[str, Any]
    ml: dict[str, Any]
    candidate_ledger: dict[str, Any]
    review_decisions: dict[str, Any]
    benchmark_scores: dict[str, Any]
    artifact_manifest: dict[str, Any]
    figure_registry: dict[str, Any]
    classification_diagnostics: dict[str, Any]
    candidate_intervals: dict[str, Any]
    class_balance: dict[str, Any]
    calibration_report: dict[str, Any]
    calibration_bin_intervals: dict[str, Any]
    robustness_report: dict[str, Any]
    probability_diagnostics: dict[str, Any]
    bootstrap_intervals: dict[str, Any]
    paired_comparison: dict[str, Any]
    statistical_summary: dict[str, Any]
    training_diagnostics: dict[str, Any]
    candidate_rank_stability: dict[str, Any]
    candidate_selection_audit: dict[str, Any]
    diagnostic_boundary: dict[str, Any]
    phase_ledger: dict[str, Any]
    figure_quality: dict[str, Any]
    security_profile: dict[str, Any]
    security_threat_model: dict[str, Any]
    security_inventory: dict[str, Any]
    security_attestation: dict[str, Any]
    schema_manifest: dict[str, Any]
    research_object_manifest: dict[str, Any]

    @property
    def output(self) -> Path:
        """Process output."""
        raise AttributeError("LoopArtifacts does not store project_root; pass output paths explicitly")


def load_loop_artifacts(project_root: Path, *, require_valid: bool = False) -> LoopArtifacts:
    """Load JSON artifacts from ``project_root/output``."""
    output = project_root / "output"
    loop_payload = _load_json(output / "data" / "autoresearch_loop.json")
    if require_valid:
        metrics = mapping(loop_payload.get("metrics"))
        if metrics.get("readiness_valid") is not True:
            raise ValueError("autoresearch_loop.json does not contain a valid final readiness state")
        readiness = _load_json(output / "reports" / "autoresearch_readiness.json")
        if readiness.get("valid") is not True:
            raise ValueError("autoresearch_readiness.json is missing or not valid")
        from .manuscript.manuscript_tokens_core import _validate_required_artifacts

        _validate_required_artifacts(project_root, loop_payload)

    data = output / "data"
    reports = output / "reports"
    figures = output / "figures"
    return LoopArtifacts(
        loop=loop_payload,
        ml=_load_optional_json(data / "ml_task_results.json"),
        candidate_ledger=_load_optional_json(data / "ml_candidate_ledger.json"),
        review_decisions=_load_optional_json(data / "review_decisions.json"),
        benchmark_scores=_load_optional_json(data / "benchmark_scores.json"),
        artifact_manifest=_load_optional_json(reports / "artifact_manifest.json"),
        figure_registry=_load_optional_json(figures / "figure_registry.json"),
        classification_diagnostics=_load_optional_json(data / "ml_classification_diagnostics.json"),
        candidate_intervals=_load_optional_json(data / "ml_candidate_intervals.json"),
        class_balance=_load_optional_json(data / "ml_class_balance.json"),
        calibration_report=_load_optional_json(data / "ml_calibration_report.json"),
        calibration_bin_intervals=_load_optional_json(data / "ml_calibration_bin_intervals.json"),
        robustness_report=_load_optional_json(data / "ml_robustness_report.json"),
        probability_diagnostics=_load_optional_json(data / "ml_probability_diagnostics.json"),
        bootstrap_intervals=_load_optional_json(data / "ml_bootstrap_intervals.json"),
        paired_comparison=_load_optional_json(data / "ml_paired_comparison.json"),
        statistical_summary=_load_optional_json(data / "ml_statistical_summary.json"),
        training_diagnostics=_load_optional_json(data / "ml_training_diagnostics.json"),
        candidate_rank_stability=_load_optional_json(data / "ml_candidate_rank_stability.json"),
        candidate_selection_audit=_load_optional_json(data / "ml_candidate_selection_audit.json"),
        diagnostic_boundary=_load_optional_json(data / "ml_diagnostic_boundary.json"),
        phase_ledger=_load_optional_json(data / "autoresearch_phase_ledger.json"),
        figure_quality=_load_optional_json(data / "figure_quality_report.json"),
        security_profile=_load_optional_json(data / "autoresearch_security_profile.json"),
        security_threat_model=_load_optional_json(data / "autoresearch_threat_model.json"),
        security_inventory=_load_optional_json(data / "autoresearch_supply_chain_inventory.json"),
        security_attestation=_load_optional_json(data / "autoresearch_integrity_attestation.json"),
        schema_manifest=_load_optional_json(data / "autoresearch_schema_manifest.json"),
        research_object_manifest=_load_optional_json(data / "research_object_manifest.json"),
    )

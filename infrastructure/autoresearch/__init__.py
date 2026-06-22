"""Deterministic AutoResearch planning and readiness validation."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AutoResearchConfig",
    "AutoResearchIssue",
    "AutoResearchPlan",
    "AutoResearchReport",
    "AutoResearchStage",
    "BenchmarkTask",
    "BudgetPolicy",
    "EvidenceLink",
    "EXTRINSIC_QUALITY_CHECKS",
    "ExperimentCandidate",
    "INTRINSIC_QUALITY_CHECKS",
    "ResearchIdea",
    "ResearchProgram",
    "ReviewGate",
    "RunLedger",
    "SecurityProfile",
    "ValidationPhase",
    "build_autoresearch_plan",
    "load_autoresearch_config",
    "mad_confidence",
    "metric_unit_from_name",
    "parse_string_sequence",
    "parse_metric_lines",
    "validate_autoresearch_overlay",
    "validate_autoresearch_plan",
    "write_autoresearch_report",
]

_EXPORTS = {
    "AutoResearchConfig": ("infrastructure.autoresearch.models", "AutoResearchConfig"),
    "AutoResearchIssue": ("infrastructure.autoresearch.models", "AutoResearchIssue"),
    "AutoResearchPlan": ("infrastructure.autoresearch.models", "AutoResearchPlan"),
    "AutoResearchReport": ("infrastructure.autoresearch.models", "AutoResearchReport"),
    "AutoResearchStage": ("infrastructure.autoresearch.models", "AutoResearchStage"),
    "BenchmarkTask": ("infrastructure.autoresearch.models", "BenchmarkTask"),
    "BudgetPolicy": ("infrastructure.autoresearch.models", "BudgetPolicy"),
    "EvidenceLink": ("infrastructure.autoresearch.models", "EvidenceLink"),
    "ExperimentCandidate": ("infrastructure.autoresearch.models", "ExperimentCandidate"),
    "ResearchIdea": ("infrastructure.autoresearch.models", "ResearchIdea"),
    "ResearchProgram": ("infrastructure.autoresearch.models", "ResearchProgram"),
    "ReviewGate": ("infrastructure.autoresearch.models", "ReviewGate"),
    "RunLedger": ("infrastructure.autoresearch.models", "RunLedger"),
    "SecurityProfile": ("infrastructure.autoresearch.models", "SecurityProfile"),
    "build_autoresearch_plan": ("infrastructure.autoresearch.planner", "build_autoresearch_plan"),
    "EXTRINSIC_QUALITY_CHECKS": (
        "infrastructure.autoresearch.validation",
        "EXTRINSIC_QUALITY_CHECKS",
    ),
    "INTRINSIC_QUALITY_CHECKS": (
        "infrastructure.autoresearch.validation",
        "INTRINSIC_QUALITY_CHECKS",
    ),
    "ValidationPhase": ("infrastructure.autoresearch.validation", "ValidationPhase"),
    "load_autoresearch_config": ("infrastructure.autoresearch.config", "load_autoresearch_config"),
    "mad_confidence": ("infrastructure.autoresearch.metrics", "mad_confidence"),
    "metric_unit_from_name": ("infrastructure.autoresearch.metrics", "metric_unit_from_name"),
    "parse_string_sequence": ("infrastructure.autoresearch.config", "parse_string_sequence"),
    "parse_metric_lines": ("infrastructure.autoresearch.metrics", "parse_metric_lines"),
    "validate_autoresearch_overlay": (
        "infrastructure.autoresearch.validation",
        "validate_autoresearch_overlay",
    ),
    "validate_autoresearch_plan": ("infrastructure.autoresearch.validation", "validate_autoresearch_plan"),
    "write_autoresearch_report": ("infrastructure.autoresearch.reports", "write_autoresearch_report"),
}


def __getattr__(name: str) -> Any:
    """Lazily resolve public AutoResearch symbols."""
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)

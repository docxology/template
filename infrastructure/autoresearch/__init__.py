"""Deterministic AutoResearch planning and readiness validation."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AutoResearchConfig",
    "AutoResearchIssue",
    "AutoResearchPlan",
    "AutoResearchReport",
    "AutoResearchStage",
    "EXTRINSIC_QUALITY_CHECKS",
    "INTRINSIC_QUALITY_CHECKS",
    "ValidationPhase",
    "build_autoresearch_plan",
    "load_autoresearch_config",
    "parse_string_sequence",
    "validate_autoresearch_plan",
    "write_autoresearch_report",
]

_EXPORTS = {
    "AutoResearchConfig": ("infrastructure.autoresearch.models", "AutoResearchConfig"),
    "AutoResearchIssue": ("infrastructure.autoresearch.models", "AutoResearchIssue"),
    "AutoResearchPlan": ("infrastructure.autoresearch.models", "AutoResearchPlan"),
    "AutoResearchReport": ("infrastructure.autoresearch.models", "AutoResearchReport"),
    "AutoResearchStage": ("infrastructure.autoresearch.models", "AutoResearchStage"),
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
    "parse_string_sequence": ("infrastructure.autoresearch.config", "parse_string_sequence"),
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

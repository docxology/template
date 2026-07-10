"""types.py — TypedDict definitions for template_pools_rules_tools.

All public return-type contracts for fonds_reader, rules_applier,
tools_invoker, and integration are declared here and re-exported from
the package root.

Importing from this module gives callers full type safety without
depending on any optional runtime library.
"""

from __future__ import annotations

import pathlib
from typing import TypedDict

__all__ = [
    # Fonds
    "BibliographyFondResult",
    "ContactsFondResult",
    "DatasetsFondResult",
    "AllFondsResult",
    "FondsSummary",
    # Rules
    "SoftRuleEntry",
    "StrongRuleEntry",
    "RuleSetResult",
    "AllRulesResult",
    # Tools
    "ToolEntry",
    "ToolValidationResult",
    "ToolEntryWithValidation",
    # Integration
    "IntegrationSummary",
    "IntegrationResult",
    "FigureDataRow",
]


# ---------------------------------------------------------------------------
# Fonds TypedDicts
# ---------------------------------------------------------------------------


class BibliographyFondResult(TypedDict):
    """Returned by ``read_bibliography_fond()`` on success."""

    manifest: object  # parsed fonds.yaml (any YAML structure)
    bib_text: str
    csv_rows: list[dict[str, str]]


class ContactsFondResult(TypedDict):
    """Returned by ``read_contacts_fond()`` on success."""

    manifest: object
    contacts: list[object]


class DatasetsFondResult(TypedDict):
    """Returned by ``read_datasets_fond()`` on success."""

    manifest: object
    datasets: list[object]


class AllFondsResult(TypedDict):
    """Returned by ``read_all_fonds()``."""

    bibliography: BibliographyFondResult | None
    contacts: ContactsFondResult | None
    datasets: DatasetsFondResult | None


class FondsSummary(TypedDict):
    """High-level counts produced by ``count_summary()``."""

    bibliography_entries: int
    contacts_count: int
    datasets_count: int
    fonds_loaded: int


# ---------------------------------------------------------------------------
# Rules TypedDicts
# ---------------------------------------------------------------------------


class SoftRuleEntry(TypedDict):
    """One entry from ``load_soft_rules()``."""

    filename: str
    content: str


class StrongRuleEntry(TypedDict):
    """One entry from ``load_strong_rules()``."""

    filename: str
    schema: object  # parsed YAML


class RuleSetResult(TypedDict):
    """Returned by ``validate_against_rules()``."""

    rule_set: str
    manifest: object | None
    soft_rules_count: int
    strong_rules_count: int
    soft_rules: list[str]
    strong_rules: list[str]
    soft_rules_loaded: list[str]
    strong_rules_loaded: list[str]
    status: str  # "ok" | "partial" | "missing"
    warnings: list[str]


class AllRulesResult(TypedDict):
    """Returned by ``load_all_project_rules()`` and ``load_all_manuscript_rules()``."""

    soft: list[SoftRuleEntry]
    strong: list[StrongRuleEntry]


# ---------------------------------------------------------------------------
# Tools TypedDicts
# ---------------------------------------------------------------------------


class ToolValidationResult(TypedDict):
    """Returned by ``validate_tool_scripts_exist()``."""

    tool: str
    entrypoints: list[str]
    missing: list[str]
    valid: bool


class ToolEntry(TypedDict):
    """One entry from ``discover_tools()`` (without validation)."""

    name: str
    path: pathlib.Path
    manifest: object | None


class ToolEntryWithValidation(TypedDict):
    """One entry from ``discover_tools()`` after validation is attached."""

    name: str
    path: pathlib.Path
    manifest: object | None
    validation: ToolValidationResult


# ---------------------------------------------------------------------------
# Integration TypedDicts
# ---------------------------------------------------------------------------


class IntegrationSummary(TypedDict):
    """High-level roll-up inside ``IntegrationResult``."""

    fonds_loaded: int
    rules_sets_ok: int
    rules_sets_total: int
    tools_discovered: int
    tools_valid: int
    bib_entries: int
    contacts: int
    datasets: int


class IntegrationResult(TypedDict):
    """Returned by ``run_integration_demo()``."""

    fonds: AllFondsResult
    rules: dict[str, RuleSetResult]
    tools: list[ToolEntryWithValidation]
    summary: IntegrationSummary


class FigureDataRow(TypedDict):
    """One row produced by ``generate_figure_data()``."""

    label: str
    count: int
    category: str  # "fond" | "rule_set" | "tool"
    status: str  # "ok" | "partial" | "missing" | "valid" | "invalid"


class CrossFondOverlapResult(TypedDict):
    """Returned by ``check_bibliography_overlap()``.

    Reports overlap counts only — never asserts full containment in either
    direction, since this project's own manuscript legitimately cites sources
    (software-engineering references) outside the curated fond, and the fond
    legitimately curates sources (e.g. GANs, LSTM) this manuscript never cites.
    """

    project_keys: list[str]
    fond_keys: list[str]
    overlap: list[str]
    project_only: list[str]
    fond_only: list[str]

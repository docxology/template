"""integration.py — Orchestrate fonds, rules, and tools into a combined demo.

``run_integration_demo()`` is the single entry point for the full demo.
It calls the three reader/validator modules and assembles their results into
a structured report dict suitable for JSON serialisation or manuscript
variable injection.
"""

from __future__ import annotations

import logging

from .fonds_reader import (
    read_bibliography_fond,
    read_contacts_fond,
    read_datasets_fond,
)
from .rules_applier import validate_against_rules
from .tools_invoker import discover_tools, validate_tool_scripts_exist
from .type_defs import (
    AllFondsResult,
    BibliographyFondResult,
    ContactsFondResult,
    DatasetsFondResult,
    FigureDataRow,
    IntegrationResult,
    IntegrationSummary,
    RuleSetResult,
    ToolEntryWithValidation,
)

__all__ = [
    "run_integration_demo",
    "generate_figure_data",
]

logger = logging.getLogger(__name__)

# Default rule sets exercised by the demo
_DEFAULT_RULE_SETS: list[str] = [
    "template_project_rules",
    "template_manuscript_rules",
]


def run_integration_demo() -> IntegrationResult:
    """Run the full integration demo and return a structured result dict.

    The returned :class:`IntegrationResult` has the following top-level keys:

    ``fonds``
      :class:`AllFondsResult` with ``bibliography``, ``contacts``, ``datasets``.
      Each value is the typed result dict for that fond, or ``None`` if absent.

    ``rules``
      Dict mapping rule-set name → :class:`RuleSetResult`.

    ``tools``
      List of :class:`ToolEntryWithValidation` dicts (one per discovered tool).

    ``summary``
      :class:`IntegrationSummary` with high-level counts and status roll-up.
    """
    # ------------------------------------------------------------------
    # Fonds
    # ------------------------------------------------------------------
    bib: BibliographyFondResult | None = read_bibliography_fond()
    contacts: ContactsFondResult | None = read_contacts_fond()
    datasets: DatasetsFondResult | None = read_datasets_fond()

    fonds = AllFondsResult(
        bibliography=bib,
        contacts=contacts,
        datasets=datasets,
    )

    bib_count: int = len(bib["csv_rows"]) if bib is not None else 0
    contacts_count: int = len(contacts["contacts"]) if contacts is not None else 0
    datasets_count: int = len(datasets["datasets"]) if datasets is not None else 0

    logger.info(
        "fonds: bibliography=%d entries, contacts=%d, datasets=%d",
        bib_count,
        contacts_count,
        datasets_count,
    )

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    rules_results: dict[str, RuleSetResult] = {}
    for rule_set in _DEFAULT_RULE_SETS:
        r: RuleSetResult = validate_against_rules(rule_set)
        rules_results[rule_set] = r
        logger.info(
            "rules[%s]: status=%s, soft=%d, strong=%d",
            rule_set,
            r["status"],
            r["soft_rules_count"],
            r["strong_rules_count"],
        )

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------
    raw_tools = discover_tools()
    tools_list: list[ToolEntryWithValidation] = []
    for tool_entry in raw_tools:
        validation = validate_tool_scripts_exist(tool_entry["name"])
        tools_list.append(
            ToolEntryWithValidation(
                name=tool_entry["name"],
                path=tool_entry["path"],
                manifest=tool_entry["manifest"],
                validation=validation,
            )
        )
    logger.info("tools: discovered %d tool(s)", len(tools_list))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    rules_ok = sum(1 for r in rules_results.values() if r["status"] == "ok")
    tools_valid = sum(1 for t in tools_list if t["validation"]["valid"])
    fonds_loaded = sum(1 for v in (bib, contacts, datasets) if v is not None)

    summary = IntegrationSummary(
        fonds_loaded=fonds_loaded,
        rules_sets_ok=rules_ok,
        rules_sets_total=len(_DEFAULT_RULE_SETS),
        tools_discovered=len(tools_list),
        tools_valid=tools_valid,
        bib_entries=bib_count,
        contacts=contacts_count,
        datasets=datasets_count,
    )

    return IntegrationResult(
        fonds=fonds,
        rules=rules_results,
        tools=tools_list,
        summary=summary,
    )


def generate_figure_data(result: IntegrationResult | None = None) -> list[FigureDataRow]:
    """Return a list of :class:`FigureDataRow` dicts suitable for plotting.

    Each row captures one measurable entity (fond, rule set, or tool) with a
    label, count, category, and status.

    If *result* is ``None``, :func:`run_integration_demo` is called internally.

    Typical use::

        rows = generate_figure_data()
        # Pass to matplotlib, pandas, or a JSON figure registry token.
    """
    if result is None:
        result = run_integration_demo()

    rows: list[FigureDataRow] = []

    # Fonds rows
    bib_fond = result["fonds"]["bibliography"]
    contacts_fond = result["fonds"]["contacts"]
    datasets_fond = result["fonds"]["datasets"]

    fond_rows: list[tuple[str, int, str]] = [
        (
            "bibliography",
            len(bib_fond["csv_rows"]) if bib_fond is not None else 0,
            "ok" if bib_fond is not None else "missing",
        ),
        (
            "contacts",
            len(contacts_fond["contacts"]) if contacts_fond is not None else 0,
            "ok" if contacts_fond is not None else "missing",
        ),
        (
            "datasets",
            len(datasets_fond["datasets"]) if datasets_fond is not None else 0,
            "ok" if datasets_fond is not None else "missing",
        ),
    ]
    for label, count, status in fond_rows:
        rows.append(FigureDataRow(label=label, count=count, category="fond", status=status))

    # Rules rows
    for rule_set_name, rule_result in result["rules"].items():
        count = rule_result["soft_rules_count"] + rule_result["strong_rules_count"]
        rows.append(
            FigureDataRow(
                label=rule_set_name,
                count=count,
                category="rule_set",
                status=rule_result["status"],
            )
        )

    # Tools rows
    for tool in result["tools"]:
        rows.append(
            FigureDataRow(
                label=tool["name"],
                count=len(tool["validation"]["entrypoints"]),
                category="tool",
                status="valid" if tool["validation"]["valid"] else "invalid",
            )
        )

    return rows

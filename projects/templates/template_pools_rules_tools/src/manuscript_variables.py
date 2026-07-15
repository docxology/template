"""manuscript_variables.py — Derive manuscript token values from the integration demo.

Shared by ``scripts/03_generate_manuscript.py`` (analysis-stage JSON export)
and ``scripts/z_generate_manuscript_variables.py`` (pre-render token
hydration + injection), so the token computation lives in exactly one place.
"""

from __future__ import annotations

from .integration import run_integration_demo

__all__ = ["generate_variables"]


def generate_variables(*, integration_runner=run_integration_demo) -> dict[str, str]:
    """Derive stringified manuscript token values from the integration demo results.

    Returns a flat ``{{UPPERCASE_KEY}}``-compatible mapping (all values
    stringified) suitable for
    :func:`infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree`.
    """
    results = integration_runner()
    summary = results["summary"]
    rules = results["rules"]

    variables: dict[str, object] = {
        "FONDS_LOADED": summary["fonds_loaded"],
        "RULES_SETS_OK": summary["rules_sets_ok"],
        "RULES_SETS_TOTAL": summary["rules_sets_total"],
        "TOOLS_DISCOVERED": summary["tools_discovered"],
        "TOOLS_VALID": summary["tools_valid"],
        "BIB_ENTRIES": summary["bib_entries"],
        "CONTACTS_COUNT": summary["contacts"],
        "DATASETS_COUNT": summary["datasets"],
        "STRONG_RULES_PROJECT": (
            rules["template_project_rules"]["strong_rules_count"]
            if "template_project_rules" in rules
            else 0
        ),
        "STRONG_RULES_MANUSCRIPT": (
            rules["template_manuscript_rules"]["strong_rules_count"]
            if "template_manuscript_rules" in rules
            else 0
        ),
        "TOOL_NAMES": ", ".join(t["name"] for t in results["tools"]),
    }

    return {key: str(value) for key, value in variables.items()}

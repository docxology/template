from __future__ import annotations

from .config import MadlibConfig
from .tokens import TokenPlan


def configured_field_inventory(config: MadlibConfig, plan: TokenPlan) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(config.explicit_paths | config.defaulted_paths):
        origin = "explicit" if path in config.explicit_paths else "defaulted"
        rows.append(
            {
                "path": path,
                "origin": origin,
                "scope": _field_scope(path),
                "summary": _field_summary(config, plan, path),
            }
        )
    return rows


def configured_field_counts(
    config: MadlibConfig,
    inventory: list[dict[str, str]],
) -> dict[str, int]:
    scopes = {scope: 0 for scope in ("schema", "section", "lexicon", "slot", "visualization")}
    for row in inventory:
        scopes[row["scope"]] = scopes.get(row["scope"], 0) + 1
    return {
        "total": len(inventory),
        "explicit": sum(1 for row in inventory if row["origin"] == "explicit"),
        "defaulted": sum(1 for row in inventory if row["origin"] == "defaulted"),
        "visualized": len(config.visualizations.enabled_flags),
        "section_level": scopes.get("section", 0),
        "lexicon_level": scopes.get("lexicon", 0),
        "slot_level": scopes.get("slot", 0),
        "visualization_level": scopes.get("visualization", 0),
        "schema_level": scopes.get("schema", 0),
    }


def _field_scope(path: str) -> str:
    if ".section_conditions." in path or ".section_titles." in path or ".narrative_moves." in path:
        return "section"
    if ".lexicon." in path:
        return "lexicon"
    if ".slots." in path:
        return "slot"
    if ".visualizations" in path:
        return "visualization"
    return "schema"


def _field_summary(config: MadlibConfig, plan: TokenPlan, path: str) -> str:
    if path == "madlib.seed":
        return str(config.seed)
    if path == "madlib.composition_depth":
        return str(config.composition_depth)
    if path == "madlib.hypothesis":
        return str(config.hypothesis)
    if path == "madlib.lexicon":
        return f"{len(config.lexicon)} categories"
    if path == "madlib.slots":
        return f"{len(config.slots)} slot rules, {len(plan.choices)} token choices"
    if path == "madlib.visualizations":
        return "enabled" if config.visualizations.enabled else "disabled"
    if path.startswith("madlib.section_conditions."):
        section = path.rsplit(".", 1)[-1]
        return "enabled" if config.section_conditions[section] else "disabled"
    if path.startswith("madlib.section_titles."):
        section = path.rsplit(".", 1)[-1]
        return str(config.section_titles[section])
    if path.startswith("madlib.narrative_moves."):
        section = path.rsplit(".", 1)[-1]
        return f"{len(config.narrative_moves[section])} moves"
    if path.startswith("madlib.lexicon."):
        category = path.rsplit(".", 1)[-1]
        return f"{len(config.lexicon.get(category, ()))} tokens"
    if path.startswith("madlib.visualizations."):
        field = path.rsplit(".", 1)[-1]
        return str(bool(getattr(config.visualizations, field))).lower()
    if path.startswith("madlib.slots."):
        return _slot_summary(config, path)
    block_counts = {
        "madlib.method_protocol": len(config.method_protocol),
        "madlib.evaluation_criteria": len(config.evaluation_criteria),
        "madlib.failure_modes": len(config.failure_modes),
        "madlib.design_principles": len(config.design_principles),
        "madlib.pipeline_phases": len(config.pipeline_phases),
        "madlib.quality_probes": len(config.quality_probes),
        "madlib.authoring_obligations": len(config.authoring_obligations),
        "madlib.audit_rules": len(config.audit_rules),
        "madlib.contribution_claims": len(config.contribution_claims),
    }
    if path in block_counts:
        return f"{block_counts[path]} entries"
    return "configured field"


def _slot_summary(config: MadlibConfig, path: str) -> str:
    parts = path.split(".")
    slot_name = parts[2] if len(parts) >= 3 else ""
    slot = next((candidate for candidate in config.slots if candidate.name == slot_name), None)
    if slot is None:
        return "slot"
    if path.endswith(".count"):
        return str(slot.count)
    if path.endswith(".section"):
        return str(slot.section)
    return f"{slot.category} -> {slot.section} ({slot.count})"

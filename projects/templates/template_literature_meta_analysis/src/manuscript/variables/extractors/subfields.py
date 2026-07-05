"""Subfield classification variables."""

from __future__ import annotations

from manuscript.variables.context import ExtractContext
from manuscript.variables.formatters import humanize_key, humanize_list


def extract_subfields(ctx: ExtractContext) -> dict[str, str]:
    subfield_cfg = ctx.cfg.get("project_config", {}).get("subfield_keywords", {}) or {}
    subfield_names = list(subfield_cfg.keys())
    variables = {
        "N_SUBFIELDS": str(len(subfield_names)),
        "SUBFIELD_LIST": humanize_list([humanize_key(k) for k in subfield_names]),
    }
    counts = ctx.load_json("subfield_classification.json")
    total = sum(v for v in counts.values() if isinstance(v, int)) if counts else 0
    table_rows = ["| Subfield | Papers | Share |", "| --- | --- | --- |"]
    if not subfield_names:
        subfield_names = [k for k in counts if not str(k).startswith("_")]
    for name in subfield_names:
        count = counts.get(name, 0)
        if counts:
            pct = (count / total * 100) if total > 0 else 0.0
            table_rows.append(f"| {humanize_key(name)} | {count} | {pct:.1f}% |")
        else:
            table_rows.append(f"| {humanize_key(name)} | — | — |")
    variables["SUBFIELD_TABLE"] = "\n".join(table_rows)
    if counts and total > 0 and subfield_names:
        top_name = max(subfield_names, key=lambda n: counts.get(n, 0))
        variables["TOP_SUBFIELD"] = humanize_key(top_name)
        variables["TOP_SUBFIELD_PCT"] = f"{counts.get(top_name, 0) / total * 100:.1f}"
    else:
        variables["TOP_SUBFIELD"] = humanize_key(subfield_names[0]) if subfield_names else "—"
        variables["TOP_SUBFIELD_PCT"] = "—"
    return variables

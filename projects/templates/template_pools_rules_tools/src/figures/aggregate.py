"""aggregate.py — all_figures wrapper over the per-figure builder modules."""

from __future__ import annotations

import pathlib
from typing import Any

from ._theme import _MPL_AVAILABLE
from .architecture import generate_architecture_overview
from .contract import generate_tool_contract
from .counts import generate_resource_counts
from .cover import generate_cover_art
from .dashboard import generate_status_dashboard
from .hierarchy import generate_rule_hierarchy
from .pipeline_flow import generate_pipeline_flow
from .resilience import generate_resilience_layers
from .taxonomy import generate_fond_taxonomy

__all__ = [
    "all_figures",
    "generate_all_figures",
]


def all_figures(
    output_dir: str | pathlib.Path | None = None,
    integration_result: Any = None,
    counts: dict[str, int] | None = None,
    statuses: dict[str, str] | None = None,
) -> dict[str, pathlib.Path | None] | None:
    """Generate all figures (architecture + content + cover) and return {name: path}.

    *counts* and *statuses*, when provided, bind ``resource_counts`` and
    ``status_dashboard`` to real integration-run data instead of their
    illustrative defaults — see ``scripts/05_generate_figures.py`` for how
    they are derived from :func:`run_integration_demo`.

    Returns None if matplotlib is unavailable.
    """
    if not _MPL_AVAILABLE:
        return None

    if output_dir is not None:
        output_dir = pathlib.Path(output_dir)

    arch = generate_architecture_overview(output_dir=output_dir)
    counts_fig = generate_resource_counts(output_dir=output_dir, counts=counts)
    dash = generate_status_dashboard(
        output_dir=output_dir, statuses=statuses, integration_result=integration_result
    )
    taxonomy = generate_fond_taxonomy(output_dir=output_dir)
    rule_tree = generate_rule_hierarchy(output_dir=output_dir)
    tool_contract = generate_tool_contract(output_dir=output_dir)
    resilience = generate_resilience_layers(output_dir=output_dir)
    pipeline = generate_pipeline_flow(output_dir=output_dir)
    cover = generate_cover_art(output_dir=output_dir)

    return {
        "architecture_overview": arch,
        "resource_counts": counts_fig,
        "status_dashboard": dash,
        "fond_taxonomy": taxonomy,
        "rule_hierarchy": rule_tree,
        "tool_contract": tool_contract,
        "resilience_layers": resilience,
        "pipeline_flow": pipeline,
        "cover_art": cover,
    }


generate_all_figures = all_figures  # alias for script use

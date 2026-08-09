"""Shared theme and registry metadata for integration figures."""

from __future__ import annotations

from dataclasses import dataclass

BLUE = "#1e3a8a"
BLUE_LIGHT = "#3b82f6"
TEAL = "#0f766e"
TEAL_LIGHT = "#14b8a6"
NEUTRAL = "#64748b"
NEUTRAL_LIGHT = "#94a3b8"
WHITE = "#ffffff"
BG = "#f8fafc"
GRID = "#e2e8f0"

STATUS_COLORS: dict[str, str] = {
    "ok": "#16a34a",
    "partial": "#d97706",
    "missing": "#dc2626",
}

STATUS_LABELS: dict[str, str] = {
    "ok": "Pass",
    "partial": "Partial",
    "missing": "Missing",
}


@dataclass(frozen=True)
class IntegrationFigureSpec:
    """Registry metadata for one generated integration figure."""

    label: str
    filename: str
    caption: str
    generated_by: str
    alt_text: str


FIGURE_REGISTRY_SCHEMA = "template-pools-rules-tools-figure-registry-v1"
INTEGRATION_FIGURE_SPECS: tuple[IntegrationFigureSpec, ...] = (
    IntegrationFigureSpec(
        label="fig:architecture",
        filename="architecture_overview.png",
        caption="Three-layer resource architecture with the integration layer.",
        generated_by="src.figures.generate_architecture_overview",
        alt_text="Diagram showing fonds, rules, and tools feeding a shared integration layer.",
    ),
    IntegrationFigureSpec(
        label="fig:counts",
        filename="resource_counts.png",
        caption="Runtime counts for discovered fonds, rules, and tools.",
        generated_by="src.figures.generate_resource_counts",
        alt_text="Bar chart comparing the runtime counts discovered for fonds, rules, and tools.",
    ),
    IntegrationFigureSpec(
        label="fig:pipeline",
        filename="status_dashboard.png",
        caption="Per-resource integration status dashboard.",
        generated_by="src.figures.generate_status_dashboard",
        alt_text=(
            "Status dashboard showing pass, partial, or missing state for each resource category."
        ),
    ),
    IntegrationFigureSpec(
        label="fig:taxonomy",
        filename="fond_taxonomy.png",
        caption="Schema taxonomy across bibliography, contacts, and dataset fonds.",
        generated_by="src.figures.generate_fond_taxonomy",
        alt_text=(
            "Taxonomy diagram comparing shared manifest fields and "
            "category-specific schemas for three fond types."
        ),
    ),
    IntegrationFigureSpec(
        label="fig:rulehier",
        filename="rule_hierarchy.png",
        caption="Soft and strong branches of the template rule hierarchy.",
        generated_by="src.figures.generate_rule_hierarchy",
        alt_text=(
            "Hierarchy diagram separating guidance-oriented soft rules from "
            "machine-enforced strong rules."
        ),
    ),
    IntegrationFigureSpec(
        label="fig:toolcontract",
        filename="tool_contract.png",
        caption="Input, behavior, output, and exit-code contracts for template tools.",
        generated_by="src.figures.generate_tool_contract",
        alt_text="Contract diagram comparing tool inputs, behavior, outputs, and exit codes.",
    ),
    IntegrationFigureSpec(
        label="fig:resilience",
        filename="resilience_layers.png",
        caption="Three-level graceful-degradation design for shared resources.",
        generated_by="src.figures.generate_resilience_layers",
        alt_text=(
            "Layered flow showing resource absence, malformed data, and missing "
            "scripts with bounded fallback responses."
        ),
    ),
    IntegrationFigureSpec(
        label="fig:pipelineflow",
        filename="pipeline_flow.png",
        caption="Thin-script pipeline from source validation through publication rendering.",
        generated_by="src.figures.generate_pipeline_flow",
        alt_text=(
            "Left-to-right pipeline from source validation through integration, "
            "figure generation, variable hydration, and publication rendering."
        ),
    ),
)


__all__ = [
    "BG",
    "BLUE",
    "BLUE_LIGHT",
    "FIGURE_REGISTRY_SCHEMA",
    "GRID",
    "INTEGRATION_FIGURE_SPECS",
    "IntegrationFigureSpec",
    "NEUTRAL",
    "NEUTRAL_LIGHT",
    "STATUS_COLORS",
    "STATUS_LABELS",
    "TEAL",
    "TEAL_LIGHT",
    "WHITE",
]

"""Project-owned provenance metadata for the Template architecture figures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArchitectureFigureSpec:
    """Registry contract for one generated manuscript figure."""

    label: str
    filename: str
    caption: str
    alt_text: str
    generated_by: str


FIGURE_REGISTRY_SCHEMA = "template-template-figure-registry-v1"
ARCHITECTURE_FIGURE_SPECS: tuple[ArchitectureFigureSpec, ...] = (
    ArchitectureFigureSpec(
        label="fig:template-architecture",
        filename="architecture_overview.png",
        caption="Two-layer architecture derived from the public repository inventory.",
        alt_text=(
            "Infrastructure module cards appear above public-project cards, joined by a pipeline arrow. "
            "Each card records the corresponding file counts and documentation badges."
        ),
        generated_by="template_template.figures.figure_architecture_overview.generate_architecture_overview",
    ),
    ArchitectureFigureSpec(
        label="fig:template-pipeline-flow",
        filename="pipeline_stages.png",
        caption="Declared pipeline stages with their complete names and tags.",
        alt_text=(
            "Pipeline stage cards list every YAML declaration in reading order, with stage numbers, "
            "complete names and tags. Their order describes declarations rather than a dependency chain."
        ),
        generated_by="template_template.figures.figure_pipeline_stages.generate_pipeline_stages",
    ),
    ArchitectureFigureSpec(
        label="fig:template-module-inventory",
        filename="module_inventory.png",
        caption="Infrastructure Python file counts by module, sorted largest first.",
        alt_text=(
            "A horizontal bar chart compares Python file counts across infrastructure modules, "
            "with the largest modules first and smaller modules forming a long tail."
        ),
        generated_by="template_template.figures.figure_module_inventory.generate_module_inventory",
    ),
    ArchitectureFigureSpec(
        label="fig:template-comparative-matrix",
        filename="comparative_feature_matrix.png",
        caption="Comparative capabilities of research tools across the declared feature matrix.",
        alt_text=(
            "A heatmap compares tools across core pipeline, quality and security, and ecosystem capabilities. "
            "Each cell distinguishes full, partial or plugin-hosted, and unavailable support."
        ),
        generated_by="template_template.figures.figure_comparative_matrix.generate_comparative_feature_matrix",
    ),
)


__all__ = ["ARCHITECTURE_FIGURE_SPECS", "FIGURE_REGISTRY_SCHEMA", "ArchitectureFigureSpec"]

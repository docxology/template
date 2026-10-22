"""Architecture visualization generation for the template project.

Generates four publication-quality figures from live introspection data.
Figure builders live in sibling modules; this module re-exports the public API
and provides :func:`generate_all_architecture_figures`.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.documentation.generated_figure_registry import write_generated_figure_registry

from .figure_architecture_overview import generate_architecture_overview, generate_architecture_presentation_panels
from .figure_comparative_matrix import (
    comparative_feature_matrix_data,
    generate_comparative_feature_matrix,
)
from .figure_module_inventory import generate_module_inventory, generate_module_inventory_presentation_panels
from .figure_pipeline_stages import generate_pipeline_stages, generate_pipeline_presentation_panels
from .figure_comparative_panels import generate_comparative_presentation_panels
from .figure_specs import ARCHITECTURE_FIGURE_SPECS, FIGURE_REGISTRY_SCHEMA
from ..core.introspection import build_infrastructure_report

__all__ = [
    "comparative_feature_matrix_data",
    "generate_all_architecture_figures",
    "generate_architecture_overview",
    "generate_comparative_feature_matrix",
    "generate_module_inventory",
    "generate_pipeline_stages",
]


def generate_all_architecture_figures(repo_root: Path, project_dir: Path) -> list[Path]:
    """Generate and register all manuscript figures, returning the four PNG paths."""
    output_dir = project_dir / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    report = build_infrastructure_report(repo_root)
    paths = [
        generate_architecture_overview(
            report.modules,
            report.projects,
            output_dir,
            report.infrastructure_version,
        ),
        generate_pipeline_stages(report.pipeline_stages, output_dir),
        generate_module_inventory(report.modules, output_dir),
        generate_comparative_feature_matrix(output_dir),
    ]
    generate_architecture_presentation_panels(
        report.modules, report.projects, output_dir, report.infrastructure_version
    )
    generate_module_inventory_presentation_panels(report.modules, output_dir)
    generate_pipeline_presentation_panels(report.pipeline_stages, output_dir)
    generate_comparative_presentation_panels(output_dir)
    write_generated_figure_registry(
        output_dir / "figure_registry.json",
        ARCHITECTURE_FIGURE_SPECS,
        paths,
        schema_version=FIGURE_REGISTRY_SCHEMA,
    )
    return paths

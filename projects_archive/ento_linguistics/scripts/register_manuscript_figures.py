#!/usr/bin/env python3
"""Register all manuscript-referenced figures in the figure registry.

This script ensures all figures referenced in the manuscript files are
registered with the FigureManager for proper cross-referencing validation.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project src and repo root to path
project_root = Path(__file__).parent.parent
repo_root = project_root.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))

# Use simple logging as fallback
import logging

from utils.figure_manager import FigureManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def register_all_manuscript_figures() -> None:
    """Register all figures referenced in manuscript files."""
    logger.info("Registering all manuscript-referenced figures...")

    # Initialize FigureManager with project-specific registry
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    figure_manager = FigureManager(
        registry_file=str(figures_dir / "figure_registry.json")
    )

    # Define all manuscript-referenced figures with their metadata
    manuscript_figures = [
        # Introduction (02_introduction.md)
        {
            "filename": "conceptual_map.png",
            "caption": "Conceptual map of the Ento-Linguistic Domains framework showing relationships between key concepts",
            "label": "fig:concept_map",
            "section": "introduction",
            "generated_by": "generate_research_figures.py",
        },
        # Experimental Results (04_experimental_results.md)
        {
            "filename": "terminology_network.png",
            "caption": "Complete terminology network showing relationships between terms across all Ento-Linguistic domains",
            "label": "fig:terminology_network",
            "section": "experimental_results",
            "generated_by": "literature_analysis_pipeline.py",
        },
        {
            "filename": "domain_comparison.png",
            "caption": "Domain-specific terminology networks showing unique structural patterns for each Ento-Linguistic domain",
            "label": "fig:domain_comparison",
            "section": "experimental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "unit_of_individuality_patterns.png",
            "caption": "Key patterns in Unit of Individuality terminology showing superorganism-individual tensions",
            "label": "fig:unit_individuality_patterns",
            "section": "experimental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "concept_hierarchy.png",
            "caption": "Hierarchical concept organization across Ento-Linguistic domains",
            "label": "fig:concept_hierarchy",
            "section": "experimental_results",
            "generated_by": "generate_research_figures.py",
        },
        # Supplemental Results - Cross-domain figures (S02_supplemental_results.md)
        {
            "filename": "domain_comparison.png",
            "caption": "Cross-domain relationship analysis showing conceptual bridges between Ento-Linguistic domains",
            "label": "fig:cross_domain_relationships",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "domain_comparison.png",
            "caption": "Evolution of framing assumptions in entomological literature over time",
            "label": "fig:framing_evolution",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "domain_comparison.png",
            "caption": "Longitudinal evolution of caste terminology usage patterns",
            "label": "fig:caste_evolution_extended",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        # Unit of Individuality domain figures
        {
            "filename": "unit_of_individuality_term_frequencies.png",
            "caption": "Term frequency distribution in Unit of Individuality domain",
            "label": "fig:unit_individuality_frequencies",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "unit_of_individuality_ambiguities.png",
            "caption": "Ambiguity patterns in Unit of Individuality terminology",
            "label": "fig:unit_individuality_ambiguities",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        # Behavior and Identity domain figures
        {
            "filename": "behavior_and_identity_term_frequencies.png",
            "caption": "Behavioral terminology frequency distribution",
            "label": "fig:behavior_identity_frequencies",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "behavior_and_identity_ambiguities.png",
            "caption": "Identity-related ambiguity patterns",
            "label": "fig:behavior_identity_ambiguities",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        # Power and Labor domain figures
        {
            "filename": "domain_comparison.png",
            "caption": "Power and Labor domain term frequencies (cross-domain comparison view)",
            "label": "fig:power_labor_frequencies",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "domain_comparison.png",
            "caption": "Power and Labor domain ambiguity analysis (cross-domain view)",
            "label": "fig:power_labor_ambiguities",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        # Sex and Reproduction domain figures
        {
            "filename": "sex_and_reproduction_term_frequencies.png",
            "caption": "Reproductive terminology frequency distribution",
            "label": "fig:sex_reproduction_frequencies",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "sex_and_reproduction_ambiguities.png",
            "caption": "Reproductive terminology ambiguity patterns",
            "label": "fig:sex_reproduction_ambiguities",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        # Kin and Relatedness domain figures
        {
            "filename": "kin_and_relatedness_term_frequencies.png",
            "caption": "Kinship terminology frequency distribution",
            "label": "fig:kin_relatedness_frequencies",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        {
            "filename": "kin_and_relatedness_ambiguities.png",
            "caption": "Kinship terminology ambiguity patterns",
            "label": "fig:kin_relatedness_ambiguities",
            "section": "supplemental_results",
            "generated_by": "generate_domain_figures.py",
        },
        # Example figures (README.md, AGENTS.md)
        {
            "filename": "example_figure.png",
            "caption": "Example figure demonstrating the figure management system",
            "label": "fig:example_figure",
            "section": "examples",
            "generated_by": "example_figure.py",
        },
        {
            "filename": "convergence_plot.png",
            "caption": "Convergence analysis showing algorithm performance",
            "label": "fig:convergence_plot",
            "section": "examples",
            "generated_by": "generate_research_figures.py",
        },
    ]

    # Register each figure
    registered = 0
    for fig_data in manuscript_figures:
        # Check if figure file exists
        fig_path = figures_dir / fig_data["filename"]
        if not fig_path.exists():
            logger.warning(
                f"Figure file not found: {fig_data['filename']} - registering anyway"
            )

        try:
            figure_manager.register_figure(
                filename=fig_data["filename"],
                caption=fig_data["caption"],
                label=fig_data["label"],
                section=fig_data["section"],
                generated_by=fig_data["generated_by"],
            )
            registered += 1
            logger.info(f"  Registered: {fig_data['label']}")
        except Exception as e:
            logger.warning(f"  Failed to register {fig_data['label']}: {e}")

    logger.info(f"✅ Registered {registered}/{len(manuscript_figures)} figures")
    logger.info(f"   Registry saved to: {figures_dir / 'figure_registry.json'}")


def main() -> None:
    """Main entry point."""
    register_all_manuscript_figures()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Insert all registered figures into the manuscript.

This script automatically inserts all registered figures from the figure registry
into appropriate manuscript sections using the MarkdownIntegration infrastructure.

The script:
1. Loads the figure registry from output/figures/figure_registry.json
2. Maps figure sections to manuscript files
3. Uses MarkdownIntegration to insert LaTeX figure blocks at appropriate locations
4. Validates that all figures are inserted correctly

Figures are inserted as LaTeX blocks with proper cross-references for PDF rendering.
"""

from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import Dict, List

# Ensure src/ and infrastructure/ are on path FIRST
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
repo_root = project_root.parent

# Add infrastructure and src paths
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(project_root / "src"))

# Infrastructure imports
from infrastructure.core.logging_utils import get_logger
from infrastructure.documentation.markdown_integration import MarkdownIntegration
from infrastructure.documentation.figure_manager import FigureManager

logger = get_logger(__name__)


def load_figure_registry() -> Dict[str, Dict]:
    """Load the figure registry from JSON file.

    Returns:
        Dictionary mapping figure labels to figure metadata
    """
    registry_file = project_root / "output" / "figures" / "figure_registry.json"
    if not registry_file.exists():
        logger.error(f"Figure registry not found: {registry_file}")
        return {}

    try:
        import json
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        logger.info(f"Loaded figure registry with {len(registry)} figures")
        return registry
    except Exception as e:
        logger.error(f"Failed to load figure registry: {e}")
        return {}


def map_section_to_file(section: str) -> Path:
    """Map figure section to manuscript file.

    Args:
        section: Figure section from registry

    Returns:
        Path to corresponding manuscript file
    """
    manuscript_dir = project_root / "manuscript"

    section_mapping = {
        "methodology": "03_methodology.md",
        "experimental_results": "04_experimental_results.md",
    }

    filename = section_mapping.get(section, "03_methodology.md")  # Default to methodology
    return manuscript_dir / filename


def get_section_insertion_points(manuscript_file: Path) -> Dict[str, str]:
    """Get section names where figures should be inserted for a manuscript file.

    Args:
        manuscript_file: Path to manuscript file

    Returns:
        Dictionary mapping figure labels to section names for insertion
    """
    # Define insertion points based on manuscript file
    if "03_methodology.md" in str(manuscript_file):
        # Methodology figures - insert after relevant subsections
        return {
            "fig:quadrant_matrix": "The 2×2 Matrix Framework",
            "fig:efe_decomposition": "Epistemic Framework Specification",
            "fig:perception_action_loop": "Pragmatic Framework Specification",
            "fig:generative_model_structure": "Framework Dimensions",
            "fig:meta_level_concepts": "Quadrant Definitions",
            "fig:fep_system_boundaries": "Active Inference as Meta-Epistemic",
            "fig:free_energy_dynamics": "Active Inference as Meta-Pragmatic",
            "fig:structure_preservation": "Quadrant 4: Higher-Order Reasoning (Meta-Cognitive)",
            "fig:physics_cognition_bridge": "Quadrant 4: Higher-Order Reasoning (Meta-Cognitive)",
            "fig:quadrant_matrix_enhanced": "Integration Across Quadrants",
        }
    elif "04_experimental_results.md" in str(manuscript_file):
        # Experimental results figures - insert after each quadrant section
        return {
            "fig:quadrant_1_data_cognitive": "Quadrant 1: Data Processing (Cognitive)",
            "fig:quadrant_2_metadata_cognitive": "Quadrant 2: Meta-Data Organization (Cognitive)",
            "fig:quadrant_3_data_metacognitive": "Quadrant 3: Reflective Processing (Meta-Cognitive)",
            "fig:quadrant_4_metadata_metacognitive": "Quadrant 4: Higher-Order Reasoning (Meta-Cognitive)",
        }
    else:
        return {}


def insert_figures_into_manuscript() -> bool:
    """Insert all registered figures into the manuscript.

    Returns:
        True if all figures inserted successfully, False otherwise
    """
    logger.info("Starting figure insertion process...")

    # Load figure registry
    registry = load_figure_registry()
    if not registry:
        return False

    # Track insertion results
    successful_insertions = 0
    failed_insertions = 0

    # Group figures by target file
    figures_by_file: Dict[Path, List[str]] = {}

    for figure_label, figure_data in registry.items():
        section = figure_data.get("section", "")
        target_file = map_section_to_file(section)
        if target_file not in figures_by_file:
            figures_by_file[target_file] = []
        figures_by_file[target_file].append(figure_label)

    # Insert figures for each file
    for manuscript_file, figure_labels in figures_by_file.items():
        logger.info(f"Processing {len(figure_labels)} figures for {manuscript_file.name}")

        # Get insertion points for this file
        insertion_points = get_section_insertion_points(manuscript_file)

        for figure_label in figure_labels:
            section_name = insertion_points.get(figure_label, "")

            if not section_name:
                logger.warning(f"No insertion point found for {figure_label}, skipping")
                failed_insertions += 1
                continue

            logger.info(f"  Inserting {figure_label} after section '{section_name}'")

            try:
                # Direct insertion approach - simpler than using MarkdownIntegration
                success = insert_figure_directly(manuscript_file, figure_label, section_name, registry[figure_label])

                if success:
                    logger.info(f"    ✅ Successfully inserted {figure_label}")
                    successful_insertions += 1
                else:
                    logger.warning(f"    ❌ Failed to insert {figure_label}")
                    failed_insertions += 1

            except Exception as e:
                logger.error(f"    ❌ Error inserting {figure_label}: {e}")
                failed_insertions += 1

    # Summary
    total_figures = len(registry)
    logger.info(f"\nFigure insertion summary:")
    logger.info(f"  Total figures: {total_figures}")
    logger.info(f"  Successfully inserted: {successful_insertions}")
    logger.info(f"  Failed insertions: {failed_insertions}")

    if failed_insertions == 0:
        logger.info("✅ All figures inserted successfully!")
        return True
    else:
        logger.warning(f"⚠️  {failed_insertions} figures failed to insert")
        return False


def insert_figure_directly(manuscript_file: Path, figure_label: str, section_name: str, figure_data: Dict) -> bool:
    """Insert a figure directly into a markdown file after a specific section.

    Args:
        manuscript_file: Path to the markdown file
        figure_label: Label of the figure to insert
        section_name: Name of the section to insert after
        figure_data: Figure metadata from registry

    Returns:
        True if insertion successful, False otherwise
    """
    try:
        # Read the file
        content = manuscript_file.read_text()

        # Check if figure is already inserted
        if f"\\label{{{figure_label}}}" in content:
            logger.debug(f"Figure {figure_label} already exists in {manuscript_file.name}")
            return True

        # Find the section header
        section_pattern = rf"## {re.escape(section_name)}"
        match = re.search(section_pattern, content)

        if not match:
            logger.debug(f"Section '{section_name}' not found in {manuscript_file.name}")
            return False

        # Find the end of this section (next section header or end of file)
        section_end = match.end()
        next_section_match = re.search(r"^## ", content[section_end:])

        if next_section_match:
            insert_pos = section_end + next_section_match.start()
        else:
            insert_pos = len(content)

        # Create LaTeX figure block
        filename = figure_data["filename"]
        caption = figure_data["caption"]
        width = figure_data.get("width", "0.8")

        # Fix width parameter - if it already contains 'textwidth', use as-is
        # Otherwise, assume it's a decimal and add 'textwidth'
        if "textwidth" not in str(width):
            width = f"{width}\\textwidth"  # Default if width became empty

        figure_block = f"""

\\begin{{figure}}[h]
\\centering
\\includegraphics[width={width}\\textwidth]{{../output/figures/{filename}}}
\\caption{{{caption}}}
\\label{{{figure_label}}}
\\end{{figure}}

"""

        # Insert the figure block
        new_content = content[:insert_pos] + figure_block + content[insert_pos:]

        # Write back
        manuscript_file.write_text(new_content)

        return True

    except Exception as e:
        logger.error(f"Error inserting figure {figure_label}: {e}")
        return False


def validate_figure_insertion() -> bool:
    """Validate that all figures are properly inserted.

    Returns:
        True if validation passes, False otherwise
    """
    logger.info("Validating figure insertions...")

    registry = load_figure_registry()
    manuscript_dir = project_root / "manuscript"
    markdown_integration = MarkdownIntegration(manuscript_dir=manuscript_dir)

    all_valid = True

    # Check each figure is present in its target file
    for figure_label, figure_data in registry.items():
        section = figure_data.get("section", "")
        target_file = map_section_to_file(section)

        if not target_file.exists():
            logger.error(f"Target file not found: {target_file}")
            all_valid = False
            continue

        # Read file content and check for figure label
        content = target_file.read_text()
        latex_label = f"\\label{{{figure_label}}}"

        if latex_label not in content:
            logger.warning(f"Figure {figure_label} not found in {target_file.name}")
            all_valid = False
        else:
            logger.info(f"✅ Figure {figure_label} found in {target_file.name}")

    if all_valid:
        logger.info("✅ All figure insertions validated successfully!")
    else:
        logger.warning("⚠️  Some figure insertions failed validation")

    return all_valid


def update_figure_references() -> bool:
    """Update markdown-style figure references to LaTeX format.

    Returns:
        True if all references updated successfully
    """
    logger.info("Updating figure references from markdown to LaTeX format...")

    manuscript_dir = project_root / "manuscript"
    updated_files = 0

    # Files that might contain figure references
    manuscript_files = [
        manuscript_dir / "02_introduction.md",
        manuscript_dir / "03_methodology.md",
        manuscript_dir / "04_experimental_results.md",
        manuscript_dir / "S02_supplemental_results.md"
    ]

    for manuscript_file in manuscript_files:
        if not manuscript_file.exists():
            continue

        try:
            content = manuscript_file.read_text()
            original_content = content

            # Convert markdown-style references (Figure [1](#fig:label)) to LaTeX
            # Pattern: (Figure [number](#fig:figure_label))
            content = re.sub(r'\(Figure \[\d+\]\(#fig:([^)]+)\)\)', r'(Figure \\ref{fig:\1})', content)

            # Also handle standalone markdown links [#fig:label]
            content = re.sub(r'\[#fig:([^]]+)\]', r'\\ref{fig:\1}', content)

            if content != original_content:
                manuscript_file.write_text(content)
                updated_files += 1
                logger.info(f"Updated references in {manuscript_file.name}")

        except Exception as e:
            logger.error(f"Error updating references in {manuscript_file.name}: {e}")
            return False

    logger.info(f"Updated references in {updated_files} files")
    return True


def main() -> int:
    """Main execution function."""
    logger.info("=== Figure Insertion Script ===")
    logger.info(f"Project: {project_root.name}")
    logger.info(f"Manuscript directory: {project_root / 'manuscript'}")
    logger.info(f"Figure registry: {project_root / 'output' / 'figures' / 'figure_registry.json'}")

    # Insert all figures
    insertion_success = insert_figures_into_manuscript()

    if not insertion_success:
        logger.error("Figure insertion failed!")
        return 1

    # Update figure references
    reference_success = update_figure_references()

    if not reference_success:
        logger.warning("Figure reference updates had issues")

    # Validate insertions
    validation_success = validate_figure_insertion()

    if validation_success:
        logger.info("\n🎉 All figures successfully inserted and validated!")
        logger.info("The manuscript now contains all registered figures as LaTeX blocks.")
        logger.info("PDF rendering should now include all figures.")
        return 0
    else:
        logger.warning("Figure validation failed - some figures may not be properly inserted")
        return 1


if __name__ == "__main__":
    exit(main())
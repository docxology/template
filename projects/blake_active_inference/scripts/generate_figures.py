#!/usr/bin/env python3
"""Generate all figures for the Blake Active Inference paper.

This script generates publication-quality graphical abstracts:
1. Doors of Perception (Markov Blanket visualization)
2. Fourfold Vision Hierarchy (Blake ↔ Active Inference mapping)
3. Perception-Action Cycle (with Blake quotation annotations)
4. Thematic Atlas (Concept mapping)
5. Newton's Sleep (Prior dominance visualization)
6. Four Zoas (Factorized model of mind)
7. Temporal Horizons (Timescales of inference)
8. Collective Jerusalem (Multi-agent generative model)

Usage:
    python generate_figures.py [output_dir]
    
    If output_dir is not specified, figures are saved to ../output/figures/
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from visualization import generate_all_figures

# Infrastructure integration
try:
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))
    from infrastructure.core import get_logger, ProgressBar
    from infrastructure.documentation.figure_manager import FigureManager
    INFRASTRUCTURE_AVAILABLE = True
    logger = get_logger("blake_active_inference.generate_figures")
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
    import logging
    logger = logging.getLogger("blake_active_inference.generate_figures")


import shutil

def main():
    """Generate all paper figures."""
    # Determine output directory
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        output_dir = Path(__file__).parent.parent / "output" / "figures"

    logger.info("Blake Active Inference - Figure Generation")
    logger.info(f"Output directory: {output_dir}")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize FigureManager if infrastructure available
    figure_manager = None
    if INFRASTRUCTURE_AVAILABLE:
        try:
            # Fix: pass registry FILE path, not directory
            registry_file = output_dir / "figure_registry.json"
            figure_manager = FigureManager(str(registry_file))
        except Exception as e:
            logger.warning(f"Could not initialize FigureManager: {e}")

    # Copy all image assets from manuscript directory
    manuscript_dir = Path(__file__).parent.parent / "manuscript"
    for img_ext in ["*.jpg", "*.png"]:
        for img_path in manuscript_dir.glob(img_ext):
            try:
                shutil.copy2(img_path, output_dir / img_path.name)
                logger.info(f"Copied manuscript asset: {img_path.name}")
            except Exception as e:
                logger.error(f"Failed to copy asset {img_path.name}: {e}")

    # Generate figures
    figures = generate_all_figures(output_dir)

    # Report results and register with infrastructure
    logger.info("Generated figures:")
    for name, path in figures.items():
        size_kb = path.stat().st_size / 1024
        logger.info(f"  {name}: {path.name} ({size_kb:.1f} KB)")
        # Print path for manifest collection
        print(str(path))
        # Register with FigureManager
        if figure_manager is not None:
            try:
                figure_manager.register_figure(
                    filename=path.name,
                    caption=f"Blake Active Inference - {name.replace('_', ' ').title()}",
                    section="results",
                    generated_by="generate_figures.py",
                )
            except Exception:
                pass

    logger.info(f"Total: {len(figures)} figures generated successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

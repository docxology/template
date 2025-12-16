#!/usr/bin/env python3
"""Biological process simulation script for graft healing.

This script demonstrates how to use src/ modules to:
1. Set up grafting parameters
2. Simulate cambium integration and healing
3. Generate results and figures
4. Create analysis reports

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure src/ and infrastructure/ are on path
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))

from infrastructure.core.logging_utils import get_logger
from infrastructure.documentation.figure_manager import FigureManager

logger = get_logger(__name__)

# Import grafting modules
from graft_parameters import GraftParameterSet, create_default_graft_parameters
from biological_simulation import CambiumIntegrationSimulation
from graft_plots import plot_healing_timeline
from graft_visualization import GraftVisualizationEngine
from graft_reporting import GraftReportGenerator


def run_healing_simulation() -> None:
    """Run a graft healing simulation example."""
    logger.info("Running graft healing simulation...")
    
    # Set up parameters
    params = create_default_graft_parameters()
    params.parameters["compatibility"] = 0.85
    params.parameters["temperature"] = 22.0
    params.parameters["humidity"] = 0.8
    params.parameters["technique_quality"] = 0.9
    params.parameters["max_days"] = 60
    
    # Create simulation
    sim = CambiumIntegrationSimulation(
        parameters=params.parameters,
        seed=42,
        output_dir="output/simulations"
    )
    
    # Run simulation
    logger.info("Running healing simulation...")
    state = sim.run(max_days=60, verbose=True)
    
    # Save results
    logger.info("Saving results...")
    saved_files = sim.save_results("graft_healing_simulation")
    for fmt, path in saved_files.items():
        logger.info(f"  Saved {fmt}: {path}")
    
    logger.info(f"✅ Simulation complete: Union strength = {state.union_strength:.3f}")


def generate_healing_figures() -> None:
    """Generate healing timeline figures."""
    logger.info("\nGenerating healing timeline figures...")
    
    # Run simulation to get data
    params = create_default_graft_parameters()
    params.parameters.update({
        "compatibility": 0.8,
        "temperature": 22.0,
        "humidity": 0.8,
        "technique_quality": 0.8,
        "max_days": 45
    })
    
    sim = CambiumIntegrationSimulation(parameters=params.parameters, seed=42)
    state = sim.run(max_days=45, verbose=False)
    
    # Extract timeline data
    days = []
    union_strengths = []
    for day_key in sorted(state.results.keys(), key=lambda x: int(x.split('_')[1])):
        day_data = state.results[day_key]
        days.append(int(day_key.split('_')[1]))
        union_strengths.append(day_data.get("union_strength", 0.0))
    
    # Create figure
    engine = GraftVisualizationEngine(output_dir="output/figures")
    figure_manager = FigureManager()
    
    import numpy as np
    fig, ax = engine.create_figure()
    plot_healing_timeline(np.array(days), np.array(union_strengths), ax=ax, 
                         label="Union Strength", color=engine.get_color(0))
    engine.apply_publication_style(ax, "Graft Union Strength Over Time", 
                                   "Days Since Grafting", "Union Strength", grid=True, legend=True)
    
    saved = engine.save_figure(fig, "healing_timeline")
    logger.info(f"  Saved figure: {saved['png']}")
    
    figure_manager.register_figure(
        filename="healing_timeline.png",
        caption="Temporal progression of graft union strength during healing",
        section="experimental_results",
        generated_by="biological_process_simulation.py"
    )
    
    import matplotlib.pyplot as plt
    plt.close(fig)


def main() -> None:
    """Main function orchestrating the biological simulation workflow."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    
    # Ensure output directories exist
    for dir_path in ["output/simulations", "output/figures", "output/reports"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    try:
        # Run simulation
        run_healing_simulation()
        
        # Generate figures
        generate_healing_figures()
        
        logger.info("\n✅ All biological simulation tasks completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during simulation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    main()


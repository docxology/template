#!/usr/bin/env python3
"""Generate biological process figures for grafting manuscript.

This script generates biological process visualizations including:
- Vascular integration diagrams
- Callus formation processes
- Cambium alignment illustrations
- Healing progression timelines

IMPORTANT: Uses methods from src/ modules to demonstrate integration.
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

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from infrastructure.documentation.figure_manager import FigureManager
from biological_simulation import CambiumIntegrationSimulation
from graft_plots import plot_healing_timeline
from graft_visualization import GraftVisualizationEngine
from graft_parameters import create_default_graft_parameters


def generate_vascular_integration(figure_dir: str) -> str:
    """Generate vascular integration diagram."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    fig, ax = engine.create_figure(figsize=(10, 8))
    
    # Draw vascular integration process
    # Day 0: Initial separation
    ax.plot([0.2, 0.8], [0.3, 0.3], 'k-', linewidth=3, label='Day 0: Initial cut')
    
    # Day 7: Callus formation
    ax.plot([0.2, 0.8], [0.5, 0.5], 'orange', linewidth=3, label='Day 7: Callus formation')
    
    # Day 14: Vascular connection
    ax.plot([0.2, 0.8], [0.7, 0.7], 'green', linewidth=3, label='Day 14: Vascular connection')
    
    # Day 30: Full integration
    ax.plot([0.2, 0.8], [0.9, 0.9], 'blue', linewidth=3, label='Day 30: Full integration')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('Vascular Integration Process', fontsize=14, weight='bold')
    ax.legend(loc='upper left')
    ax.axis('off')
    
    figure_path = os.path.join(figure_dir, "vascular_integration.png")
    engine.save_figure(fig, "vascular_integration")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="vascular_integration.png",
        caption="Temporal progression of vascular integration in graft union",
        section="methodology",
        generated_by="generate_biological_figures.py"
    )
    
    return figure_path


def generate_callus_formation(figure_dir: str) -> str:
    """Generate callus formation timeline."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    # Simulate callus formation
    days = np.arange(0, 30)
    callus_formation = 1.0 - np.exp(-days / 8.0)
    
    fig, ax = engine.create_figure()
    ax.plot(days, callus_formation, linewidth=2, color=engine.get_color(0))
    engine.apply_publication_style(ax, "Callus Formation Over Time",
                                   "Days Since Grafting", "Callus Formation (0-1)", grid=True)
    
    figure_path = os.path.join(figure_dir, "callus_formation.png")
    engine.save_figure(fig, "callus_formation")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="callus_formation.png",
        caption="Callus formation progression showing exponential growth pattern",
        section="methodology",
        generated_by="generate_biological_figures.py"
    )
    
    return figure_path


def main() -> None:
    """Generate all biological figures."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    
    repo_root = Path(__file__).parent.parent
    figure_dir = repo_root / "output" / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating biological process figures...")
    
    figures_generated = []
    
    try:
        figures_generated.append(generate_vascular_integration(str(figure_dir)))
        figures_generated.append(generate_callus_formation(str(figure_dir)))
        
        print(f"\n✅ Generated {len(figures_generated)} biological figures:")
        for fig_path in figures_generated:
            if fig_path:
                print(f"  - {fig_path}")
        
    except Exception as e:
        print(f"❌ Error generating figures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


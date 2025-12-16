#!/usr/bin/env python3
"""Generate figures specifically referenced in the grafting manuscript.

This script generates the exact figures referenced in 04_experimental_results.md:
- compatibility_matrix.png
- environmental_effects.png

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
from infrastructure.core.logging_utils import get_logger, log_substep

# Import grafting modules from src/
from graft_data_generator import generate_compatibility_matrix
from graft_plots import plot_compatibility_matrix, plot_environmental_effects
from graft_visualization import GraftVisualizationEngine

logger = get_logger(__name__)


def _setup_directories() -> tuple[str, str]:
    """Setup output directories."""
    output_dir = project_root / "output"
    figure_dir = output_dir / "figures"
    
    figure_dir.mkdir(parents=True, exist_ok=True)
    
    return str(output_dir), str(figure_dir)


def generate_compatibility_matrix_figure(figure_dir: str) -> str:
    """Generate species compatibility matrix figure."""
    log_substep("Generating compatibility matrix figure")
    
    # Generate compatibility matrix using src/ module
    n_species = 15
    compat_matrix = generate_compatibility_matrix(
        n_species=n_species,
        phylogenetic_structure=True,
        seed=42
    )
    
    # Create visualization
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    fig, ax = engine.create_figure(figsize=(10, 8))
    
    # Plot compatibility matrix
    plot_compatibility_matrix(compat_matrix, ax=ax)
    
    # Style the plot
    ax.set_title('Species Compatibility Matrix', fontsize=16, weight='bold', pad=20)
    
    # Save figure
    saved = engine.save_figure(fig, "compatibility_matrix")
    plt.close(fig)
    
    # Register with figure manager
    figure_manager.register_figure(
        filename="compatibility_matrix.png",
        caption="Species compatibility matrix showing graft success probabilities between rootstock-scion pairs",
        section="experimental_results",
        label="fig:compatibility_matrix",
        generated_by="generate_manuscript_figures.py"
    )
    
    logger.info(f"  Generated: {saved['png']}")
    return saved['png']


def generate_environmental_effects_figure(figure_dir: str) -> str:
    """Generate environmental effects figure."""
    log_substep("Generating environmental effects figure")
    
    # Generate environmental data
    temperature_range = np.linspace(10, 35, 50)
    humidity_range = np.linspace(30, 100, 50)
    
    # Calculate success rates based on temperature and humidity
    def calculate_success_rate(temp: float, humidity: float) -> float:
        """Calculate success rate based on environmental conditions."""
        # Optimal temperature: 20-25°C
        if 20 <= temp <= 25:
            temp_factor = 1.0
        elif 15 <= temp < 20 or 25 < temp <= 30:
            temp_factor = 0.9
        else:
            temp_factor = 0.7
        
        # Optimal humidity: 70-90%
        if 70 <= humidity <= 90:
            humidity_factor = 1.0
        elif 50 <= humidity < 70 or 90 < humidity <= 100:
            humidity_factor = 0.85
        else:
            humidity_factor = 0.65
        
        # Base success rate
        base_rate = 0.82
        return base_rate * temp_factor * humidity_factor
    
    # Generate success rate data
    temp_success = np.array([
        calculate_success_rate(t, 80)  # Fixed humidity at 80%
        for t in temperature_range
    ])
    
    humidity_success = np.array([
        calculate_success_rate(22.5, h)  # Fixed temperature at 22.5°C
        for h in humidity_range
    ])
    
    # Create visualization
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    fig, (ax1, ax2) = engine.create_figure(nrows=1, ncols=2, figsize=(14, 5))
    
    # Temperature effects plot
    ax1.plot(temperature_range, temp_success, linewidth=2, color=engine.get_color(0))
    ax1.axvspan(20, 25, alpha=0.2, color='green', label='Optimal Range')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Success Rate', fontsize=12)
    ax1.set_title('Temperature Effects on Graft Success', fontsize=14, weight='bold')
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Humidity effects plot
    ax2.plot(humidity_range, humidity_success, linewidth=2, color=engine.get_color(1))
    ax2.axvspan(70, 90, alpha=0.2, color='green', label='Optimal Range')
    ax2.set_xlabel('Relative Humidity (%)', fontsize=12)
    ax2.set_ylabel('Success Rate', fontsize=12)
    ax2.set_title('Humidity Effects on Graft Success', fontsize=14, weight='bold')
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    
    # Save figure
    saved = engine.save_figure(fig, "environmental_effects")
    plt.close(fig)
    
    # Register with figure manager
    figure_manager.register_figure(
        filename="environmental_effects.png",
        caption="Graft success as function of temperature and humidity conditions",
        section="experimental_results",
        label="fig:environmental_effects",
        generated_by="generate_manuscript_figures.py"
    )
    
    logger.info(f"  Generated: {saved['png']}")
    return saved['png']


def main() -> None:
    """Generate all manuscript figures."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    
    output_dir, figure_dir = _setup_directories()
    
    logger.info("Generating manuscript figures...")
    
    figures_generated = []
    
    try:
        # Generate compatibility matrix
        fig_path = generate_compatibility_matrix_figure(figure_dir)
        figures_generated.append(fig_path)
        
        # Generate environmental effects
        fig_path = generate_environmental_effects_figure(figure_dir)
        figures_generated.append(fig_path)
        
        logger.info(f"\n✅ Generated {len(figures_generated)} manuscript figures:")
        for fig_path in figures_generated:
            if fig_path:
                logger.info(f"  - {fig_path}")
        
    except Exception as e:
        logger.error(f"❌ Error generating figures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


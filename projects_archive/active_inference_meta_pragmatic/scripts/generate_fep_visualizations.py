#!/usr/bin/env python3
"""Generate Free Energy Principle Visualizations.

This script creates visualizations of Free Energy Principle concepts:
- System boundaries and Markov blankets
- Free energy minimization over time
- Structure preservation dynamics
- Bridge between physics and cognition

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure src/ is on path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Local imports
from utils.logging import get_logger
from utils.figure_manager import FigureManager

# Import src/ modules
from free_energy_principle import FreeEnergyPrinciple, define_what_is_a_thing
from visualization import VisualizationEngine

logger = get_logger(__name__)


def main() -> None:
    """Generate Free Energy Principle visualizations."""
    logger.info("Generating Free Energy Principle visualizations...")

    # Setup output directory
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    viz_engine = VisualizationEngine(output_dir=str(output_dir))
    figure_manager = FigureManager()

    # Generate FEP system boundary visualization
    create_system_boundary_diagram(viz_engine, figure_manager)

    # Generate free energy minimization dynamics
    create_free_energy_dynamics(viz_engine, figure_manager)

    # Generate structure preservation visualization
    create_structure_preservation(viz_engine, figure_manager)

    # Generate physics-cognition bridge
    create_physics_cognition_bridge(viz_engine, figure_manager)

    logger.info("✅ Free Energy Principle visualizations completed")


def create_system_boundary_diagram(viz_engine: VisualizationEngine,
                                 figure_manager: FigureManager) -> None:
    """Create system boundary and Markov blanket visualization."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_title('Free Energy Principle: System Boundaries and Markov Blankets',
                fontweight='bold', pad=20)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Draw external environment
    ax.add_patch(plt.Rectangle((1, 1), 10, 6, fill=True, alpha=0.1,
                             edgecolor='blue', linewidth=2, linestyle='--'))
    ax.text(6, 7.2, 'External Environment', ha='center', va='center',
            fontsize=12, fontweight='bold')

    # Draw Markov blanket (system boundary)
    ax.add_patch(plt.Rectangle((3, 2.5), 6, 3, fill=True, alpha=0.2,
                             edgecolor='red', linewidth=3))
    ax.text(6, 4, 'Markov Blanket\n(System Boundary)', ha='center', va='center',
            fontsize=11, fontweight='bold', color='red')

    # Draw internal states
    ax.add_patch(plt.Circle((6, 4), 0.8, fill=True, alpha=0.3, color='green'))
    ax.text(6, 4, 'Internal\nStates', ha='center', va='center',
            fontsize=10, fontweight='bold')

    # Draw sensory states
    ax.add_patch(plt.Rectangle((2.5, 3.5), 1.5, 1, fill=True, alpha=0.4, color='orange'))
    ax.text(3.25, 4, 'Sensory\nStates', ha='center', va='center',
            fontsize=9, fontweight='bold')

    # Draw active states
    ax.add_patch(plt.Rectangle((8.0, 3.5), 1.5, 1, fill=True, alpha=0.4, color='purple'))
    ax.text(8.75, 4, 'Active\nStates', ha='center', va='center',
            fontsize=9, fontweight='bold')

    # Draw information flows
    # External to sensory
    ax.arrow(2, 4, 0.4, 0, head_width=0.1, head_length=0.2,
             fc='orange', ec='orange', alpha=0.7)
    ax.text(2.2, 4.2, 'External\ninfluences', fontsize=8, color='orange')

    # Sensory to internal
    ax.arrow(4, 4, 1.8, 0, head_width=0.1, head_length=0.2,
             fc='blue', ec='blue', alpha=0.7)
    ax.text(5, 4.2, 'Sensory\ninput', fontsize=8, color='blue')

    # Internal to active
    ax.arrow(6.8, 4, 1.2, 0, head_width=0.1, head_length=0.2,
             fc='purple', ec='purple', alpha=0.7)
    ax.text(7.5, 4.2, 'Action\nselection', fontsize=8, color='purple')

    # Active to external
    ax.arrow(9.5, 4, 0.5, 0, head_width=0.1, head_length=0.2,
             fc='red', ec='red', alpha=0.7)
    ax.text(9.8, 4.2, 'External\nactions', fontsize=8, color='red')

    # Add FEP principle
    ax.text(6, 1.5, 'Free Energy Principle:\nSystems minimize variational free energy\nto maintain structural integrity',
            ha='center', va='center', fontsize=10,
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', alpha=0.5))

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "fep_system_boundaries")
    logger.info(f"Saved FEP system boundaries: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="fep_system_boundaries.png",
        caption="Free Energy Principle system boundaries showing Markov blanket separating internal and external states",
        section="methodology",
        generated_by="generate_fep_visualizations.py"
    )


def create_free_energy_dynamics(viz_engine: VisualizationEngine,
                              figure_manager: FigureManager) -> None:
    """Create free energy minimization dynamics visualization."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Free Energy Minimization Dynamics', fontweight='bold')

    # Simulate free energy minimization
    np.random.seed(42)
    time_steps = 100

    # Generate synthetic free energy trajectory
    t = np.arange(time_steps)
    base_fe = 5.0 * np.exp(-t / 30)  # Exponential decay
    noise = 0.1 * np.random.randn(time_steps)
    free_energy = base_fe + noise

    # Ensure non-negative
    free_energy = np.maximum(free_energy, 0.01)

    # Top plot: Free energy over time
    ax1.plot(t, free_energy, 'b-', linewidth=2, alpha=0.8)
    ax1.fill_between(t, free_energy, alpha=0.3, color='blue')
    ax1.set_ylabel('Variational Free Energy')
    ax1.set_title('Free Energy Minimization Over Time')
    ax1.grid(True, alpha=0.3)

    # Add convergence annotation
    final_fe = free_energy[-10:].mean()
    ax1.axhline(y=final_fe, color='red', linestyle='--', alpha=0.7)
    ax1.text(time_steps * 0.8, final_fe + 0.1, '.3f',
            fontsize=10, color='red', fontweight='bold')

    # Bottom plot: Free energy components
    epistemic = 0.4 * free_energy * (0.8 + 0.4 * np.sin(t / 10))
    pragmatic = free_energy - epistemic

    ax2.plot(t, epistemic, 'g-', label='Epistemic', linewidth=2)
    ax2.plot(t, pragmatic, 'r-', label='Pragmatic', linewidth=2)
    ax2.plot(t, free_energy, 'k--', label='Total FE', linewidth=1.5)
    ax2.set_xlabel('Time Steps')
    ax2.set_ylabel('Free Energy Components')
    ax2.set_title('Free Energy Components During Minimization')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "free_energy_dynamics")
    logger.info(f"Saved free energy dynamics: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="free_energy_dynamics.png",
        caption="Free energy minimization dynamics showing convergence over time and epistemic/pragmatic components",
        section="methodology",
        generated_by="generate_fep_visualizations.py"
    )


def create_structure_preservation(viz_engine: VisualizationEngine,
                                figure_manager: FigureManager) -> None:
    """Create structure preservation visualization."""
    # Create system states
    system_states = {
        'internal': np.array([0.5, 0.3, 0.2]),
        'external': np.array([0.1, 0.9]),
        'sensory': np.array([0.4, 0.6])
    }

    fep = FreeEnergyPrinciple(system_states)
    preservation_data = fep.demonstrate_structure_preservation(time_steps=50)

    fig, axes = plt.subplots(3, 1, figsize=(12, 9))
    fig.suptitle('Structure Preservation in Free Energy Minimization', fontweight='bold')

    # Plot internal states evolution
    internal_states = preservation_data['internal_states']
    time_steps = preservation_data['time_steps']

    for i in range(internal_states.shape[1]):
        axes[0].plot(range(len(internal_states)), internal_states[:, i],
                    label=f'Internal State {i+1}', linewidth=2)
    axes[0].set_ylabel('Internal State Values')
    axes[0].set_title('Internal State Evolution (Structure Preservation)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot free energy trajectory
    fe_history = preservation_data['free_energy_history']
    axes[1].plot(range(len(fe_history)), fe_history, 'r-', linewidth=2)
    axes[1].set_ylabel('Free Energy')
    axes[1].set_title('Free Energy Minimization Trajectory')
    axes[1].grid(True, alpha=0.3)

    # Add convergence indicator
    converged = np.std(fe_history[-10:]) < 0.01
    status_color = 'green' if converged else 'orange'
    axes[1].text(time_steps * 0.7, max(fe_history) * 0.8,
                f'Converged: {converged}', fontsize=12, color=status_color,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=status_color, alpha=0.2))

    # Plot structure preservation metric
    # Calculate preservation as stability of internal state distribution
    preservation_metric = []
    for t in range(1, time_steps):
        prev_dist = internal_states[t-1]
        curr_dist = internal_states[t]
        # KL divergence as preservation metric (lower = more preserved)
        kl_div = np.sum(curr_dist * np.log((curr_dist + 1e-10) / (prev_dist + 1e-10)))
        preservation_metric.append(kl_div)

    axes[2].plot(range(1, time_steps), preservation_metric, 'b-', linewidth=2)
    axes[2].set_xlabel('Time Steps')
    axes[2].set_ylabel('Structure Change (KL Divergence)')
    axes[2].set_title('Structure Preservation Metric (Lower = More Stable)')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "structure_preservation")
    logger.info(f"Saved structure preservation: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="structure_preservation.png",
        caption="Structure preservation dynamics showing how systems maintain internal organization through free energy minimization",
        section="methodology",
        generated_by="generate_fep_visualizations.py"
    )


def create_physics_cognition_bridge(viz_engine: VisualizationEngine,
                                  figure_manager: FigureManager) -> None:
    """Create physics-cognition bridge visualization."""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_title('Free Energy Principle: Bridge Between Physics and Cognition',
                fontweight='bold', pad=20)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Left side: Physics
    ax.add_patch(plt.Rectangle((1, 2), 4, 4, fill=True, alpha=0.2, color='blue'))
    ax.text(3, 5, 'PHYSICS\nDOMAIN', ha='center', va='center',
            fontsize=14, fontweight='bold', color='blue')

    physics_concepts = [
        'Thermodynamics',
        'Entropy minimization',
        'System boundaries',
        'Energy conservation',
        'Self-organization'
    ]

    for i, concept in enumerate(physics_concepts):
        ax.text(1.5, 3.5 - i*0.6, f'• {concept}', fontsize=10, color='blue')

    # Right side: Cognition
    ax.add_patch(plt.Rectangle((9, 2), 4, 4, fill=True, alpha=0.2, color='green'))
    ax.text(11, 5, 'COGNITION\nDOMAIN', ha='center', va='center',
            fontsize=14, fontweight='bold', color='green')

    cognition_concepts = [
        'Perception',
        'Learning',
        'Decision making',
        'Action selection',
        'Belief updating'
    ]

    for i, concept in enumerate(cognition_concepts):
        ax.text(9.5, 3.5 - i*0.6, f'• {concept}', fontsize=10, color='green')

    # Center: FEP as bridge
    ax.add_patch(plt.Rectangle((6, 3), 2, 2, fill=True, alpha=0.3, color='red'))
    ax.text(7, 4, 'FREE ENERGY\nPRINCIPLE', ha='center', va='center',
            fontsize=12, fontweight='bold', color='red')

    bridge_concepts = [
        'Unified formalism',
        'Minimization principle',
        'Markov blankets',
        'Variational inference',
        'Structure preservation'
    ]

    for i, concept in enumerate(bridge_concepts):
        ax.text(6.2, 3.5 - i*0.3, f'• {concept}', fontsize=9, color='red')

    # Connecting arrows
    ax.arrow(5, 4, 0.8, 0, head_width=0.1, head_length=0.2,
             fc='purple', ec='purple', alpha=0.7)
    ax.text(5.5, 4.2, 'Unifies', fontsize=10, color='purple')

    ax.arrow(8.2, 4, 0.8, 0, head_width=0.1, head_length=0.2,
             fc='purple', ec='purple', alpha=0.7)
    ax.text(8.7, 4.2, 'Explains', fontsize=10, color='purple')

    # Add explanatory text
    explanation = """
    The Free Energy Principle provides a unified mathematical framework that bridges physics and cognition.
    Diverse phenomena - from thermodynamic systems to cognitive agents - can be understood as minimizing
    variational free energy to maintain structural integrity and adapt to their environments.
    """
    ax.text(7, 1.5, explanation, ha='center', va='center', fontsize=10,
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', alpha=0.3))

    # Add Active Inference connection
    ax.text(7, 1, 'Active Inference applies FEP to cognitive systems',
            ha='center', va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.5))

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "physics_cognition_bridge")
    logger.info(f"Saved physics-cognition bridge: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="physics_cognition_bridge.png",
        caption="Free Energy Principle as the bridge between physics and cognition domains",
        section="methodology",
        generated_by="generate_fep_visualizations.py"
    )


if __name__ == "__main__":
    main()
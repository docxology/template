#!/usr/bin/env python3
"""Generate Quadrant-Specific Examples Visualization.

This script creates visualizations showing specific examples for each quadrant
of the 2x2 framework:
- Quadrant 1: Data processing with EFE
- Quadrant 2: Meta-data organization
- Quadrant 3: Reflective processing
- Quadrant 4: Higher-order reasoning

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure src/ and infrastructure/ are on path FIRST
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))

# Infrastructure imports
from infrastructure.core.logging_utils import get_logger
from infrastructure.documentation.figure_manager import FigureManager

# Import src/ modules
from active_inference import ActiveInferenceFramework
from data_generator import generate_time_series
from generative_models import create_simple_generative_model
from meta_cognition import MetaCognitiveSystem
from visualization import VisualizationEngine

logger = get_logger(__name__)


def main() -> None:
    """Generate quadrant-specific examples."""
    logger.info("Generating quadrant-specific examples...")

    # Setup output directory
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    viz_engine = VisualizationEngine(output_dir=str(output_dir))
    figure_manager = FigureManager()

    # Generate examples for each quadrant
    create_quadrant_1_example(viz_engine, figure_manager)  # Data + Cognitive
    create_quadrant_2_example(viz_engine, figure_manager)  # Meta-Data + Cognitive
    create_quadrant_3_example(viz_engine, figure_manager)  # Data + Meta-Cognitive
    create_quadrant_4_example(viz_engine, figure_manager)  # Meta-Data + Meta-Cognitive

    logger.info("✅ Quadrant examples completed")


def create_quadrant_1_example(viz_engine: VisualizationEngine,
                            figure_manager: FigureManager) -> None:
    """Create Quadrant 1 example: Basic data processing with EFE."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Quadrant 1: Data Processing (Cognitive) - EFE in Action',
                fontweight='bold')

    # Create simple generative model
    model = create_simple_generative_model()
    framework = ActiveInferenceFramework(model)

    # Generate time series data (simulating sensory input)
    time, sensory_data = generate_time_series(n_points=50, trend="sinusoidal")

    # Convert to observations
    observations = np.clip((sensory_data + 1) / 2, 0, 1)  # Normalize to [0,1]
    observation_indices = (observations * (model.n_observations - 1)).astype(int)

    # Simulate EFE calculation for different policies
    policies = [
        np.array([0]),  # Stay in current inference mode
        np.array([1]),  # Switch inference strategy
    ]

    policy_labels = ['Conservative\nInference', 'Exploratory\nInference']
    efe_values = []

    for policy in policies:
        posterior = np.array([0.6, 0.4])  # Current belief state
        efe_total, efe_components = framework.calculate_expected_free_energy(
            posterior, policy
        )
        efe_values.append(efe_total)

    # Top plot: Sensory data and EFE landscape
    ax1.plot(time[:30], observations[:30], 'b-', linewidth=2, label='Sensory Input')
    ax1.set_ylabel('Observation Value')
    ax1.set_title('Raw Sensory Data Processing')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Bottom plot: EFE for different policies
    bars = ax2.bar(policy_labels, efe_values, color=['lightblue', 'lightcoral'], alpha=0.7)
    ax2.set_ylabel('Expected Free Energy (EFE)')
    ax2.set_title('Policy Selection via EFE Minimization')
    ax2.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, value in zip(bars, efe_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom')

    # Add explanation
    explanation = """
    Quadrant 1: Basic cognitive processing of raw sensory data.
    The agent processes observations and selects actions by minimizing EFE,
    balancing epistemic information gain with pragmatic goal achievement.
    """
    fig.text(0.5, 0.02, explanation, ha='center', va='center',
            fontsize=10, style='italic',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.5))

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "quadrant_1_data_cognitive")
    logger.info(f"Saved Quadrant 1 example: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="quadrant_1_data_cognitive.png",
        caption="Quadrant 1 example: Basic data processing showing EFE minimization for policy selection",
        section="experimental_results",
        generated_by="generate_quadrant_examples.py"
    )


def create_quadrant_2_example(viz_engine: VisualizationEngine,
                            figure_manager: FigureManager) -> None:
    """Create Quadrant 2 example: Meta-data organization."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Quadrant 2: Meta-Data Organization (Cognitive) - Enhanced Processing',
                fontweight='bold')

    # Simulate meta-data enhanced processing
    np.random.seed(42)
    n_samples = 100

    # Generate base data
    base_data = np.random.normal(0, 1, n_samples)

    # Add meta-data: confidence scores and timestamps
    confidence_scores = np.random.beta(2, 1, n_samples)  # Skewed toward high confidence
    timestamps = np.arange(n_samples)

    # Quality-based processing: weight by confidence
    quality_weighted = base_data * confidence_scores

    # Top plot: Base data vs quality-weighted
    ax1.plot(timestamps, base_data, 'b-', alpha=0.7, label='Raw Data')
    ax1.plot(timestamps, quality_weighted, 'r-', linewidth=2, label='Quality-Weighted')
    ax1.fill_between(timestamps, base_data, quality_weighted,
                    where=(quality_weighted > base_data), alpha=0.3, color='red')
    ax1.set_ylabel('Data Value')
    ax1.set_title('Meta-Data Enhanced Processing')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Bottom plot: Confidence distribution and processing reliability
    ax2.hist(confidence_scores, bins=20, alpha=0.7, color='green', edgecolor='black')
    ax2.axvline(np.mean(confidence_scores), color='red', linestyle='--',
               linewidth=2, label=f'Mean: {np.mean(confidence_scores):.2f}')
    ax2.set_xlabel('Confidence Score')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Confidence Meta-Data Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add explanation
    explanation = """
    Quadrant 2: Meta-data organization enhances cognitive processing.
    Raw data is processed with additional meta-information (confidence scores,
    timestamps) to improve reliability and temporal awareness of processing.
    """
    fig.text(0.5, 0.02, explanation, ha='center', va='center',
            fontsize=10, style='italic',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.5))

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "quadrant_2_metadata_cognitive")
    logger.info(f"Saved Quadrant 2 example: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="quadrant_2_metadata_cognitive.png",
        caption="Quadrant 2 example: Meta-data organization showing quality-weighted processing with confidence scores",
        section="experimental_results",
        generated_by="generate_quadrant_examples.py"
    )


def create_quadrant_3_example(viz_engine: VisualizationEngine,
                            figure_manager: FigureManager) -> None:
    """Create Quadrant 3 example: Reflective processing (meta-cognitive)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Quadrant 3: Reflective Processing (Meta-Cognitive) - Self-Monitoring',
                fontweight='bold')

    # Simulate meta-cognitive monitoring
    meta_system = MetaCognitiveSystem()

    # Simulate different confidence scenarios
    scenarios = [
        {'beliefs': np.array([0.9, 0.05, 0.05]), 'uncertainty': 0.1, 'label': 'High Confidence'},
        {'beliefs': np.array([0.6, 0.3, 0.1]), 'uncertainty': 0.3, 'label': 'Moderate Confidence'},
        {'beliefs': np.array([0.4, 0.3, 0.3]), 'uncertainty': 0.7, 'label': 'Low Confidence'}
    ]

    confidence_scores = []
    attention_allocations = []

    for scenario in scenarios:
        assessment = meta_system.assess_inference_confidence(
            scenario['beliefs'], scenario['uncertainty']
        )
        confidence_scores.append(assessment['confidence_score'])

        # Get attention allocation
        attention = meta_system.adjust_attention_allocation(
            assessment, {'monitoring': 1.0, 'processing': 1.0, 'evaluation': 1.0}
        )
        attention_allocations.append(attention['monitoring'])

    # Top plot: Confidence assessment across scenarios
    bars1 = ax1.bar([s['label'] for s in scenarios], confidence_scores,
                   color=['green', 'orange', 'red'], alpha=0.7)
    ax1.set_ylabel('Confidence Score')
    ax1.set_title('Meta-Cognitive Confidence Assessment')
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, score in zip(bars1, confidence_scores):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{score:.2f}', ha='center', va='bottom')

    # Bottom plot: Attention allocation based on confidence
    bars2 = ax2.bar([s['label'] for s in scenarios], attention_allocations,
                   color=['lightgreen', 'orange', 'red'], alpha=0.7)
    ax2.set_ylabel('Attention Allocation (Monitoring)')
    ax2.set_title('Adaptive Attention Allocation')
    ax2.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, alloc in zip(bars2, attention_allocations):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{alloc:.2f}', ha='center', va='bottom')

    # Add explanation
    explanation = """
    Quadrant 3: Reflective processing enables meta-cognitive evaluation.
    The system assesses its own confidence in inferences and adaptively
    allocates attention resources based on self-assessment.
    """
    fig.text(0.5, 0.02, explanation, ha='center', va='center',
            fontsize=10, style='italic',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.5))

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "quadrant_3_data_metacognitive")
    logger.info(f"Saved Quadrant 3 example: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="quadrant_3_data_metacognitive.png",
        caption="Quadrant 3 example: Meta-cognitive reflective processing showing confidence assessment and adaptive attention",
        section="experimental_results",
        generated_by="generate_quadrant_examples.py"
    )


def create_quadrant_4_example(viz_engine: VisualizationEngine,
                            figure_manager: FigureManager) -> None:
    """Create Quadrant 4 example: Higher-order reasoning."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_title('Quadrant 4: Higher-Order Reasoning (Meta-Cognitive) - Framework Adaptation',
                fontweight='bold', pad=20)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Draw hierarchical reasoning structure
    levels = [
        {'name': 'Framework Level', 'y': 6.5, 'color': 'red', 'desc': 'Meta-epistemic/meta-pragmatic'},
        {'name': 'Strategy Level', 'y': 4.5, 'color': 'orange', 'desc': 'Processing strategies'},
        {'name': 'Inference Level', 'y': 2.5, 'color': 'blue', 'desc': 'Basic inference'}
    ]

    for level in levels:
        # Draw level box
        ax.add_patch(plt.Rectangle((2, level['y']-0.3), 8, 0.6,
                                 fill=True, alpha=0.3, color=level['color']))
        ax.text(6, level['y'], f"{level['name']}: {level['desc']}",
               ha='center', va='center', fontsize=11, fontweight='bold')

    # Draw meta-level connections
    ax.arrow(6, 6.2, 0, -1.2, head_width=0.1, head_length=0.2,
             fc='red', ec='red', alpha=0.7)
    ax.text(6.5, 5, 'Controls', fontsize=9, color='red')

    ax.arrow(6, 4.2, 0, -1.2, head_width=0.1, head_length=0.2,
             fc='orange', ec='orange', alpha=0.7)
    ax.text(6.5, 3, 'Selects', fontsize=9, color='orange')

    # Add reasoning examples
    examples = [
        "Epistemic framework: What can be known?",
        "Pragmatic framework: What matters?",
        "Strategy adaptation: When to switch approaches?",
        "Meta-cognitive evaluation: How well am I processing?"
    ]

    for i, example in enumerate(examples):
        y_pos = 1.5 - i * 0.4
        color = ['red', 'red', 'orange', 'blue'][i]
        ax.text(6, y_pos, f"• {example}", ha='center', va='center',
               fontsize=10, color=color)

    # Add central concept
    ax.text(6, 7.2, 'Higher-Order Reasoning', ha='center', va='center',
            fontsize=14, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.5))

    # Add explanation
    explanation = """
    Quadrant 4: Higher-order reasoning involves meta-data about meta-cognition.
    The system reasons about its own reasoning frameworks, enabling framework-level
    adaptation and meta-epistemic/meta-pragmatic control.
    """
    ax.text(6, 0.8, explanation, ha='center', va='center',
            fontsize=10, style='italic',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.5))

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "quadrant_4_metadata_metacognitive")
    logger.info(f"Saved Quadrant 4 example: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="quadrant_4_metadata_metacognitive.png",
        caption="Quadrant 4 example: Higher-order reasoning showing framework-level meta-cognitive processing",
        section="experimental_results",
        generated_by="generate_quadrant_examples.py"
    )


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Generate comprehensive research figures for the manuscript.

This script demonstrates how to create multiple figures that are referenced
in the markdown files, showing proper figure generation, labeling, and
cross-referencing capabilities.

IMPORTANT: This script demonstrates integration with src/ modules by using
the mathematical functions from example.py to process data for the figures.
"""
from __future__ import annotations

import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from typing import Tuple, List


def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path for imports."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def _setup_directories() -> Tuple[str, str, str]:
    """Setup output directories and return paths."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(repo_root, "output")
    data_dir = os.path.join(output_dir, "data")
    figure_dir = os.path.join(output_dir, "figures")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(figure_dir, exist_ok=True)
    
    return output_dir, data_dir, figure_dir


def generate_convergence_plot(figure_dir: str, data_dir: str) -> str:
    """Generate convergence analysis plot using src/ functions."""
    # Import src/ functions for data processing
    try:
        from example import add_numbers, multiply_numbers, calculate_average
        print("✅ Using src/ functions for convergence plot")
    except ImportError as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""
    
    # Generate synthetic convergence data
    iterations = np.arange(1, 101)
    
    # Use src/ functions to process the data
    our_method_raw = 2.0 * np.exp(-0.1 * iterations) + 0.1
    baseline_raw = 1.5 * np.exp(-0.05 * iterations) + 0.2
    
    # Apply src/ functions to demonstrate integration
    our_method_list: List[float] = []
    baseline_list: List[float] = []
    for i, (our_val, base_val) in enumerate(zip(our_method_raw, baseline_raw)):
        # Use add_numbers and multiply_numbers from src/
        our_processed = add_numbers(our_val, 0.0)  # Identity operation
        base_processed = multiply_numbers(base_val, 1.0)  # Identity operation
        our_method_list.append(our_processed)
        baseline_list.append(base_processed)
    
    our_method = np.array(our_method_list)
    baseline = np.array(baseline_list)
    
    # Calculate statistics using src/ functions
    our_avg = calculate_average(our_method.tolist())
    base_avg = calculate_average(baseline.tolist())
    
    print(f"Convergence analysis using src/ functions:")
    print(f"  Our method average: {our_avg:.6f}")
    print(f"  Baseline average: {base_avg:.6f}")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogy(iterations, our_method, 'b-', linewidth=2, label='Our Method')
    ax.semilogy(iterations, baseline, 'r--', linewidth=2, label='Baseline')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Objective Value')
    ax.set_title('Algorithm Convergence Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add statistics as text
    ax.text(0.05, 0.95, f'Our Method Avg: {our_avg:.3f}\nBaseline Avg: {base_avg:.3f}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    # Save figure
    figure_path = os.path.join(figure_dir, "convergence_plot.png")
    fig.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Save data
    data_path = os.path.join(data_dir, "convergence_data.npz")
    np.savez(data_path, iterations=iterations, our_method=our_method, baseline=baseline,
              our_avg=our_avg, base_avg=base_avg)
    
    print(figure_path)
    print(data_path)
    return figure_path


def generate_experimental_setup(figure_dir: str, data_dir: str) -> str:
    """Generate experimental setup diagram."""
    # Import src/ functions for validation
    try:
        from example import is_even, is_odd
        print("✅ Using src/ functions for experimental setup validation")
        
        # Demonstrate src/ function usage
        num_components = 3
        print(f"Number of components: {num_components}")
        print(f"  Is even: {is_even(num_components)}")
        print(f"  Is odd: {is_odd(num_components)}")
    except ImportError as e:
        print(f"❌ Failed to import from src/example.py: {e}")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a simple flowchart-like diagram
    components = ['Data\nPreprocessing', 'Algorithm\nExecution', 'Performance\nEvaluation']
    x_positions = [2, 6, 10]
    y_positions = [4, 4, 4]
    
    for i, (comp, x, y) in enumerate(zip(components, x_positions, y_positions)):
        # Draw boxes
        rect = plt.Rectangle((x-1, y-0.5), 2, 1, facecolor='lightblue', 
                           edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, comp, ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Draw arrows
        if i < len(components) - 1:
            ax.arrow(x+1, y, 1.5, 0, head_width=0.2, head_length=0.2, 
                    fc='black', ec='black', linewidth=2)
    
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.set_title('Experimental Pipeline', fontsize=14, fontweight='bold')
    ax.axis('off')
    
    figure_path = os.path.join(figure_dir, "experimental_setup.png")
    fig.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(figure_path)
    return figure_path


def main() -> None:
    """Generate all research figures using src/ modules."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    _ensure_src_on_path()
    
    output_dir, data_dir, figure_dir = _setup_directories()
    
    print("Generating research figures using src/ modules...")
    
    # Generate all figures
    figures = [
        generate_convergence_plot(figure_dir, data_dir),
        generate_experimental_setup(figure_dir, data_dir),
    ]
    
    # Filter out any empty results
    figures = [f for f in figures if f]
    
    print(f"\n✅ Generated {len(figures)} research figures:")
    for fig in figures:
        print(f"   - {os.path.basename(fig)}")
    
    print(f"\n📁 All outputs saved to: {output_dir}")
    print(f"   Figures: {figure_dir}")
    print(f"   Data: {data_dir}")
    
    print(f"\n🔗 Integration with src/ modules demonstrated:")
    print(f"   - Mathematical functions from example.py used for data processing")
    print(f"   - Statistical analysis using src/ functions")
    print(f"   - Proper error handling for missing imports")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Example project-specific script for generating figures.

This script demonstrates how to create project-specific scripts that will be
automatically executed by the generic render_pdf.sh system.

The script should:
1. Generate any necessary figures/data
2. Save outputs to the appropriate output directories
3. Print the paths of generated files
4. Handle errors gracefully
5. IMPORTANT: Use methods from src/ modules to demonstrate integration
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def _setup_paths() -> None:
    """Set up Python paths for src/ and infrastructure modules."""
    # Check if PYTHONPATH has been set (e.g., by test environment)
    pythonpath = os.environ.get("PYTHONPATH", "")
    if pythonpath:
        # Add PYTHONPATH entries to sys.path if not already there
        for path in pythonpath.split(":"):
            if path and path not in sys.path:
                sys.path.insert(0, path)

    # Detect execution context - could be project root or test environment
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Parent of scripts/
    src_path = os.path.join(project_root, "src")

    # If src_path doesn't exist, we might be in a test environment - look for src/ relative to current dir
    if not os.path.exists(src_path):
        # Check if we're in a test environment with src/ in current directory
        test_src_path = os.path.join(os.getcwd(), "src")
        if os.path.exists(test_src_path):
            src_path = test_src_path
            project_root = os.getcwd()

    # Only add paths if they're not already there, and don't remove existing paths
    # This allows environment variables like PYTHONPATH to take precedence
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Try to find repo root (may not exist in test environments)
    repo_root = os.path.dirname(project_root)
    if (
        os.path.exists(os.path.join(repo_root, "infrastructure"))
        and repo_root not in sys.path
    ):
        sys.path.insert(0, repo_root)


def main() -> None:
    """Generate example figure and data using src/ modules."""
    # Set matplotlib backend for headless operation
    os.environ.setdefault("MPLBACKEND", "Agg")

    # Set up paths dynamically based on execution context
    _setup_paths()

    # Import logger after path setup - with graceful fallback
    try:
        from src.utils.logging import get_logger

        logger = get_logger(__name__)
    except ImportError:
        # Fallback to standard logging if src.utils.logging not available
        import logging

        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        logger = logging.getLogger(__name__)

    # Import scientific modules from src/
    try:
        from example import (add_numbers, calculate_average, find_maximum,
                             find_minimum, multiply_numbers)

        logger.info("✅ Successfully imported functions from src/example.py")
        print(
            "✅ Successfully imported functions from src/example.py"
        )  # Also print for test capture
    except (ImportError, SyntaxError, ModuleNotFoundError) as e:
        logger.error(f"❌ Failed to import from src/example.py: {e}")
        print(f"❌ Failed to import from src/example.py: {e}")
        return

    # Import project-specific modules (if they exist)
    try:
        from paths import get_data_dir, get_figure_dir, get_output_dir

        output_dir = get_output_dir()
        data_dir = get_data_dir()
        figure_dir = get_figure_dir()
    except ImportError:
        # Fallback if paths module doesn't exist
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        output_dir = os.path.join(repo_root, "output")
        data_dir = os.path.join(output_dir, "data")
        figure_dir = os.path.join(output_dir, "figures")

        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(figure_dir, exist_ok=True)

    # Generate example data using src/ functions
    x = np.linspace(0, 10, 100)

    # Use src/ functions to process the data
    y_values = []
    for xi in x:
        # Use add_numbers and multiply_numbers from src/
        base = add_numbers(xi, 1.0)  # Add 1 to each x value
        scaled = multiply_numbers(base, 0.5)  # Scale by 0.5
        y_values.append(scaled)

    y = np.array(y_values)

    # Apply additional processing using src/ functions
    y_processed = y * np.sin(x) * np.exp(-x / 5)

    # Use src/ functions to analyze the data
    avg_y = calculate_average(y_processed.tolist())
    max_y = find_maximum(y_processed.tolist())
    min_y = find_minimum(y_processed.tolist())

    logger.info(f"Data analysis using src/ functions:")
    logger.info(f"  Average: {avg_y:.6f}")
    logger.info(f"  Maximum: {max_y:.6f}")
    logger.info(f"  Minimum: {min_y:.6f}")

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left subplot: Original data
    ax1.plot(x, y, "b-", linewidth=2, label="Processed Data")
    ax1.set_xlabel("X")
    ax1.set_ylabel("Y")
    ax1.set_title("Data Processing with src/ Functions")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Right subplot: Final result
    ax2.plot(x, y_processed, "r-", linewidth=2, label="Final Result")
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_title("Example Project Figure")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add statistics as text
    ax2.text(
        0.05,
        0.95,
        f"Avg: {avg_y:.3f}\nMax: {max_y:.3f}\nMin: {min_y:.3f}",
        transform=ax2.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()

    # Save figure
    figure_path = os.path.join(figure_dir, "example_figure.png")
    fig.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Register figure with FigureManager for cross-referencing
    try:
        from src.utils.figure_manager import FigureManager

        fm = FigureManager(
            registry_file=os.path.join(figure_dir, "figure_registry.json")
        )
        fm.register_figure(
            filename="example_figure.png",
            caption="Example project figure showing data processing with src/ functions",
            label="fig:example_figure",
            section="introduction",
            generated_by="example_figure.py",
        )
        logger.info(f"  Registered figure: fig:example_figure")
    except ImportError as e:
        logger.warning(
            f"  ⚠️  Could not register figure (FigureManager not available): {e}"
        )

    # Save data
    data_path = os.path.join(data_dir, "example_data.npz")
    np.savez(
        data_path,
        x=x,
        y=y,
        y_processed=y_processed,
        avg_y=avg_y,
        max_y=max_y,
        min_y=min_y,
    )

    csv_path = os.path.join(data_dir, "example_data.csv")
    with open(csv_path, "w") as f:
        f.write("x,y,y_processed\n")
        for xi, yi, ypi in zip(x, y, y_processed):
            f.write(f"{xi:.6f},{yi:.6f},{ypi:.6f}\n")

    # Print generated paths (this is what the render system captures)
    print(f"Generated: {figure_path}")
    print(f"Generated: {data_path}")
    print(f"Generated: {csv_path}")

    logger.info(f"✅ Generated example figure using src/ functions: {figure_path}")
    logger.info(f"✅ Generated example data: {data_path}")
    logger.info(f"✅ Generated example CSV: {csv_path}")

    # Also print key messages for test capture
    print(f"✅ Generated example figure using src/ functions: {figure_path}")
    print(f"✅ Generated example data: {data_path}")
    print(f"✅ Generated example CSV: {csv_path}")


if __name__ == "__main__":
    main()

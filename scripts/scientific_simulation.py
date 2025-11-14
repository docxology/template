#!/usr/bin/env python3
"""Scientific simulation script demonstrating the simulation framework.

This script demonstrates how to use src/ modules to:
1. Set up parameters
2. Run simulations
3. Generate results and figures
4. Create analysis reports

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure src/ is on path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

# Import src/ modules
from data_generator import generate_time_series, generate_synthetic_data
from figure_manager import FigureManager
from parameters import ParameterSet, ParameterSweep
from performance import analyze_convergence, analyze_scalability
from reporting import ReportGenerator
from simulation import SimpleSimulation, SimulationBase
from statistics import calculate_descriptive_stats
from validation import ValidationFramework


def run_simulation_example() -> None:
    """Run a simple simulation example."""
    print("Running scientific simulation example...")
    
    # Set up parameters
    params = ParameterSet()
    params.add_parameter("max_iterations", 100)
    params.add_parameter("target_value", 5.0)
    
    # Create simulation
    sim = SimpleSimulation(
        parameters=params.parameters,
        seed=42,
        output_dir="output/simulations"
    )
    
    # Run simulation
    print("Running simulation...")
    state = sim.run(max_iterations=100, verbose=True)
    
    # Save results
    print("Saving results...")
    saved_files = sim.save_results("simulation_example")
    for fmt, path in saved_files.items():
        print(f"  Saved {fmt}: {path}")
    
    print("✅ Simulation complete")


def run_parameter_sweep_example() -> None:
    """Run parameter sweep example."""
    print("\nRunning parameter sweep example...")
    
    # Base parameters
    base_params = ParameterSet()
    base_params.add_parameter("max_iterations", 50)
    base_params.add_parameter("target_value", 5.0)
    
    # Create sweep
    sweep = ParameterSweep(base_params)
    sweep.add_sweep("target_value", [3.0, 5.0, 7.0])
    
    print(f"Total combinations: {sweep.get_sweep_size()}")
    
    # Run all combinations
    results = []
    for i, params in enumerate(sweep.generate_combinations()):
        print(f"  Running combination {i+1}/{sweep.get_sweep_size()}...")
        sim = SimpleSimulation(parameters=params, seed=42+i)
        state = sim.run(max_iterations=50, verbose=False)
        results.append({
            "parameters": params,
            "final_value": state.results.get(f"iteration_{state.iteration-1}", {}).get("value", 0)
        })
    
    print(f"✅ Parameter sweep complete: {len(results)} runs")


def generate_analysis_figures() -> None:
    """Generate analysis figures using src/ modules."""
    print("\nGenerating analysis figures...")
    
    # Generate data
    time, values = generate_time_series(
        n_points=100,
        trend="sinusoidal",
        noise_level=0.1,
        seed=42
    )
    
    # Analyze convergence
    convergence = analyze_convergence(values, target=None)
    print(f"  Convergence: {convergence.is_converged}")
    
    # Calculate statistics
    stats = calculate_descriptive_stats(values)
    print(f"  Mean: {stats.mean:.4f}, Std: {stats.std:.4f}")
    
    # Create figure using src/ visualization
    from visualization import VisualizationEngine
    from plots import plot_line, plot_convergence
    
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()
    
    # Plot time series
    plot_line(time, values, ax=ax, label="Time Series", color=engine.get_color(0))
    engine.apply_publication_style(ax, "Time Series Analysis", "Time", "Value", grid=True, legend=True)
    
    # Save figure
    figure_manager = FigureManager()
    saved = engine.save_figure(fig, "scientific_simulation_timeseries")
    print(f"  Saved figure: {saved['png']}")
    
    # Register figure
    fig_meta = figure_manager.register_figure(
        filename="scientific_simulation_timeseries.png",
        caption="Time series data generated for scientific simulation analysis",
        section="experimental_results",
        generated_by="scientific_simulation.py"
    )
    print(f"  Registered figure: {fig_meta.label}")
    
    plt.close(fig)


def generate_report() -> None:
    """Generate analysis report."""
    print("\nGenerating analysis report...")
    
    # Generate some results
    data = generate_synthetic_data(100, n_features=1, distribution="normal", seed=42)
    stats = calculate_descriptive_stats(data)
    
    # Create report
    report_gen = ReportGenerator(output_dir="output/reports")
    
    results = {
        "summary": {
            "mean": stats.mean,
            "std": stats.std,
            "median": stats.median
        },
        "findings": [
            "Simulation completed successfully",
            f"Mean value: {stats.mean:.4f}",
            f"Standard deviation: {stats.std:.4f}"
        ],
        "tables": {
            "Statistics": {
                "Metric": ["Mean", "Std", "Median", "Min", "Max"],
                "Value": [
                    f"{stats.mean:.4f}",
                    f"{stats.std:.4f}",
                    f"{stats.median:.4f}",
                    f"{stats.min:.4f}",
                    f"{stats.max:.4f}"
                ]
            }
        }
    }
    
    # Generate markdown report
    report_path = report_gen.generate_markdown_report(
        "Scientific Simulation Report",
        results,
        "simulation_report"
    )
    print(f"  Generated report: {report_path}")
    
    print("✅ Report generation complete")


def validate_results() -> None:
    """Validate simulation results."""
    print("\nValidating results...")
    
    validator = ValidationFramework()
    
    # Generate test data
    data = generate_synthetic_data(100, distribution="normal", seed=42)
    
    # Validate bounds
    validator.validate_bounds(data, "test_data", min_value=-5.0, max_value=5.0)
    
    # Validate sanity
    validator.validate_sanity(
        float(data.mean()),
        "mean_value",
        expected_order_of_magnitude=0.1
    )
    
    # Detect anomalies
    validator.detect_anomalies(data, method="iqr", threshold=1.5)
    
    # Generate validation report
    report = validator.generate_validation_report()
    print(f"  Validation checks: {report['summary']['total_checks']}")
    print(f"  Passed: {report['summary']['passed']}")
    print(f"  Failed: {report['summary']['failed']}")
    
    print("✅ Validation complete")


def main() -> None:
    """Main function orchestrating the scientific simulation workflow."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    
    # Ensure output directories exist
    for dir_path in ["output/simulations", "output/figures", "output/reports"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    try:
        # Run simulation
        run_simulation_example()
        
        # Run parameter sweep
        run_parameter_sweep_example()
        
        # Generate figures
        generate_analysis_figures()
        
        # Generate report
        generate_report()
        
        # Validate results
        validate_results()
        
        print("\n✅ All scientific simulation tasks completed successfully!")
        print("\nGenerated outputs:")
        print("  - Simulations: output/simulations/")
        print("  - Figures: output/figures/")
        print("  - Reports: output/reports/")
        
    except ImportError as e:
        print(f"❌ Failed to import from src/ modules: {e}")
        print("Make sure all src/ modules are available")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    main()


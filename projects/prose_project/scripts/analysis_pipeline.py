#!/usr/bin/env python3
"""Analysis pipeline script for prose project.

This script demonstrates mathematical visualization capabilities by generating
publication-quality figures for the manuscript. It serves as a thin orchestrator
that imports mathematical functions from src/ and generates figures for
manuscript integration.
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add project src to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from prose_smoke import identity, constant_value

# Add infrastructure imports for performance monitoring
try:
    # Ensure repo root is on path for infrastructure imports
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    from infrastructure.core import (
        monitor_performance,
        ProgressBar,
        get_logger,
        TemplateError,
        CheckpointManager,
        retry_with_backoff,
        SystemHealthChecker,
        log_operation,
        log_success,
        log_stage,
    )
    from infrastructure.core.exceptions import (
        ScriptExecutionError,
        ValidationError,
        BuildError,
        TemplateError,
    )
    from infrastructure.rendering import (
        RenderManager,
        get_render_manager,
    )
    from infrastructure.publishing import (
        extract_publication_metadata,
        generate_citation_bibtex,
    )
    from infrastructure.core.logging_utils import (
        log_operation,
        log_success,
        log_stage,
    )
    from infrastructure.scientific import (
        check_numerical_stability,
        benchmark_function,
    )
    from infrastructure.reporting import (
        generate_output_summary,
        get_error_aggregator,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False


def run_scientific_analysis():
    """Run scientific analysis demonstrating infrastructure capabilities."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    import time
    start_time = time.time()

    if logger:
        logger.info("Running scientific analysis...")
        logger.info("Starting numerical stability and performance benchmarking")

    try:
        # Define test functions for analysis
        def linear_function(x):
            return 2.0 * x + 1.0

        def quadratic_function(x):
            return x**2 - 4*x + 4

        def exponential_function(x):
            return np.exp(0.5 * x)

        test_functions = [
            ("Linear", linear_function),
            ("Quadratic", quadratic_function),
            ("Exponential", exponential_function),
        ]

        analysis_results = {}

        for func_name, func in test_functions:
            func_start_time = time.time()
            if logger:
                logger.info(f"Analyzing {func_name} function...")

            # Test numerical stability
            try:
                test_inputs = np.linspace(-5, 5, 100).tolist()
                if logger:
                    logger.debug(f"  Testing numerical stability with {len(test_inputs)} inputs")
                stability_result = check_numerical_stability(
                    func,
                    test_inputs=test_inputs,
                    tolerance=1e-12
                )
                stability_duration = time.time() - func_start_time
                if logger:
                    is_stable = stability_result.stability_score > 0.8
                    logger.info(f"  Stability: {'✅ Stable' if is_stable else '⚠️ Unstable'} (score: {stability_result.stability_score:.4f}, {stability_duration:.3f}s)")
            except Exception as e:
                if logger:
                    logger.error(f"  Stability check failed for {func_name}: {e}")
                    logger.error(f"    Function: {func.__name__}")
                    logger.error(f"    Error type: {type(e).__name__}")
                raise

            # Benchmark performance
            try:
                benchmark_result = benchmark_function(
                    func,
                    test_inputs=[np.array([i]) for i in np.linspace(-5, 5, 20)],
                    iterations=10
                )
                if logger:
                    logger.info(f"  Benchmark: {benchmark_result.execution_time:.6f}s avg")
            except TypeError as e:
                if logger:
                    logger.error(f"  Benchmark failed for {func_name}: {e}")
                    logger.error(f"    Function: {func.__name__}")
                    logger.error(f"    Expected parameter: iterations (not num_runs)")
                raise
            except AttributeError as e:
                if logger:
                    logger.error(f"  Benchmark result access failed for {func_name}: {e}")
                    logger.error(f"    BenchmarkResult is a dataclass, use .execution_time attribute (not dict access)")
                raise
            except Exception as e:
                if logger:
                    logger.error(f"  Unexpected benchmark error for {func_name}: {e}")
                raise

            analysis_results[func_name] = {
                'stability': stability_result,
                'benchmark': benchmark_result,
            }

        # Save analysis results
        output_dir = project_root / "output" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)

        analysis_path = output_dir / "scientific_analysis.json"
        import json

        # Convert results to serializable format
        serializable_results = {}
        for func_name, results in analysis_results.items():
            # Handle StabilityTest dataclass
            stability_data = results['stability']
            if hasattr(stability_data, 'stability_score'):
                # StabilityTest dataclass
                stability_dict = {
                    'overall_stable': bool(stability_data.stability_score > 0.8),  # Convert numpy bool to Python bool
                    'stability_score': float(stability_data.stability_score),
                    'function_name': str(stability_data.function_name),
                    'test_name': str(stability_data.test_name),
                    'input_range': [float(stability_data.input_range[0]), float(stability_data.input_range[1])],
                    'actual_behavior': str(stability_data.actual_behavior),
                    'recommendations': [str(r) for r in stability_data.recommendations],  # Ensure all items are strings
                }
            else:
                # Legacy dict format (for backward compatibility)
                stability_dict = {
                    'overall_stable': bool(stability_data.get('overall_stable', False)),  # Ensure Python bool
                    'max_gradient': float(stability_data.get('max_gradient', 0.0)),
                    'condition_number': float(stability_data.get('condition_number', 0.0)),
                }
            
            # Handle BenchmarkResult dataclass
            benchmark_data = results['benchmark']
            if hasattr(benchmark_data, 'execution_time'):
                # BenchmarkResult dataclass - ensure all values are JSON serializable
                benchmark_dict = {
                    'execution_time': float(benchmark_data.execution_time),
                    'iterations': int(benchmark_data.iterations) if hasattr(benchmark_data, 'iterations') else 0,
                    'memory_usage': float(benchmark_data.memory_usage) if hasattr(benchmark_data, 'memory_usage') and benchmark_data.memory_usage is not None else None,
                    'function_name': str(benchmark_data.function_name) if hasattr(benchmark_data, 'function_name') else '',
                    'result_summary': str(benchmark_data.result_summary) if hasattr(benchmark_data, 'result_summary') else '',
                    'timestamp': str(benchmark_data.timestamp) if hasattr(benchmark_data, 'timestamp') else '',
                    'parameters': {str(k): (bool(v) if isinstance(v, (bool, np.bool_)) else (float(v) if isinstance(v, (int, float, np.number)) else str(v))) for k, v in benchmark_data.parameters.items()} if hasattr(benchmark_data, 'parameters') and benchmark_data.parameters else {},
                }
            else:
                # Legacy dict format
                benchmark_dict = {
                    'execution_time': float(benchmark_data.get('execution_time', 0.0)),
                    'iterations': int(benchmark_data.get('iterations', 0)),
                    'memory_usage': float(benchmark_data.get('memory_usage', 0.0)) if benchmark_data.get('memory_usage') is not None else None,
                }
            
            serializable_results[func_name] = {
                'stability': stability_dict,
                'benchmark': benchmark_dict,
            }

        with open(analysis_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        total_duration = time.time() - start_time
        if logger:
            logger.info(f"Saved scientific analysis to: {analysis_path}")
            logger.info(f"Scientific analysis completed in {total_duration:.2f}s")
        return analysis_path

    except ValidationError as e:
        total_duration = time.time() - start_time
        if logger:
            logger.warning(f"Scientific analysis validation failed after {total_duration:.2f}s: {e}")
            logger.warning(f"  Error type: ValidationError")
            logger.warning(f"  Suggestion: Check input data validity and function implementations")
        return None
    except TypeError as e:
        total_duration = time.time() - start_time
        if logger:
            logger.error(f"Scientific analysis parameter error after {total_duration:.2f}s: {e}")
            logger.error(f"  Error type: TypeError (likely parameter mismatch)")
            logger.error(f"  Suggestion: Verify function signatures match expected parameters")
        return None
    except AttributeError as e:
        total_duration = time.time() - start_time
        if logger:
            logger.error(f"Scientific analysis attribute error after {total_duration:.2f}s: {e}")
            logger.error(f"  Error type: AttributeError (likely accessing wrong object type)")
            logger.error(f"  Suggestion: Check if result objects are dataclasses vs dicts")
        return None
    except Exception as e:
        total_duration = time.time() - start_time
        if logger:
            logger.error(f"Unexpected error in scientific analysis after {total_duration:.2f}s: {e}")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.error(f"  Suggestion: Review error details and check system requirements")
        return None


def generate_mathematical_visualization():
    """Generate mathematical visualization for manuscript."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Generating mathematical visualization...")

    # Create sample mathematical data
    x = np.linspace(-2, 2, 100)

    # Generate different mathematical functions
    functions = {
        'Linear': x,
        'Quadratic': x**2,
        'Cubic': x**3,
        'Exponential': np.exp(x/2),
        'Sine': np.sin(2*np.pi*x),
    }

    # Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Function comparison
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    for i, (name, y) in enumerate(functions.items()):
        ax1.plot(x, y, color=colors[i], linewidth=2, label=name)
    ax1.set_xlabel('x')
    ax1.set_ylabel('f(x)')
    ax1.set_title('Mathematical Function Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Convergence behavior (simulated)
    iterations = np.arange(1, 51)
    convergence_rates = [1/np.sqrt(k) for k in iterations]  # 1/sqrt(k) convergence
    ax2.plot(iterations, convergence_rates, 'bo-', linewidth=2, markersize=4)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Error')
    ax2.set_title('Algorithmic Convergence (1/√k)')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Statistical distribution
    np.random.seed(42)  # For reproducibility
    data = np.random.normal(0, 1, 1000)
    ax3.hist(data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    ax3.axvline(np.mean(data), color='red', linestyle='--', linewidth=2, label='Mean')
    ax3.axvline(np.median(data), color='green', linestyle='--', linewidth=2, label='Median')
    ax3.set_xlabel('Value')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Statistical Distribution Analysis')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Mathematical relationships
    x_vals = np.linspace(0.1, 5, 50)
    y1 = np.log(x_vals)  # Logarithmic growth
    y2 = np.sqrt(x_vals)  # Square root growth
    y3 = x_vals**0.3  # Sub-linear growth

    ax4.plot(x_vals, y1, 'r-', linewidth=2, label='log(x)')
    ax4.plot(x_vals, y2, 'g-', linewidth=2, label='√x')
    ax4.plot(x_vals, x_vals, 'b-', linewidth=2, label='x')
    ax4.plot(x_vals, y3, 'm-', linewidth=2, label='x^0.3')
    ax4.set_xlabel('x')
    ax4.set_ylabel('f(x)')
    ax4.set_title('Growth Rate Comparisons')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_path = output_dir / "mathematical_visualization.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    if logger:
        logger.info(f"Saved mathematical visualization to: {plot_path}")
    return plot_path


def generate_mathematical_visualization_with_progress():
    """Generate mathematical visualization for manuscript with progress tracking."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    print("Generating mathematical visualization...")

    # Create sample mathematical data
    x = np.linspace(-2, 2, 100)

    # Generate different mathematical functions
    functions = {
        'Linear': x,
        'Quadratic': x**2,
        'Cubic': x**3,
        'Exponential': np.exp(x/2),
        'Sine': np.sin(2*np.pi*x),
    }

    # Create visualization with progress tracking
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Function comparison
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    for i, (name, y) in enumerate(functions.items()):
        ax1.plot(x, y, color=colors[i], linewidth=2, label=name)
    ax1.set_xlabel('x')
    ax1.set_ylabel('f(x)')
    ax1.set_title('Mathematical Function Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Convergence behavior (simulated)
    iterations = np.arange(1, 51)
    convergence_rates = [1/np.sqrt(k) for k in iterations]  # 1/sqrt(k) convergence
    ax2.plot(iterations, convergence_rates, 'bo-', linewidth=2, markersize=4)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Error')
    ax2.set_title('Algorithmic Convergence (1/√k)')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Statistical distribution
    np.random.seed(42)  # For reproducibility
    data = np.random.normal(0, 1, 1000)
    ax3.hist(data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    ax3.axvline(np.mean(data), color='red', linestyle='--', linewidth=2, label='Mean')
    ax3.axvline(np.median(data), color='green', linestyle='--', linewidth=2, label='Median')
    ax3.set_xlabel('Value')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Statistical Distribution Analysis')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Mathematical relationships
    x_vals = np.linspace(0.1, 5, 50)
    y1 = np.log(x_vals)  # Logarithmic growth
    y2 = np.sqrt(x_vals)  # Square root growth
    y3 = x_vals**0.3  # Sub-linear growth

    ax4.plot(x_vals, y1, 'r-', linewidth=2, label='log(x)')
    ax4.plot(x_vals, y2, 'g-', linewidth=2, label='√x')
    ax4.plot(x_vals, x_vals, 'b-', linewidth=2, label='x')
    ax4.plot(x_vals, y3, 'm-', linewidth=2, label='x^0.3')
    ax4.set_xlabel('x')
    ax4.set_ylabel('f(x)')
    ax4.set_title('Growth Rate Comparisons')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_path = output_dir / "mathematical_visualization.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved mathematical visualization to: {plot_path}")
    return plot_path


def generate_theoretical_analysis():
    """Generate theoretical analysis visualization."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Generating theoretical analysis visualization...")

    # Create data for theoretical analysis
    x = np.linspace(0.01, 2, 100)

    # Different convergence rates
    linear_conv = 1 - 0.1 * x  # Linear convergence
    quadratic_conv = np.exp(-x)  # Quadratic convergence
    superlinear_conv = np.exp(-x**2)  # Superlinear convergence

    plt.figure(figsize=(10, 6))

    plt.plot(x, linear_conv, 'b-', linewidth=2, label='Linear Convergence')
    plt.plot(x, quadratic_conv, 'r-', linewidth=2, label='Quadratic Convergence')
    plt.plot(x, superlinear_conv, 'g-', linewidth=2, label='Superlinear Convergence')

    plt.xlabel('Iteration/Step Size')
    plt.ylabel('Convergence Factor')
    plt.title('Theoretical Convergence Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.1)

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "theoretical_analysis.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved theoretical analysis to: {plot_path}")
    return plot_path


def generate_theoretical_analysis_with_progress():
    """Generate theoretical analysis visualization with progress tracking."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    print("Generating theoretical analysis visualization...")

    # Create data for theoretical analysis
    x = np.linspace(0.01, 2, 100)

    # Different convergence rates
    linear_conv = 1 - 0.1 * x  # Linear convergence
    quadratic_conv = np.exp(-x)  # Quadratic convergence
    superlinear_conv = np.exp(-x**2)  # Superlinear convergence

    plt.figure(figsize=(10, 6))

    plt.plot(x, linear_conv, 'b-', linewidth=2, label='Linear Convergence')
    plt.plot(x, quadratic_conv, 'r-', linewidth=2, label='Quadratic Convergence')
    plt.plot(x, superlinear_conv, 'g-', linewidth=2, label='Superlinear Convergence')

    plt.xlabel('Iteration/Step Size')
    plt.ylabel('Convergence Factor')
    plt.title('Theoretical Convergence Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.1)

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "theoretical_analysis.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved theoretical analysis to: {plot_path}")
    return plot_path


def run_mathematical_demonstration():
    """Run mathematical function demonstration."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    print("Running mathematical demonstration...")

    # Demonstrate functions from src/
    test_values = [0, 1, 2, 3, 5]

    print("Mathematical function demonstration:")
    for value in test_values:
        identity_result = identity(value)
        constant_result = constant_value()
        if logger:
            logger.info(f"  identity({value}) = {identity_result}, constant_value() = {constant_result}")

    return {"test_values": test_values, "identity_results": [identity(v) for v in test_values]}


def run_mathematical_demonstration_with_progress(progress_bar):
    """Run mathematical function demonstration with progress tracking."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    # Demonstrate functions from src/
    test_values = [0, 1, 2, 3, 5]

    results = []
    for value in test_values:
        identity_result = identity(value)
        constant_result = constant_value()
        results.append((value, identity_result, constant_result))
        progress_bar.update(1)

    print("Mathematical function demonstration:")
    for value, identity_result, constant_result in results:
        if logger:
            logger.info(f"  identity({value}) = {identity_result}, constant_value() = {constant_result}")

    return {"test_values": test_values, "identity_results": [identity(v) for v in test_values]}


def save_analysis_data(analysis_results):
    """Save analysis data to file."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    print("Saving analysis data...")

    output_dir = project_root / "output" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / "mathematical_analysis.json"

    import json
    with open(data_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)

    if logger:
        logger.info(f"Saved analysis data to: {data_path}")
    return data_path


def save_analysis_data_with_progress(analysis_results, progress_bar):
    """Save analysis data to file with progress tracking."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    output_dir = project_root / "output" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / "mathematical_analysis.json"

    import json
    with open(data_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)

    progress_bar.update(1)
    if logger:
        logger.info(f"Saved analysis data to: {data_path}")
    return data_path


def register_figure():
    """Register generated figures for manuscript reference."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    try:
        # Ensure repo root is on path for infrastructure imports
        repo_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(repo_root))

        from infrastructure.documentation.figure_manager import FigureManager

        # Use project-specific registry path
        registry_file = project_root / "output" / "figures" / "figure_registry.json"
        fm = FigureManager(registry_file=str(registry_file))

        # Register figures
        figures = [
            ("mathematical_visualization.png", "Comprehensive mathematical visualization with multiple plots", "fig:math_viz"),
            ("theoretical_analysis.png", "Theoretical convergence analysis visualization", "fig:theory_analysis")
        ]

        for filename, caption, label in figures:
            fm.register_figure(
                filename=filename,
                caption=caption,
                label=label,
                section="Results",
                generated_by="analysis_pipeline.py"
            )
            if logger:
                logger.info(f"Registered figure with label: {label}")

    except ImportError as e:
        if logger:
            logger.warning(f"Figure manager not available: {e}")
    except Exception as e:
        if logger:
            logger.warning(f"Failed to register figures: {e}")


def main():
    """Main analysis function."""
    # Initialize logger for performance monitoring
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Starting prose project analysis pipeline...")
        logger.info(f"Project root: {project_root}")

    # Initialize output variables
    math_viz = None
    theory_viz = None
    data_path = None
    scientific_analysis_path = None

    if logger:
        logger.info("Starting prose project analysis pipeline")

    try:
        # System health check
        if INFRASTRUCTURE_AVAILABLE:
            health_checker = SystemHealthChecker()
            if logger:
                logger.info("Running system health check...")
            health_status = health_checker.get_health_status()
            if health_status.get('overall_status') != 'healthy':
                if logger:
                    logger.warning("System health check failed:")
                    for check_name, check_result in health_status.get('checks', {}).items():
                        if check_result.get('status') != 'healthy':
                            logger.warning(f"  - {check_name}: {check_result.get('error', 'unknown error')}")
            else:
                if logger:
                    logger.info("System health check passed")

        # Initialize checkpoint manager
        checkpoint_manager = None
        if INFRASTRUCTURE_AVAILABLE:
            checkpoint_dir = project_root / "output" / "checkpoints"
            checkpoint_manager = CheckpointManager(checkpoint_dir)
            if logger:
                logger.info("Checkpoint manager initialized")

        # Performance monitoring setup (if available)
        monitor = None
        if INFRASTRUCTURE_AVAILABLE:
            from infrastructure.core.performance import PerformanceMonitor
            monitor = PerformanceMonitor()
            monitor.start()
            if logger:
                logger.info("Performance monitoring enabled")

            # Run mathematical demonstration with progress tracking
            if logger:
                logger.info("Running mathematical demonstration...")
            if INFRASTRUCTURE_AVAILABLE:
                progress = ProgressBar(total=5, task="Mathematical tests")
                demo_results = run_mathematical_demonstration_with_progress(progress)
                progress.finish()
            else:
                demo_results = run_mathematical_demonstration()

            # Run scientific analysis
            scientific_analysis_path = None
            if INFRASTRUCTURE_AVAILABLE:
                with log_operation("Running scientific analysis", logger=logger):
                    scientific_analysis_path = run_scientific_analysis()
            else:
                scientific_analysis_path = run_scientific_analysis()

            # Generate figures with progress tracking
            if logger:
                logger.info("Generating mathematical visualization...")
            if INFRASTRUCTURE_AVAILABLE:
                math_viz = generate_mathematical_visualization_with_progress()
            else:
                math_viz = generate_mathematical_visualization()

            if logger:
                logger.info("Generating theoretical analysis...")
            if INFRASTRUCTURE_AVAILABLE:
                theory_viz = generate_theoretical_analysis_with_progress()
            else:
                theory_viz = generate_theoretical_analysis()

            # Save analysis data with progress tracking
            if logger:
                logger.info("Saving analysis data...")
            if INFRASTRUCTURE_AVAILABLE:
                progress = ProgressBar(total=1, task="Saving data")
                data_path = save_analysis_data_with_progress(demo_results, progress)
                progress.finish()
            else:
                data_path = save_analysis_data(demo_results)

            # Run scientific validation (if infrastructure available)
            stability_report = None
            benchmark_report = None

            if INFRASTRUCTURE_AVAILABLE:
                if logger:
                    logger.info("Running scientific validation...")
                import time
                validation_start = time.time()

                # Validate numerical stability of mathematical functions
                if logger:
                    logger.info("  [1/2] Validating numerical stability...")
                stability_report = validate_mathematical_functions()
                if logger:
                    logger.info(f"  ✅ Stability validation completed")

                # Benchmark mathematical operations
                if logger:
                    logger.info("  [2/2] Benchmarking performance...")
                benchmark_report = benchmark_mathematical_operations()
                if logger:
                    logger.info(f"  ✅ Performance benchmarking completed")

                # Generate validation reports
                if logger:
                    logger.info("  Generating validation reports...")
                save_scientific_validation_reports(stability_report, benchmark_report)
                validation_duration = time.time() - validation_start
                if logger:
                    logger.info(f"Scientific validation completed in {validation_duration:.2f}s")

            # Register figures if possible
            if logger:
                logger.info("Registering figures...")
            register_figure()

            # Multi-format rendering (if available)
            if INFRASTRUCTURE_AVAILABLE:
                with log_operation("Rendering outputs in multiple formats", logger=logger):
                    try:
                        render_manager = get_render_manager()
                        # Render HTML version of analysis
                        # Create temporary markdown file for rendering
                        temp_md = project_root / "output" / "temp_analysis.md"
                        temp_md.parent.mkdir(parents=True, exist_ok=True)
                        with open(temp_md, 'w') as f:
                            f.write(f"# Mathematical Analysis Results\n\nAnalysis completed with mathematical demonstrations.")
                        html_output = render_manager.render_web(temp_md)
                        # Clean up temp file
                        if temp_md.exists():
                            temp_md.unlink()
                        if html_output and logger:
                            logger.info(f"Rendered HTML output: {html_output}")
                    except Exception as e:
                        if logger:
                            logger.warning(f"Rendering failed: {e}")

            # Publishing integration demonstration
            if INFRASTRUCTURE_AVAILABLE:
                with log_operation("Publishing integration demonstration", logger=logger):
                    try:
                        # Extract publication metadata from manuscript
                        manuscript_dir = project_root / "manuscript"
                        if manuscript_dir.exists():
                            metadata = extract_publication_metadata([manuscript_dir])
                            if metadata and logger:
                                logger.info("Publication metadata extracted")
                                # Generate sample citations
                                bibtex = generate_citation_bibtex(metadata)
                                if bibtex:
                                    logger.info("BibTeX citation generated")
                    except Exception as e:
                        if logger:
                            logger.warning(f"Publishing demonstration failed: {e}")

        # Log performance metrics
        if monitor and INFRASTRUCTURE_AVAILABLE:
            performance_metrics = monitor.stop()
            if logger:
                logger.info("Performance Summary:")
                logger.info(f"Duration: {performance_metrics.duration:.2f}s")
                logger.info(f"Memory: {performance_metrics.resource_usage.memory_mb:.1f}MB")

            # Save performance data
            output_dir = project_root / "output" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)

            import json
            perf_path = output_dir / "analysis_performance.json"
            with open(perf_path, 'w') as f:
                json.dump(performance_metrics.to_dict(), f, indent=2, default=str)
            print(f"Performance data saved to: {perf_path}")

            if logger:
                logger.info(f"Performance data saved to: {perf_path}")

        if logger:
            logger.info("Analysis pipeline complete!")
            logger.info(f"Generated mathematical visualization: {math_viz}")
            logger.info(f"Generated theoretical analysis: {theory_viz}")
            logger.info(f"Generated analysis data: {data_path}")
            logger.info(f"Generated scientific analysis: {scientific_analysis_path}")

            if INFRASTRUCTURE_AVAILABLE and (stability_report or benchmark_report):
                logger.info("Generated scientific validation reports:")
                if stability_report:
                    logger.info("  - Numerical stability analysis")
                if benchmark_report:
                    logger.info("  - Performance benchmarking results")

        if logger:
            logger.info(f"Generated scientific analysis: {scientific_analysis_path}")
            logger.info("Prose project analysis pipeline completed successfully")

    except Exception as e:
        # Handle script execution errors
        print(f"\n❌ Script execution failed: {e}")
        if hasattr(e, 'recovery_commands') and e.recovery_commands:
            print("Suggested recovery commands:")
            for cmd in e.recovery_commands:
                print(f"  {cmd}")
        if logger:
            logger.error(f"Script execution error: {e}", exc_info=True)
        raise

    except TemplateError as e:
        # Handle infrastructure template errors
        if logger:
            logger.error(f"Infrastructure error: {e}")
            if e.suggestions:
                logger.error("Suggestions:")
                for suggestion in e.suggestions:
                    logger.error(f"  • {suggestion}")
        if logger:
            logger.error(f"Infrastructure error: {e}", exc_info=True)
        raise

    except ImportError as e:
        # Handle missing dependencies
        if logger:
            logger.error(f"Import error: {e}")
            logger.error("Suggestions:")
            logger.error("  • Install missing dependencies: pip install -r requirements.txt")
            logger.error("  • Check infrastructure module availability")
        if logger:
            logger.error(f"Import error: {e}", exc_info=True)
        raise

    except FileNotFoundError as e:
        # Handle missing files
        if logger:
            logger.error(f"File not found: {e}")
            logger.error("Suggestions:")
            logger.error("  • Ensure project structure is correct")
            logger.error("  • Check that source code exists in src/ directory")
        if logger:
            logger.error(f"File not found error: {e}", exc_info=True)
        raise

    except Exception as e:
        # Handle unexpected errors with context
        error_msg = f"Unexpected error during prose project analysis: {e}"
        if logger:
            logger.error(error_msg)
            logger.error("Suggestions:")
            logger.error("  • Check system requirements and dependencies")
            logger.error("  • Review error logs for detailed information")
            logger.error("  • Ensure sufficient disk space and memory")
        if logger:
            logger.error(error_msg, exc_info=True)
        raise


def validate_mathematical_functions():
    """Validate numerical stability of mathematical functions."""
    try:
        logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

        if logger:
            logger.info("Validating numerical stability of mathematical functions")

        # Test functions from src/ for numerical stability
        test_inputs = [
            -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 5.0, 10.0,
            1e-6, 1e-3, 1e3, 1e6  # Edge cases
        ]

        # Check stability of identity function
        def test_identity(x):
            return identity(x)

        # Check stability of constant function
        def test_constant():
            return constant_value()

        stability_results = {}

        # Test identity function stability
        identity_stability = check_numerical_stability(
            test_identity,
            test_inputs,
            tolerance=1e-10
        )
        stability_results['identity_function'] = identity_stability

        # Test constant function stability
        constant_stability = check_numerical_stability(
            lambda x: constant_value(),  # Wrap to take parameter
            test_inputs,
            tolerance=1e-10
        )
        stability_results['constant_function'] = constant_stability

        if logger:
            logger.info(f"Validated stability for {len(stability_results)} functions")

        return stability_results

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Scientific validation failed: {e}")
        return None


def benchmark_mathematical_operations():
    """Benchmark performance of mathematical operations."""
    try:
        logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

        if logger:
            logger.info("Benchmarking mathematical operations")

        # Benchmark test inputs
        benchmark_inputs = [
            (0,), (1,), (2,), (5,), (10,), (-1,), (-5,),
            (0.1,), (0.01,), (0.001,), (100,), (1000,)
        ]

        # Benchmark identity function
        def identity_wrapper(x):
            return identity(x)

        identity_benchmark = benchmark_function(
            identity_wrapper,
            benchmark_inputs,
            iterations=1000
        )

        # Benchmark constant function
        def constant_wrapper(x):
            return constant_value()

        constant_benchmark = benchmark_function(
            constant_wrapper,
            benchmark_inputs,
            iterations=1000
        )

        benchmark_results = {
            'identity_function': identity_benchmark,
            'constant_function': constant_benchmark
        }

        if logger:
            logger.info(f"Completed benchmarking for {len(benchmark_results)} operations")

        return benchmark_results

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Performance benchmarking failed: {e}")
        return None


def save_scientific_validation_reports(stability_report, benchmark_report):
    """Save scientific validation reports to output directory."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None
    import time
    start_time = time.time()
    
    try:
        output_dir = project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if logger:
            logger.info("Saving scientific validation reports...")
            logger.info(f"  Output directory: {output_dir}")

        import json

        # Save stability report
        if stability_report:
            stability_path = output_dir / "mathematical_stability.json"
            if logger:
                logger.info(f"  Saving stability report to: {stability_path}")
            with open(stability_path, 'w') as f:
                json.dump(stability_report, f, indent=2, default=str)
            if logger:
                logger.info(f"  ✅ Saved stability report ({len(stability_report)} functions)")
            print(f"Saved stability report to: {stability_path}")
        else:
            if logger:
                logger.warning("  ⚠️ No stability report to save")

        # Save benchmark report
        if benchmark_report:
            benchmark_path = output_dir / "mathematical_benchmark.json"
            if logger:
                logger.info(f"  Saving benchmark report to: {benchmark_path}")
            with open(benchmark_path, 'w') as f:
                json.dump(benchmark_report, f, indent=2, default=str)
            if logger:
                logger.info(f"  ✅ Saved benchmark report ({len(benchmark_report)} functions)")
            print(f"Saved benchmark report to: {benchmark_path}")
        else:
            if logger:
                logger.warning("  ⚠️ No benchmark report to save")

        # Create validation summary
        summary_path = output_dir / "scientific_validation_summary.md"
        with open(summary_path, 'w') as f:
            f.write("# Scientific Validation Summary\n\n")
            f.write("## Mathematical Functions Validation\n\n")

            if stability_report:
                f.write("### Numerical Stability\n\n")
                for func_name, stability in stability_report.items():
                    f.write(f"**{func_name}:**\n")
                    if stability.stability_score > 0.8:
                        f.write(f"- ✅ Stable (score: {stability.stability_score:.2f})\n")
                    else:
                        f.write(f"- ❌ Unstable (score: {stability.stability_score:.2f})\n")
                    f.write("\n")

            if benchmark_report:
                f.write("### Performance Benchmarking\n\n")
                for func_name, benchmark in benchmark_report.items():
                    f.write(f"**{func_name}:**\n")
                    # Handle both dataclass and dict formats for backward compatibility
                    if hasattr(benchmark, 'execution_time'):
                        # BenchmarkResult dataclass
                        avg_time = f"{benchmark.execution_time:.6f}s"
                        iterations = benchmark.iterations
                        memory = f"{benchmark.memory_usage:.1f}MB" if benchmark.memory_usage is not None else "N/A"
                        f.write(f"- Average execution time: {avg_time}\n")
                        f.write(f"- Iterations: {iterations}\n")
                        f.write(f"- Memory usage: {memory}\n")
                    elif isinstance(benchmark, dict):
                        # Legacy dict format
                        avg_time = benchmark.get('mean_time', benchmark.get('execution_time', 'N/A'))
                        f.write(f"- Average execution time: {avg_time}\n")
                    else:
                        f.write(f"- Average execution time: N/A (unknown format)\n")
                    f.write("\n")

        duration = time.time() - start_time
        if logger:
            logger.info(f"  ✅ Saved validation summary to: {summary_path}")
            logger.info(f"Report generation completed in {duration:.2f}s")
        print(f"Saved validation summary to: {summary_path}")

    except AttributeError as e:
        duration = time.time() - start_time
        if logger:
            logger.error(f"Failed to save validation reports after {duration:.2f}s: {e}")
            logger.error(f"  Error type: AttributeError")
            logger.error(f"  Issue: Attempting to access attribute on wrong object type")
            logger.error(f"  Suggestion: BenchmarkResult is a dataclass - use .execution_time not .get('mean_time')")
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to save validation reports: {e}")
    except Exception as e:
        duration = time.time() - start_time
        if logger:
            logger.error(f"Failed to save validation reports after {duration:.2f}s: {e}")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.error(f"  Suggestion: Check file permissions and disk space")
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to save validation reports: {e}")


if __name__ == "__main__":
    main()
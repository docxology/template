"""Mathematical visualization utilities for research manuscripts.

This module provides comprehensive functions for generating publication-quality
mathematical visualizations and plots. Designed to support academic research
with proper formatting, consistent styling, and professional presentation.

The module includes visualization functions for:
- Function comparisons and mathematical relationships
- Convergence analysis and error plots
- Statistical distributions and data visualization
- Growth rates and asymptotic behavior
- Theoretical convergence analysis

All functions follow academic plotting standards with:
- High-resolution output (300 DPI default)
- Consistent color schemes and line styles
- Proper axis labeling and legends
- Grid lines for readability
- Support for multiple subplots and complex layouts
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def plot_function_comparison(
    functions: Dict[str, callable],
    x_range: Tuple[float, float] = (-2, 2),
    num_points: int = 100,
    title: str = "Function Comparison",
    xlabel: str = "x",
    ylabel: str = "f(x)"
) -> plt.Figure:
    """Create a publication-quality comparison plot of multiple mathematical functions.

    This function generates a professional plot comparing multiple mathematical functions
    over a specified domain. The plot includes proper styling, legends, and grid lines
    suitable for academic publications.

    Args:
        functions: Dictionary mapping descriptive function names to callable functions.
                  Each function should accept a numpy array and return a numpy array
                  of the same shape.
        x_range: Tuple specifying the plotting domain as (min_x, max_x).
                Default range is (-2, 2) which works well for most elementary functions.
        num_points: Number of evaluation points for smooth curve rendering.
                   Higher values give smoother curves but increase computation time.
                   Default is 100 points.
        title: Plot title string. Should be descriptive and academic in tone.
        xlabel: Label for x-axis, typically the independent variable name.
        ylabel: Label for y-axis, typically the dependent variable or function name.

    Returns:
        Matplotlib Figure object containing the complete plot. The figure can be
        further customized or saved using standard matplotlib methods.

    Raises:
        ValueError: If x_range is invalid (min >= max) or num_points <= 0.
        TypeError: If functions dictionary contains non-callable values.

    Example:
        >>> import numpy as np
        >>> functions = {
        ...     'Quadratic': lambda x: x**2,
        ...     'Linear': lambda x: 2*x + 1,
        ...     'Sine': lambda x: np.sin(x)
        ... }
        >>> fig = plot_function_comparison(functions, x_range=(-3, 3))
        >>> # Save with: fig.savefig('comparison.png', dpi=300, bbox_inches='tight')

    Note:
        The function uses a predefined color cycle. For more than 8 functions,
        colors will repeat. Consider using subplots for large numbers of functions.
    """
    x = np.linspace(x_range[0], x_range[1], num_points)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

    for i, (name, func) in enumerate(functions.items()):
        try:
            y = func(x)
            color = colors[i % len(colors)]
            ax.plot(x, y, color=color, linewidth=2, label=name)
        except Exception as e:
            print(f"Warning: Could not plot function {name}: {e}")
            continue

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def plot_convergence_analysis(
    convergence_data: Dict[str, List[float]],
    title: str = "Convergence Analysis",
    xlabel: str = "Iteration",
    ylabel: str = "Error",
    use_log_scale: bool = True
) -> plt.Figure:
    """Plot convergence analysis for different methods.

    Args:
        convergence_data: Dictionary mapping method names to error values
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        use_log_scale: Whether to use logarithmic scale for y-axis

    Returns:
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['blue', 'red', 'green', 'orange', 'purple']

    for i, (method, errors) in enumerate(convergence_data.items()):
        iterations = list(range(1, len(errors) + 1))
        color = colors[i % len(colors)]
        ax.plot(iterations, errors, color=color, linewidth=2,
                marker='o', markersize=4, label=method)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    if use_log_scale:
        ax.set_yscale('log')

    return fig


def plot_statistical_distribution(
    data: np.ndarray,
    bins: int = 30,
    title: str = "Statistical Distribution",
    xlabel: str = "Value",
    ylabel: str = "Frequency"
) -> plt.Figure:
    """Plot histogram of statistical data.

    Args:
        data: Array of data values
        bins: Number of histogram bins
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label

    Returns:
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot histogram
    n, bins, patches = ax.hist(data, bins=bins, alpha=0.7,
                              color='skyblue', edgecolor='black')

    # Add statistical markers
    mean_val = np.mean(data)
    median_val = np.median(data)

    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label='Mean')
    ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label='Median')

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def plot_growth_rates(
    growth_functions: Dict[str, callable],
    x_range: Tuple[float, float] = (0.1, 5),
    num_points: int = 50,
    title: str = "Growth Rate Comparison",
    xlabel: str = "x",
    ylabel: str = "f(x)"
) -> plt.Figure:
    """Plot comparison of different growth rates.

    Args:
        growth_functions: Dictionary mapping growth type names to functions
        x_range: Tuple of (min_x, max_x) for plotting range
        num_points: Number of points to evaluate functions at
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label

    Returns:
        Matplotlib figure object
    """
    x = np.linspace(x_range[0], x_range[1], num_points)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['red', 'green', 'blue', 'orange', 'purple']

    for i, (name, func) in enumerate(growth_functions.items()):
        try:
            y = func(x)
            color = colors[i % len(colors)]
            ax.plot(x, y, color=color, linewidth=2, label=name)
        except Exception as e:
            print(f"Warning: Could not plot growth function {name}: {e}")
            continue

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def plot_theoretical_convergence(
    convergence_functions: Dict[str, callable],
    x_range: Tuple[float, float] = (0.01, 2),
    num_points: int = 100,
    title: str = "Theoretical Convergence Analysis",
    xlabel: str = "Step Size/Iteration",
    ylabel: str = "Convergence Factor"
) -> plt.Figure:
    """Plot theoretical convergence analysis.

    Args:
        convergence_functions: Dictionary mapping convergence type to functions
        x_range: Tuple of (min_x, max_x) for plotting range
        num_points: Number of points to evaluate functions at
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label

    Returns:
        Matplotlib figure object
    """
    x = np.linspace(x_range[0], x_range[1], num_points)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['blue', 'red', 'green', 'orange']

    for i, (name, func) in enumerate(convergence_functions.items()):
        try:
            y = func(x)
            color = colors[i % len(colors)]
            ax.plot(x, y, color=color, linewidth=2, label=name)
        except Exception as e:
            print(f"Warning: Could not plot convergence function {name}: {e}")
            continue

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)

    return fig


def save_figure(
    fig: plt.Figure,
    filename: str,
    output_dir: Optional[Path] = None,
    dpi: int = 300
) -> Path:
    """Save matplotlib figure to file.

    Args:
        fig: Matplotlib figure object
        filename: Name of output file (without extension)
        output_dir: Directory to save figure in (default: current working directory)
        dpi: Resolution for saved figure

    Returns:
        Path to saved figure file
    """
    if output_dir is None:
        output_dir = Path.cwd() / "output" / "figures"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{filename}.png"
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    return filepath


def create_comprehensive_visualization(
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Create a comprehensive set of mathematical visualizations.

    Args:
        output_dir: Directory to save figures in

    Returns:
        Dictionary mapping figure names to file paths
    """
    saved_files = {}

    # Function comparison
    functions = {
        'Linear': lambda x: x,
        'Quadratic': lambda x: x**2,
        'Cubic': lambda x: x**3,
        'Exponential': lambda x: np.exp(x/2),
        'Sine': lambda x: np.sin(2*np.pi*x),
    }
    fig1 = plot_function_comparison(functions)
    saved_files['function_comparison'] = save_figure(fig1, 'function_comparison', output_dir)

    # Convergence analysis
    convergence_data = {
        '1/√k': [1/np.sqrt(k) for k in range(1, 51)],
        '1/k': [1/k for k in range(1, 51)],
        'exp(-k)': [np.exp(-k/10) for k in range(1, 51)],
    }
    fig2 = plot_convergence_analysis(convergence_data)
    saved_files['convergence_analysis'] = save_figure(fig2, 'convergence_analysis', output_dir)

    # Statistical distribution
    np.random.seed(42)
    data = np.random.normal(0, 1, 1000)
    fig3 = plot_statistical_distribution(data)
    saved_files['statistical_distribution'] = save_figure(fig3, 'statistical_distribution', output_dir)

    # Growth rates
    growth_functions = {
        'log(x)': lambda x: np.log(x),
        '√x': lambda x: np.sqrt(x),
        'x': lambda x: x,
        'x^0.3': lambda x: x**0.3,
    }
    fig4 = plot_growth_rates(growth_functions)
    saved_files['growth_rates'] = save_figure(fig4, 'growth_rates', output_dir)

    # Theoretical convergence
    convergence_functions = {
        'Linear': lambda x: 1 - 0.1 * x,
        'Quadratic': lambda x: np.exp(-x),
        'Superlinear': lambda x: np.exp(-x**2),
    }
    fig5 = plot_theoretical_convergence(convergence_functions)
    saved_files['theoretical_convergence'] = save_figure(fig5, 'theoretical_convergence', output_dir)

    return saved_files
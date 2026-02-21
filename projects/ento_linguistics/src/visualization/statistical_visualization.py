"""Statistical visualization module for Ento-Linguistic analysis.

This module provides specialized visualizations for statistical analysis results,
including significance testing, correlation matrices, distribution comparisons,
effect sizes, and confidence intervals.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

try:
    from .concept_visualization import ConceptVisualizer
except ImportError:
    from concept_visualization import ConceptVisualizer

__all__ = [
    "StatisticalVisualizer",
]


class StatisticalVisualizer(ConceptVisualizer):
    """Visualizer for statistical analysis results.

    This class provides methods for visualizing statistical test results,
    correlations, distributions, and other quantitative analyses.
    """

    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """Initialize statistical visualizer.

        Args:
            figsize: Default figure size for plots
        """
        super().__init__(figsize)
        self.significance_colors = {
            "significant": "#d62728",  # Red
            "marginally_significant": "#ff7f0e",  # Orange
            "not_significant": "#2ca02c",  # Green
        }

    def visualize_statistical_significance(
        self,
        significance_results: Dict[str, Any],
        filepath: Optional[Path] = None,
        title: str = "Statistical Significance Analysis",
    ) -> plt.Figure:
        """Visualize statistical significance test results.

        Args:
            significance_results: Results from statistical significance testing
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # P-value visualization
        if "p_value" in significance_results:
            p_val = significance_results["p_value"]
            threshold = significance_results.get("significance_threshold", 0.05)

            # P-value bar chart
            ax1.bar(
                ["P-Value", "Threshold"],
                [p_val, threshold],
                color=["skyblue", "red"],
                alpha=0.7,
                edgecolor="black",
            )
            ax1.axhline(
                y=threshold,
                color="red",
                linestyle="--",
                alpha=0.7,
                label=f"α = {threshold}",
            )
            ax1.set_ylabel("Value")
            ax1.set_title("P-Value vs Significance Threshold")
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Significance status
            is_significant = p_val < threshold
            status_color = "green" if is_significant else "red"
            status_text = "SIGNIFICANT" if is_significant else "NOT SIGNIFICANT"

            ax1.text(
                0.5,
                max(p_val, threshold) * 0.8,
                status_text,
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color=status_color,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            )

        # Chi-square statistic
        if "chi_square_statistic" in significance_results:
            chi_sq = significance_results["chi_square_statistic"]
            effect_size = significance_results.get("effect_size", 0)

            ax2.bar(
                ["Chi-Square", "Effect Size"],
                [chi_sq, effect_size],
                color=["orange", "purple"],
                alpha=0.7,
                edgecolor="black",
            )
            ax2.set_ylabel("Value")
            ax2.set_title("Test Statistics")
            ax2.grid(True, alpha=0.3)

        # Significant patterns
        if "significant_patterns" in significance_results:
            patterns = significance_results["significant_patterns"]
            if patterns:
                # Count pattern frequencies (simplified)
                pattern_counts = {pattern: 1 for pattern in patterns}

                ax3.bar(range(len(patterns)), [1] * len(patterns))
                ax3.set_xticks(range(len(patterns)))
                ax3.set_xticklabels(patterns, rotation=45, ha="right")
                ax3.set_ylabel("Significance")
                ax3.set_title("Significant Patterns")
                ax3.grid(True, alpha=0.3)
            else:
                ax3.text(
                    0.5,
                    0.5,
                    "No Significant Patterns Found",
                    transform=ax3.transAxes,
                    ha="center",
                    va="center",
                    fontsize=12,
                    style="italic",
                )
                ax3.set_title("Significant Patterns")
                ax3.axis("off")

        # Effect size interpretation
        if "effect_size" in significance_results:
            effect_size = significance_results["effect_size"]

            # Effect size categories
            categories = ["Negligible", "Small", "Medium", "Large"]
            thresholds = [0.1, 0.3, 0.5, float("inf")]
            category_colors = ["lightgray", "lightblue", "orange", "red"]

            # Determine category
            category_idx = 0
            for i, threshold in enumerate(thresholds):
                if effect_size <= threshold:
                    category_idx = i
                    break

            ax4.bar(
                ["Effect Size"],
                [effect_size],
                color=category_colors[category_idx],
                alpha=0.7,
                edgecolor="black",
                width=0.5,
            )
            ax4.axhline(
                y=thresholds[category_idx],
                color=category_colors[category_idx],
                linestyle="--",
                alpha=0.7,
                label=categories[category_idx],
            )
            ax4.set_ylabel("Effect Size")
            ax4.set_title("Effect Size Magnitude")
            ax4.legend()
            ax4.grid(True, alpha=0.3)

            # Add interpretation text
            ax4.text(
                0,
                effect_size * 0.5,
                f"{categories[category_idx]}\n({effect_size:.3f})",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
            )

        plt.suptitle(title, fontsize=16, fontweight="bold")
        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def create_correlation_matrix_plot(
        self,
        correlation_data: Dict[str, Dict[str, float]],
        filepath: Optional[Path] = None,
        title: str = "Correlation Matrix",
    ) -> plt.Figure:
        """Create a correlation matrix heatmap visualization.

        Args:
            correlation_data: Dictionary of correlation coefficients
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Extract variable names and correlation matrix
        variables = list(correlation_data.keys())
        n_vars = len(variables)

        # Create correlation matrix
        corr_matrix = np.zeros((n_vars, n_vars))

        for i, var1 in enumerate(variables):
            for j, var2 in enumerate(variables):
                if i == j:
                    corr_matrix[i, j] = 1.0  # Perfect correlation with self
                else:
                    corr_matrix[i, j] = correlation_data[var1].get(var2, 0)

        # Create heatmap
        im = ax.imshow(corr_matrix, cmap="RdYlBu_r", aspect="equal", vmin=-1, vmax=1)

        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Correlation Coefficient", rotation=-90, va="bottom")

        # Add labels
        ax.set_xticks(range(n_vars))
        ax.set_yticks(range(n_vars))
        ax.set_xticklabels(variables, rotation=45, ha="right")
        ax.set_yticklabels(variables)

        # Add correlation values as text
        for i in range(n_vars):
            for j in range(n_vars):
                text = ax.text(
                    j,
                    i,
                    ".2f",
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8),
                )

        ax.set_title(title, fontsize=14, fontweight="bold")
        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def visualize_distribution_comparison(
        self,
        distribution_data: Dict[str, List[float]],
        filepath: Optional[Path] = None,
        title: str = "Distribution Comparison",
    ) -> plt.Figure:
        """Visualize and compare multiple data distributions.

        Args:
            distribution_data: Dictionary mapping distribution names to data arrays
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        distributions = list(distribution_data.keys())
        colors = plt.cm.tab10(np.linspace(0, 1, len(distributions)))

        # Box plots
        data_lists = [distribution_data[dist] for dist in distributions]
        bp = ax1.boxplot(data_lists, tick_labels=distributions, patch_artist=True)
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
        ax1.set_ylabel("Value")
        ax1.set_title("Box Plot Comparison")
        ax1.grid(True, alpha=0.3)

        # Violin plots
        parts = ax2.violinplot(data_lists, showmeans=True, showextrema=True)
        for i, (pc, color) in enumerate(zip(parts["bodies"], colors)):
            pc.set_facecolor(color)
            pc.set_edgecolor("black")
            pc.set_alpha(0.7)
        ax2.set_xticks(range(1, len(distributions) + 1))
        ax2.set_xticklabels(distributions)
        ax2.set_ylabel("Value")
        ax2.set_title("Violin Plot Comparison")
        ax2.grid(True, alpha=0.3)

        # Histograms
        for i, (name, data) in enumerate(distribution_data.items()):
            ax3.hist(
                data, bins=20, alpha=0.7, label=name, color=colors[i], edgecolor="black"
            )
        ax3.set_xlabel("Value")
        ax3.set_ylabel("Frequency")
        ax3.set_title("Histogram Comparison")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Cumulative distribution functions
        for i, (name, data) in enumerate(distribution_data.items()):
            sorted_data = np.sort(data)
            yvals = np.arange(len(sorted_data)) / float(len(sorted_data) - 1)
            ax4.plot(sorted_data, yvals, label=name, color=colors[i], linewidth=2)
        ax4.set_xlabel("Value")
        ax4.set_ylabel("Cumulative Probability")
        ax4.set_title("CDF Comparison")
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.suptitle(title, fontsize=16, fontweight="bold")
        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def visualize_effect_sizes(
        self,
        effect_size_data: Dict[str, Dict[str, float]],
        filepath: Optional[Path] = None,
        title: str = "Effect Size Analysis",
    ) -> plt.Figure:
        """Visualize effect sizes with interpretation guidelines.

        Args:
            effect_size_data: Dictionary of effect size results
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Extract effect sizes and labels
        labels = []
        effect_sizes = []
        categories = []

        for comparison, data in effect_size_data.items():
            es = data.get("effect_size", 0)
            effect_sizes.append(es)
            labels.append(comparison)

            # Categorize effect size
            if abs(es) < 0.2:
                categories.append("Negligible")
            elif abs(es) < 0.5:
                categories.append("Small")
            elif abs(es) < 0.8:
                categories.append("Medium")
            else:
                categories.append("Large")

        # Color mapping for categories
        category_colors = {
            "Negligible": "lightgray",
            "Small": "lightblue",
            "Medium": "orange",
            "Large": "red",
        }

        colors = [category_colors[cat] for cat in categories]

        # Create horizontal bar chart
        bars = ax.barh(
            range(len(effect_sizes)),
            effect_sizes,
            color=colors,
            alpha=0.7,
            edgecolor="black",
        )

        # Add value labels
        for i, (bar, es) in enumerate(zip(bars, effect_sizes)):
            width = bar.get_width()
            label_x = width + 0.01 if width >= 0 else width - 0.01
            ax.text(
                label_x,
                bar.get_y() + bar.get_height() / 2,
                ".2f",
                ha="left" if width >= 0 else "right",
                va="center",
                fontsize=9,
                fontweight="bold",
            )

        # Add interpretation zones
        ax.axvline(x=-0.2, color="gray", linestyle="--", alpha=0.5)
        ax.axvline(x=0.2, color="gray", linestyle="--", alpha=0.5)
        ax.axvline(x=-0.5, color="orange", linestyle="--", alpha=0.5)
        ax.axvline(x=0.5, color="orange", linestyle="--", alpha=0.5)
        ax.axvline(x=-0.8, color="red", linestyle="--", alpha=0.5)
        ax.axvline(x=0.8, color="red", linestyle="--", alpha=0.5)

        # Add zone labels
        ax.text(
            -0.1,
            len(effect_sizes) * 0.9,
            "Negligible",
            ha="center",
            va="center",
            fontsize=8,
            style="italic",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="lightgray", alpha=0.7),
        )
        ax.text(
            -0.35,
            len(effect_sizes) * 0.9,
            "Small",
            ha="center",
            va="center",
            fontsize=8,
            style="italic",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="lightblue", alpha=0.7),
        )
        ax.text(
            -0.65,
            len(effect_sizes) * 0.9,
            "Medium",
            ha="center",
            va="center",
            fontsize=8,
            style="italic",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="orange", alpha=0.7),
        )
        ax.text(
            -0.9,
            len(effect_sizes) * 0.8,
            "Large",
            ha="center",
            va="center",
            fontsize=8,
            style="italic",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="red", alpha=0.7),
        )

        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel("Effect Size (Cohen's d)")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)

        # Add legend
        legend_elements = [
            patches.Patch(facecolor=color, edgecolor="black", label=cat, alpha=0.7)
            for cat, color in category_colors.items()
        ]
        ax.legend(
            handles=legend_elements,
            title="Effect Size Magnitude",
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def plot_confidence_intervals(
        self,
        ci_data: Dict[str, Dict[str, float]],
        filepath: Optional[Path] = None,
        title: str = "Confidence Intervals",
    ) -> plt.Figure:
        """Plot confidence intervals for multiple estimates.

        Args:
            ci_data: Dictionary with keys 'estimate', 'ci_lower', 'ci_upper' for each group
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        groups = list(ci_data.keys())
        estimates = [ci_data[group]["estimate"] for group in groups]
        ci_lowers = [ci_data[group]["ci_lower"] for group in groups]
        ci_uppers = [ci_data[group]["ci_upper"] for group in groups]

        # Calculate error bars
        yerr_lower = [est - lower for est, lower in zip(estimates, ci_lowers)]
        yerr_upper = [upper - est for est, upper in zip(estimates, ci_uppers)]
        yerr = [yerr_lower, yerr_upper]

        # Create plot
        x_positions = range(len(groups))
        ax.errorbar(
            x_positions,
            estimates,
            yerr=yerr,
            fmt="o",
            color="blue",
            ecolor="black",
            capsize=5,
            capthick=2,
            markersize=8,
            linewidth=2,
            alpha=0.8,
        )

        # Add reference line at zero if appropriate
        if min(ci_lowers) < 0 < max(ci_uppers):
            ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

        # Add significance indicators
        for i, (group, estimate) in enumerate(zip(groups, estimates)):
            ci_lower = ci_lowers[i]
            ci_upper = ci_uppers[i]

            # Check if CI excludes zero (for difference measures)
            if ci_lower > 0 or ci_upper < 0:
                # Significant result
                ax.plot(
                    i,
                    estimate,
                    "o",
                    markersize=10,
                    markerfacecolor="red",
                    markeredgecolor="black",
                    markeredgewidth=2,
                )
                ax.text(
                    i,
                    estimate + (ci_upper - estimate) * 0.1,
                    "*",
                    ha="center",
                    va="bottom",
                    fontsize=16,
                    fontweight="bold",
                )

        ax.set_xticks(x_positions)
        ax.set_xticklabels(groups, rotation=45, ha="right")
        ax.set_ylabel("Estimate")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)

        # Add legend
        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="blue",
                markersize=8,
                label="Estimate",
                linestyle="None",
            ),
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="red",
                markersize=10,
                markerfacecolor="red",
                markeredgecolor="black",
                label="Statistically Significant",
                linestyle="None",
            ),
        ]
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc="upper left")

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def create_statistical_dashboard(
        self,
        dashboard_data: Dict[str, Any],
        filepath: Optional[Path] = None,
        title: str = "Statistical Analysis Dashboard",
    ) -> plt.Figure:
        """Create a comprehensive statistical dashboard.

        Args:
            dashboard_data: Dictionary containing various statistical results
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(3, 3, figsize=(20, 15))
        axes = axes.flatten()

        plot_idx = 0

        # Plot 1: Statistical significance (if available)
        if "significance_results" in dashboard_data and plot_idx < len(axes):
            sig_data = dashboard_data["significance_results"]
            if "p_value" in sig_data:
                p_val = sig_data["p_value"]
                threshold = sig_data.get("significance_threshold", 0.05)

                axes[plot_idx].bar(
                    ["P-Value", "Threshold"],
                    [p_val, threshold],
                    color=["skyblue", "red"],
                    alpha=0.7,
                )
                axes[plot_idx].set_title("Statistical Significance")
                axes[plot_idx].grid(True, alpha=0.3)
                plot_idx += 1

        # Plot 2: Effect sizes (if available)
        if "effect_sizes" in dashboard_data and plot_idx < len(axes):
            es_data = dashboard_data["effect_sizes"]
            if es_data:
                labels = list(es_data.keys())[:5]  # Limit to 5
                values = [es_data[label] for label in labels]

                axes[plot_idx].barh(labels, values, color="lightgreen", alpha=0.7)
                axes[plot_idx].set_title("Effect Sizes")
                axes[plot_idx].grid(True, alpha=0.3)
                plot_idx += 1

        # Plot 3: Distribution comparison (if available)
        if "distributions" in dashboard_data and plot_idx < len(axes):
            dist_data = dashboard_data["distributions"]
            if len(dist_data) >= 2:
                # Simple box plot for first two distributions
                dist_names = list(dist_data.keys())[:2]
                data_lists = [dist_data[name] for name in dist_names]

                axes[plot_idx].boxplot(data_lists, tick_labels=dist_names)
                axes[plot_idx].set_title("Distribution Comparison")
                axes[plot_idx].grid(True, alpha=0.3)
                plot_idx += 1

        # Plot 4: Correlation heatmap (if available)
        if "correlation_matrix" in dashboard_data and plot_idx < len(axes):
            corr_data = dashboard_data["correlation_matrix"]
            if corr_data:
                # Create simple correlation visualization
                variables = list(corr_data.keys())[:4]  # Limit to 4x4
                corr_matrix = np.eye(len(variables))

                for i, v1 in enumerate(variables):
                    for j, v2 in enumerate(variables):
                        corr_matrix[i, j] = corr_data[v1].get(v2, 0)

                im = axes[plot_idx].imshow(corr_matrix, cmap="RdYlBu_r", aspect="equal")
                axes[plot_idx].set_xticks(range(len(variables)))
                axes[plot_idx].set_yticks(range(len(variables)))
                axes[plot_idx].set_xticklabels(variables, rotation=45, ha="right")
                axes[plot_idx].set_yticklabels(variables)
                axes[plot_idx].set_title("Correlation Matrix")
                plt.colorbar(im, ax=axes[plot_idx])
                plot_idx += 1

        # Plot 5: Confidence intervals (if available)
        if "confidence_intervals" in dashboard_data and plot_idx < len(axes):
            ci_data = dashboard_data["confidence_intervals"]
            if ci_data:
                groups = list(ci_data.keys())[:4]  # Limit to 4
                estimates = [ci_data[g]["estimate"] for g in groups]
                lowers = [ci_data[g]["ci_lower"] for g in groups]
                uppers = [ci_data[g]["ci_upper"] for g in groups]

                x_pos = range(len(groups))
                yerr_lower = [est - low for est, low in zip(estimates, lowers)]
                yerr_upper = [up - est for est, up in zip(estimates, uppers)]

                axes[plot_idx].errorbar(
                    x_pos, estimates, yerr=[yerr_lower, yerr_upper], fmt="o", capsize=5
                )
                axes[plot_idx].set_xticks(x_pos)
                axes[plot_idx].set_xticklabels(groups, rotation=45, ha="right")
                axes[plot_idx].set_title("Confidence Intervals")
                axes[plot_idx].grid(True, alpha=0.3)
                plot_idx += 1

        # Hide unused subplots
        for i in range(plot_idx, len(axes)):
            axes[i].axis("off")

        plt.suptitle(title, fontsize=16, fontweight="bold")
        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def visualize_hypothesis_testing(
        self,
        hypothesis_results: List[Dict[str, Any]],
        filepath: Optional[Path] = None,
        title: str = "Hypothesis Testing Results",
    ) -> plt.Figure:
        """Visualize results from multiple hypothesis tests.

        Args:
            hypothesis_results: List of hypothesis test results
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Extract test results
        test_names = []
        p_values = []
        effect_sizes = []
        significances = []

        for result in hypothesis_results:
            test_names.append(result.get("test_name", f"Test {len(test_names) + 1}"))
            p_values.append(result.get("p_value", 1.0))
            effect_sizes.append(result.get("effect_size", 0))
            significances.append(result.get("p_value", 1.0) < 0.05)

        # Create scatter plot
        colors = ["red" if sig else "blue" for sig in significances]
        sizes = [abs(es) * 100 + 50 for es in effect_sizes]  # Size based on effect size

        scatter = ax.scatter(
            p_values, effect_sizes, c=colors, s=sizes, alpha=0.7, edgecolors="black"
        )

        # Add significance threshold line
        ax.axvline(x=0.05, color="red", linestyle="--", alpha=0.7, label="α = 0.05")

        # Add labels for significant results
        for i, (name, p_val, es, sig) in enumerate(
            zip(test_names, p_values, effect_sizes, significances)
        ):
            if sig:
                ax.annotate(
                    name,
                    (p_val, es),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.8),
                )

        ax.set_xlabel("P-Value")
        ax.set_ylabel("Effect Size")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xscale("log")  # Log scale for p-values
        ax.grid(True, alpha=0.3)

        # Add legend
        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="red",
                markersize=8,
                label="Significant (p < 0.05)",
                linestyle="None",
            ),
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="blue",
                markersize=8,
                label="Not Significant",
                linestyle="None",
            ),
            plt.Line2D(
                [0], [0], color="red", linestyle="--", label="Significance Threshold"
            ),
        ]
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc="upper left")

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

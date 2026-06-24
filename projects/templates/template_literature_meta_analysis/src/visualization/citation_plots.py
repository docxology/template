"""Citation network visualizations.

Provides network graph drawings and degree distribution histograms
for the literature citation network.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from visualization.style import VIZ_CONFIG


def plot_citation_network(
    graph: nx.DiGraph,
    output_path: Path,
    max_nodes: int = 100,
) -> Path:
    """Draw citation network using spring layout.

    Node size is proportional to in-degree. Nodes are colored by
    community assignment if a 'community' attribute exists on nodes,
    otherwise all nodes use the primary palette color.

    For graphs larger than max_nodes, a subgraph of the highest
    in-degree nodes is drawn.

    Args:
        graph: Directed citation graph (networkx DiGraph).
        output_path: File path to save the figure.
        max_nodes: Maximum number of nodes to draw.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # If graph is too large, take highest in-degree subgraph
    if graph.number_of_nodes() > max_nodes:
        in_degrees = dict(graph.in_degree())
        top_nodes = sorted(in_degrees, key=in_degrees.get, reverse=True)[:max_nodes]
        subgraph = graph.subgraph(top_nodes).copy()
    else:
        subgraph = graph

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    if subgraph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No nodes in graph", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    # Compute layout
    pos = nx.spring_layout(subgraph, seed=42, k=1.5 / (subgraph.number_of_nodes() ** 0.5 + 1))

    # Node sizes proportional to in-degree
    in_degrees = dict(subgraph.in_degree())
    max_deg = max(in_degrees.values()) if in_degrees else 1
    node_sizes = [100 + 500 * (in_degrees.get(n, 0) / max(max_deg, 1)) for n in subgraph.nodes()]

    # Node colors by community if available
    has_community = all("community" in subgraph.nodes[n] for n in subgraph.nodes())
    if has_community and subgraph.number_of_nodes() > 0:
        communities = [subgraph.nodes[n]["community"] for n in subgraph.nodes()]
        unique_communities = sorted(set(communities))
        palette = VIZ_CONFIG["palette"]
        community_color_map = {c: palette[i % len(palette)] for i, c in enumerate(unique_communities)}
        node_colors = [community_color_map[c] for c in communities]
    else:
        node_colors = [VIZ_CONFIG["palette"][0]] * subgraph.number_of_nodes()

    # Draw
    nx.draw_networkx_edges(
        subgraph,
        pos,
        ax=ax,
        alpha=0.2,
        edge_color=VIZ_CONFIG["edge_color"],
        arrows=True,
        arrowsize=8,
    )
    nx.draw_networkx_nodes(
        subgraph,
        pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=0.8,
        edgecolors="white",
        linewidths=0.5,
    )

    # Label top-5 highest in-degree nodes
    top5 = sorted(in_degrees, key=in_degrees.get, reverse=True)[:5]
    for node in top5:
        if node in pos:
            x, y = pos[node]
            short_label = str(node)[:25]
            ax.annotate(
                short_label,
                (x, y),
                fontsize=max(VIZ_CONFIG["font_size"] - 4, 16),
                fontweight="bold",
                alpha=0.85,
                ha="center",
                va="bottom",
                xytext=(0, 6),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, lw=0),
            )

    ax.set_title(
        f"Citation Network ({subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges)",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.set_axis_off()

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_degree_distribution(
    graph: nx.DiGraph,
    output_path: Path,
) -> Path:
    """Histogram of in-degree distribution for the citation network.

    Uses logarithmic x-axis binning when maximum degree exceeds 20.

    Args:
        graph: Directed citation graph (networkx DiGraph).
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    if graph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No nodes in graph", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    in_degrees = [d for _, d in graph.in_degree()]
    in_arr = np.array(in_degrees, dtype=float)

    max_degree = max(in_degrees) if in_degrees else 0

    # Use log-log scale if range warrants it
    use_loglog = max_degree > 20

    if use_loglog:
        # Log-spaced bins for power-law visualization
        bins = np.logspace(0, np.log10(max_degree + 1), num=25)
        ax.hist(
            in_arr[in_arr > 0],
            bins=bins,
            color=VIZ_CONFIG["palette"][0],
            edgecolor="white",
            alpha=0.8,
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
    else:
        n_bins = min(max_degree + 1, 30)
        n_bins = max(n_bins, 1)
        ax.hist(
            in_degrees,
            bins=n_bins,
            color=VIZ_CONFIG["palette"][0],
            edgecolor="white",
            alpha=0.8,
        )

    # Mean and median vertical lines
    mean_deg = float(np.mean(in_arr))
    median_deg = float(np.median(in_arr))
    ax.axvline(mean_deg, color=VIZ_CONFIG["palette"][1], linestyle="--", linewidth=2, label=f"Mean = {mean_deg:.1f}")
    ax.axvline(
        median_deg, color=VIZ_CONFIG["palette"][2], linestyle="-.", linewidth=2, label=f"Median = {median_deg:.0f}"
    )

    ax.set_xlabel("In-Degree (Citations Received)", fontsize=VIZ_CONFIG["font_size"])
    ax.set_ylabel("Number of Papers", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        "Citation In-Degree Distribution",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.legend(fontsize=max(VIZ_CONFIG["font_size"] - 2, 16), framealpha=0.9)
    ax.grid(axis="y", alpha=VIZ_CONFIG["grid_alpha"])

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path

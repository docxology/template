"""Concept visualization for Ento-Linguistic analysis.

This module provides visualization functions for conceptual mappings,
terminology networks, and domain relationships in Ento-Linguistic research.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib.pyplot as plt
import numpy as np

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    from ..analysis.conceptual_mapping import ConceptMap
except (ImportError, ValueError):
    from analysis.conceptual_mapping import ConceptMap

__all__ = [
    "ConceptVisualizer",
]


class ConceptVisualizer:
    """Visualize conceptual mappings and terminology networks.

    This class provides methods for creating publication-quality visualizations
    of conceptual structures, terminology relationships, and domain interactions.
    """

    # Color scheme for Ento-Linguistic domains
    DOMAIN_COLORS = {
        "unit_of_individuality": "#1f77b4",  # Blue
        "behavior_and_identity": "#ff7f0e",  # Orange
        "power_and_labor": "#2ca02c",  # Green
        "sex_and_reproduction": "#d62728",  # Red
        "kin_and_relatedness": "#9467bd",  # Purple
        "economics": "#8c564b",  # Brown
    }

    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """Initialize concept visualizer.

        Args:
            figsize: Default figure size for plots
        """
        self.figsize = figsize
        plt.style.use("default")  # Use matplotlib default style

    def visualize_concept_map(
        self,
        concept_map: ConceptMap,
        filepath: Optional[Path] = None,
        title: str = "Ento-Linguistic Concept Map",
    ) -> plt.Figure:
        """Create a publication-quality network visualization of the concept map.

        Features:
        - Formatted display labels (Title Case, no underscores)
        - Node size proportional to term count
        - Edge width proportional to relationship strength
        - Term-count annotations on each node
        - Domain-based coloring with alpha gradients
        - Data statistics subtitle
        - 16pt minimum font for publication readability

        Args:
            concept_map: Concept map to visualize
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        _MIN_FONT = 16  # Template visualization standard

        fig, ax = plt.subplots(figsize=(14, 10))

        if not HAS_NETWORKX:
            ax.text(0.5, 0.5, "networkx not available\nInstall with: pip install networkx",
                    ha="center", va="center", transform=ax.transAxes, fontsize=_MIN_FONT)
            ax.set_title(title, fontsize=_MIN_FONT + 2, fontweight="bold")
            ax.axis("off")
            if filepath:
                fig.savefig(filepath, dpi=300, bbox_inches="tight")
                plt.close(fig)
            return fig

        # ── Build graph ──────────────────────────────────────────────
        G = nx.Graph()

        # Human-readable label mapping
        def _format_label(raw_name: str) -> str:
            """Convert 'unit_of_individuality' -> 'Unit of\nIndividuality'."""
            words = raw_name.replace("_", " ").title().split()
            # Wrap long labels across two lines
            if len(words) > 2:
                mid = len(words) // 2
                return " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
            return " ".join(words)

        display_labels = {}

        # Add nodes (concepts)
        for concept_name, concept in concept_map.concepts.items():
            n_terms = len(concept.terms)
            G.add_node(
                concept_name,
                size=n_terms,
                domains=list(concept.domains),
            )
            display_labels[concept_name] = _format_label(concept_name)

        # Add edges (relationships)
        for (c1, c2), weight in concept_map.concept_relationships.items():
            if c1 in G.nodes() and c2 in G.nodes():
                G.add_edge(c1, c2, weight=weight)

        if len(G.nodes()) == 0:
            ax.text(0.5, 0.5, "No concepts in map",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=_MIN_FONT)
            ax.axis("off")
            return fig

        # ── Layout ───────────────────────────────────────────────────
        pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42)

        # ── Draw edges with width based on relationship strength ─────
        if G.edges():
            edge_weights = [G.edges[e]["weight"] for e in G.edges()]
            max_w = max(edge_weights) if edge_weights else 1
            min_w = min(edge_weights) if edge_weights else 0
            # Normalize edge widths to 1–6 range
            if max_w > min_w:
                norm_widths = [1 + 5 * (w - min_w) / (max_w - min_w) for w in edge_weights]
            else:
                norm_widths = [3.0] * len(edge_weights)

            nx.draw_networkx_edges(
                G, pos, width=norm_widths,
                edge_color="#b0b0b0", alpha=0.5, ax=ax,
                style="solid",
            )

            # Edge weight labels on the midpoint of each edge
            edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=edge_labels,
                font_size=max(9, _MIN_FONT - 6),
                font_color="#666666", ax=ax,
            )

        # ── Draw nodes ───────────────────────────────────────────────
        node_list = list(G.nodes())
        term_counts = [G.nodes[n]["size"] for n in node_list]
        max_terms = max(term_counts) if term_counts else 1

        # Scale node sizes: 800–3500 range
        node_sizes = [800 + 2700 * (tc / max_terms) for tc in term_counts]

        node_colors = [self._get_concept_color(n, concept_map) for n in node_list]

        # Draw nodes with bold outline
        nx.draw_networkx_nodes(
            G, pos, nodelist=node_list,
            node_size=node_sizes, node_color=node_colors,
            alpha=0.85, ax=ax,
            edgecolors="#333333", linewidths=1.5,
        )

        # ── Draw labels ──────────────────────────────────────────────
        nx.draw_networkx_labels(
            G, pos, labels=display_labels,
            font_size=max(11, _MIN_FONT - 4), font_weight="bold",
            font_color="#1a1a1a", ax=ax,
        )

        # ── Term-count annotations ───────────────────────────────────
        for node in node_list:
            x, y = pos[node]
            n_terms = G.nodes[node]["size"]
            ax.annotate(
                f"{n_terms} terms",
                xy=(x, y), xytext=(0, -18),
                textcoords="offset points",
                ha="center", va="top",
                fontsize=max(9, _MIN_FONT - 6),
                fontstyle="italic",
                color="#555555",
            )

        # ── Legend ───────────────────────────────────────────────────
        self._add_domain_legend(ax)

        # ── Title with data statistics ───────────────────────────────
        total_concepts = len(G.nodes())
        total_relationships = len(G.edges())
        total_terms = sum(term_counts)
        ax.set_title(
            title,
            fontsize=_MIN_FONT + 2, fontweight="bold", pad=20,
        )
        ax.text(
            0.5, 1.01,
            f"{total_concepts} concepts · {total_relationships} relationships · "
            f"{total_terms} total terms",
            transform=ax.transAxes,
            ha="center", va="bottom",
            fontsize=max(10, _MIN_FONT - 4),
            color="#666666", fontstyle="italic",
        )

        ax.axis("off")
        fig.patch.set_facecolor("#fafafa")
        ax.set_facecolor("#fafafa")

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)

        return fig

    def _get_concept_color(self, concept_name: str, concept_map: ConceptMap) -> str:
        """Get color for a concept based on its domains.

        Args:
            concept_name: Name of concept
            concept_map: Concept map containing the concept

        Returns:
            Color string
        """
        if concept_name in concept_map.concepts:
            domains = concept_map.concepts[concept_name].domains
            if domains:
                # Use the first domain's color
                primary_domain = next(iter(domains))
                return self.DOMAIN_COLORS.get(primary_domain, "#7f7f7f")

        return "#7f7f7f"  # Default gray

    def _add_domain_legend(self, ax: plt.Axes) -> None:
        """Add a legend for domain colors.

        Args:
            ax: Matplotlib axes object
        """
        legend_elements = []
        for domain, color in self.DOMAIN_COLORS.items():
            domain_name = domain.replace("_", " ").title()
            legend_elements.append(
                plt.Rectangle(
                    (0, 0), 1, 1, facecolor=color, alpha=0.7, label=domain_name
                )
            )

        ax.legend(
            handles=legend_elements,
            loc="upper left",
            bbox_to_anchor=(1.05, 1),
            title="Ento-Linguistic Domains",
        )

    def visualize_terminology_network(
        self,
        terms: Dict[str, Any],
        relationships: Dict[Tuple[str, str], float],
        filepath: Optional[Path] = None,
        title: str = "Terminology Network",
    ) -> plt.Figure:
        """Visualize a terminology network.

        Args:
            terms: Dictionary of term information
            relationships: Dictionary of term relationships
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        if not HAS_NETWORKX:
            ax.text(0.5, 0.5, "networkx not available\nInstall with: pip install networkx",
                    ha="center", va="center", transform=ax.transAxes, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.axis("off")
            if filepath:
                fig.savefig(filepath, dpi=300, bbox_inches="tight")
                plt.close(fig)
            return fig

        # Create network graph
        G = nx.Graph()

        # Add nodes (terms)
        for term_name, term_info in terms:
            domains = getattr(term_info, "domains", [])
            frequency = getattr(term_info, "frequency", 1)

            G.add_node(
                term_name,
                domains=domains,
                frequency=frequency,
                size=min(frequency * 10 + 50, 500),
            )  # Cap size

        # Add edges (relationships)
        for (term1, term2), weight in relationships.items():
            if term1 in G.nodes() and term2 in G.nodes():
                G.add_edge(term1, term2, weight=weight)

        # Remove isolated nodes for cleaner visualization
        G.remove_nodes_from(list(nx.isolates(G)))

        if len(G.nodes()) == 0:
            # No connected terms
            ax.text(
                0.5,
                0.5,
                "No connected terms found",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title)
            ax.axis("off")
            if filepath:
                fig.savefig(filepath, dpi=300, bbox_inches="tight")
                plt.close(fig)
            return fig

        # Calculate layout
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

        # Draw nodes
        node_sizes = [G.nodes[node]["size"] for node in G.nodes()]
        node_colors = [self._get_term_color(node, G) for node in G.nodes()]

        nx.draw_networkx_nodes(
            G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.7, ax=ax
        )

        # Draw edges
        if G.edges():
            edge_weights = [G.edges[edge]["weight"] * 2 for edge in G.edges()]
            nx.draw_networkx_edges(
                G, pos, width=edge_weights, edge_color="gray", alpha=0.5, ax=ax
            )

        # Draw labels (only for important terms)
        important_terms = sorted(
            G.nodes(), key=lambda x: G.nodes[x]["frequency"], reverse=True
        )[
            :20
        ]  # Top 20 terms

        label_pos = {term: pos[term] for term in important_terms if term in pos}
        label_dict = {term: term for term in label_pos}
        nx.draw_networkx_labels(G, label_pos, labels=label_dict, font_size=8, ax=ax)

        # Add legend
        self._add_domain_legend(ax)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)

        return fig

    def _get_term_color(self, term: str, G) -> str:
        """Get color for a term based on its domains.

        Args:
            term: Term name
            G: Network graph

        Returns:
            Color string
        """
        domains = G.nodes[term].get("domains", [])
        if domains:
            # Use primary domain color
            primary_domain = domains[0]
            return self.DOMAIN_COLORS.get(primary_domain, "#7f7f7f")

        return "#7f7f7f"  # Default gray

    def create_domain_comparison_plot(
        self,
        domain_data: Dict[str, Dict[str, Any]],
        filepath: Optional[Path] = None,
        terms: Optional[Dict[str, Any]] = None,
    ) -> plt.Figure:
        """Create a 2×3 comparison plot across all six Ento-Linguistic domains.

        Panels:
          (0,0) Term count per domain
          (0,1) Average extraction confidence per domain
          (1,0) Total corpus frequency per domain
          (1,1) Mean semantic entropy (ambiguity) computed from actual terms
          (2,0) Bridging-term count (terms assigned to >1 domain)
          (2,1) Mean CACE aggregate score per domain

        Args:
            domain_data: Domain statistics dict from run_analysis_pipeline
            filepath: Optional path to save figure
            terms: Full term dict (used to derive ambiguity & bridging counts)

        Returns:
            Matplotlib Figure
        """
        _MIN_FONT = 16

        domains = list(domain_data.keys())
        short_labels = [
            d.replace("_and_", " &\n").replace("_of_", " of\n").replace("_", " ").title()
            for d in domains
        ]
        domain_colors = [self.DOMAIN_COLORS.get(d, "#7f7f7f") for d in domains]

        fig, axes = plt.subplots(3, 2, figsize=(16, 18))
        fig.suptitle(
            "Ento-Linguistic Domain Comparison",
            fontsize=max(20, _MIN_FONT + 2),
            fontweight="bold",
            y=1.01,
        )

        def _bar(ax, values, ylabel, title, *, fmt=".0f"):
            """Helper: draw a bar chart with value labels."""
            bars = ax.bar(range(len(domains)), values, color=domain_colors, alpha=0.82,
                          edgecolor="white", linewidth=0.5)
            for bar, v in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{v:{fmt}}", ha="center", va="bottom",
                        fontsize=max(9, _MIN_FONT - 5), fontweight="bold")
            ax.set_xticks(range(len(domains)))
            ax.set_xticklabels(short_labels, fontsize=max(9, _MIN_FONT - 5), rotation=30, ha="right")
            ax.set_ylabel(ylabel, fontsize=_MIN_FONT - 2)
            ax.set_title(title, fontsize=_MIN_FONT, fontweight="bold", pad=6)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.tick_params(axis="y", labelsize=max(9, _MIN_FONT - 5))

        # Panel (0,0): term counts
        term_counts = [domain_data[d].get("term_count", 0) for d in domains]
        _bar(axes[0, 0], term_counts, "Number of Terms", "Terminology Count per Domain")

        # Panel (0,1): avg confidence
        conf = [float(domain_data[d].get("avg_confidence", 0.0)) for d in domains]
        _bar(axes[0, 1], conf, "Confidence Score", "Average Extraction Confidence", fmt=".3f")

        # Panel (1,0): total frequency
        freq = [domain_data[d].get("total_frequency", 0) for d in domains]
        _bar(axes[1, 0], freq, "Corpus Frequency", "Total Term Frequency per Domain")

        # Panel (1,1): Mean semantic entropy per domain
        # Priority: (1) domain_data['semantic_entropy'] from validated S02 table
        #           (2) mean of term-level semantic_entropy if present
        #           (3) pre-computed ambiguity_score fallback
        entropy_vals = []
        for domain in domains:
            # Check for validated domain-level entropy first (from S02 supplemental table)
            domain_h = domain_data[domain].get("semantic_entropy", None)
            if domain_h is not None and domain_h > 0.0:
                entropy_vals.append(float(domain_h))
            elif terms:
                domain_terms = [
                    t for t in terms.values() if domain in getattr(t, "domains", [])
                ]
                if domain_terms:
                    # Only use term-level semantic_entropy if explicitly set (not a proxy)
                    explicit_entropies = [
                        getattr(t, "semantic_entropy")
                        for t in domain_terms
                        if hasattr(t, "semantic_entropy") and isinstance(
                            getattr(t, "semantic_entropy"), (int, float)
                        )
                    ]
                    if explicit_entropies:
                        entropy_vals.append(float(np.mean(explicit_entropies)))
                    else:
                        entropy_vals.append(0.0)
                else:
                    entropy_vals.append(0.0)
            else:
                # Last resort: pre-computed ambiguity_score
                raw = domain_data[domain].get(
                    "ambiguity_score",
                    domain_data[domain].get("avg_ambiguity", 0.0),
                )
                entropy_vals.append(float(raw) if raw else 0.0)
        _bar(axes[1, 1], entropy_vals, "Mean H(t) bits",
             "Semantic Entropy (Ambiguity) per Domain", fmt=".2f")

        # Panel (2,0): bridging term count
        bridging = []
        for domain in domains:
            if terms:
                count = sum(1 for t in terms.values()
                            if domain in getattr(t, "domains", [])
                            and len(getattr(t, "domains", [])) > 1)
            else:
                count = len(domain_data[domain].get("bridging_terms", set()))
            bridging.append(count)
        _bar(axes[2, 0], bridging, "Number of Bridging Terms",
             "Cross-Domain Bridging Terms")

        # Panel (2,1): CACE aggregate (Clarity·Appropriateness·Consistency·Evolvability)
        try:
            from analysis.cace_scoring import evaluate_term_cace
            cace_vals = []
            for domain in domains:
                if terms:
                    domain_terms = [
                        (name, t) for name, t in terms.items()
                        if domain in getattr(t, "domains", [])
                    ]
                    if domain_terms:
                        scores = []
                        for name, t in domain_terms[:50]:  # Sample first 50 for speed
                            sc = evaluate_term_cace(
                                term=name,
                                semantic_entropy=getattr(t, "semantic_entropy", 0.0),
                                contexts=getattr(t, "contexts", [])[:10],
                                domains=getattr(t, "domains", []),
                            )
                            scores.append(sc.aggregate)
                        cace_vals.append(float(np.mean(scores)))
                    else:
                        cace_vals.append(0.5)
                else:
                    cace_vals.append(0.5)
        except Exception:
            # Fallback: derive from confidence and entropy
            cace_vals = [
                min(1.0, float(domain_data[d].get("avg_confidence", 0.5)))
                for d in domains
            ]
        _bar(axes[2, 1], cace_vals, "Mean CACE Score [0–1]",
             "CACE Aggregate Score per Domain", fmt=".3f")

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)

        return fig

    def create_domain_overview_grid(
        self,
        domain_data: Dict[str, Dict[str, Any]],
        terms: Dict[str, Any],
        filepath: Optional[Path] = None,
    ) -> plt.Figure:
        """6-panel grid: one subplot per domain showing top-10 terms by frequency.

        Each panel is a horizontal bar chart coloured by semantic entropy,
        with a shared colour bar on the right. This replaces the 12 scattered
        per-domain frequency and ambiguity single-panel figures.

        Args:
            domain_data: Domain statistics dict
            terms: Full term dict from analysis pipeline
            filepath: Optional path to save figure

        Returns:
            Matplotlib Figure
        """
        _MIN_FONT = 14
        valid_domains = [
            "unit_of_individuality",
            "behavior_and_identity",
            "power_and_labor",
            "sex_and_reproduction",
            "kin_and_relatedness",
            "economics",
        ]
        domain_titles = [
            "Unit of Individuality",
            "Behavior & Identity",
            "Power & Labor",
            "Sex & Reproduction",
            "Kin & Relatedness",
            "Economics",
        ]

        fig, axes = plt.subplots(3, 2, figsize=(18, 22))
        fig.suptitle(
            "Domain Terminology Overview: Top Terms by Frequency & Semantic Entropy",
            fontsize=max(18, _MIN_FONT + 2), fontweight="bold", y=1.005,
        )

        all_axes = axes.flatten()
        global_max_entropy = 1.0  # normalise colour scale

        # First pass: compute global max entropy for shared colormap
        for domain in valid_domains:
            domain_terms = [
                (name, t) for name, t in terms.items()
                if domain in getattr(t, "domains", [])
            ]
            if domain_terms:
                max_e = max(
                    getattr(t, "semantic_entropy",
                             float(len(getattr(t, "domains", [1]))))
                    for _, t in domain_terms
                )
                global_max_entropy = max(global_max_entropy, max_e)

        cmap = plt.cm.get_cmap("YlOrRd")

        for idx, (domain, title) in enumerate(zip(valid_domains, domain_titles)):
            ax = all_axes[idx]
            domain_color = self.DOMAIN_COLORS.get(domain, "#7f7f7f")

            domain_terms = [
                (name, t) for name, t in terms.items()
                if domain in getattr(t, "domains", [])
            ]
            if not domain_terms:
                ax.text(0.5, 0.5, "No terms extracted", ha="center", va="center",
                        transform=ax.transAxes, fontsize=_MIN_FONT, color="#888")
                ax.set_title(title, fontsize=_MIN_FONT, fontweight="bold",
                             color=domain_color)
                ax.axis("off")
                continue

            # Top 10 by frequency
            top = sorted(domain_terms, key=lambda x: x[1].frequency, reverse=True)[:10]
            names = [n for n, _ in top]
            freqs = [t.frequency for _, t in top]
            entropies = [
                getattr(t, "semantic_entropy",
                         float(len(getattr(t, "domains", [1]))))
                for _, t in top
            ]

            # Normalise entropy → colour
            norm_e = [min(1.0, e / global_max_entropy) for e in entropies]
            bar_colors = [cmap(ne) for ne in norm_e]

            bars = ax.barh(range(len(names)), freqs, color=bar_colors,
                           edgecolor="white", linewidth=0.4)
            for bar, f in zip(bars, freqs):
                ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                        str(f), va="center", ha="left",
                        fontsize=max(8, _MIN_FONT - 4), fontweight="bold")

            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names, fontsize=max(9, _MIN_FONT - 3))
            ax.invert_yaxis()
            ax.set_xlabel("Corpus Frequency", fontsize=_MIN_FONT - 2)
            ax.set_title(
                f"{title}  ({len(domain_terms)} terms)",
                fontsize=_MIN_FONT, fontweight="bold", color=domain_color, pad=6,
            )
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        # Shared entropy colour bar
        sm = plt.cm.ScalarMappable(cmap=cmap,
                                    norm=plt.Normalize(vmin=0, vmax=global_max_entropy))
        sm.set_array([])
        fig.colorbar(sm, ax=all_axes, orientation="vertical", fraction=0.012, pad=0.03,
                     label="Semantic Entropy H(t) bits")

        # Use constrained_layout instead of tight_layout — the colorbar axes
        # are not compatible with tight_layout and would trigger a UserWarning.
        fig.set_layout_engine("constrained")

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)

        return fig

    def create_domain_patterns_grid(
        self,
        terms: Dict[str, Any],
        filepath: Optional[Path] = None,
    ) -> plt.Figure:
        """6-panel donut grid: one chart per domain showing POS tag composition.

        Replaces the 6 scattered ``{domain}_patterns.png`` single-bar charts
        with informative donut plots showing how each domain's vocabulary is
        structured (noun compounds, adjective-noun, verb-noun, etc.).

        Args:
            terms: Full term dict from analysis pipeline
            filepath: Optional path to save figure

        Returns:
            Matplotlib Figure
        """
        _MIN_FONT = 14
        valid_domains = [
            "unit_of_individuality",
            "behavior_and_identity",
            "power_and_labor",
            "sex_and_reproduction",
            "kin_and_relatedness",
            "economics",
        ]
        domain_titles = [
            "Unit of Individuality",
            "Behavior & Identity",
            "Power & Labor",
            "Sex & Reproduction",
            "Kin & Relatedness",
            "Economics",
        ]

        fig, axes = plt.subplots(3, 2, figsize=(16, 20))
        fig.suptitle(
            "Domain Vocabulary Composition: Part-of-Speech Patterns",
            fontsize=max(18, _MIN_FONT + 2), fontweight="bold", y=1.005,
        )
        all_axes = axes.flatten()

        palette = [
            "#4e79a7", "#f28e2b", "#59a14f", "#e15759",
            "#76b7b2", "#edc948", "#b07aa1", "#ff9da7",
        ]

        for idx, (domain, title) in enumerate(zip(valid_domains, domain_titles)):
            ax = all_axes[idx]
            domain_color = self.DOMAIN_COLORS.get(domain, "#7f7f7f")

            domain_terms = [
                t for t in terms.values() if domain in getattr(t, "domains", [])
            ]
            if not domain_terms:
                ax.text(0.5, 0.5, "No terms", ha="center", va="center",
                        transform=ax.transAxes, fontsize=_MIN_FONT, color="#888")
                ax.set_title(title, fontsize=_MIN_FONT, fontweight="bold",
                             color=domain_color)
                ax.axis("off")
                continue

            # Build POS composition from pos_tags attribute
            pos_counts: Dict[str, int] = {}
            for t in domain_terms:
                tags = getattr(t, "pos_tags", [])
                if tags:
                    for tag in tags:
                        label = tag.upper()
                        pos_counts[label] = pos_counts.get(label, 0) + 1
                else:
                    # Estimate from term surface form:
                    # multi-word → likely compound; single → noun
                    words = getattr(t, "text", "").split() or [""]
                    label = "Compound" if len(words) > 1 else "Noun"
                    pos_counts[label] = pos_counts.get(label, 0) + 1

            if not pos_counts:
                pos_counts = {"Noun": 1}

            # Sort by count descending, cap at 7 for readability
            sorted_items = sorted(pos_counts.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_items) > 7:
                top_items = sorted_items[:6]
                other_count = sum(v for _, v in sorted_items[6:])
                top_items.append(("Other", other_count))
            else:
                top_items = sorted_items

            labels = [k for k, _ in top_items]
            sizes = [v for _, v in top_items]
            colors = palette[:len(labels)]

            wedge_props = {"width": 0.5, "edgecolor": "white", "linewidth": 1.5}
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors,
                autopct="%1.0f%%", startangle=90,
                wedgeprops=wedge_props,
                textprops={"fontsize": max(9, _MIN_FONT - 4)},
            )
            for at in autotexts:
                at.set_fontsize(max(8, _MIN_FONT - 5))
                at.set_fontweight("bold")

            # Centre annotation
            n_terms = len(domain_terms)
            ax.text(0, 0, f"{n_terms}\nterms", ha="center", va="center",
                    fontsize=max(9, _MIN_FONT - 3), fontweight="bold", color="#333")

            ax.set_title(
                title, fontsize=_MIN_FONT, fontweight="bold",
                color=domain_color, pad=10,
            )

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)

        return fig

    def visualize_concept_hierarchy(
        self, concept_hierarchy: Dict[str, Any], filepath: Optional[Path] = None
    ) -> plt.Figure:
        """Visualize concept hierarchy as a 2-panel figure.

        Panel 1 (left): Horizontal bar chart of centrality scores ranked
            from highest (core) to lowest (peripheral). Bars are coloured by
            domain membership and annotated with their score.
        Panel 2 (right): Scatter plot of centrality score vs. term count.
            Node size encodes centrality; colour encodes domain.

        Args:
            concept_hierarchy: Dict with keys 'centrality_scores', 'core_concepts',
                'peripheral_concepts'. The optional key 'term_counts' maps concept
                name -> number of associated terms.
            filepath: Optional path to save figure

        Returns:
            Matplotlib Figure
        """
        _MIN_FONT = 16
        from matplotlib.patches import Patch

        hierarchy_data = concept_hierarchy.get("centrality_scores", {})
        core_concepts = concept_hierarchy.get("core_concepts", [])
        peripheral_concepts = concept_hierarchy.get("peripheral_concepts", [])
        term_counts_map = concept_hierarchy.get("term_counts", {})

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, max(7, len(hierarchy_data) * 0.45 + 3)))
        fig.suptitle(
            "Ento-Linguistic Concept Hierarchy",
            fontsize=max(20, _MIN_FONT + 2), fontweight="bold", y=1.02,
        )

        if not hierarchy_data:
            for ax in (ax1, ax2):
                ax.text(0.5, 0.5, "No hierarchy data available",
                        ha="center", va="center", transform=ax.transAxes,
                        fontsize=_MIN_FONT)
                ax.axis("off")
            if filepath:
                fig.savefig(filepath, dpi=300, bbox_inches="tight")
                plt.close(fig)
            return fig

        # ── Panel 1: Centrality rank bar chart ───────────────────────
        sorted_concepts = sorted(
            hierarchy_data.items(), key=lambda x: x[1], reverse=True
        )
        concepts = [c for c, _ in sorted_concepts]
        scores = [s for _, s in sorted_concepts]

        # Colour: core=green, peripheral=red, other=steelblue
        def _concept_color(c: str) -> str:
            if c in core_concepts:
                return "#2ca02c"
            if c in peripheral_concepts:
                return "#d62728"
            return "#4e79a7"

        bar_colors = [_concept_color(c) for c in concepts]
        y_pos = np.arange(len(concepts))
        bars = ax1.barh(y_pos, scores, color=bar_colors, alpha=0.82,
                        edgecolor="white", linewidth=0.5)
        for bar, score in zip(bars, scores):
            ax1.text(bar.get_width() + max(0.1, max(scores) * 0.01),
                     bar.get_y() + bar.get_height() / 2,
                     f"{score:.1f}", va="center", ha="left",
                     fontsize=max(9, _MIN_FONT - 5), fontweight="bold")

        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(concepts, fontsize=max(9, _MIN_FONT - 4))
        ax1.invert_yaxis()
        ax1.set_xlabel("Centrality Score (Connection Count)", fontsize=_MIN_FONT - 2)
        ax1.set_title("Concept Centrality Ranking", fontsize=_MIN_FONT,
                      fontweight="bold", pad=8)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)

        legend_elements = [
            Patch(facecolor="#2ca02c", alpha=0.82, label="Core"),
            Patch(facecolor="#d62728", alpha=0.82, label="Peripheral"),
            Patch(facecolor="#4e79a7", alpha=0.82, label="Other"),
        ]
        ax1.legend(handles=legend_elements, loc="lower right",
                   fontsize=max(9, _MIN_FONT - 5))

        # ── Panel 2: Centrality vs Term-count scatter ─────────────────
        sc_x = scores  # centrality on x
        sc_y = [term_counts_map.get(c, 1) for c in concepts]  # terms on y
        sc_colors = [_concept_color(c) for c in concepts]
        sc_sizes = [max(80, s * 40) for s in scores]  # node size ∝ centrality

        ax2.scatter(sc_x, sc_y, c=sc_colors, s=sc_sizes, alpha=0.8,
                    edgecolors="white", linewidths=0.8)

        # Label top-10 by centrality
        for c, x, y in zip(concepts[:10], sc_x[:10], sc_y[:10]):
            label = c.replace("_", " ").title()
            ax2.annotate(
                label, (x, y),
                xytext=(5, 3), textcoords="offset points",
                fontsize=max(8, _MIN_FONT - 6), color="#333",
                fontweight="bold",
            )

        ax2.set_xlabel("Centrality Score", fontsize=_MIN_FONT - 2)
        ax2.set_ylabel("Number of Associated Terms", fontsize=_MIN_FONT - 2)
        ax2.set_title("Centrality vs Term Association", fontsize=_MIN_FONT,
                      fontweight="bold", pad=8)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.tick_params(labelsize=max(9, _MIN_FONT - 5))

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)

        return fig

    def create_anthropomorphic_analysis_plot(
        self,
        anthropomorphic_data: Dict[str, List[str]],
        filepath: Optional[Path] = None,
    ) -> plt.Figure:
        """Create a 2-panel visualization of anthropomorphic terminology.

        Panel 1 (left): Horizontal bar chart counting terms per anthropomorphic
            category (Hierarchical Terms, Economic Metaphors, etc.).
        Panel 2 (right): Table of sample terms per category, showing up to 5
            examples per row for editorial review.

        Args:
            anthropomorphic_data: Dict mapping category name -> list of terms
            filepath: Optional path to save figure

        Returns:
            Matplotlib Figure
        """
        _MIN_FONT = 16

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8),
                                        gridspec_kw={"width_ratios": [1, 1.6]})
        fig.suptitle(
            "Anthropomorphic Terminology in Entomological Discourse",
            fontsize=max(20, _MIN_FONT + 2), fontweight="bold", y=1.02,
        )

        if not anthropomorphic_data:
            for ax in (ax1, ax2):
                ax.text(0.5, 0.5, "No anthropomorphic data available",
                        ha="center", va="center", transform=ax.transAxes,
                        fontsize=_MIN_FONT)
                ax.axis("off")
            if filepath:
                fig.savefig(filepath, dpi=300, bbox_inches="tight")
                plt.close(fig)
            return fig

        # ── Panel 1: Category bar chart ───────────────────────────────
        categories = list(anthropomorphic_data.keys())
        counts = [len(terms_list) for terms_list in anthropomorphic_data.values()]
        palette = list(self.DOMAIN_COLORS.values())
        bar_colors = [palette[i % len(palette)] for i in range(len(categories))]

        y_pos = np.arange(len(categories))
        bars = ax1.barh(y_pos, counts, color=bar_colors, alpha=0.82,
                        edgecolor="white", linewidth=0.5)

        for bar, count in zip(bars, counts):
            ax1.text(bar.get_width() + max(0.05, max(counts) * 0.02),
                     bar.get_y() + bar.get_height() / 2,
                     str(count), va="center", ha="left",
                     fontsize=max(10, _MIN_FONT - 4), fontweight="bold")

        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(categories, fontsize=max(10, _MIN_FONT - 4))
        ax1.invert_yaxis()
        ax1.set_xlabel("Number of Terms", fontsize=_MIN_FONT - 2)
        ax1.set_title("Terms per Anthropomorphic Category",
                      fontsize=_MIN_FONT, fontweight="bold", pad=8)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        total = sum(counts)
        ax1.text(0.98, 0.02, f"Total: {total} terms",
                 transform=ax1.transAxes, ha="right", va="bottom",
                 fontsize=max(10, _MIN_FONT - 5), color="#555", fontstyle="italic")

        # ── Panel 2: Sample terms table ───────────────────────────────
        ax2.axis("off")
        ax2.set_title("Sample Terms by Category",
                      fontsize=_MIN_FONT, fontweight="bold", pad=8)

        row_height = 1.0 / (len(categories) + 1)
        header_y = 1.0 - row_height / 2

        ax2.text(0.02, header_y, "Category", transform=ax2.transAxes,
                 fontsize=max(10, _MIN_FONT - 4), fontweight="bold", va="center")
        ax2.text(0.35, header_y, "Example Terms", transform=ax2.transAxes,
                 fontsize=max(10, _MIN_FONT - 4), fontweight="bold", va="center")
        # Header separator line (use plot with transform to avoid axhline restriction)
        ax2.plot([0, 1], [header_y - row_height / 2, header_y - row_height / 2],
                 color="#ccc", linewidth=0.8, transform=ax2.transAxes,
                 clip_on=False)

        for row_idx, (cat, terms_list) in enumerate(anthropomorphic_data.items()):
            y = header_y - (row_idx + 1) * row_height
            bg_color = "#f5f5f5" if row_idx % 2 == 0 else "white"
            # Background stripe: use fill_betweenx in transAxes coords
            ax2.fill_betweenx(
                [y - row_height / 2, y + row_height / 2],
                0, 1,
                color=bg_color, alpha=0.6,
                transform=ax2.transAxes,
                zorder=0,
            )

            cat_color = palette[row_idx % len(palette)]
            ax2.text(0.02, y, cat, transform=ax2.transAxes,
                     fontsize=max(9, _MIN_FONT - 5), va="center",
                     color=cat_color, fontweight="bold")

            sample = ", ".join(terms_list[:5])
            if len(terms_list) > 5:
                sample += f" … (+{len(terms_list) - 5})"
            ax2.text(0.35, y, sample, transform=ax2.transAxes,
                     fontsize=max(9, _MIN_FONT - 6), va="center", color="#333")

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)

        return fig

    def export_visualization_metadata(
        self, figures: Dict[str, plt.Figure], metadata_file: Path
    ) -> None:
        """Export metadata about created visualizations.

        Args:
            figures: Dictionary of figure names to figure objects
            metadata_file: Path to save metadata
        """
        import json
        from datetime import datetime

        metadata = {
            "creation_date": datetime.now().isoformat(),
            "figures": {},
            "visualization_settings": {
                "figsize": self.figsize,
                "domain_colors": self.DOMAIN_COLORS,
            },
        }

        for fig_name, fig in figures.items():
            # Get figure dimensions and other properties
            fig_metadata = {
                "name": fig_name,
                "size_inches": fig.get_size_inches().tolist(),
                "dpi": 300,  # Default DPI for saving
                "axes_count": len(fig.axes),
            }
            metadata["figures"][fig_name] = fig_metadata

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def visualize_term_cooccurrence(
        self,
        cooccurrence_matrix: Dict[str, Dict[str, int]],
        filepath: Optional[Path] = None,
        title: str = "Term Co-occurrence Network",
    ) -> plt.Figure:
        """Create a network visualization of term co-occurrence patterns.

        Args:
            cooccurrence_matrix: Dictionary mapping term pairs to co-occurrence counts
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Build NetworkX graph from co-occurrence matrix
        try:
            import networkx as nx
        except ImportError:
            # Fallback: simple visualization
            self._create_fallback_cooccurrence_plot(cooccurrence_matrix, ax, title)
            if filepath:
                fig.savefig(filepath, dpi=300, bbox_inches="tight")
            return fig

        G = nx.Graph()

        # Add nodes (terms)
        terms = set()
        for term1, cooccurs in cooccurrence_matrix.items():
            terms.add(term1)
            terms.update(cooccurs.keys())

        for term in terms:
            G.add_node(term)

        # Add edges with weights
        for term1, cooccurs in cooccurrence_matrix.items():
            for term2, weight in cooccurs.items():
                if weight > 0:  # Only add edges with co-occurrences
                    G.add_edge(term1, term2, weight=weight)

        # Calculate node positions using force-directed layout
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # Draw nodes with size based on degree
        node_sizes = [G.degree(node) * 100 + 300 for node in G.nodes()]
        node_colors = ["lightblue" for _ in G.nodes()]  # Default color

        nx.draw_networkx_nodes(
            G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.7, ax=ax
        )

        # Draw edges with width based on co-occurrence strength
        edge_weights = [G.edges[edge]["weight"] * 0.5 for edge in G.edges()]
        nx.draw_networkx_edges(
            G, pos, width=edge_weights, edge_color="gray", alpha=0.6, ax=ax
        )

        # Draw labels for high-degree nodes only
        high_degree_nodes = [node for node in G.nodes() if G.degree(node) > 2]
        labels = {node: node for node in high_degree_nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight="bold", ax=ax)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def create_domain_overlap_heatmap(
        self,
        domain_overlaps: Dict[str, Dict[str, Any]],
        filepath: Optional[Path] = None,
        title: str = "Domain Term Overlap Heatmap",
    ) -> plt.Figure:
        """Create a heatmap visualization of term overlap between domains.

        Args:
            domain_overlaps: Dictionary of domain pair overlaps.
                Keys can use '||' or '_and_' as pair separator.
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        import numpy as np

        fig, ax = plt.subplots(figsize=(10, 8))

        # ── Parse domain pair keys ───────────────────────────────────
        domain_pairs = list(domain_overlaps.keys())
        domains = set()

        def _split_pair(pair: str):
            """Split a pair key into two domain names."""
            if "||" in pair:
                return pair.split("||", 1)
            if "_and_" in pair:
                return pair.split("_and_", 1)
            if "_" in pair and len(pair.split("_")) == 2:
                return pair.split("_")
            return None

        for pair in domain_pairs:
            parts = _split_pair(pair)
            if parts:
                domains.add(parts[0])
                domains.add(parts[1])

        domains = sorted(list(domains))

        # Guard against empty or single-domain data that would cause
        # singular transformation warnings in imshow
        if len(domains) < 2:
            ax.text(
                0.5,
                0.5,
                "Insufficient domain data for heatmap",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title)
            ax.axis("off")
            return fig

        domain_to_idx = {domain: i for i, domain in enumerate(domains)}

        # Create overlap matrix
        overlap_matrix = np.zeros((len(domains), len(domains)))

        for pair, data in domain_overlaps.items():
            parts = _split_pair(pair)
            if not parts:
                continue

            d1, d2 = parts
            if d1 in domain_to_idx and d2 in domain_to_idx:
                overlap_pct = data.get("overlap_percentage", 0)
                i, j = domain_to_idx[d1], domain_to_idx[d2]
                overlap_matrix[i, j] = overlap_pct
                overlap_matrix[j, i] = overlap_pct  # Symmetric

        # Create heatmap
        im = ax.imshow(overlap_matrix, cmap="YlOrRd", aspect="equal")

        # Readable labels
        display_labels = [d.replace("_", " ").title() for d in domains]

        # Add labels
        ax.set_xticks(range(len(domains)))
        ax.set_yticks(range(len(domains)))
        ax.set_xticklabels(display_labels, rotation=45, ha="right")
        ax.set_yticklabels(display_labels)

        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Overlap Percentage", rotation=-90, va="bottom")

        # Add text annotations
        for i in range(len(domains)):
            for j in range(len(domains)):
                if overlap_matrix[i, j] > 0:
                    ax.text(
                        j, i, f"{overlap_matrix[i, j]:.1f}",
                        ha="center", va="center", color="black", fontsize=8
                    )

        ax.set_title(title, fontsize=14, fontweight="bold")
        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def visualize_concept_evolution(
        self,
        evolution_data: Dict[str, Dict[str, Any]],
        filepath: Optional[Path] = None,
        title: str = "Concept Evolution Over Time",
    ) -> plt.Figure:
        """Create a temporal visualization of concept evolution.

        Args:
            evolution_data: Dictionary of concept evolution metrics
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # Extract data for plotting
        concepts = list(evolution_data.keys())[
            :6
        ]  # Limit to 6 concepts for readability
        time_points = []

        # Collect evolution data
        term_counts = []
        relationship_counts = []
        stability_scores = []

        for concept in concepts:
            data = evolution_data[concept]
            term_evolution = data.get("term_count_evolution", [])
            rel_evolution = data.get("relationship_count_evolution", [])
            stability = data.get("term_stability", [])

            if term_evolution:
                if not time_points:
                    time_points = list(range(len(term_evolution)))
                term_counts.append(term_evolution)
                relationship_counts.append(rel_evolution)
                stability_scores.append(stability)

        if not time_points:
            # Fallback for empty data
            ax1.text(
                0.5,
                0.5,
                "No evolution data available",
                transform=ax1.transAxes,
                ha="center",
                va="center",
            )
            ax1.set_title("Term Count Evolution")
            ax1.axis("off")
        else:
            # Plot term count evolution
            for i, (concept, counts) in enumerate(zip(concepts, term_counts)):
                ax1.plot(time_points, counts, marker="o", label=concept, linewidth=2)

            ax1.set_xlabel("Time Period")
            ax1.set_ylabel("Term Count")
            ax1.set_title("Term Count Evolution")
            ax1.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            ax1.grid(True, alpha=0.3)

            # Plot relationship evolution
            for i, (concept, counts) in enumerate(zip(concepts, relationship_counts)):
                ax2.plot(time_points, counts, marker="s", label=concept, linewidth=2)

            ax2.set_xlabel("Time Period")
            ax2.set_ylabel("Relationship Count")
            ax2.set_title("Relationship Evolution")
            ax2.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            ax2.grid(True, alpha=0.3)

            # Plot stability over time
            for i, (concept, stability) in enumerate(zip(concepts, stability_scores)):
                ax3.plot(time_points, stability, marker="^", label=concept, linewidth=2)

            ax3.set_xlabel("Time Period")
            ax3.set_ylabel("Stability Score")
            ax3.set_title("Term Stability Over Time")
            ax3.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            ax3.grid(True, alpha=0.3)

            # Plot growth rates
            growth_rates = []
            concept_names = []
            for concept, data in evolution_data.items():
                rate = data.get("term_growth_rate", 0)
                growth_rates.append(rate)
                concept_names.append(
                    concept[:15] + "..." if len(concept) > 15 else concept
                )

            ax4.bar(range(len(growth_rates)), growth_rates)
            ax4.set_xlabel("Concepts")
            ax4.set_ylabel("Growth Rate")
            ax4.set_title("Term Growth Rates")
            ax4.set_xticks(range(len(concept_names)))
            ax4.set_xticklabels(concept_names, rotation=45, ha="right")

        plt.suptitle(title, fontsize=16, fontweight="bold")
        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def create_statistical_summary_plot(
        self,
        statistical_data: Dict[str, Dict[str, Any]],
        filepath: Optional[Path] = None,
        title: str = "Statistical Summary",
    ) -> plt.Figure:
        """Create a multi-panel statistical summary visualization.

        Args:
            statistical_data: Dictionary of statistical analysis results
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        import numpy as np

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Extract data for different plot types
        if "frequency_stats" in statistical_data:
            freq_data = statistical_data["frequency_stats"]

            # Frequency distribution histogram
            if "frequency_distribution" in freq_data:
                dist_data = freq_data["frequency_distribution"]
                if "counts" in dist_data and dist_data["counts"]:
                    axes[0, 0].bar(
                        range(len(dist_data["counts"])),
                        dist_data["counts"],
                        alpha=0.7,
                        color="skyblue",
                        edgecolor="black",
                    )
                    axes[0, 0].set_xlabel("Frequency Bins")
                    axes[0, 0].set_ylabel("Count")
                    axes[0, 0].set_title("Term Frequency Distribution")
                    axes[0, 0].grid(True, alpha=0.3)

            # Top terms bar chart
            if "top_terms" in freq_data and freq_data["top_terms"]:
                terms = [
                    (
                        item["term"][:15] + "..."
                        if len(item["term"]) > 15
                        else item["term"]
                    )
                    for item in freq_data["top_terms"]
                ]
                frequencies = [item["frequency"] for item in freq_data["top_terms"]]

                axes[0, 1].barh(
                    terms, frequencies, color="lightgreen", edgecolor="black"
                )
                axes[0, 1].set_xlabel("Frequency")
                axes[0, 1].set_title("Top Terms by Frequency")
                axes[0, 1].grid(True, alpha=0.3)

        # Statistical significance plot
        if "statistical_significance" in statistical_data:
            sig_data = statistical_data["statistical_significance"]

            if "p_value" in sig_data and "chi_square_statistic" in sig_data:
                # P-value vs significance threshold
                p_val = sig_data["p_value"]
                threshold = sig_data.get("significance_threshold", 0.05)
                chi_sq = sig_data["chi_square_statistic"]

                axes[1, 0].bar(
                    ["Chi-Square Statistic", "P-Value Threshold"],
                    [chi_sq, threshold],
                    color=["orange", "red"],
                    alpha=0.7,
                )
                axes[1, 0].axhline(
                    y=p_val,
                    color="blue",
                    linestyle="--",
                    label=f"Actual P-Value: {p_val:.4f}",
                )
                axes[1, 0].set_ylabel("Value")
                axes[1, 0].set_title("Statistical Significance Analysis")
                axes[1, 0].legend()
                axes[1, 0].grid(True, alpha=0.3)

        # Ambiguity metrics
        if (
            "ambiguity_metrics" in statistical_data
            and "domain_metrics" in statistical_data["ambiguity_metrics"]
        ):
            domain_metrics = statistical_data["ambiguity_metrics"]["domain_metrics"]

            if domain_metrics:
                metrics = [
                    "average_context_diversity",
                    "average_ambiguity_score",
                    "max_ambiguity_score",
                ]
                values = [domain_metrics.get(metric, 0) for metric in metrics]

                axes[1, 1].bar(
                    metrics, values, color="purple", alpha=0.7, edgecolor="black"
                )
                axes[1, 1].set_ylabel("Score")
                axes[1, 1].set_title("Domain Ambiguity Metrics")
                axes[1, 1].tick_params(axis="x", rotation=45)
                axes[1, 1].grid(True, alpha=0.3)

        plt.suptitle(title, fontsize=16, fontweight="bold")
        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches="tight")

        return fig

    def create_interactive_concept_network(
        self,
        concept_map: ConceptMap,
        output_dir: Path,
        title: str = "Interactive Concept Network",
    ) -> str:
        """Create an interactive HTML visualization of the concept network.

        Args:
            concept_map: Concept map to visualize
            output_dir: Directory to save HTML file
            title: Visualization title

        Returns:
            Path to created HTML file
        """
        try:
            import networkx as nx
            import plotly.graph_objects as go
        except ImportError:
            # Fallback: create static network and return path to it
            static_fig = self.visualize_concept_map(concept_map, title=title)
            static_path = output_dir / "concept_network_static.png"
            static_fig.savefig(static_path, dpi=300, bbox_inches="tight")
            plt.close(static_fig)
            return str(static_path)

        # Create NetworkX graph
        G = nx.Graph()

        # Add nodes with attributes
        for concept_name, concept in concept_map.concepts.items():
            G.add_node(
                concept_name,
                size=len(concept.terms),
                domains=list(concept.domains),
                description=concept.description,
            )

        # Add edges with weights
        for (concept1, concept2), weight in concept_map.concept_relationships.items():
            G.add_edge(concept1, concept2, weight=weight)

        # Calculate positions
        pos = nx.spring_layout(G, k=1, iterations=50, seed=42, dim=3)

        # Create edge traces
        edge_x, edge_y, edge_z = [], [], []
        for edge in G.edges():
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

        edge_trace = go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line=dict(width=2, color="gray"),
            hoverinfo="none",
            name="relationships",
        )

        # Create node traces
        node_x, node_y, node_z = [], [], []
        node_text, node_sizes, node_colors = [], [], []

        for node in G.nodes():
            x, y, z = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)

            # Node information
            domains = G.nodes[node]["domains"]
            size = G.nodes[node]["size"]
            description = G.nodes[node]["description"]

            node_text.append(
                f"Concept: {node}<br>Domains: {', '.join(domains)}<br>Terms: {size}<br>{description}"
            )
            node_sizes.append(size * 5 + 20)  # Scale node size
            node_colors.append(self._get_concept_color_3d(node, concept_map))

        node_trace = go.Scatter3d(
            x=node_x,
            y=node_y,
            z=node_z,
            mode="markers",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                opacity=0.8,
                line=dict(width=2, color="black"),
            ),
            text=node_text,
            hoverinfo="text",
            name="concepts",
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace])

        fig.update_layout(
            title=title,
            showlegend=False,
            scene=dict(
                xaxis=dict(showbackground=False),
                yaxis=dict(showbackground=False),
                zaxis=dict(showbackground=False),
            ),
            margin=dict(l=0, r=0, t=40, b=0),
        )

        # Save HTML file
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / "interactive_concept_network.html"
        fig.write_html(str(html_path))

        return str(html_path)

    def _get_concept_color_3d(self, concept_name: str, concept_map: ConceptMap) -> str:
        """Get color for 3D visualization based on dominant domain."""
        if concept_name in concept_map.concepts:
            concept = concept_map.concepts[concept_name]
            if concept.domains:
                # Use first domain's color
                domain = next(iter(concept.domains))
                return self.DOMAIN_COLORS.get(domain, "gray")

        return "gray"

    def _create_fallback_cooccurrence_plot(
        self, cooccurrence_matrix: Dict[str, Dict[str, int]], ax: plt.Axes, title: str
    ) -> None:
        """Create a fallback co-occurrence visualization without NetworkX."""
        # Simple bar chart of co-occurrence frequencies
        term_pairs = []
        frequencies = []

        for term1, cooccurs in cooccurrence_matrix.items():
            for term2, freq in cooccurs.items():
                if freq > 0:
                    term_pairs.append(f"{term1}-{term2}")
                    frequencies.append(freq)

        # Sort by frequency
        sorted_pairs = sorted(zip(frequencies, term_pairs), reverse=True)[:20]  # Top 20
        if not sorted_pairs:
            ax.text(0.5, 0.5, "No co-occurrence data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12)
            ax.set_title(title)
            return
        frequencies, term_pairs = zip(*sorted_pairs)

        ax.barh(
            range(len(term_pairs)), frequencies, color="lightcoral", edgecolor="black"
        )
        ax.set_yticks(range(len(term_pairs)))
        ax.set_yticklabels(term_pairs, fontsize=8)
        ax.set_xlabel("Co-occurrence Frequency")
        ax.set_title(f"{title} (Top 20 Pairs)")
        ax.grid(True, alpha=0.3)

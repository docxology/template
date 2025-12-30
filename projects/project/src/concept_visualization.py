"""Concept visualization for Ento-Linguistic analysis.

This module provides visualization functions for conceptual mappings,
terminology networks, and domain relationships in Ento-Linguistic research.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Dict, Set, Optional, Tuple, Any
import numpy as np
from pathlib import Path

try:
    from .conceptual_mapping import ConceptMap
except ImportError:
    from conceptual_mapping import ConceptMap


class ConceptVisualizer:
    """Visualize conceptual mappings and terminology networks.

    This class provides methods for creating publication-quality visualizations
    of conceptual structures, terminology relationships, and domain interactions.
    """

    # Color scheme for Ento-Linguistic domains
    DOMAIN_COLORS = {
        'unit_of_individuality': '#1f77b4',  # Blue
        'behavior_and_identity': '#ff7f0e',  # Orange
        'power_and_labor': '#2ca02c',       # Green
        'sex_and_reproduction': '#d62728',  # Red
        'kin_and_relatedness': '#9467bd',   # Purple
        'economics': '#8c564b'              # Brown
    }

    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """Initialize concept visualizer.

        Args:
            figsize: Default figure size for plots
        """
        self.figsize = figsize
        plt.style.use('default')  # Use matplotlib default style

    def visualize_concept_map(self, concept_map: ConceptMap,
                            filepath: Optional[Path] = None,
                            title: str = "Ento-Linguistic Concept Map") -> plt.Figure:
        """Create a network visualization of the concept map.

        Args:
            concept_map: Concept map to visualize
            filepath: Optional path to save figure
            title: Plot title

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Create network graph
        G = nx.Graph()

        # Add nodes (concepts)
        for concept_name, concept in concept_map.concepts.items():
            G.add_node(concept_name,
                      size=len(concept.terms),
                      domains=list(concept.domains))

        # Add edges (relationships)
        for (concept1, concept2), weight in concept_map.concept_relationships.items():
            G.add_edge(concept1, concept2, weight=weight)

        # Calculate node positions using force-directed layout
        pos = nx.spring_layout(G, k=1, iterations=50, seed=42)

        # Draw nodes with size based on term count
        node_sizes = [G.nodes[node]['size'] * 100 + 300 for node in G.nodes()]
        node_colors = [self._get_concept_color(node, concept_map) for node in G.nodes()]

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                             node_color=node_colors, alpha=0.7, ax=ax)

        # Draw edges with width based on relationship strength
        edge_weights = [G.edges[edge]['weight'] * 2 for edge in G.edges()]
        nx.draw_networkx_edges(G, pos, width=edge_weights,
                             edge_color='gray', alpha=0.6, ax=ax)

        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)

        # Add legend
        self._add_domain_legend(ax)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
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
                return self.DOMAIN_COLORS.get(primary_domain, '#7f7f7f')

        return '#7f7f7f'  # Default gray

    def _add_domain_legend(self, ax: plt.Axes) -> None:
        """Add a legend for domain colors.

        Args:
            ax: Matplotlib axes object
        """
        legend_elements = []
        for domain, color in self.DOMAIN_COLORS.items():
            domain_name = domain.replace('_', ' ').title()
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.7,
                                               label=domain_name))

        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1),
                 title="Ento-Linguistic Domains")

    def visualize_terminology_network(self, terms: Dict[str, Any],
                                    relationships: Dict[Tuple[str, str], float],
                                    filepath: Optional[Path] = None,
                                    title: str = "Terminology Network") -> plt.Figure:
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

        # Create network graph
        G = nx.Graph()

        # Add nodes (terms)
        for term_name, term_info in terms:
            domains = term_info.domains if hasattr(term_info, 'domains') else []
            frequency = term_info.frequency if hasattr(term_info, 'frequency') else 1

            G.add_node(term_name,
                      domains=domains,
                      frequency=frequency,
                      size=min(frequency * 10 + 50, 500))  # Cap size

        # Add edges (relationships)
        for (term1, term2), weight in relationships.items():
            if term1 in G.nodes() and term2 in G.nodes():
                G.add_edge(term1, term2, weight=weight)

        # Remove isolated nodes for cleaner visualization
        G.remove_nodes_from(list(nx.isolates(G)))

        if len(G.nodes()) == 0:
            # No connected terms
            ax.text(0.5, 0.5, "No connected terms found",
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            ax.axis('off')
            return fig

        # Calculate layout
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

        # Draw nodes
        node_sizes = [G.nodes[node]['size'] for node in G.nodes()]
        node_colors = [self._get_term_color(node, G) for node in G.nodes()]

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                             node_color=node_colors, alpha=0.7, ax=ax)

        # Draw edges
        if G.edges():
            edge_weights = [G.edges[edge]['weight'] * 2 for edge in G.edges()]
            nx.draw_networkx_edges(G, pos, width=edge_weights,
                                 edge_color='gray', alpha=0.5, ax=ax)

        # Draw labels (only for important terms)
        important_terms = sorted(G.nodes(),
                               key=lambda x: G.nodes[x]['frequency'],
                               reverse=True)[:20]  # Top 20 terms

        label_pos = {term: pos[term] for term in important_terms}
        nx.draw_networkx_labels(G, label_pos, font_size=8, ax=ax)

        # Add legend
        self._add_domain_legend(ax)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)

        return fig

    def _get_term_color(self, term: str, G: nx.Graph) -> str:
        """Get color for a term based on its domains.

        Args:
            term: Term name
            G: Network graph

        Returns:
            Color string
        """
        domains = G.nodes[term].get('domains', [])
        if domains:
            # Use primary domain color
            primary_domain = domains[0]
            return self.DOMAIN_COLORS.get(primary_domain, '#7f7f7f')

        return '#7f7f7f'  # Default gray

    def create_domain_comparison_plot(self, domain_data: Dict[str, Dict[str, Any]],
                                    filepath: Optional[Path] = None) -> plt.Figure:
        """Create a comparison plot across domains.

        Args:
            domain_data: Dictionary with domain statistics
            filepath: Optional path to save figure

        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle("Ento-Linguistic Domain Comparison", fontsize=16, fontweight='bold')

        domains = list(domain_data.keys())
        domain_colors = [self.DOMAIN_COLORS.get(domain, '#7f7f7f') for domain in domains]

        # Plot 1: Term counts
        term_counts = [domain_data[d].get('term_count', 0) for d in domains]
        axes[0,0].bar(domains, term_counts, color=domain_colors, alpha=0.7)
        axes[0,0].set_title('Terminology Count by Domain')
        axes[0,0].set_ylabel('Number of Terms')
        axes[0,0].tick_params(axis='x', rotation=45)

        # Plot 2: Average confidence
        avg_confidence = [domain_data[d].get('avg_confidence', 0) for d in domains]
        axes[0,1].bar(domains, avg_confidence, color=domain_colors, alpha=0.7)
        axes[0,1].set_title('Average Term Confidence by Domain')
        axes[0,1].set_ylabel('Confidence Score')
        axes[0,1].tick_params(axis='x', rotation=45)

        # Plot 3: Total frequency
        total_freq = [domain_data[d].get('total_frequency', 0) for d in domains]
        axes[1,0].bar(domains, total_freq, color=domain_colors, alpha=0.7)
        axes[1,0].set_title('Total Term Frequency by Domain')
        axes[1,0].set_ylabel('Total Frequency')
        axes[1,0].tick_params(axis='x', rotation=45)

        # Plot 4: Bridging terms
        bridging_counts = [len(domain_data[d].get('bridging_terms', set())) for d in domains]
        axes[1,1].bar(domains, bridging_counts, color=domain_colors, alpha=0.7)
        axes[1,1].set_title('Cross-Domain Bridging Terms')
        axes[1,1].set_ylabel('Number of Bridging Terms')
        axes[1,1].tick_params(axis='x', rotation=45)

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)

        return fig

    def visualize_concept_hierarchy(self, concept_hierarchy: Dict[str, Any],
                                  filepath: Optional[Path] = None) -> plt.Figure:
        """Visualize concept hierarchy.

        Args:
            concept_hierarchy: Hierarchy data
            filepath: Optional path to save figure

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Create hierarchical layout
        hierarchy_data = concept_hierarchy.get('centrality_scores', {})
        core_concepts = concept_hierarchy.get('core_concepts', [])
        peripheral_concepts = concept_hierarchy.get('peripheral_concepts', [])

        if not hierarchy_data:
            ax.text(0.5, 0.5, "No hierarchy data available",
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Concept Hierarchy")
            ax.axis('off')
            return fig

        # Sort concepts by centrality
        sorted_concepts = sorted(hierarchy_data.items(), key=lambda x: x[1], reverse=True)
        concepts, centrality_scores = zip(*sorted_concepts)

        # Color code core vs peripheral
        colors = []
        for concept in concepts:
            if concept in core_concepts:
                colors.append('#2ca02c')  # Green for core
            elif concept in peripheral_concepts:
                colors.append('#d62728')  # Red for peripheral
            else:
                colors.append('#7f7f7f')  # Gray for others

        # Create horizontal bar chart
        y_pos = np.arange(len(concepts))
        ax.barh(y_pos, centrality_scores, color=colors, alpha=0.7)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(concepts)
        ax.set_xlabel('Centrality Score')
        ax.set_title('Concept Hierarchy by Centrality', fontsize=14, fontweight='bold')

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ca02c', alpha=0.7, label='Core Concepts'),
            Patch(facecolor='#d62728', alpha=0.7, label='Peripheral Concepts'),
            Patch(facecolor='#7f7f7f', alpha=0.7, label='Other Concepts')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)

        return fig

    def create_anthropomorphic_analysis_plot(self, anthropomorphic_data: Dict[str, List[str]],
                                           filepath: Optional[Path] = None) -> plt.Figure:
        """Create visualization of anthropomorphic concepts.

        Args:
            anthropomorphic_data: Anthropomorphic analysis results
            filepath: Optional path to save figure

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        if not anthropomorphic_data:
            ax.text(0.5, 0.5, "No anthropomorphic data available",
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Anthropomorphic Concept Analysis")
            ax.axis('off')
            return fig

        # Count terms by category
        categories = list(anthropomorphic_data.keys())
        counts = [len(terms) for terms in anthropomorphic_data.values()]

        # Create bar chart
        bars = ax.bar(categories, counts, alpha=0.7, color='#ff7f0e')

        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{count}', ha='center', va='bottom')

        ax.set_xlabel('Anthropomorphic Categories')
        ax.set_ylabel('Number of Terms')
        ax.set_title('Anthropomorphic Terminology by Category', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)

        # Add sample terms as text
        y_pos = 0.95
        ax.text(1.05, y_pos, "Sample Terms:", transform=ax.transAxes,
               fontsize=10, fontweight='bold')
        y_pos -= 0.05

        for category, terms in anthropomorphic_data.items():
            if terms:
                sample_terms = terms[:3]  # Show up to 3 examples
                term_text = f"{category}: {', '.join(sample_terms)}"
                ax.text(1.05, y_pos, term_text, transform=ax.transAxes,
                       fontsize=8, wrap=True)
                y_pos -= 0.05

        plt.tight_layout()

        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)

        return fig

    def export_visualization_metadata(self, figures: Dict[str, plt.Figure],
                                    metadata_file: Path) -> None:
        """Export metadata about created visualizations.

        Args:
            figures: Dictionary of figure names to figure objects
            metadata_file: Path to save metadata
        """
        import json
        from datetime import datetime

        metadata = {
            'creation_date': datetime.now().isoformat(),
            'figures': {},
            'visualization_settings': {
                'figsize': self.figsize,
                'domain_colors': self.DOMAIN_COLORS
            }
        }

        for fig_name, fig in figures.items():
            # Get figure dimensions and other properties
            fig_metadata = {
                'name': fig_name,
                'size_inches': fig.get_size_inches().tolist(),
                'dpi': 300,  # Default DPI for saving
                'axes_count': len(fig.axes)
            }
            metadata['figures'][fig_name] = fig_metadata

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
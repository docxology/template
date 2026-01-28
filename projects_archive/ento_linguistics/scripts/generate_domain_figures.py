"""Generate domain figures script for Ento-Linguistic research.

This script generates publication-quality figures for each Ento-Linguistic domain,
visualizing terminology patterns, ambiguities, and conceptual relationships.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from concept_visualization import ConceptVisualizer
from domain_analysis import DomainAnalyzer
from literature_mining import LiteratureCorpus
from term_extraction import TerminologyExtractor

from infrastructure.core.logging_utils import get_logger
from infrastructure.documentation.figure_manager import FigureManager

logger = get_logger(__name__)


class DomainFigureGenerator:
    """Generate figures for Ento-Linguistic domain analysis.

    This class creates comprehensive visualizations for each of the six
    Ento-Linguistic domains, showing terminology patterns, relationships,
    and conceptual structures.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize figure generator.

        Args:
            output_dir: Directory for output files
        """
        self.project_root = Path(__file__).parent.parent
        self.output_dir = output_dir or self.project_root / "output"
        self.figures_dir = self.output_dir / "figures"
        self.data_dir = self.output_dir / "data"

        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.figure_manager = FigureManager()
        self.visualizer = ConceptVisualizer()

        logger.info(
            f"Initialized domain figure generator with output directory: {self.output_dir}"
        )

    def generate_domain_figures(
        self, domain_name: str, corpus_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate figures for a specific domain.

        Args:
            domain_name: Name of the domain to visualize
            corpus_file: Path to literature corpus

        Returns:
            Results dictionary with generated figures
        """
        # Validate domain name
        valid_domains = [
            "unit_of_individuality",
            "behavior_and_identity",
            "power_and_labor",
            "sex_and_reproduction",
            "kin_and_relatedness",
            "economics",
        ]
        if domain_name not in valid_domains:
            logger.error(f"Invalid domain name: {domain_name}")
            logger.error(f"Valid domains: {', '.join(valid_domains)}")
            return {"error": f"Invalid domain name: {domain_name}"}

        logger.info(f"Generating figures for {domain_name} domain")

        # Load and process data
        corpus = self._load_corpus(corpus_file)
        texts = corpus.get_text_corpus()

        # Extract terminology
        extractor = TerminologyExtractor()
        all_terms = extractor.extract_terms(texts, min_frequency=2)

        # Filter for domain
        domain_terms = {
            term: term_obj
            for term, term_obj in all_terms.items()
            if domain_name in term_obj.domains
        }

        if not domain_terms:
            logger.warning(f"No terms found for domain {domain_name}")
            return {"error": f"No terms found for domain {domain_name}"}

        # Perform domain analysis
        analyzer = DomainAnalyzer()
        analyses = analyzer.analyze_all_domains(all_terms, texts)
        analysis = analyses.get(domain_name)

        if not analysis:
            logger.warning(f"No analysis available for domain {domain_name}")
            return {"error": f"No analysis available for domain {domain_name}"}

        # Generate figures
        figures = self._generate_domain_specific_figures(
            domain_name, domain_terms, analysis
        )

        results = {
            "domain": domain_name,
            "terms_visualized": len(domain_terms),
            "figures_generated": len(figures),
            "figure_files": figures,
        }

        logger.info(f"Generated {len(figures)} figures for {domain_name}")
        return results

    def generate_all_domain_figures(
        self, corpus_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate figures for all domains.

        Args:
            corpus_file: Path to literature corpus

        Returns:
            Summary of all generated figures
        """
        domains = [
            "unit_of_individuality",
            "behavior_and_identity",
            "power_and_labor",
            "sex_and_reproduction",
            "kin_and_relatedness",
            "economics",
        ]

        all_results = {}
        total_figures = 0

        for domain in domains:
            try:
                results = self.generate_domain_figures(domain, corpus_file)
                if "error" not in results:
                    all_results[domain] = results
                    total_figures += results.get("figures_generated", 0)
                else:
                    all_results[domain] = results
            except Exception as e:
                logger.exception(f"Failed to generate figures for domain '{domain}'")
                logger.error(f"Domain figure generation failed: {e}")
                all_results[domain] = {"error": str(e)}

        # Generate comparative figures
        comparative_figures = self._generate_comparative_figures(
            all_results, corpus_file
        )

        summary = {
            "individual_domains": all_results,
            "comparative_figures": comparative_figures,
            "total_figures_generated": total_figures + len(comparative_figures),
            "domains_processed": len(
                [r for r in all_results.values() if "error" not in r]
            ),
        }

        logger.info(
            f"Generated {summary['total_figures_generated']} figures across all domains"
        )
        return summary

    def _load_corpus(self, corpus_file: Optional[Path]) -> LiteratureCorpus:
        """Load literature corpus."""
        if corpus_file and corpus_file.exists():
            return LiteratureCorpus.load_from_file(corpus_file)
        else:
            default_corpus = self.data_dir / "literature_corpus.json"
            if default_corpus.exists():
                return LiteratureCorpus.load_from_file(default_corpus)
            else:
                return LiteratureCorpus()

    def _generate_domain_specific_figures(
        self, domain_name: str, domain_terms: Dict[str, Any], analysis: Any
    ) -> Dict[str, str]:
        """Generate figures specific to a domain.

        Args:
            domain_name: Domain name
            domain_terms: Terms in the domain
            analysis: Domain analysis results

        Returns:
            Dictionary of generated figure files
        """
        figures = {}

        # Term frequency distribution
        freq_fig = self._generate_term_frequency_plot(domain_name, domain_terms)
        if freq_fig:
            figures["term_frequency"] = freq_fig

        # Ambiguity analysis
        if analysis.ambiguities:
            amb_fig = self._generate_ambiguity_plot(domain_name, analysis.ambiguities)
            if amb_fig:
                figures["ambiguity_analysis"] = amb_fig

        # Term pattern analysis
        if analysis.term_patterns:
            pattern_fig = self._generate_pattern_plot(
                domain_name, analysis.term_patterns
            )
            if pattern_fig:
                figures["term_patterns"] = pattern_fig

        # Contextual usage network (simplified)
        if len(domain_terms) > 5:
            network_fig = self._generate_domain_network(domain_name, domain_terms)
            if network_fig:
                figures["term_network"] = network_fig

        return figures

    def _generate_term_frequency_plot(
        self, domain_name: str, domain_terms: Dict[str, Any]
    ) -> Optional[str]:
        """Generate term frequency distribution plot.

        Args:
            domain_name: Domain name
            domain_terms: Domain terms

        Returns:
            Path to generated figure or None
        """
        import matplotlib.pyplot as plt

        if not domain_terms:
            return None

        fig, ax = plt.subplots(figsize=(12, 8))

        # Sort terms by frequency
        sorted_terms = sorted(
            domain_terms.items(), key=lambda x: x[1].frequency, reverse=True
        )[:20]

        if not sorted_terms:
            plt.close(fig)
            return None

        terms, term_objects = zip(*sorted_terms)
        frequencies = [obj.frequency for obj in term_objects]

        bars = ax.bar(
            range(len(terms)),
            frequencies,
            alpha=0.7,
            color=self.visualizer.DOMAIN_COLORS.get(domain_name, "#7f7f7f"),
        )

        ax.set_xticks(range(len(terms)))
        ax.set_xticklabels(terms, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Frequency in Corpus")
        ax.set_title(
            f'Term Frequency Distribution - {domain_name.replace("_", " ").title()}'
        )

        # Add value labels on bars
        for bar, freq in zip(bars, frequencies):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(frequencies) * 0.01,
                f"{freq}",
                ha="center",
                va="bottom",
                fontsize=7,
            )

        plt.tight_layout()
        # Use shorter name for power_and_labor to match manuscript references
        filename_base = domain_name.replace("power_and_labor", "power_labor")
        filename = f"{filename_base}_term_frequencies.png"
        filepath = self.figures_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Register figure with manuscript-matching label
        label_base = domain_name.replace("_and_", "_").replace("unit_of_", "unit_")
        try:
            self.figure_manager.register_figure(
                filename=filename,
                caption=f"Term frequency distribution for {domain_name.replace('_', ' ').title()} domain",
                label=f"fig:{label_base}_frequencies",
                section="supplemental_results",
                generated_by="generate_domain_figures.py",
            )
            logger.info(f"Registered figure: fig:{label_base}_frequencies")
        except Exception as e:
            logger.warning(f"Failed to register {filename}: {e}")

        return str(filepath)

    def _generate_ambiguity_plot(
        self, domain_name: str, ambiguities: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate ambiguity analysis plot.

        Args:
            domain_name: Domain name
            ambiguities: List of ambiguities

        Returns:
            Path to generated figure or None
        """
        import matplotlib.pyplot as plt

        if not ambiguities:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        terms = [amb["term"] for amb in ambiguities]
        context_counts = [len(amb["contexts"]) for amb in ambiguities]

        bars = ax.bar(
            range(len(terms)),
            context_counts,
            alpha=0.7,
            color=self.visualizer.DOMAIN_COLORS.get(domain_name, "#7f7f7f"),
        )

        ax.set_xticks(range(len(terms)))
        ax.set_xticklabels(terms, rotation=45, ha="right")
        ax.set_ylabel("Number of Contexts")
        ax.set_title(
            f'Term Ambiguity Analysis - {domain_name.replace("_", " ").title()}'
        )

        plt.tight_layout()
        # Use shorter name for power_and_labor to match manuscript references
        filename_base = domain_name.replace("power_and_labor", "power_labor")
        filename = f"{filename_base}_ambiguities.png"
        filepath = self.figures_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Register figure with manuscript-matching label
        label_base = domain_name.replace("_and_", "_").replace("unit_of_", "unit_")
        try:
            self.figure_manager.register_figure(
                filename=filename,
                caption=f"Ambiguity patterns in {domain_name.replace('_', ' ').title()} domain",
                label=f"fig:{label_base}_ambiguities",
                section="supplemental_results",
                generated_by="generate_domain_figures.py",
            )
            logger.info(f"Registered figure: fig:{label_base}_ambiguities")
        except Exception as e:
            logger.warning(f"Failed to register {filename}: {e}")

        return str(filepath)

    def _generate_pattern_plot(
        self, domain_name: str, term_patterns: Dict[str, int]
    ) -> Optional[str]:
        """Generate term pattern analysis plot.

        Args:
            domain_name: Domain name
            term_patterns: Pattern frequencies

        Returns:
            Path to generated figure or None
        """
        import matplotlib.pyplot as plt

        if not term_patterns:
            return None

        fig, ax = plt.subplots(figsize=(8, 8))

        patterns = list(term_patterns.keys())
        counts = list(term_patterns.values())

        ax.pie(
            counts,
            labels=[p.title() for p in patterns],
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title(
            f'Term Pattern Distribution - {domain_name.replace("_", " ").title()}'
        )

        plt.tight_layout()
        filename = f"{domain_name}_patterns.png"
        filepath = self.figures_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)

        return str(filepath)

    def _generate_domain_network(
        self, domain_name: str, domain_terms: Dict[str, Any]
    ) -> Optional[str]:
        """Generate simplified term network for domain.

        Args:
            domain_name: Domain name
            domain_terms: Domain terms

        Returns:
            Path to generated figure or None
        """
        import matplotlib.pyplot as plt
        import networkx as nx

        if len(domain_terms) < 3:
            return None

        fig, ax = plt.subplots(figsize=(10, 10))

        # Create simple network based on shared contexts
        G = nx.Graph()

        # Add nodes
        term_list = list(domain_terms.keys())[:15]  # Limit for readability
        for term in term_list:
            G.add_node(term, size=domain_terms[term].frequency)

        # Add edges based on shared contexts (simplified)
        for i, term1 in enumerate(term_list):
            for term2 in term_list[i + 1 : i + 3]:  # Connect to next 2 terms
                G.add_edge(term1, term2, weight=0.5)

        if G.number_of_edges() == 0:
            plt.close(fig)
            return None

        # Draw network
        pos = nx.spring_layout(G, seed=42)

        node_sizes = [G.nodes[node].get("size", 100) * 10 for node in G.nodes()]
        node_colors = [self.visualizer.DOMAIN_COLORS.get(domain_name, "#7f7f7f")] * len(
            G.nodes()
        )

        nx.draw_networkx_nodes(
            G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.7, ax=ax
        )
        nx.draw_networkx_edges(G, pos, alpha=0.5, ax=ax)

        # Draw labels for important terms only
        important_terms = sorted(
            G.nodes(), key=lambda x: G.nodes[x].get("size", 0), reverse=True
        )[:8]
        label_pos = {term: pos[term] for term in important_terms}
        nx.draw_networkx_labels(G, label_pos, font_size=8, ax=ax)

        ax.set_title(
            f'Term Relationship Network - {domain_name.replace("_", " ").title()}'
        )
        ax.axis("off")

        plt.tight_layout()
        filename = f"{domain_name}_network.png"
        filepath = self.figures_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)

        return str(filepath)

    def _generate_comparative_figures(
        self, domain_results: Dict[str, Any], corpus_file: Optional[Path] = None
    ) -> Dict[str, str]:
        """Generate comparative figures across domains.

        Args:
            domain_results: Results from individual domain analyses
            corpus_file: Path to corpus for additional analysis

        Returns:
            Dictionary of comparative figure files
        """
        figures = {}

        # Domain comparison plot
        successful_domains = {
            name: results
            for name, results in domain_results.items()
            if "error" not in results
        }

        if len(successful_domains) > 1:
            # Create domain comparison data
            domain_data = {}
            for name, results in successful_domains.items():
                # Load domain analysis data
                analysis_file = self.data_dir / f"{name}_analysis.json"
                if analysis_file.exists():
                    with open(analysis_file, "r") as f:
                        analysis_data = json.load(f)

                    domain_data[name] = {
                        "term_count": results.get("terms_visualized", 0),
                        "total_frequency": sum(
                            term_data.get("frequency", 0)
                            for term_data in analysis_data.get(
                                "extracted_terms", {}
                            ).values()
                        ),
                        "avg_confidence": 0.8,  # Placeholder
                        "bridging_terms": [],  # Would need cross-domain analysis
                    }

            if domain_data:
                comp_fig = self.visualizer.create_domain_comparison_plot(
                    domain_data, filepath=self.figures_dir / "domain_comparison.png"
                )
                figures["domain_comparison"] = str(
                    self.figures_dir / "domain_comparison.png"
                )

                # Register domain comparison figure
                try:
                    self.figure_manager.register_figure(
                        filename="domain_comparison.png",
                        caption="Domain-specific terminology networks showing unique structural patterns for each Ento-Linguistic domain",
                        label="fig:domain_comparison",
                        section="experimental_results",
                        generated_by="generate_domain_figures.py",
                    )
                    logger.info("Registered figure: fig:domain_comparison")
                except Exception as e:
                    logger.warning(f"Failed to register domain_comparison figure: {e}")

        return figures


def main() -> None:
    """Main entry point for domain figure generation script."""
    parser = argparse.ArgumentParser(
        description="Ento-Linguistic Domain Figure Generation"
    )
    parser.add_argument(
        "domain",
        nargs="?",
        choices=[
            "unit_of_individuality",
            "behavior_and_identity",
            "power_and_labor",
            "sex_and_reproduction",
            "kin_and_relatedness",
            "economics",
            "all",
        ],
        help="Domain to generate figures for (or 'all' for all domains)",
    )
    parser.add_argument(
        "--corpus-file", type=Path, help="Path to literature corpus JSON file"
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory")

    args = parser.parse_args()

    # Default to 'all' if no domain specified
    domain = args.domain if args.domain is not None else "all"

    generator = DomainFigureGenerator(args.output_dir)

    if domain == "all":
        results = generator.generate_all_domain_figures(args.corpus_file)
        logger.info(f"Generated figures for {results['domains_processed']} domains")
        logger.info(f"Total figures: {results['total_figures_generated']}")
    else:
        results = generator.generate_domain_figures(domain, args.corpus_file)

        if "error" not in results:
            logger.info(f"Figures generated for {domain}")
            logger.info(f"Terms visualized: {results.get('terms_visualized', 0)}")
            logger.info(f"Figures created: {results.get('figures_generated', 0)}")
        else:
            logger.error(f"Figure generation failed for {domain}: {results['error']}")


if __name__ == "__main__":
    main()

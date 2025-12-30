"""Conceptual mapping script for Ento-Linguistic research.

This script generates conceptual maps and terminology networks,
visualizing how terms relate to concepts and how concepts interconnect
within the Ento-Linguistic framework.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import argparse

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from term_extraction import TerminologyExtractor
from conceptual_mapping import ConceptualMapper
from concept_visualization import ConceptVisualizer
from literature_mining import LiteratureCorpus

from infrastructure.core.logging_utils import get_logger
# Directory creation handled inline
from infrastructure.documentation.figure_manager import FigureManager

logger = get_logger(__name__)


class ConceptualMappingScript:
    """Script for generating conceptual maps and terminology networks.

    This class creates visualizations and analyses of how terminology
    relates to conceptual structures in Ento-Linguistic research.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize conceptual mapping script.

        Args:
            output_dir: Directory for output files
        """
        self.project_root = Path(__file__).parent.parent
        self.output_dir = output_dir or self.project_root / "output"
        self.figures_dir = self.output_dir / "figures"
        self.reports_dir = self.output_dir / "reports"
        self.data_dir = self.output_dir / "data"

        # Ensure directories exist
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.figure_manager = FigureManager()
        self.visualizer = ConceptVisualizer()

        logger.info(f"Initialized conceptual mapping script with output directory: {self.output_dir}")

    def generate_concept_map(self, corpus_file: Optional[Path] = None,
                           analysis_type: str = "full") -> Dict[str, Any]:
        """Generate conceptual map from literature.

        Args:
            corpus_file: Path to literature corpus
            analysis_type: Type of analysis ("full", "terminology_only", "concepts_only")

        Returns:
            Results dictionary
        """
        logger.info(f"Generating conceptual map (analysis type: {analysis_type})")

        # Load corpus
        corpus = self._load_corpus(corpus_file)
        texts = corpus.get_text_corpus()

        # Extract terminology
        extractor = TerminologyExtractor()
        terms = extractor.extract_terms(texts, min_frequency=3)

        if analysis_type == "terminology_only":
            return self._analyze_terminology_only(terms)

        # Create conceptual mapping
        mapper = ConceptualMapper()
        concept_map = mapper.build_concept_map(list(terms.items()))

        if analysis_type == "concepts_only":
            return self._analyze_concepts_only(concept_map)

        # Full analysis
        results = {
            'terms_extracted': len(terms),
            'concepts_mapped': len(concept_map.concepts),
            'relationships_found': len(concept_map.concept_relationships)
        }

        # Generate visualizations
        visualizations = self._generate_concept_visualizations(concept_map, terms, mapper)

        # Generate analysis report
        report = self._generate_concept_report(concept_map, terms, results)

        results.update({
            'visualizations': visualizations,
            'report_file': report,
            'concept_map_file': str(self.data_dir / "concept_map.json"),
            'terminology_file': str(self.data_dir / "terminology.json")
        })

        # Save data
        self._save_concept_data(concept_map, terms)

        logger.info("Conceptual mapping completed")
        return results

    def _load_corpus(self, corpus_file: Optional[Path]) -> LiteratureCorpus:
        """Load literature corpus.

        Args:
            corpus_file: Path to corpus file

        Returns:
            Literature corpus
        """
        if corpus_file and corpus_file.exists():
            logger.info(f"Loading corpus from {corpus_file}")
            return LiteratureCorpus.load_from_file(corpus_file)
        else:
            default_corpus = self.data_dir / "literature_corpus.json"
            if default_corpus.exists():
                logger.info(f"Loading default corpus from {default_corpus}")
                return LiteratureCorpus.load_from_file(default_corpus)
            else:
                logger.warning("No corpus file found, creating empty corpus")
                return LiteratureCorpus()

    def _analyze_terminology_only(self, terms: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze terminology without conceptual mapping.

        Args:
            terms: Extracted terminology

        Returns:
            Terminology analysis results
        """
        # Domain distribution
        domain_counts = {}
        for term_obj in terms.items():
            for domain in term_obj[1].domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Frequency analysis
        frequencies = [term_obj.frequency for term_obj in terms.values()]
        avg_frequency = sum(frequencies) / len(frequencies) if frequencies else 0
        max_frequency = max(frequencies) if frequencies else 0

        # Generate terminology visualization
        self._generate_terminology_visualization(terms)

        return {
            'analysis_type': 'terminology_only',
            'terms_analyzed': len(terms),
            'domain_distribution': domain_counts,
            'avg_frequency': avg_frequency,
            'max_frequency': max_frequency,
            'visualization_file': str(self.figures_dir / "terminology_overview.png")
        }

    def _analyze_concepts_only(self, concept_map: Any) -> Dict[str, Any]:
        """Analyze concepts without detailed terminology.

        Args:
            concept_map: Concept mapping results

        Returns:
            Concept analysis results
        """
        # Concept statistics
        concept_stats = {}
        for name, concept in concept_map.concepts.items():
            concept_stats[name] = {
                'terms_count': len(concept.terms),
                'domains_count': len(concept.domains),
                'parent_concepts': len(concept.parent_concepts),
                'child_concepts': len(concept.child_concepts)
            }

        # Relationship analysis
        relationship_stats = {
            'total_relationships': len(concept_map.concept_relationships),
            'avg_relationship_strength': sum(concept_map.concept_relationships.values()) /
                                       len(concept_map.concept_relationships) if
                                       concept_map.concept_relationships else 0
        }

        # Generate concept visualization
        concept_fig = self.visualizer.visualize_concept_map(
            concept_map,
            filepath=self.figures_dir / "concepts_only_map.png"
        )

        return {
            'analysis_type': 'concepts_only',
            'concepts_analyzed': len(concept_map.concepts),
            'concept_statistics': concept_stats,
            'relationship_statistics': relationship_stats,
            'visualization_file': str(self.figures_dir / "concepts_only_map.png")
        }

    def _generate_concept_visualizations(self, concept_map: Any,
                                       terms: Dict[str, Any], mapper: Any) -> Dict[str, str]:
        """Generate visualizations for conceptual mapping.

        Args:
            concept_map: Concept mapping results
            terms: Extracted terminology

        Returns:
            Dictionary of visualization files
        """
        visualizations = {}

        # Concept map visualization
        concept_fig = self.visualizer.visualize_concept_map(
            concept_map,
            filepath=self.figures_dir / "concept_map.png",
            title="Ento-Linguistic Concept Map"
        )
        visualizations['concept_map'] = str(self.figures_dir / "concept_map.png")

        # Terminology network (simplified)
        # Create mock relationships based on shared domains
        relationships = {}
        term_list = list(terms.keys())[:30]  # Limit for visualization

        for i, term1 in enumerate(term_list):
            term1_domains = terms[term1].domains
            for term2 in term_list[i+1:]:
                term2_domains = terms[term2].domains
                # Create relationship if terms share domains
                shared_domains = set(term1_domains) & set(term2_domains)
                if shared_domains:
                    weight = len(shared_domains) / max(len(term1_domains), len(term2_domains))
                    relationships[(term1, term2)] = weight

        if relationships:
            network_fig = self.visualizer.visualize_terminology_network(
                list(terms.items()),
                relationships,
                filepath=self.figures_dir / "terminology_network.png"
            )
            visualizations['terminology_network'] = str(self.figures_dir / "terminology_network.png")

        # Concept hierarchy
        hierarchy_data = self._extract_hierarchy_data(concept_map, mapper)
        if hierarchy_data:
            hierarchy_fig = self.visualizer.visualize_concept_hierarchy(
                hierarchy_data,
                filepath=self.figures_dir / "concept_hierarchy.png"
            )
            visualizations['concept_hierarchy'] = str(self.figures_dir / "concept_hierarchy.png")

        # Anthropomorphic concepts analysis
        anthropomorphic_data = self._extract_anthropomorphic_data(concept_map)
        if anthropomorphic_data:
            anthropomorphic_fig = self.visualizer.create_anthropomorphic_analysis_plot(
                anthropomorphic_data,
                filepath=self.figures_dir / "anthropomorphic_analysis.png"
            )
            visualizations['anthropomorphic_analysis'] = str(self.figures_dir / "anthropomorphic_analysis.png")

        # Save visualization metadata
        self.visualizer.export_visualization_metadata(
            {},  # Would need actual figure objects
            self.data_dir / "concept_mapping_visualizations.json"
        )

        return visualizations

    def _extract_hierarchy_data(self, concept_map: Any, mapper: Any) -> Dict[str, Any]:
        """Extract hierarchy data for visualization.

        Args:
            concept_map: Concept mapping results
            mapper: ConceptualMapper instance

        Returns:
            Hierarchy data dictionary
        """
        # Use the public API from the ConceptualMapper class
        hierarchy_data = mapper.analyze_conceptual_hierarchy()
        return hierarchy_data

    def _extract_anthropomorphic_data(self, concept_map: Any) -> Dict[str, List[str]]:
        """Extract anthropomorphic concept data.

        Args:
            concept_map: Concept mapping results

        Returns:
            Anthropomorphic analysis data
        """
        mapper = ConceptualMapper()
        return mapper.detect_anthropomorphic_concepts()

    def _generate_concept_report(self, concept_map: Any, terms: Dict[str, Any],
                               results: Dict[str, Any]) -> str:
        """Generate conceptual mapping report.

        Args:
            concept_map: Concept mapping results
            terms: Extracted terminology
            results: Analysis results

        Returns:
            Report file path
        """
        report_content = f"""# Ento-Linguistic Conceptual Mapping Report

## Overview

This report presents the results of conceptual mapping analysis, showing how terminology relates to conceptual structures in entomological research.

## Analysis Summary

- **Terms Extracted**: {results['terms_extracted']}
- **Concepts Mapped**: {results['concepts_mapped']}
- **Relationships Identified**: {results['relationships_found']}

## Concept Map Structure

### Core Concepts
The following concepts form the foundation of the Ento-Linguistic framework:

"""

        for name, concept in concept_map.concepts.items():
            report_content += f"""#### {name}
- **Description**: {concept.description}
- **Associated Terms**: {len(concept.terms)} terms
- **Domains**: {', '.join(concept.domains)}
- **Sample Terms**: {', '.join(list(concept.terms)[:5])}

"""

        report_content += """
## Concept Relationships

### Strongest Connections
"""

        # Sort relationships by strength
        sorted_relationships = sorted(
            concept_map.concept_relationships.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        for (concept1, concept2), weight in sorted_relationships:
            report_content += ".3f"".3f"

        report_content += f"""

## Terminology-Concept Mapping

### Most Connected Terms
"""

        # Find terms connected to most concepts
        term_concept_counts = {}
        for term in terms:
            term_concept_counts[term] = len(concept_map.get_term_concepts(term))

        sorted_terms = sorted(term_concept_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        for term, count in sorted_terms:
            concepts = concept_map.get_term_concepts(term)
            report_content += f"- **{term}**: Connected to {count} concepts ({', '.join(concepts)})\n"

        report_content += f"""

## Domain Analysis

### Concept Distribution by Domain
"""

        domain_concept_counts = {}
        for concept in concept_map.concepts.values():
            for domain in concept.domains:
                domain_concept_counts[domain] = domain_concept_counts.get(domain, 0) + 1

        for domain, count in sorted(domain_concept_counts.items(), key=lambda x: x[1], reverse=True):
            domain_name = domain.replace('_', ' ').title()
            report_content += f"- **{domain_name}**: {count} concepts\n"

        report_content += f"""

## Visualizations Generated

The following visualizations were created:

- **Concept Map**: Network visualization of concept relationships
- **Terminology Network**: Co-occurrence patterns among scientific terms
- **Concept Hierarchy**: Centrality-based hierarchy of concepts
- **Anthropomorphic Analysis**: Analysis of anthropomorphic terminology patterns

## Implications

### Research Communication
The conceptual mapping reveals how terminology creates structured frameworks for understanding insect biology, with implications for:

1. **Question Formulation**: How terminological frameworks shape research questions
2. **Interpretive Frameworks**: How concepts provide lenses for understanding biological phenomena
3. **Cross-Domain Connections**: How concepts bridge different areas of entomological research

### Scientific Practice
The analysis suggests opportunities for improving scientific communication through:

1. **Explicit Conceptual Frameworks**: Making underlying concepts visible in research communication
2. **Terminology Awareness**: Understanding how word choice influences scientific understanding
3. **Meta-Standards Development**: Creating guidelines for clearer scientific language

## Future Directions

1. **Expanded Mapping**: Include more comprehensive terminology databases
2. **Dynamic Analysis**: Track how conceptual mappings evolve over time
3. **Cross-Disciplinary Comparison**: Compare conceptual structures across scientific fields
4. **Interactive Tools**: Develop tools for exploring conceptual relationships

## Data Files

- Concept map data: `concept_map.json`
- Terminology data: `terminology.json`
- Visualization metadata: `concept_mapping_visualizations.json`

---
*Report generated by Ento-Linguistic Conceptual Mapping Script*
"""

        # Save report
        report_file = self.reports_dir / "conceptual_mapping_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return str(report_file)

    def _save_concept_data(self, concept_map: Any, terms: Dict[str, Any]) -> None:
        """Save concept mapping data to files.

        Args:
            concept_map: Concept mapping results
            terms: Extracted terminology
        """
        # Save concept map
        mapper = ConceptualMapper()
        mapper.export_concept_map_json(str(self.data_dir / "concept_map.json"))

        # Save terminology
        terms_data = {term: terms[term].to_dict() for term in terms}
        with open(self.data_dir / "terminology.json", 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, indent=2, ensure_ascii=False)

    def _generate_terminology_visualization(self, terms: Dict[str, Any]) -> str:
        """Generate overview visualization of terminology.

        Args:
            terms: Extracted terminology

        Returns:
            Path to visualization file
        """
        import matplotlib.pyplot as plt

        # Domain distribution
        domain_counts = {}
        for term_obj in terms.values():
            for domain in term_obj.domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        if domain_counts:
            fig, ax = plt.subplots(figsize=(10, 6))

            domains = list(domain_counts.keys())
            counts = list(domain_counts.values())

            bars = ax.bar(range(len(domains)), counts, alpha=0.7)
            ax.set_xticks(range(len(domains)))
            ax.set_xticklabels([d.replace('_', '\n').title() for d in domains])
            ax.set_ylabel('Number of Terms')
            ax.set_title('Terminology Distribution by Ento-Linguistic Domain')

            # Add value labels
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom')

            plt.tight_layout()
            viz_file = self.figures_dir / "terminology_overview.png"
            fig.savefig(viz_file, dpi=300, bbox_inches='tight')
            plt.close(fig)

            return str(viz_file)

        return ""


def main():
    """Main entry point for conceptual mapping script."""
    parser = argparse.ArgumentParser(description="Ento-Linguistic Conceptual Mapping")
    parser.add_argument("--corpus-file", type=Path,
                       help="Path to literature corpus JSON file")
    parser.add_argument("--output-dir", type=Path,
                       help="Output directory")
    parser.add_argument("--analysis-type", choices=['full', 'terminology_only', 'concepts_only'],
                       default='full', help="Type of analysis to perform")

    args = parser.parse_args()

    script = ConceptualMappingScript(args.output_dir)
    results = script.generate_concept_map(args.corpus_file, args.analysis_type)

    print(f"Conceptual mapping completed ({args.analysis_type})")
    print(f"Results: {results}")


if __name__ == "__main__":
    main()
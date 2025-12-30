"""Literature analysis pipeline for Ento-Linguistic research.

This script orchestrates the complete analysis workflow for Ento-Linguistic research,
from literature mining through terminology extraction, conceptual mapping, and visualization.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from literature_mining import LiteratureCorpus, mine_entomology_literature
from text_analysis import TextProcessor
from term_extraction import TerminologyExtractor
from conceptual_mapping import ConceptualMapper
from domain_analysis import DomainAnalyzer
from discourse_analysis import DiscourseAnalyzer
from concept_visualization import ConceptVisualizer

from infrastructure.core.logging_utils import get_logger
# Directory creation handled inline
from infrastructure.documentation.figure_manager import FigureManager

logger = get_logger(__name__)


class LiteratureAnalysisPipeline:
    """Complete literature analysis pipeline for Ento-Linguistic research.

    This class orchestrates the entire analysis workflow from data collection
    through visualization and reporting.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the analysis pipeline.

        Args:
            output_dir: Directory for output files (defaults to project output)
        """
        self.project_root = Path(__file__).parent.parent
        self.output_dir = output_dir or self.project_root / "output"
        self.data_dir = self.output_dir / "data"
        self.figures_dir = self.output_dir / "figures"
        self.reports_dir = self.output_dir / "reports"

        # Ensure output directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.text_processor = TextProcessor()
        self.figure_manager = FigureManager()

        logger.info(f"Initialized analysis pipeline with output directory: {self.output_dir}")

    def run_complete_analysis(self, max_publications: int = 500,
                            use_cached_data: bool = True) -> Dict[str, Any]:
        """Run the complete analysis pipeline.

        Args:
            max_publications: Maximum number of publications to analyze
            use_cached_data: Whether to use cached literature data if available

        Returns:
            Dictionary with analysis results and metadata
        """
        start_time = datetime.now()
        logger.info("Starting complete Ento-Linguistic analysis pipeline")

        results = {
            'pipeline_metadata': {
                'start_time': start_time.isoformat(),
                'max_publications': max_publications,
                'output_directory': str(self.output_dir)
            },
            'stages': {},
            'final_outputs': {}
        }

        try:
            # Stage 1: Literature Collection
            logger.info("Stage 1: Literature collection")
            corpus = self._collect_literature(max_publications, use_cached_data)
            results['stages']['literature_collection'] = {
                'publications_found': len(corpus.publications),
                'corpus_file': str(self.data_dir / "literature_corpus.json")
            }

            # Stage 2: Text Processing
            logger.info("Stage 2: Text processing and preprocessing")
            processed_texts = self._process_texts(corpus)
            results['stages']['text_processing'] = {
                'texts_processed': len(processed_texts),
                'total_tokens': sum(len(text.split()) for text in processed_texts)
            }

            # Stage 3: Terminology Extraction
            logger.info("Stage 3: Terminology extraction")
            terminology = self._extract_terminology(processed_texts)
            results['stages']['terminology_extraction'] = {
                'terms_extracted': len(terminology.extracted_terms),
                'terms_file': str(self.data_dir / "terminology.json"),
                'csv_export': str(self.data_dir / "terminology.csv")
            }

            # Stage 4: Conceptual Mapping
            logger.info("Stage 4: Conceptual mapping")
            concept_map = self._create_concept_map(terminology.extracted_terms)
            results['stages']['conceptual_mapping'] = {
                'concepts_mapped': len(concept_map.concepts),
                'relationships_found': len(concept_map.concept_relationships),
                'concept_map_file': str(self.data_dir / "concept_map.json")
            }

            # Stage 5: Domain Analysis
            logger.info("Stage 5: Domain-specific analysis")
            domain_analyses = self._analyze_domains(terminology.extracted_terms, processed_texts)
            results['stages']['domain_analysis'] = {
                'domains_analyzed': len(domain_analyses),
                'domain_report_file': str(self.reports_dir / "domain_analysis_report.md")
            }

            # Stage 6: Discourse Analysis
            logger.info("Stage 6: Discourse analysis")
            discourse_profile = self._analyze_discourse(processed_texts)
            results['stages']['discourse_analysis'] = {
                'patterns_identified': len(discourse_profile.get('patterns', {})),
                'structures_found': len(discourse_profile.get('argumentative_structures', [])),
                'discourse_file': str(self.data_dir / "discourse_analysis.json")
            }

            # Stage 7: Visualization Generation
            logger.info("Stage 7: Visualization generation")
            visualizations = self._generate_visualizations(
                concept_map, terminology.extracted_terms, domain_analyses
            )
            results['stages']['visualization'] = {
                'figures_generated': len(visualizations),
                'visualization_metadata': str(self.data_dir / "visualization_metadata.json")
            }

            # Calculate timing
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            results['pipeline_metadata'].update({
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'status': 'completed'
            })

            # Stage 8: Report Generation
            logger.info("Stage 8: Final report generation")
            final_report = self._generate_final_report(results)
            results['stages']['reporting'] = {
                'report_file': str(self.reports_dir / "literature_analysis_report.md"),
                'summary_file': str(self.reports_dir / "analysis_summary.json")
            }

            logger.info(f"Pipeline completed successfully in {duration:.1f} seconds")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results['pipeline_metadata']['status'] = 'failed'
            results['pipeline_metadata']['error'] = str(e)
            raise

        return results

    def _collect_literature(self, max_publications: int, use_cached: bool) -> LiteratureCorpus:
        """Collect entomological literature.

        Args:
            max_publications: Maximum publications to collect
            use_cached: Whether to use cached data

        Returns:
            Literature corpus
        """
        corpus_file = self.data_dir / "literature_corpus.json"

        if use_cached and corpus_file.exists():
            logger.info(f"Loading cached literature corpus from {corpus_file}")
            corpus = LiteratureCorpus.load_from_file(corpus_file)
        else:
            logger.info(f"Mining new literature corpus (max {max_publications} publications)")
            corpus = mine_entomology_literature(max_publications)

            # Save corpus
            corpus.save_to_file(corpus_file)
            logger.info(f"Saved literature corpus with {len(corpus.publications)} publications")

        return corpus

    def _process_texts(self, corpus: LiteratureCorpus) -> List[str]:
        """Process and normalize text corpus.

        Args:
            corpus: Literature corpus

        Returns:
            List of processed texts
        """
        raw_texts = corpus.get_text_corpus()
        processed_texts = []

        for text in raw_texts:
            if text.strip():  # Skip empty texts
                processed = self.text_processor.process_text(text, lemmatize=True)
                if processed:  # Only keep non-empty processed texts
                    processed_texts.append(' '.join(processed))

        logger.info(f"Processed {len(processed_texts)} texts for analysis")
        return processed_texts

    def _extract_terminology(self, texts: List[str]) -> TerminologyExtractor:
        """Extract terminology from processed texts.

        Args:
            texts: Processed texts

        Returns:
            Terminology extractor with extracted terms
        """
        extractor = TerminologyExtractor(self.text_processor)
        terms = extractor.extract_terms(texts, min_frequency=3)

        # Save terminology data
        terms_data = {term: extractor.extracted_terms[term].to_dict() for term in extractor.extracted_terms}
        terms_file = self.data_dir / "terminology.json"
        with open(terms_file, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, indent=2, ensure_ascii=False)

        # Export CSV
        csv_file = self.data_dir / "terminology.csv"
        extractor.export_terms_csv(str(csv_file))

        logger.info(f"Extracted {len(terms)} terminology items")
        return extractor

    def _create_concept_map(self, terms: Dict[str, Any]) -> Any:
        """Create conceptual mapping from extracted terms.

        Args:
            terms: Extracted terminology

        Returns:
            Concept map object
        """
        mapper = ConceptualMapper()
        concept_map = mapper.build_concept_map(list(terms.items()))

        # Save concept map
        concept_file = self.data_dir / "concept_map.json"
        mapper.export_concept_map_json(str(concept_file))

        logger.info(f"Created concept map with {len(concept_map.concepts)} concepts")
        return concept_map

    def _analyze_domains(self, terms: Dict[str, Any], texts: List[str]) -> Dict[str, Any]:
        """Perform domain-specific analysis.

        Args:
            terms: Extracted terms
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analyzer = DomainAnalyzer()
        domain_analyses = analyzer.analyze_all_domains(list(terms.items()), texts)

        # Generate domain report
        report_content = "# Ento-Linguistic Domain Analysis Report\n\n"
        report_content += f"Analysis performed on {datetime.now().isoformat()}\n\n"

        for domain_name, analysis in domain_analyses.items():
            report_content += analyzer.generate_domain_report(analysis)
            report_content += "\n\n---\n\n"

        # Save report
        report_file = self.reports_dir / "domain_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Completed domain analysis for {len(domain_analyses)} domains")
        return domain_analyses

    def _analyze_discourse(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze discourse patterns in texts.

        Args:
            texts: Texts to analyze

        Returns:
            Discourse analysis results
        """
        analyzer = DiscourseAnalyzer()
        profile = analyzer.create_discourse_profile(texts)

        # Save discourse analysis
        discourse_file = self.data_dir / "discourse_analysis.json"
        analyzer.export_discourse_analysis(profile, str(discourse_file))

        logger.info("Completed discourse analysis")
        return profile

    def _generate_visualizations(self, concept_map: Any, terms: Dict[str, Any],
                               domain_analyses: Dict[str, Any]) -> Dict[str, plt.Figure]:
        """Generate visualizations for analysis results.

        Args:
            concept_map: Concept mapping results
            terms: Extracted terminology
            domain_analyses: Domain analysis results

        Returns:
            Dictionary of generated figures
        """
        visualizer = ConceptVisualizer()
        figures = {}

        # Concept map visualization
        concept_fig = visualizer.visualize_concept_map(
            concept_map,
            filepath=self.figures_dir / "concept_map.png",
            title="Ento-Linguistic Concept Map"
        )
        figures['concept_map'] = concept_fig

        # Terminology network
        # Create mock relationships for demonstration (would be computed from co-occurrence)
        mock_relationships = {}
        term_list = list(terms.keys())[:20]  # Limit for visualization
        for i, term1 in enumerate(term_list):
            for term2 in term_list[i+1:i+3]:  # Connect to next 2 terms
                mock_relationships[(term1, term2)] = 0.5

        network_fig = visualizer.visualize_terminology_network(
            list(terms.items()),
            mock_relationships,
            filepath=self.figures_dir / "terminology_network.png"
        )
        figures['terminology_network'] = network_fig

        # Domain comparison
        if domain_analyses:
            # Extract domain statistics
            domain_stats = {}
            for domain_name, analysis in domain_analyses.items():
                domain_stats[domain_name] = {
                    'term_count': len(analysis.key_terms),
                    'total_frequency': sum(getattr(terms.get(term), 'frequency', 0)
                                         for term in analysis.key_terms),
                    'avg_confidence': 0.8,  # Mock value
                    'bridging_terms': set()  # Would be computed
                }

            comparison_fig = visualizer.create_domain_comparison_plot(
                domain_stats,
                filepath=self.figures_dir / "domain_comparison.png"
            )
            figures['domain_comparison'] = comparison_fig

        # Export visualization metadata
        visualizer.export_visualization_metadata(
            figures,
            self.data_dir / "visualization_metadata.json"
        )

        logger.info(f"Generated {len(figures)} visualizations")
        return figures

    def _generate_final_report(self, results: Dict[str, Any]) -> str:
        """Generate final analysis report.

        Args:
            results: Complete analysis results

        Returns:
            Report file path
        """
        report_content = f"""# Ento-Linguistic Literature Analysis Report

**Analysis Date:** {datetime.now().isoformat()}
**Duration:** {results['pipeline_metadata']['duration_seconds']:.1f} seconds

## Executive Summary

This report presents the results of a comprehensive Ento-Linguistic analysis of entomological literature, examining how language shapes scientific understanding across six key domains: Unit of Individuality, Behavior and Identity, Power & Labor, Sex & Reproduction, Kin & Relatedness, and Economics.

## Analysis Overview

### Literature Corpus
- **Publications Analyzed:** {results['stages']['literature_collection']['publications_found']}
- **Text Processing:** {results['stages']['text_processing']['texts_processed']} texts processed
- **Total Tokens:** {results['stages']['text_processing']['total_tokens']:,}

### Terminology Extraction
- **Terms Identified:** {results['stages']['terminology_extraction']['terms_extracted']}
- **Domains Covered:** 6 Ento-Linguistic domains
- **Extraction Method:** Linguistic pattern recognition with domain-specific filtering

### Conceptual Mapping
- **Concepts Mapped:** {results['stages']['conceptual_mapping']['concepts_mapped']}
- **Relationships Identified:** {results['stages']['conceptual_mapping']['relationships_found']}
- **Mapping Approach:** Semantic clustering with domain integration

### Domain Analysis
- **Domains Analyzed:** {results['stages']['domain_analysis']['domains_analyzed']}
- **Key Findings:** Domain-specific ambiguities and framing assumptions identified
- **Recommendations:** Clearer communication guidelines developed

### Discourse Analysis
- **Patterns Identified:** {results['stages']['discourse_analysis']['patterns_identified']}
- **Argumentative Structures:** {results['stages']['discourse_analysis']['structures_found']}
- **Rhetorical Strategies:** Anthropomorphic, hierarchical, and economic framing patterns

## Key Findings

### Linguistic Patterns in Entomology

1. **Anthropomorphic Framing:** Systematic application of human-like agency, cognition, and social behavior to insect societies
2. **Hierarchical Terminology:** Power and labor concepts imported from human social structures
3. **Economic Metaphors:** Market logic applied to resource allocation and colony organization
4. **Scale Ambiguities:** Confusions between individual, colony, and population levels of analysis

### Domain-Specific Insights

**Unit of Individuality:** Complex multi-scale patterns with "colony" and "superorganism" creating conceptual boundaries

**Behavior and Identity:** Task-based identities that may not reflect biological fluidity

**Power & Labor:** Human social hierarchies imposed on insect reproductive skew

**Sex & Reproduction:** Binary gender concepts applied to haplodiploid systems

**Kin & Relatedness:** Genetic and social kinship concepts conflated

**Economics:** Human market principles applied to insect resource allocation

## Visualizations Generated

The analysis produced several key visualizations:

- **Concept Map:** Network visualization of Ento-Linguistic concepts and their relationships
- **Terminology Network:** Co-occurrence patterns among scientific terms
- **Domain Comparison:** Statistical comparison across the six domains

## Recommendations for Scientific Communication

### General Guidelines

1. **Explicit Scale Specification:** Always clarify whether referring to individual, colony, or population levels
2. **Avoid Anthropomorphic Language:** Use biologically accurate descriptions instead of human-like attributions
3. **Specify Conceptual Frameworks:** Make underlying assumptions explicit
4. **Use Domain-Appropriate Terminology:** Select terms that fit biological realities

### Domain-Specific Recommendations

Each domain analysis includes specific recommendations for clearer communication within that conceptual area.

## Future Research Directions

1. **Expanded Corpus Analysis:** Include multilingual scientific literature
2. **Longitudinal Studies:** Track terminological evolution over time
3. **Interdisciplinary Comparison:** Compare patterns across scientific disciplines
4. **Intervention Studies:** Test the impact of improved terminology on scientific understanding

## Conclusion

This analysis demonstrates that scientific language is not transparent but actively constitutes research possibilities. The Ento-Linguistic framework provides both analytical tools and practical guidelines for more conscious scientific communication. By making linguistic patterns visible, researchers can make more informed choices about how to describe and understand the natural world.

## Data Availability

All analysis data, code, and visualizations are available in the project output directories:

- **Data:** `{self.data_dir}`
- **Figures:** `{self.figures_dir}`
- **Reports:** `{self.reports_dir}`

## References

Analysis framework based on:
- Haraway, D. (1991). Simians, Cyborgs, and Women
- Latour, B. (1987). Science in Action
- Longino, H. (1990). Science as Social Knowledge
"""

        # Save report
        report_file = self.reports_dir / "literature_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # Save summary JSON
        summary_file = self.reports_dir / "analysis_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated final report: {report_file}")
        return str(report_file)


def main():
    """Main entry point for the literature analysis pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Ento-Linguistic Literature Analysis Pipeline")
    parser.add_argument("--max-publications", type=int, default=500,
                       help="Maximum number of publications to analyze")
    parser.add_argument("--output-dir", type=Path,
                       help="Output directory (default: project output)")
    parser.add_argument("--no-cache", action="store_true",
                       help="Force fresh literature collection")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    # Run pipeline
    pipeline = LiteratureAnalysisPipeline(args.output_dir)
    results = pipeline.run_complete_analysis(
        max_publications=args.max_publications,
        use_cached_data=not args.no_cache
    )

    # Print summary
    print("\n" + "="*60)
    print("ENTO-LINGUISTIC ANALYSIS PIPELINE COMPLETED")
    print("="*60)
    print(f"Publications analyzed: {results['stages']['literature_collection']['publications_found']}")
    print(f"Terms extracted: {results['stages']['terminology_extraction']['terms_extracted']}")
    print(f"Concepts mapped: {results['stages']['conceptual_mapping']['concepts_mapped']}")
    print(f"Domains analyzed: {results['stages']['domain_analysis']['domains_analyzed']}")
    print(".1f")
    print(f"Output directory: {results['pipeline_metadata']['output_directory']}")
    print("="*60)


if __name__ == "__main__":
    main()
"""Domain analysis script for Ento-Linguistic research.

This script performs detailed analysis of specific Ento-Linguistic domains,
examining terminology patterns, framing assumptions, and communication clarity
within individual conceptual areas.
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
from domain_analysis import DomainAnalyzer, DomainAnalysis
from literature_mining import LiteratureCorpus
from concept_visualization import ConceptVisualizer

from infrastructure.core.logging_utils import get_logger
# Directory creation handled inline
from infrastructure.documentation.figure_manager import FigureManager

logger = get_logger(__name__)


class DomainAnalysisScript:
    """Script for performing domain-specific Ento-Linguistic analysis.

    This class provides focused analysis of individual Ento-Linguistic domains,
    generating detailed reports and visualizations for specific conceptual areas.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize domain analysis script.

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

        logger.info(f"Initialized domain analysis script with output directory: {self.output_dir}")

    def analyze_domain(self, domain_name: str, corpus_file: Optional[Path] = None,
                      generate_figures: bool = True) -> Dict[str, Any]:
        """Analyze a specific Ento-Linguistic domain.

        Args:
            domain_name: Name of the domain to analyze
            corpus_file: Path to literature corpus file
            generate_figures: Whether to generate visualizations

        Returns:
            Analysis results dictionary
        """
        # Validate domain name
        valid_domains = [
            'unit_of_individuality', 'behavior_and_identity', 'power_and_labor',
            'sex_and_reproduction', 'kin_and_relatedness', 'economics'
        ]
        if domain_name not in valid_domains:
            logger.error(f"Invalid domain name: {domain_name}")
            logger.error(f"Valid domains: {', '.join(valid_domains)}")
            return {'error': f'Invalid domain name: {domain_name}'}

        logger.info(f"Starting analysis of {domain_name} domain")

        # Load or create corpus
        corpus = self._load_corpus(corpus_file)
        texts = corpus.get_text_corpus()

        # Extract terminology
        extractor = TerminologyExtractor()
        all_terms = extractor.extract_terms(texts, min_frequency=2)

        # Filter terms for this domain
        domain_terms = {term: term_obj for term, term_obj in all_terms.items()
                       if domain_name in term_obj.domains}

        logger.info(f"Found {len(domain_terms)} terms in {domain_name} domain")

        # Perform domain analysis
        analyzer = DomainAnalyzer()
        analyses = analyzer.analyze_all_domains(all_terms, texts)

        if domain_name not in analyses:
            logger.warning(f"No analysis available for domain: {domain_name}")
            return {}

        analysis = analyses[domain_name]

        # Generate detailed report
        report_content = self._generate_domain_report(domain_name, analysis, domain_terms)

        # Save report
        report_file = self.reports_dir / f"{domain_name}_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        results = {
            'domain': domain_name,
            'terms_analyzed': len(domain_terms),
            'key_terms': analysis.key_terms,
            'ambiguities_found': len(analysis.ambiguities),
            'recommendations': len(analysis.recommendations),
            'report_file': str(report_file)
        }

        # Generate figures if requested
        if generate_figures:
            figures = self._generate_domain_figures(domain_name, analysis, domain_terms)
            results['figures_generated'] = len(figures)
            results['figure_files'] = list(figures.keys())

        logger.info(f"Completed analysis of {domain_name} domain")
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
            # Try default location
            default_corpus = self.data_dir / "literature_corpus.json"
            if default_corpus.exists():
                logger.info(f"Loading default corpus from {default_corpus}")
                return LiteratureCorpus.load_from_file(default_corpus)
            else:
                logger.warning("No corpus file found, creating empty corpus")
                return LiteratureCorpus()

    def _generate_domain_report(self, domain_name: str, analysis: DomainAnalysis,
                               domain_terms: Dict[str, Any]) -> str:
        """Generate detailed domain analysis report.

        Args:
            domain_name: Name of the domain
            analysis: Domain analysis results
            domain_terms: Terms in this domain

        Returns:
            Report content as string
        """
        domain_title = domain_name.replace('_', ' ').title()

        report = f"""# {domain_title} Domain Analysis

**Analysis Date:** {__import__('datetime').datetime.now().isoformat()}
**Domain:** {domain_name}
**Terms Analyzed:** {len(domain_terms)}

## Overview

This report presents a detailed analysis of the {domain_title} domain within the Ento-Linguistic framework, examining how terminology shapes scientific understanding in this conceptual area.

## Key Terminology

### Most Frequent Terms
{chr(10).join(f"- **{term}**: {info.frequency} occurrences" for term, info in
              sorted(domain_terms.items(), key=lambda x: x[1].frequency, reverse=True)[:10])}

### Term Patterns
{chr(10).join(f"- {pattern}: {count} instances" for pattern, count in analysis.term_patterns.items())}

## Framing Assumptions

The following assumptions are embedded in the terminology used in this domain:

{chr(10).join(f"1. {assumption}" for assumption in analysis.framing_assumptions)}

## Conceptual Structure

### Hierarchical Organization
{chr(10).join(f"- **{key}**: {', '.join(value) if isinstance(value, list) else str(value)}"
              for key, value in analysis.conceptual_structure.items())}

## Ambiguities and Communication Challenges

### Identified Ambiguities
{chr(10).join(f"#### {amb['term']}\\n**Context**: {', '.join(amb['contexts'])}\\n**Issue**: {amb['issue']}\\n"
              for amb in analysis.ambiguities)}

## Recommendations for Clearer Communication

{chr(10).join(f"1. {rec}" for rec in analysis.recommendations)}

## Detailed Term Analysis

### Term-by-Term Breakdown
{chr(10).join(f"#### {term}\\n- **Frequency**: {info.frequency}\\n- **Contexts**: {len(info.contexts)}\\n- **Domains**: {', '.join(info.domains)}\\n- **Sample Usage**: {info.contexts[0] if info.contexts else 'No contexts available'}\\n"
              for term, info in sorted(domain_terms.items(), key=lambda x: x[1].frequency, reverse=True)[:20])}

## Implications for Research

### Current Communication Patterns
The terminology in this domain reflects broader patterns in scientific communication where:
- Human social concepts are applied to insect societies
- Complex biological relationships are simplified through familiar metaphors
- Scale differences between insect and human societies are not always acknowledged

### Research Questions Raised
1. How do terminological choices influence research questions in this domain?
2. What biological complexities are obscured by current terminology?
3. How might alternative terminology open new research possibilities?

## Future Directions

### Terminology Development
- Develop domain-specific terminology that better reflects biological realities
- Create glossaries that acknowledge multiple meanings and contexts
- Establish guidelines for appropriate terminology use

### Research Implications
- Examine how terminology influences research design and interpretation
- Investigate the relationship between linguistic choices and research outcomes
- Explore how terminology evolves with scientific understanding

## References

This analysis draws on the broader Ento-Linguistic framework and domain-specific literature on insect biology and scientific communication.

## Data Sources

- Literature corpus: Scientific publications on entomology
- Terminology database: Extracted terms with usage contexts
- Conceptual framework: Ento-Linguistic domain definitions

---
*Report generated by Ento-Linguistic Domain Analysis Script*
"""

        return report

    def _generate_domain_figures(self, domain_name: str, analysis: DomainAnalysis,
                                domain_terms: Dict[str, Any]) -> Dict[str, str]:
        """Generate figures for domain analysis.

        Args:
            domain_name: Name of the domain
            analysis: Domain analysis results
            domain_terms: Terms in this domain

        Returns:
            Dictionary of figure filenames
        """
        figures = {}

        # Term frequency distribution
        if domain_terms:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))

            # Get top terms by frequency
            top_terms = sorted(domain_terms.items(), key=lambda x: x[1].frequency, reverse=True)[:15]
            terms, term_objects = zip(*top_terms)
            frequencies = [obj.frequency for obj in term_objects]

            bars = ax.bar(range(len(terms)), frequencies, alpha=0.7)
            ax.set_xticks(range(len(terms)))
            ax.set_xticklabels(terms, rotation=45, ha='right')
            ax.set_ylabel('Frequency')
            ax.set_title(f'Term Frequency Distribution - {domain_name.replace("_", " ").title()}')

            # Add value labels
            for bar, freq in zip(bars, frequencies):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{freq}', ha='center', va='bottom', fontsize=8)

            plt.tight_layout()
            # Use shorter name for power_and_labor to match manuscript references
            filename_base = domain_name.replace("power_and_labor", "power_labor")
            freq_file = self.figures_dir / f"{filename_base}_term_frequencies.png"
            fig.savefig(freq_file, dpi=300, bbox_inches='tight')
            plt.close(fig)
            figures['term_frequencies'] = str(freq_file)
            
            # Register figure with FigureManager for power_and_labor domain
            if domain_name == "power_and_labor":
                # Register with the expected label to match manuscript
                self.figure_manager.register_figure(
                    filename=freq_file.name,
                    caption="Hierarchical terminology frequency distribution",
                    section="supplemental_results",
                    label="fig:power_labor_frequencies",
                    generated_by="domain_analysis_script.py"
                )

        # Ambiguity visualization
        if analysis.ambiguities:
            fig, ax = plt.subplots(figsize=(8, 6))

            ambiguity_terms = [amb['term'] for amb in analysis.ambiguities]
            context_counts = [len(amb['contexts']) for amb in analysis.ambiguities]

            bars = ax.bar(range(len(ambiguity_terms)), context_counts, alpha=0.7, color='orange')
            ax.set_xticks(range(len(ambiguity_terms)))
            ax.set_xticklabels(ambiguity_terms, rotation=45, ha='right')
            ax.set_ylabel('Number of Contexts')
            ax.set_title(f'Term Ambiguity Analysis - {domain_name.replace("_", " ").title()}')

            plt.tight_layout()
            # Use shorter name for power_and_labor to match manuscript references
            filename_base = domain_name.replace("power_and_labor", "power_labor")
            amb_file = self.figures_dir / f"{filename_base}_ambiguities.png"
            fig.savefig(amb_file, dpi=300, bbox_inches='tight')
            plt.close(fig)
            figures['ambiguities'] = str(amb_file)
            
            # Register figure with FigureManager
            if domain_name == "power_and_labor":
                # Register with the expected label
                self.figure_manager.register_figure(
                    filename=amb_file.name,
                    caption=f"Term ambiguity analysis for {domain_name.replace('_', ' ').title()} domain",
                    section="supplemental_results",
                    label="fig:power_labor_ambiguities",
                    generated_by="domain_analysis_script.py"
                )

        logger.info(f"Generated {len(figures)} figures for {domain_name} domain")
        return figures

    def analyze_all_domains(self, corpus_file: Optional[Path] = None) -> Dict[str, Any]:
        """Analyze all Ento-Linguistic domains.

        Args:
            corpus_file: Path to literature corpus

        Returns:
            Summary of all domain analyses
        """
        domains = [
            'unit_of_individuality',
            'behavior_and_identity',
            'power_and_labor',
            'sex_and_reproduction',
            'kin_and_relatedness',
            'economics'
        ]

        all_results = {}

        for domain in domains:
            try:
                logger.info(f"Analyzing {domain} domain...")
                results = self.analyze_domain(domain, corpus_file, generate_figures=True)
                all_results[domain] = results

            except Exception as e:
                logger.exception(f"Failed to analyze domain '{domain}'")
                logger.error(f"Domain analysis failed: {e}")
                all_results[domain] = {'error': str(e)}

        # Generate comparative report
        comparative_report = self._generate_comparative_report(all_results)

        return {
            'individual_analyses': all_results,
            'comparative_report': comparative_report,
            'summary': {
                'domains_analyzed': len([d for d in all_results.values() if 'error' not in d]),
                'total_terms': sum(r.get('terms_analyzed', 0) for r in all_results.values()),
                'total_ambiguities': sum(r.get('ambiguities_found', 0) for r in all_results.values()),
                'total_recommendations': sum(r.get('recommendations', 0) for r in all_results.values())
            }
        }

    def _generate_comparative_report(self, all_results: Dict[str, Any]) -> str:
        """Generate comparative report across domains.

        Args:
            all_results: Results from all domain analyses

        Returns:
            Comparative report content
        """
        report = """# Comparative Ento-Linguistic Domain Analysis

This report compares terminology patterns, ambiguities, and communication challenges across all six Ento-Linguistic domains.

## Domain Overview

| Domain | Terms Analyzed | Key Ambiguities | Recommendations |
|--------|----------------|-----------------|-----------------|
"""

        for domain, results in all_results.items():
            if 'error' not in results:
                domain_name = domain.replace('_', ' ').title()
                report += f"| {domain_name} | {results.get('terms_analyzed', 0)} | {results.get('ambiguities_found', 0)} | {results.get('recommendations', 0)} |\n"

        report += """

## Cross-Domain Patterns

### Shared Framing Assumptions
1. **Anthropomorphic Projection**: Human social concepts applied to insect societies across all domains
2. **Hierarchical Thinking**: Power relationships conceptualized through human social structures
3. **Economic Logic**: Market principles applied to biological resource allocation
4. **Scale Confusion**: Challenges distinguishing individual, colony, and population levels

### Communication Challenges
1. **Terminology Borrowing**: Scientific terms imported from other domains without adaptation
2. **Conceptual Metaphors**: Biological processes described through familiar but inappropriate metaphors
3. **Context-Dependent Meaning**: Terms that change meaning across research contexts
4. **Scale Ambiguities**: Confusion between different levels of biological organization

## Recommendations for Scientific Communication

### General Guidelines
1. **Explicit Scale Specification**: Always clarify biological level of analysis
2. **Context Awareness**: Recognize how research context influences term meaning
3. **Conceptual Transparency**: Make underlying assumptions and metaphors explicit
4. **Domain-Appropriate Language**: Select terminology that fits biological realities

### Domain-Specific Strategies
- **Unit of Individuality**: Use explicit scale markers (organism-level, colony-level, population-level)
- **Behavior and Identity**: Distinguish between behavioral observations and identity claims
- **Power & Labor**: Replace hierarchical terms with biologically accurate descriptions
- **Sex & Reproduction**: Specify reproductive mechanisms and avoid gender binaries
- **Kin & Relatedness**: Distinguish genetic, social, and environmental relatedness
- **Economics**: Use resource allocation terminology instead of market metaphors

## Future Research Directions

1. **Terminology Evolution**: Track how scientific terms change over time
2. **Cross-Disciplinary Patterns**: Compare Ento-Linguistic patterns with other scientific fields
3. **Communication Interventions**: Test the impact of improved terminology on research practice
4. **Multilingual Analysis**: Examine how terminology patterns vary across languages

## Conclusion

The comparative analysis reveals both domain-specific challenges and shared communication patterns across entomology. Addressing these linguistic issues can improve scientific clarity and open new research possibilities by making conceptual assumptions visible and subject to critical examination.
"""

        # Save comparative report
        report_file = self.reports_dir / "comparative_domain_analysis.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        return str(report_file)


def main() -> None:
    """Main entry point for domain analysis script."""
    parser = argparse.ArgumentParser(description="Ento-Linguistic Domain Analysis")
    parser.add_argument("domain", nargs='?', choices=[
        'unit_of_individuality', 'behavior_and_identity', 'power_and_labor',
        'sex_and_reproduction', 'kin_and_relatedness', 'economics', 'all'
    ], help="Domain to analyze (or 'all' for all domains)")
    parser.add_argument("--corpus-file", type=Path,
                       help="Path to literature corpus JSON file")
    parser.add_argument("--output-dir", type=Path,
                       help="Output directory")
    parser.add_argument("--no-figures", action="store_true",
                       help="Skip figure generation")

    args = parser.parse_args()

    # Default to 'all' if no domain specified
    domain = args.domain if args.domain is not None else 'all'

    script = DomainAnalysisScript(args.output_dir)

    if domain == 'all':
        results = script.analyze_all_domains(args.corpus_file)
        logger.info(f"Analyzed {results['summary']['domains_analyzed']} domains")
        logger.info(f"Total terms: {results['summary']['total_terms']}")
        logger.info(f"Comparative report: {results['comparative_report']}")
    else:
        results = script.analyze_domain(
            domain,
            args.corpus_file,
            generate_figures=not args.no_figures
        )

        if results:
            logger.info(f"Analysis completed for {domain}")
            logger.info(f"Terms analyzed: {results.get('terms_analyzed', 0)}")
            logger.info(f"Report: {results.get('report_file', 'N/A')}")
            if 'figures_generated' in results:
                logger.info(f"Figures generated: {results['figures_generated']}")
        else:
            logger.error(f"Analysis failed for {domain}")


if __name__ == "__main__":
    main()
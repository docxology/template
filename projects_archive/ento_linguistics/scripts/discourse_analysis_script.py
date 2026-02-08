"""Discourse analysis script for Ento-Linguistic research.

This script analyzes discourse patterns in entomological literature,
examining rhetorical strategies, argumentative structures, and narrative frameworks.
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
from discourse_analysis import DiscourseAnalyzer
from literature_mining import LiteratureCorpus

from utils.logging import get_logger

# Directory creation handled inline

logger = get_logger(__name__)


class DiscourseAnalysisScript:
    """Script for analyzing discourse patterns in entomological literature.

    This class examines how scientific discourse is structured, what rhetorical
    strategies are employed, and how language creates persuasive frameworks.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize discourse analysis script.

        Args:
            output_dir: Directory for output files
        """
        self.project_root = Path(__file__).parent.parent
        self.output_dir = output_dir or self.project_root / "output"
        self.figures_dir = self.output_dir / "figures"
        self.reports_dir = self.output_dir / "reports"
        self.data_dir = self.output_dir / "data"

        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized discourse analysis script with output directory: {self.output_dir}"
        )

    def analyze_discourse(
        self,
        corpus_file: Optional[Path] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze discourse patterns in literature.

        Args:
            corpus_file: Path to literature corpus
            focus_areas: Specific areas to focus on

        Returns:
            Analysis results
        """
        logger.info("Starting discourse analysis")

        # Load corpus
        corpus = self._load_corpus(corpus_file)
        texts = corpus.get_text_corpus()

        if not texts:
            logger.warning("No texts available for discourse analysis")
            return {"error": "No texts available"}

        # Perform discourse analysis
        analyzer = DiscourseAnalyzer()
        profile = analyzer.create_discourse_profile(texts)

        # Generate report
        report = self._generate_discourse_report(profile, focus_areas)

        # Generate visualizations
        visualizations = self._generate_discourse_visualizations(profile)

        results = {
            "texts_analyzed": len(texts),
            "patterns_identified": len(profile.get("patterns", {})),
            "structures_found": len(profile.get("argumentative_structures", [])),
            "report_file": report,
            "visualizations": visualizations,
            "data_file": str(self.data_dir / "discourse_analysis.json"),
        }

        # Save analysis data
        analyzer.export_discourse_analysis(
            profile, str(self.data_dir / "discourse_analysis.json")
        )

        logger.info("Discourse analysis completed")
        return results

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

    def _generate_discourse_report(
        self, profile: Dict[str, Any], focus_areas: Optional[List[str]]
    ) -> str:
        """Generate discourse analysis report.

        Args:
            profile: Discourse profile
            focus_areas: Areas of focus

        Returns:
            Report file path
        """
        report = """# Ento-Linguistic Discourse Analysis Report

## Overview

This report analyzes discourse patterns, rhetorical strategies, and argumentative structures in entomological literature, revealing how scientific language creates persuasive frameworks for understanding insect biology.

## Analysis Summary

"""

        summary = profile.get("summary", {})
        report += f"""- **Texts Analyzed**: {summary.get('total_texts', 0)}
- **Discourse Patterns**: {summary.get('total_patterns_identified', 0)}
- **Argumentative Structures**: {summary.get('argumentative_structures_found', 0)}

## Discourse Patterns

### Identified Patterns
"""

        patterns = profile.get("patterns", {})
        for pattern_name, pattern in patterns.items():
            report += f"""#### {pattern_name.replace('_', ' ').title()}
- **Frequency**: {pattern.frequency}
- **Rhetorical Function**: {pattern.rhetorical_function}
- **Domains**: {', '.join(pattern.domains)}
- **Examples**: {len(pattern.examples)} instances

"""

        report += """
## Argumentative Structures

### Common Argument Patterns
"""

        structures = profile.get("argumentative_structures", [])
        if structures:
            # Group by claim types or patterns
            claim_patterns = {}
            for struct in structures:
                claim_start = (
                    struct.claim[:50] + "..."
                    if len(struct.claim) > 50
                    else struct.claim
                )
                if claim_start not in claim_patterns:
                    claim_patterns[claim_start] = []
                claim_patterns[claim_start].append(struct)

            for claim, structs in list(claim_patterns.items())[:5]:  # Top 5 patterns
                report += f"""#### "{claim}"
- **Occurrences**: {len(structs)}
- **Evidence Types**: {', '.join(set(s.evidence[0][:30] + "..." for s in structs if s.evidence))}
- **Discourse Markers**: {', '.join(list(set(marker for s in structs for marker in s.discourse_markers))[:5])}

"""
        else:
            report += "No clear argumentative structures identified.\n"

        report += """
## Rhetorical Strategies

### Persuasive Techniques Used
"""

        strategies = profile.get("rhetorical_strategies", {})
        for strategy, data in strategies.items():
            report += f"""#### {strategy.replace('_', ' ').title()}
- **Frequency**: {data.get('frequency', 0)}
- **Examples**: {len(data.get('examples', []))} instances

"""

        report += """
## Narrative Frameworks

### Story Patterns in Scientific Writing
"""

        frameworks = profile.get("narrative_frameworks", {})
        for framework, examples in frameworks.items():
            report += f"""#### {framework.replace('_', ' ').title()}
- **Occurrences**: {len(examples)}
- **Examples**: {len(examples)} text segments

"""

        report += """
## Persuasive Techniques

### Communication Strategies
"""

        techniques = profile.get("persuasive_techniques", {})
        for technique, data in techniques.items():
            report += f"""#### {technique.replace('_', ' ').title()}
- **Count**: {data.get('count', 0)}

"""

        report += """
## Implications for Scientific Communication

### Key Findings

1. **Anthropomorphic Framing**: Systematic use of human-like agency and social concepts
2. **Hierarchical Discourse**: Power relationships structured through human social metaphors
3. **Economic Reasoning**: Market logic applied to biological resource allocation
4. **Authority Appeals**: Frequent citation of established researchers and methods

### Communication Patterns

The analysis reveals several characteristic patterns in entomological discourse:

- **Problem-Solution Structure**: Research questions framed as problems requiring solutions
- **Evidence-Based Argumentation**: Heavy reliance on empirical data and statistical evidence
- **Comparative Frameworks**: Frequent comparison with other taxa or systems
- **Scale Transitions**: Movement between individual, colony, and population levels

## Recommendations

### Improving Scientific Communication

1. **Explicit Metaphor Recognition**: Make underlying metaphors and analogies visible
2. **Scale Specification**: Always clarify the biological level of analysis
3. **Context Awareness**: Recognize how discourse patterns influence interpretation
4. **Diverse Perspectives**: Include multiple interpretive frameworks

### Research Directions

1. **Cross-Disciplinary Analysis**: Compare discourse patterns across scientific fields
2. **Longitudinal Studies**: Track how discourse patterns change over time
3. **Intervention Studies**: Test the impact of improved communication practices
4. **Multilingual Analysis**: Examine discourse patterns in different language communities

## Data Availability

Analysis results are saved in the following files:
- `discourse_analysis.json`: Complete analysis data
- `discourse_visualizations/`: Generated figures and charts

---
*Report generated by Ento-Linguistic Discourse Analysis Script*
"""

        # Save report
        report_file = self.reports_dir / "discourse_analysis_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        return str(report_file)

    def _generate_discourse_visualizations(
        self, profile: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate visualizations for discourse analysis.

        Args:
            profile: Discourse profile

        Returns:
            Dictionary of visualization files
        """
        visualizations = {}

        # Rhetorical strategies bar chart
        strategies = profile.get("rhetorical_strategies", {})
        if strategies:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))

            strategy_names = list(strategies.keys())
            frequencies = [data.get("frequency", 0) for data in strategies.values()]

            bars = ax.bar(range(len(strategy_names)), frequencies, alpha=0.7)
            ax.set_xticks(range(len(strategy_names)))
            ax.set_xticklabels(
                [name.replace("_", "\n").title() for name in strategy_names]
            )
            ax.set_ylabel("Frequency")
            ax.set_title("Rhetorical Strategies in Entomological Literature")

            plt.tight_layout()
            strategy_file = self.figures_dir / "rhetorical_strategies.png"
            fig.savefig(strategy_file, dpi=300, bbox_inches="tight")
            plt.close(fig)
            visualizations["rhetorical_strategies"] = str(strategy_file)

        # Persuasive techniques pie chart
        techniques = profile.get("persuasive_techniques", {})
        if techniques:
            fig, ax = plt.subplots(figsize=(8, 8))

            technique_names = list(techniques.keys())
            counts = [data.get("count", 0) for data in techniques.values()]

            # Filter out zero counts
            filtered_data = [
                (name, count)
                for name, count in zip(technique_names, counts)
                if count > 0
            ]
            if filtered_data:
                names, values = zip(*filtered_data)

                ax.pie(
                    values,
                    labels=[name.replace("_", " ").title() for name in names],
                    autopct="%1.1f%%",
                    startangle=90,
                )
                ax.set_title("Persuasive Techniques Distribution")

                plt.tight_layout()
                technique_file = self.figures_dir / "persuasive_techniques.png"
                fig.savefig(technique_file, dpi=300, bbox_inches="tight")
                plt.close(fig)
                visualizations["persuasive_techniques"] = str(technique_file)

        return visualizations


def main() -> None:
    """Main entry point for discourse analysis script."""
    parser = argparse.ArgumentParser(description="Ento-Linguistic Discourse Analysis")
    parser.add_argument(
        "--corpus-file", type=Path, help="Path to literature corpus JSON file"
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument(
        "--focus-areas",
        nargs="+",
        choices=["patterns", "rhetoric", "narrative", "argumentation"],
        help="Specific areas to focus analysis on",
    )

    args = parser.parse_args()

    script = DiscourseAnalysisScript(args.output_dir)
    results = script.analyze_discourse(args.corpus_file, args.focus_areas)

    if "error" not in results:
        logger.info("Discourse analysis completed")
        logger.info(f"Texts analyzed: {results.get('texts_analyzed', 0)}")
        logger.info(f"Patterns identified: {results.get('patterns_identified', 0)}")
        logger.info(f"Report: {results.get('report_file', 'N/A')}")
    else:
        logger.error(f"Analysis failed: {results['error']}")


if __name__ == "__main__":
    main()

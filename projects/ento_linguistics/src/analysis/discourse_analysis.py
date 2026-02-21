"""Discourse analysis for Ento-Linguistic research.

This module provides functionality for analyzing how language structures
scientific discourse in entomology, examining rhetorical patterns,
argumentative structures, and narrative frameworks.

This is a facade module that delegates to focused sub-modules while
maintaining full backward compatibility:
  - discourse_patterns: Core data classes and pattern detection
  - rhetorical_analysis: Rhetorical strategies, narrative frameworks, scoring
  - persuasive_analysis: Persuasive techniques, framing effects, conceptual shifts
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set

try:
    from .text_analysis import LinguisticFeatureExtractor, TextProcessor
except ImportError:
    from text_analysis import LinguisticFeatureExtractor, TextProcessor

__all__ = [
    "DiscourseAnalyzer",
    "DiscoursePattern",
    "ArgumentativeStructure",
    "DISCOURSE_MARKERS",
    "extract_argumentative_structure",
    "identify_patterns_in_text",
    "analyze_rhetorical_strategies",
    "analyze_narrative_frequency",
    "identify_narrative_frameworks",
    "quantify_rhetorical_patterns",
    "score_argumentative_structures",
    "analyze_persuasive_techniques",
    "analyze_term_usage_context",
    "measure_persuasive_effectiveness",
    "quantify_framing_effects",
    "track_conceptual_shifts",
]

# Re-export data classes from discourse_patterns
from .discourse_patterns import (
    ArgumentativeStructure,
    DiscoursePattern,
    DISCOURSE_MARKERS,
    extract_argumentative_structure,
    identify_patterns_in_text,
)

# Re-export rhetorical analysis functions
from .rhetorical_analysis import (
    analyze_narrative_frequency,
    analyze_rhetorical_strategies,
    identify_narrative_frameworks,
    quantify_rhetorical_patterns,
    score_argumentative_structures,
)

# Re-export persuasive analysis functions
from .persuasive_analysis import (
    analyze_persuasive_techniques,
    analyze_term_usage_context,
    measure_persuasive_effectiveness,
    quantify_framing_effects,
    track_conceptual_shifts,
)


class DiscourseAnalyzer:
    """Analyze discourse patterns in entomological literature.

    This class examines how scientific discourse is structured, what rhetorical
    strategies are employed, and how language creates persuasive frameworks
    for understanding ant biology and behavior.
    """

    # Expose class-level discourse markers for backward compatibility
    DISCOURSE_MARKERS = DISCOURSE_MARKERS

    def __init__(self):
        """Initialize discourse analyzer."""
        self.text_processor = TextProcessor()
        self.feature_extractor = LinguisticFeatureExtractor()

    def analyze_discourse_patterns(
        self, texts: List[str]
    ) -> Dict[str, DiscoursePattern]:
        """Analyze discourse patterns across texts.

        Args:
            texts: List of texts to analyze (must contain valid strings)

        Returns:
            Dictionary of identified discourse patterns

        Raises:
            ValueError: If texts input is invalid
        """
        # Input validation
        if not isinstance(texts, list):
            raise ValueError("texts must be a list")
        if not texts:
            return {}

        # Filter out invalid texts
        valid_texts = [text for text in texts if isinstance(text, str) and text.strip()]
        if not valid_texts:
            return {}

        patterns = {}

        # Analyze each text
        for text in valid_texts:
            text_patterns = self._identify_patterns_in_text(text)
            for pattern_type, pattern_data in text_patterns.items():
                if pattern_type not in patterns:
                    patterns[pattern_type] = DiscoursePattern(
                        pattern_type=pattern_type,
                        rhetorical_function=pattern_data.get("function", ""),
                    )

                pattern = patterns[pattern_type]
                pattern.add_example(pattern_data.get("example", ""))
                if "domain" in pattern_data:
                    pattern.domains.add(pattern_data["domain"])

        return patterns

    def _identify_patterns_in_text(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Identify discourse patterns in a single text."""
        return identify_patterns_in_text(text)

    def analyze_argumentative_structures(
        self, texts: List[str]
    ) -> List[ArgumentativeStructure]:
        """Analyze argumentative structures in texts.

        Args:
            texts: Texts to analyze

        Returns:
            List of identified argumentative structures
        """
        structures = []

        for text in texts:
            # Split into sentences for analysis
            sentences = self.text_processor.tokenize_sentences(text)

            # Look for argumentative patterns
            structure = self._extract_argumentative_structure(sentences)
            if structure.claim:  # Only add if we found a claim
                structures.append(structure)

        return structures

    def _extract_argumentative_structure(
        self, sentences: List[str]
    ) -> ArgumentativeStructure:
        """Extract argumentative structure from sentences."""
        return extract_argumentative_structure(sentences)

    def analyze_rhetorical_strategies(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze rhetorical strategies used in texts."""
        return analyze_rhetorical_strategies(texts)

    def identify_narrative_frameworks(self, texts: List[str]) -> Dict[str, List[str]]:
        """Identify narrative frameworks used in texts."""
        return identify_narrative_frameworks(texts)

    def analyze_persuasive_techniques(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze persuasive techniques used in scientific writing."""
        return analyze_persuasive_techniques(texts)

    def create_discourse_profile(self, texts: List[str]) -> Dict[str, Any]:
        """Create a comprehensive discourse profile for a set of texts.

        Args:
            texts: Texts to analyze

        Returns:
            Comprehensive discourse profile
        """
        profile = {
            "patterns": self.analyze_discourse_patterns(texts),
            "argumentative_structures": self.analyze_argumentative_structures(texts),
            "rhetorical_strategies": self.analyze_rhetorical_strategies(texts),
            "narrative_frameworks": self.identify_narrative_frameworks(texts),
            "persuasive_techniques": self.analyze_persuasive_techniques(texts),
        }

        # Add summary statistics
        profile["summary"] = {
            "total_texts": len(texts),
            "avg_text_length": (
                sum(len(text) for text in texts) / len(texts) if texts else 0
            ),
            "total_patterns_identified": (
                len(profile["patterns"]) if profile["patterns"] else 0
            ),
            "total_pattern_instances": (
                sum(pattern.frequency for pattern in profile["patterns"].values())
                if profile["patterns"]
                else 0
            ),
            "argumentative_structures_found": len(profile["argumentative_structures"]),
        }

        return profile

    def compare_discourse_profiles(
        self, profile1: Dict[str, Any], profile2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two discourse profiles.

        Args:
            profile1: First discourse profile
            profile2: Second discourse profile

        Returns:
            Comparison results
        """
        comparison = {
            "pattern_differences": {},
            "rhetorical_differences": {},
            "structural_differences": {},
        }

        # Compare patterns
        patterns1 = set(profile1["patterns"].keys())
        patterns2 = set(profile2["patterns"].keys())

        comparison["pattern_differences"] = {
            "unique_to_first": patterns1 - patterns2,
            "unique_to_second": patterns2 - patterns1,
            "shared": patterns1 & patterns2,
        }

        # Compare rhetorical strategies
        for strategy in profile1["rhetorical_strategies"]:
            if strategy in profile2["rhetorical_strategies"]:
                freq1 = profile1["rhetorical_strategies"][strategy]["frequency"]
                freq2 = profile2["rhetorical_strategies"][strategy]["frequency"]
                comparison["rhetorical_differences"][strategy] = {
                    "first": freq1,
                    "second": freq2,
                    "ratio": freq2 / freq1 if freq1 > 0 else float("inf"),
                }

        return comparison

    def export_discourse_analysis(self, profile: Dict[str, Any], filepath: str) -> None:
        """Export discourse analysis results to file.

        Args:
            profile: Discourse profile to export
            filepath: Path to output file
        """
        # Convert dataclasses to dictionaries for JSON serialization
        serializable_profile = {}
        for key, value in profile.items():
            if key == "patterns":
                serializable_profile[key] = {
                    pattern_type: {
                        "pattern_type": pattern.pattern_type,
                        "examples": pattern.examples,
                        "frequency": pattern.frequency,
                        "domains": list(pattern.domains),
                        "rhetorical_function": pattern.rhetorical_function,
                    }
                    for pattern_type, pattern in value.items()
                }
            elif key == "argumentative_structures":
                serializable_profile[key] = [
                    {
                        "claim": struct.claim,
                        "evidence": struct.evidence,
                        "warrant": struct.warrant,
                        "qualification": struct.qualification,
                        "discourse_markers": struct.discourse_markers,
                    }
                    for struct in value
                ]
            else:
                serializable_profile[key] = value

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_profile, f, indent=2, ensure_ascii=False)

    def quantify_rhetorical_patterns(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Quantify rhetorical patterns with frequency and effectiveness metrics."""
        return quantify_rhetorical_patterns(texts)

    def score_argumentative_structures(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Score argumentative structures for strength and coherence."""
        structures = self.analyze_argumentative_structures(texts)
        return score_argumentative_structures(structures, texts)

    def analyze_narrative_frequency(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze frequency and distribution of narrative frameworks."""
        return analyze_narrative_frequency(texts)

    def measure_persuasive_effectiveness(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Measure effectiveness of persuasive techniques."""
        return measure_persuasive_effectiveness(texts)

    def analyze_term_usage_context(
        self, terms: List[str], texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze context-dependent term usage patterns."""
        return analyze_term_usage_context(terms, texts)

    def track_conceptual_shifts(
        self, texts: List[str], time_periods: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Track how concepts shift in discourse over time or contexts."""
        return track_conceptual_shifts(
            texts,
            time_periods,
            rhetorical_analyzer=self.analyze_rhetorical_strategies,
        )

    def quantify_framing_effects(
        self, texts: List[str], framing_concepts: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Quantify the impact of framing assumptions on discourse."""
        return quantify_framing_effects(
            texts,
            framing_concepts,
            rhetorical_analyzer=self.analyze_rhetorical_strategies,
            argumentative_analyzer=self.analyze_argumentative_structures,
        )

    # --- Private helper proxies for backward compatibility ---

    @staticmethod
    def _calculate_persuasiveness(pattern_data):
        from .rhetorical_analysis import _calculate_persuasiveness
        return _calculate_persuasiveness(pattern_data)

    @staticmethod
    def _evaluate_claim_strength(claim):
        from .rhetorical_analysis import _evaluate_claim_strength
        return _evaluate_claim_strength(claim)

    @staticmethod
    def _evaluate_evidence_quality(evidence):
        from .rhetorical_analysis import _evaluate_evidence_quality
        return _evaluate_evidence_quality(evidence)

    @staticmethod
    def _evaluate_reasoning_coherence(reasoning):
        from .rhetorical_analysis import _evaluate_reasoning_coherence
        return _evaluate_reasoning_coherence(reasoning)

    @staticmethod
    def _calculate_structure_confidence(structure):
        from .rhetorical_analysis import _calculate_structure_confidence
        return _calculate_structure_confidence(structure)

    @staticmethod
    def _calculate_framework_consistency(framework_texts):
        from .rhetorical_analysis import _calculate_framework_consistency
        return _calculate_framework_consistency(framework_texts)

    @staticmethod
    def _rate_technique_effectiveness(technique_data):
        from .persuasive_analysis import _rate_technique_effectiveness
        return _rate_technique_effectiveness(technique_data)

    @staticmethod
    def _calculate_technique_impact(technique_data):
        from .persuasive_analysis import _calculate_technique_impact
        return _calculate_technique_impact(technique_data)

    @staticmethod
    def _classify_context_type(sentence, term):
        from .persuasive_analysis import _classify_context_type
        return _classify_context_type(sentence, term)

    @staticmethod
    def _calculate_usage_consistency(contexts):
        from .persuasive_analysis import _calculate_usage_consistency
        return _calculate_usage_consistency(contexts)

    @staticmethod
    def _get_framing_indicators(framing_concept):
        from .persuasive_analysis import _get_framing_indicators
        return _get_framing_indicators(framing_concept)

    @staticmethod
    def _calculate_framing_consistency(framed_texts, indicators):
        from .persuasive_analysis import _calculate_framing_consistency
        return _calculate_framing_consistency(framed_texts, indicators)

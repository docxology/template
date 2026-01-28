"""Discourse analysis for Ento-Linguistic research.

This module provides functionality for analyzing how language structures
scientific discourse in entomology, examining rhetorical patterns,
argumentative structures, and narrative frameworks.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from .text_analysis import LinguisticFeatureExtractor, TextProcessor
except ImportError:
    from text_analysis import LinguisticFeatureExtractor, TextProcessor


@dataclass
class DiscoursePattern:
    """Represents a pattern in scientific discourse.

    Attributes:
        pattern_type: Type of discourse pattern
        examples: Example text instances
        frequency: How often this pattern appears
        domains: Ento-Linguistic domains where this appears
        rhetorical_function: What this pattern accomplishes rhetorically
    """

    pattern_type: str
    examples: List[str] = field(default_factory=list)
    frequency: int = 0
    domains: Set[str] = field(default_factory=set)
    rhetorical_function: str = ""

    def add_example(self, example: str) -> None:
        """Add an example of this pattern.

        Args:
            example: Example text
        """
        self.examples.append(example)
        self.frequency = len(self.examples)


@dataclass
class ArgumentativeStructure:
    """Represents argumentative structures in scientific texts.

    Attributes:
        claim: Main claim being made
        evidence: Supporting evidence
        warrant: Connection between claim and evidence
        qualification: Limits or conditions on the claim
        discourse_markers: Linguistic markers used
    """

    claim: str = ""
    evidence: List[str] = field(default_factory=list)
    warrant: str = ""
    qualification: str = ""
    discourse_markers: List[str] = field(default_factory=list)


class DiscourseAnalyzer:
    """Analyze discourse patterns in entomological literature.

    This class examines how scientific discourse is structured, what rhetorical
    strategies are employed, and how language creates persuasive frameworks
    for understanding ant biology and behavior.
    """

    # Discourse markers for different rhetorical functions
    DISCOURSE_MARKERS = {
        "causation": [
            "because",
            "since",
            "due to",
            "as a result",
            "therefore",
            "thus",
            "consequently",
        ],
        "contrast": [
            "however",
            "although",
            "but",
            "yet",
            "nevertheless",
            "whereas",
            "despite",
        ],
        "evidence": [
            "according to",
            "as shown in",
            "the data indicate",
            "research shows",
            "studies demonstrate",
        ],
        "generalization": [
            "typically",
            "generally",
            "usually",
            "in general",
            "often",
            "frequently",
        ],
        "hedging": [
            "may",
            "might",
            "could",
            "possibly",
            "perhaps",
            "likely",
            "probably",
        ],
        "certainty": [
            "clearly",
            "obviously",
            "definitely",
            "certainly",
            "undoubtedly",
            "evidently",
        ],
    }

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
        """Identify discourse patterns in a single text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary of patterns found
        """
        patterns = {}

        # Anthropomorphic framing patterns
        anthropomorphic_matches = re.findall(
            r"\b(ants?|colony|queen|workers?)\s+(choose|decide|prefer|select|communicate|cooperate|compete)\b",
            text.lower(),
        )

        if anthropomorphic_matches:
            patterns["anthropomorphic_framing"] = {
                "example": f"Found {len(anthropomorphic_matches)} anthropomorphic constructions",
                "function": "Imposes human-like agency on insect societies",
                "domain": "behavior_and_identity",
            }

        # Hierarchical language patterns
        hierarchy_matches = re.findall(
            r"\b(dominant|subordinate|superior|inferior|control|authority|command)\b",
            text.lower(),
        )

        if hierarchy_matches:
            patterns["hierarchical_framing"] = {
                "example": f"Found {len(hierarchy_matches)} hierarchical terms",
                "function": "Structures social relationships as human-like hierarchies",
                "domain": "power_and_labor",
            }

        # Economic metaphor patterns
        economic_matches = re.findall(
            r"\b(cost|benefit|trade|exchange|investment|profit|value)\b", text.lower()
        )

        if economic_matches:
            patterns["economic_metaphors"] = {
                "example": f"Found {len(economic_matches)} economic metaphors",
                "function": "Applies market logic to biological processes",
                "domain": "economics",
            }

        # Scale ambiguity patterns
        scale_patterns = re.findall(
            r"\b(individual|colony|population|society|group)\s+(behavior|trait|characteristic|property)\b",
            text.lower(),
        )

        if scale_patterns:
            patterns["scale_ambiguity"] = {
                "example": f"Found {len(scale_patterns)} scale-ambiguous constructions",
                "function": "Creates confusion about biological levels of analysis",
                "domain": "unit_of_individuality",
            }

        return patterns

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
        """Extract argumentative structure from sentences.

        Args:
            sentences: List of sentences

        Returns:
            Argumentative structure
        """
        structure = ArgumentativeStructure()

        # Simple pattern matching for claims and evidence
        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Look for claim indicators
            if any(
                word in sentence_lower
                for word in ["therefore", "thus", "consequently", "we conclude"]
            ):
                structure.claim = sentence.strip()

            # Look for evidence indicators
            elif any(
                phrase in sentence_lower
                for phrase in ["research shows", "studies demonstrate", "data indicate"]
            ):
                structure.evidence.append(sentence.strip())

            # Look for warrant indicators
            elif any(word in sentence_lower for word in ["because", "since", "due to"]):
                structure.warrant = sentence.strip()

            # Look for qualification indicators
            elif any(
                word in sentence_lower for word in ["however", "although", "but", "yet"]
            ):
                structure.qualification = sentence.strip()

            # Collect discourse markers
            for category, markers in self.DISCOURSE_MARKERS.items():
                for marker in markers:
                    if marker in sentence_lower:
                        structure.discourse_markers.append(marker)

        return structure

    def analyze_rhetorical_strategies(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze rhetorical strategies used in texts.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of rhetorical strategy analysis
        """
        strategies = {
            "authority": {"frequency": 0, "examples": []},
            "analogy": {"frequency": 0, "examples": []},
            "generalization": {"frequency": 0, "examples": []},
            "anecdotal": {"frequency": 0, "examples": []},
        }

        for text in texts:
            # Authority citations
            citations = re.findall(r"\(.*?20\d{2}.*?\)", text)
            strategies["authority"]["frequency"] += len(citations)
            if citations:
                strategies["authority"]["examples"].extend(citations[:2])

            # Analogies
            analogies = re.findall(r"\blike\s+.*?\bant|ant.*?\blike\s+", text.lower())
            strategies["analogy"]["frequency"] += len(analogies)
            if analogies:
                strategies["analogy"]["examples"].extend(analogies[:2])

            # Generalizations
            generalizations = re.findall(
                r"\b(all|every|always|never)\s+.*?\bant", text.lower()
            )
            strategies["generalization"]["frequency"] += len(generalizations)
            if generalizations:
                strategies["generalization"]["examples"].extend(generalizations[:2])

            # Anecdotal evidence
            anecdotal = re.findall(
                r"\b(for\s+example|such\s+as|consider|imagine)\b", text.lower()
            )
            strategies["anecdotal"]["frequency"] += len(anecdotal)
            if anecdotal:
                strategies["anecdotal"]["examples"].extend(anecdotal[:2])

        return strategies

    def identify_narrative_frameworks(self, texts: List[str]) -> Dict[str, List[str]]:
        """Identify narrative frameworks used in texts.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of narrative frameworks and examples
        """
        frameworks = {
            "progress_narrative": [],
            "conflict_narrative": [],
            "discovery_narrative": [],
            "complexity_narrative": [],
        }

        for text in texts:
            text_lower = text.lower()

            # Progress narratives (advancement, improvement)
            if any(
                word in text_lower
                for word in ["advance", "improvement", "progress", "development"]
            ):
                frameworks["progress_narrative"].append(text[:100] + "...")

            # Conflict narratives (struggle, adaptation)
            if any(
                word in text_lower
                for word in ["struggle", "adaptation", "conflict", "competition"]
            ):
                frameworks["conflict_narrative"].append(text[:100] + "...")

            # Discovery narratives (finding, revealing)
            if any(
                word in text_lower for word in ["discover", "reveal", "find", "uncover"]
            ):
                frameworks["discovery_narrative"].append(text[:100] + "...")

            # Complexity narratives (complex, sophisticated)
            if any(
                word in text_lower
                for word in ["complex", "sophisticated", "intricate", "elaborate"]
            ):
                frameworks["complexity_narrative"].append(text[:100] + "...")

        return frameworks

    def analyze_persuasive_techniques(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze persuasive techniques used in scientific writing.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of persuasive technique analysis
        """
        techniques = {
            "rhetorical_questions": {"count": 0, "examples": []},
            "metaphorical_language": {"count": 0, "examples": []},
            "quantitative_emphasis": {"count": 0, "examples": []},
            "authoritative_citations": {"count": 0, "examples": []},
        }

        for text in texts:
            # Rhetorical questions
            questions = re.findall(r"\b(how|what|why|when|where)\s+.*?\?", text)
            techniques["rhetorical_questions"]["count"] += len(questions)
            techniques["rhetorical_questions"]["examples"].extend(questions[:3])

            # Metaphorical language
            metaphors = re.findall(r"\blike\s+a|as\s+a|similar\s+to\b", text.lower())
            techniques["metaphorical_language"]["count"] += len(metaphors)

            # Quantitative emphasis
            quantitative = re.findall(
                r"\b(\d+(?:\.\d+)?\%|\d+(?:\.\d+)?\s+times?)\b", text
            )
            techniques["quantitative_emphasis"]["count"] += len(quantitative)

            # Authoritative citations
            citations = re.findall(r"\(.*?20\d{2}.*?\)", text)
            techniques["authoritative_citations"]["count"] += len(citations)

        return techniques

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
        import json

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
        """Quantify rhetorical patterns with frequency and effectiveness metrics.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of quantified rhetorical patterns
        """
        patterns = self.analyze_rhetorical_strategies(texts)
        quantified_patterns = {}

        for pattern_name, pattern_data in patterns.items():
            # Calculate frequency metrics
            total_occurrences = sum(pattern_data.get("frequency", {}).values())
            text_coverage = (
                len(pattern_data.get("texts", [])) / len(texts) if texts else 0
            )

            # Calculate effectiveness metrics (simplified)
            effectiveness_score = (
                min(total_occurrences / len(texts), 1.0) if texts else 0
            )

            quantified_patterns[pattern_name] = {
                "total_occurrences": total_occurrences,
                "text_coverage": text_coverage,
                "effectiveness_score": effectiveness_score,
                "frequency_distribution": pattern_data.get("frequency", {}),
                "context_examples": pattern_data.get("examples", [])[
                    :5
                ],  # Limit examples
                "persuasiveness_rating": self._calculate_persuasiveness(pattern_data),
            }

        return quantified_patterns

    def score_argumentative_structures(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Score argumentative structures for strength and coherence.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of scored argumentative structures
        """
        structures = self.analyze_argumentative_structures(texts)
        scored_structures = {}

        for structure in structures:
            # Calculate structure strength
            claim_strength = self._evaluate_claim_strength(structure.claim)
            evidence_quality = self._evaluate_evidence_quality(structure.evidence)
            reasoning_coherence = self._evaluate_reasoning_coherence(
                structure.reasoning
            )

            overall_strength = (
                claim_strength + evidence_quality + reasoning_coherence
            ) / 3

            scored_structures[f"structure_{len(scored_structures)}"] = {
                "claim": structure.claim,
                "evidence": structure.evidence,
                "reasoning": structure.reasoning,
                "claim_strength": claim_strength,
                "evidence_quality": evidence_quality,
                "reasoning_coherence": reasoning_coherence,
                "overall_strength": overall_strength,
                "structure_type": structure.structure_type,
                "confidence_score": self._calculate_structure_confidence(structure),
            }

        return scored_structures

    def analyze_narrative_frequency(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze frequency and distribution of narrative frameworks.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of narrative framework frequencies
        """
        frameworks = self.identify_narrative_frameworks(texts)
        framework_analysis = {}

        total_texts = len(texts)

        for framework_type, framework_texts in frameworks.items():
            frequency = len(framework_texts)
            coverage = frequency / total_texts if total_texts > 0 else 0

            # Analyze framework characteristics
            avg_length = (
                sum(len(text.split()) for text in framework_texts) / frequency
                if frequency > 0
                else 0
            )
            unique_phrases = set()
            for text in framework_texts:
                words = text.lower().split()
                for i in range(len(words) - 1):
                    unique_phrases.add(f"{words[i]} {words[i+1]}")

            framework_analysis[framework_type] = {
                "frequency": frequency,
                "coverage_percentage": coverage * 100,
                "average_text_length": avg_length,
                "unique_phrase_count": len(unique_phrases),
                "examples": framework_texts[:3],  # Limit examples
                "consistency_score": self._calculate_framework_consistency(
                    framework_texts
                ),
            }

        return framework_analysis

    def measure_persuasive_effectiveness(
        self, texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Measure effectiveness of persuasive techniques.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of persuasive technique effectiveness metrics
        """
        techniques = self.analyze_persuasive_techniques(texts)
        effectiveness_analysis = {}

        for technique_name, technique_data in techniques.items():
            # Calculate effectiveness metrics
            usage_frequency = technique_data.get("frequency", 0)
            context_relevance = len(technique_data.get("contexts", []))

            # Impact score based on usage and context relevance
            impact_score = min((usage_frequency + context_relevance) / 20, 1.0)

            effectiveness_analysis[technique_name] = {
                "usage_frequency": usage_frequency,
                "context_relevance": context_relevance,
                "impact_score": impact_score,
                "effectiveness_rating": self._rate_technique_effectiveness(
                    technique_data
                ),
                "success_examples": technique_data.get("examples", [])[:3],
                "usage_distribution": technique_data.get("distribution", {}),
            }

        return effectiveness_analysis

    def analyze_term_usage_context(
        self, terms: List[str], texts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze context-dependent term usage patterns.

        Args:
            terms: Terms to analyze
            texts: Source texts

        Returns:
            Dictionary of term usage context analysis
        """
        context_analysis = {}

        for term in terms:
            term_contexts = []
            term_positions = []

            # Find all contexts where term appears
            for i, text in enumerate(texts):
                sentences = text.split(".")
                for j, sentence in enumerate(sentences):
                    if term.lower() in sentence.lower():
                        term_contexts.append(
                            {
                                "text_index": i,
                                "sentence_index": j,
                                "sentence": sentence.strip(),
                                "context_type": self._classify_context_type(
                                    sentence, term
                                ),
                            }
                        )
                        term_positions.append((i, j))

            if term_contexts:
                # Analyze usage patterns
                context_types = {}
                for context in term_contexts:
                    ctx_type = context["context_type"]
                    context_types[ctx_type] = context_types.get(ctx_type, 0) + 1

                # Calculate context diversity
                total_contexts = len(term_contexts)
                context_diversity = (
                    len(context_types) / total_contexts if total_contexts > 0 else 0
                )

                # Analyze positional patterns
                positions = [pos[1] for pos in term_positions]  # Sentence positions
                position_distribution = {
                    "early": sum(1 for pos in positions if pos < 3),
                    "middle": sum(1 for pos in positions if 3 <= pos < 7),
                    "late": sum(1 for pos in positions if pos >= 7),
                }

                context_analysis[term] = {
                    "total_occurrences": total_contexts,
                    "context_diversity": context_diversity,
                    "context_types": context_types,
                    "position_distribution": position_distribution,
                    "usage_consistency": self._calculate_usage_consistency(
                        term_contexts
                    ),
                    "context_examples": term_contexts[:5],  # Limit examples
                }

        return context_analysis

    def track_conceptual_shifts(
        self, texts: List[str], time_periods: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Track how concepts shift in discourse over time or contexts.

        Args:
            texts: Texts to analyze
            time_periods: Optional time periods for temporal analysis

        Returns:
            Dictionary of conceptual shift analysis
        """
        if time_periods and len(time_periods) != len(texts):
            raise ValueError("time_periods must have same length as texts")

        # If no time periods provided, create sequential periods
        if not time_periods:
            time_periods = [f"period_{i}" for i in range(len(texts))]

        shifts = {}
        period_groups = {}

        # Group texts by time period
        for period, text in zip(time_periods, texts):
            if period not in period_groups:
                period_groups[period] = []
            period_groups[period].append(text)

        # Analyze conceptual evolution
        periods_list = sorted(period_groups.keys())
        for i in range(len(periods_list) - 1):
            current_period = periods_list[i]
            next_period = periods_list[i + 1]

            current_texts = period_groups[current_period]
            next_texts = period_groups[next_period]

            # Compare conceptual patterns between periods
            current_patterns = self.analyze_rhetorical_strategies(current_texts)
            next_patterns = self.analyze_rhetorical_strategies(next_texts)

            # Calculate pattern shifts
            pattern_shifts = {}
            for pattern_name in set(current_patterns.keys()) | set(
                next_patterns.keys()
            ):
                current_freq = current_patterns.get(pattern_name, {}).get(
                    "total_occurrences", 0
                )
                next_freq = next_patterns.get(pattern_name, {}).get(
                    "total_occurrences", 0
                )

                shift_magnitude = abs(next_freq - current_freq)
                shift_direction = (
                    "increased"
                    if next_freq > current_freq
                    else "decreased" if next_freq < current_freq else "stable"
                )

                pattern_shifts[pattern_name] = {
                    "from_frequency": current_freq,
                    "to_frequency": next_freq,
                    "shift_magnitude": shift_magnitude,
                    "shift_direction": shift_direction,
                    "relative_change": (
                        (next_freq - current_freq) / current_freq
                        if current_freq > 0
                        else 0
                    ),
                }

            shifts[f"{current_period}_to_{next_period}"] = {
                "pattern_shifts": pattern_shifts,
                "overall_shift_intensity": sum(
                    shift["shift_magnitude"] for shift in pattern_shifts.values()
                ),
                "significant_shifts": [
                    name
                    for name, shift in pattern_shifts.items()
                    if shift["shift_magnitude"] > 2
                ],
            }

        return shifts

    def quantify_framing_effects(
        self, texts: List[str], framing_concepts: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Quantify the impact of framing assumptions on discourse.

        Args:
            texts: Texts to analyze
            framing_concepts: Optional list of framing concepts to analyze

        Returns:
            Dictionary of framing effect quantification
        """
        if framing_concepts is None:
            framing_concepts = [
                "anthropomorphic",
                "mechanistic",
                "teleological",
                "reductionist",
                "holistic",
                "deterministic",
            ]

        framing_analysis = {}

        for concept in framing_concepts:
            # Find texts that use this framing
            framed_texts = []
            framing_indicators = self._get_framing_indicators(concept)

            for text in texts:
                if any(
                    indicator.lower() in text.lower()
                    for indicator in framing_indicators
                ):
                    framed_texts.append(text)

            if framed_texts:
                # Analyze framing impact
                framing_strength = len(framed_texts) / len(texts)
                consistency_score = self._calculate_framing_consistency(
                    framed_texts, framing_indicators
                )

                # Analyze downstream effects
                downstream_patterns = self.analyze_rhetorical_strategies(framed_texts)
                argumentation_structures = self.analyze_argumentative_structures(
                    framed_texts
                )

                framing_analysis[concept] = {
                    "framing_strength": framing_strength,
                    "consistency_score": consistency_score,
                    "affected_texts": len(framed_texts),
                    "downstream_rhetorical_patterns": len(downstream_patterns),
                    "argumentation_structures": len(argumentation_structures),
                    "framing_indicators_used": framing_indicators,
                    "impact_score": framing_strength * consistency_score,
                }

        return framing_analysis

    # Helper methods for the new analysis functions

    def _calculate_persuasiveness(self, pattern_data: Dict[str, Any]) -> float:
        """Calculate persuasiveness rating for a rhetorical pattern."""
        frequency = sum(pattern_data.get("frequency", {}).values())
        context_count = len(pattern_data.get("contexts", []))
        return min((frequency + context_count) / 10, 1.0)  # Normalized score

    def _evaluate_claim_strength(self, claim: str) -> float:
        """Evaluate the strength of a claim."""
        # Simplified evaluation based on claim characteristics
        score = 0.5  # Base score

        if len(claim.split()) > 5:  # Substantial claims
            score += 0.2
        if "?" not in claim:  # Declarative rather than interrogative
            score += 0.1
        if any(
            word in claim.lower() for word in ["therefore", "thus", "hence"]
        ):  # Logical connectors
            score += 0.2

        return min(score, 1.0)

    def _evaluate_evidence_quality(self, evidence: List[str]) -> float:
        """Evaluate the quality of evidence."""
        if not evidence:
            return 0.0

        total_quality = 0
        for ev in evidence:
            quality = 0.5  # Base quality
            if len(ev.split()) > 10:  # Substantial evidence
                quality += 0.2
            if any(
                word in ev.lower()
                for word in ["data", "study", "research", "observation"]
            ):
                quality += 0.3
            total_quality += quality

        return min(total_quality / len(evidence), 1.0)

    def _evaluate_reasoning_coherence(self, reasoning: str) -> float:
        """Evaluate reasoning coherence."""
        coherence_indicators = [
            "because",
            "therefore",
            "thus",
            "hence",
            "consequently",
            "accordingly",
        ]
        connector_count = sum(
            1 for indicator in coherence_indicators if indicator in reasoning.lower()
        )

        base_coherence = 0.3
        coherence_bonus = min(connector_count * 0.1, 0.7)

        return min(base_coherence + coherence_bonus, 1.0)

    def _calculate_structure_confidence(
        self, structure: ArgumentativeStructure
    ) -> float:
        """Calculate confidence score for argumentative structure."""
        confidence = 0.5

        if structure.claim and len(structure.claim.split()) > 3:
            confidence += 0.2
        if structure.evidence and len(structure.evidence) > 0:
            confidence += 0.2
        if structure.reasoning and len(structure.reasoning.split()) > 5:
            confidence += 0.1

        return min(confidence, 1.0)

    def _calculate_framework_consistency(self, framework_texts: List[str]) -> float:
        """Calculate consistency score for narrative framework."""
        if len(framework_texts) < 2:
            return 1.0

        # Simple consistency based on text similarity
        avg_length = sum(len(text.split()) for text in framework_texts) / len(
            framework_texts
        )
        length_variance = sum(
            (len(text.split()) - avg_length) ** 2 for text in framework_texts
        ) / len(framework_texts)

        # Lower variance = higher consistency
        consistency = max(0, 1.0 - (length_variance / (avg_length**2)))

        return consistency

    def _rate_technique_effectiveness(self, technique_data: Dict[str, Any]) -> str:
        """Rate the effectiveness of a persuasive technique."""
        impact = self._calculate_technique_impact(technique_data)

        if impact > 0.8:
            return "highly_effective"
        elif impact > 0.6:
            return "effective"
        elif impact > 0.4:
            return "moderately_effective"
        elif impact > 0.2:
            return "minimally_effective"
        else:
            return "ineffective"

    def _calculate_technique_impact(self, technique_data: Dict[str, Any]) -> float:
        """Calculate impact score for persuasive technique."""
        frequency = technique_data.get("frequency", 0)
        context_count = len(technique_data.get("contexts", []))

        # Impact based on usage and context relevance
        impact = min((frequency + context_count) / 20, 1.0)

        return impact

    def _classify_context_type(self, sentence: str, term: str) -> str:
        """Classify the context type of term usage."""
        sentence_lower = sentence.lower()
        term_lower = term.lower()

        # Simple classification based on surrounding words
        if any(
            word in sentence_lower for word in ["however", "but", "although", "despite"]
        ):
            return "contrastive"
        elif any(word in sentence_lower for word in ["because", "since", "due to"]):
            return "causal"
        elif any(
            word in sentence_lower for word in ["for example", "such as", "including"]
        ):
            return "exemplifying"
        elif "?" in sentence:
            return "interrogative"
        elif any(
            word in sentence_lower
            for word in ["therefore", "thus", "hence", "consequently"]
        ):
            return "conclusive"
        else:
            return "descriptive"

    def _calculate_usage_consistency(self, contexts: List[Dict[str, Any]]) -> float:
        """Calculate consistency of term usage across contexts."""
        if len(contexts) < 2:
            return 1.0

        context_types = [ctx["context_type"] for ctx in contexts]
        most_common_type = max(set(context_types), key=context_types.count)
        consistency = context_types.count(most_common_type) / len(context_types)

        return consistency

    def _get_framing_indicators(self, framing_concept: str) -> List[str]:
        """Get indicator words/phrases for a framing concept."""
        indicators = {
            "anthropomorphic": [
                "think",
                "believe",
                "know",
                "understand",
                "decide",
                "choose",
                "prefer",
            ],
            "mechanistic": [
                "mechanism",
                "process",
                "system",
                "function",
                "operate",
                "control",
            ],
            "teleological": [
                "purpose",
                "goal",
                "function",
                "design",
                "adapt",
                "optimize",
            ],
            "reductionist": [
                "reduce",
                "simplify",
                "break down",
                "component",
                "element",
                "part",
            ],
            "holistic": [
                "whole",
                "system",
                "integrated",
                "complete",
                "comprehensive",
                "unified",
            ],
            "deterministic": [
                "determine",
                "cause",
                "result",
                "predict",
                "inevitable",
                "necessary",
            ],
        }

        return indicators.get(framing_concept, [])

    def _calculate_framing_consistency(
        self, framed_texts: List[str], indicators: List[str]
    ) -> float:
        """Calculate consistency of framing usage."""
        if not framed_texts:
            return 0.0

        total_indicator_usage = 0
        for text in framed_texts:
            text_lower = text.lower()
            text_indicators = sum(
                1 for indicator in indicators if indicator in text_lower
            )
            total_indicator_usage += min(
                text_indicators, len(indicators)
            )  # Cap at max indicators

        consistency = total_indicator_usage / (len(framed_texts) * len(indicators))

        return min(consistency, 1.0)

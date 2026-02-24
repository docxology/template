"""Core discourse pattern data structures and detection for Ento-Linguistic research.

This module provides the foundational data classes and core pattern detection
methods for analyzing how language structures scientific discourse in entomology.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

try:
    from .text_analysis import LinguisticFeatureExtractor, TextProcessor
except ImportError:
    from text_analysis import LinguisticFeatureExtractor, TextProcessor

try:
    from ..core.logging import get_logger
except (ImportError, ValueError):
    import logging

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

__all__ = [
    "DiscoursePattern",
    "ArgumentativeStructure",
    "DISCOURSE_MARKERS",
    "identify_patterns_in_text",
    "extract_argumentative_structure",
]


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


def identify_patterns_in_text(text: str) -> Dict[str, Dict[str, Any]]:
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


def extract_argumentative_structure(
    sentences: List[str],
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
        for category, markers in DISCOURSE_MARKERS.items():
            for marker in markers:
                if marker in sentence_lower:
                    structure.discourse_markers.append(marker)

    return structure

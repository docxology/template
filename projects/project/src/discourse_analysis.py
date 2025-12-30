"""Discourse analysis for Ento-Linguistic research.

This module provides functionality for analyzing how language structures
scientific discourse in entomology, examining rhetorical patterns,
argumentative structures, and narrative frameworks.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field

try:
    from .text_analysis import TextProcessor, LinguisticFeatureExtractor
except ImportError:
    from text_analysis import TextProcessor, LinguisticFeatureExtractor


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
        'causation': ['because', 'since', 'due to', 'as a result', 'therefore', 'thus', 'consequently'],
        'contrast': ['however', 'although', 'but', 'yet', 'nevertheless', 'whereas', 'despite'],
        'evidence': ['according to', 'as shown in', 'the data indicate', 'research shows', 'studies demonstrate'],
        'generalization': ['typically', 'generally', 'usually', 'in general', 'often', 'frequently'],
        'hedging': ['may', 'might', 'could', 'possibly', 'perhaps', 'likely', 'probably'],
        'certainty': ['clearly', 'obviously', 'definitely', 'certainly', 'undoubtedly', 'evidently']
    }

    def __init__(self):
        """Initialize discourse analyzer."""
        self.text_processor = TextProcessor()
        self.feature_extractor = LinguisticFeatureExtractor()

    def analyze_discourse_patterns(self, texts: List[str]) -> Dict[str, DiscoursePattern]:
        """Analyze discourse patterns across texts.

        Args:
            texts: List of texts to analyze

        Returns:
            Dictionary of identified discourse patterns
        """
        patterns = {}

        # Analyze each text
        for text in texts:
            text_patterns = self._identify_patterns_in_text(text)
            for pattern_type, pattern_data in text_patterns.items():
                if pattern_type not in patterns:
                    patterns[pattern_type] = DiscoursePattern(
                        pattern_type=pattern_type,
                        rhetorical_function=pattern_data.get('function', '')
                    )

                pattern = patterns[pattern_type]
                pattern.add_example(pattern_data.get('example', ''))
                if 'domain' in pattern_data:
                    pattern.domains.add(pattern_data['domain'])

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
            r'\b(ants?|colony|queen|workers?)\s+(choose|decide|prefer|select|communicate|cooperate|compete)\b',
            text.lower()
        )

        if anthropomorphic_matches:
            patterns['anthropomorphic_framing'] = {
                'example': f"Found {len(anthropomorphic_matches)} anthropomorphic constructions",
                'function': 'Imposes human-like agency on insect societies',
                'domain': 'behavior_and_identity'
            }

        # Hierarchical language patterns
        hierarchy_matches = re.findall(
            r'\b(dominant|subordinate|superior|inferior|control|authority|command)\b',
            text.lower()
        )

        if hierarchy_matches:
            patterns['hierarchical_framing'] = {
                'example': f"Found {len(hierarchy_matches)} hierarchical terms",
                'function': 'Structures social relationships as human-like hierarchies',
                'domain': 'power_and_labor'
            }

        # Economic metaphor patterns
        economic_matches = re.findall(
            r'\b(cost|benefit|trade|exchange|investment|profit|value)\b',
            text.lower()
        )

        if economic_matches:
            patterns['economic_metaphors'] = {
                'example': f"Found {len(economic_matches)} economic metaphors",
                'function': 'Applies market logic to biological processes',
                'domain': 'economics'
            }

        # Scale ambiguity patterns
        scale_patterns = re.findall(
            r'\b(individual|colony|population|society|group)\s+(behavior|trait|characteristic|property)\b',
            text.lower()
        )

        if scale_patterns:
            patterns['scale_ambiguity'] = {
                'example': f"Found {len(scale_patterns)} scale-ambiguous constructions",
                'function': 'Creates confusion about biological levels of analysis',
                'domain': 'unit_of_individuality'
            }

        return patterns

    def analyze_argumentative_structures(self, texts: List[str]) -> List[ArgumentativeStructure]:
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

    def _extract_argumentative_structure(self, sentences: List[str]) -> ArgumentativeStructure:
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
            if any(word in sentence_lower for word in ['therefore', 'thus', 'consequently', 'we conclude']):
                structure.claim = sentence.strip()

            # Look for evidence indicators
            elif any(phrase in sentence_lower for phrase in ['research shows', 'studies demonstrate', 'data indicate']):
                structure.evidence.append(sentence.strip())

            # Look for warrant indicators
            elif any(word in sentence_lower for word in ['because', 'since', 'due to']):
                structure.warrant = sentence.strip()

            # Look for qualification indicators
            elif any(word in sentence_lower for word in ['however', 'although', 'but', 'yet']):
                structure.qualification = sentence.strip()

            # Collect discourse markers
            for category, markers in self.DISCOURSE_MARKERS.items():
                for marker in markers:
                    if marker in sentence_lower:
                        structure.discourse_markers.append(marker)

        return structure

    def analyze_rhetorical_strategies(self, texts: List[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze rhetorical strategies used in texts.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of rhetorical strategy analysis
        """
        strategies = {
            'authority': {'frequency': 0, 'examples': []},
            'analogy': {'frequency': 0, 'examples': []},
            'generalization': {'frequency': 0, 'examples': []},
            'anecdotal': {'frequency': 0, 'examples': []}
        }

        for text in texts:
            # Authority citations
            citations = re.findall(r'\(.*?20\d{2}.*?\)', text)
            strategies['authority']['frequency'] += len(citations)
            if citations:
                strategies['authority']['examples'].extend(citations[:2])

            # Analogies
            analogies = re.findall(r'\blike\s+.*?\bant|ant.*?\blike\s+', text.lower())
            strategies['analogy']['frequency'] += len(analogies)
            if analogies:
                strategies['analogy']['examples'].extend(analogies[:2])

            # Generalizations
            generalizations = re.findall(r'\b(all|every|always|never)\s+.*?\bant', text.lower())
            strategies['generalization']['frequency'] += len(generalizations)
            if generalizations:
                strategies['generalization']['examples'].extend(generalizations[:2])

            # Anecdotal evidence
            anecdotal = re.findall(r'\b(for\s+example|such\s+as|consider|imagine)\b', text.lower())
            strategies['anecdotal']['frequency'] += len(anecdotal)
            if anecdotal:
                strategies['anecdotal']['examples'].extend(anecdotal[:2])

        return strategies

    def identify_narrative_frameworks(self, texts: List[str]) -> Dict[str, List[str]]:
        """Identify narrative frameworks used in texts.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of narrative frameworks and examples
        """
        frameworks = {
            'progress_narrative': [],
            'conflict_narrative': [],
            'discovery_narrative': [],
            'complexity_narrative': []
        }

        for text in texts:
            text_lower = text.lower()

            # Progress narratives (advancement, improvement)
            if any(word in text_lower for word in ['advance', 'improvement', 'progress', 'development']):
                frameworks['progress_narrative'].append(text[:100] + '...')

            # Conflict narratives (struggle, adaptation)
            if any(word in text_lower for word in ['struggle', 'adaptation', 'conflict', 'competition']):
                frameworks['conflict_narrative'].append(text[:100] + '...')

            # Discovery narratives (finding, revealing)
            if any(word in text_lower for word in ['discover', 'reveal', 'find', 'uncover']):
                frameworks['discovery_narrative'].append(text[:100] + '...')

            # Complexity narratives (complex, sophisticated)
            if any(word in text_lower for word in ['complex', 'sophisticated', 'intricate', 'elaborate']):
                frameworks['complexity_narrative'].append(text[:100] + '...')

        return frameworks

    def analyze_persuasive_techniques(self, texts: List[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze persuasive techniques used in scientific writing.

        Args:
            texts: Texts to analyze

        Returns:
            Dictionary of persuasive technique analysis
        """
        techniques = {
            'rhetorical_questions': {'count': 0, 'examples': []},
            'metaphorical_language': {'count': 0, 'examples': []},
            'quantitative_emphasis': {'count': 0, 'examples': []},
            'authoritative_citations': {'count': 0, 'examples': []}
        }

        for text in texts:
            # Rhetorical questions
            questions = re.findall(r'\b(how|what|why|when|where)\s+.*?\?', text)
            techniques['rhetorical_questions']['count'] += len(questions)
            techniques['rhetorical_questions']['examples'].extend(questions[:3])

            # Metaphorical language
            metaphors = re.findall(r'\blike\s+a|as\s+a|similar\s+to\b', text.lower())
            techniques['metaphorical_language']['count'] += len(metaphors)

            # Quantitative emphasis
            quantitative = re.findall(r'\b(\d+(?:\.\d+)?\%|\d+(?:\.\d+)?\s+times?)\b', text)
            techniques['quantitative_emphasis']['count'] += len(quantitative)

            # Authoritative citations
            citations = re.findall(r'\(.*?20\d{2}.*?\)', text)
            techniques['authoritative_citations']['count'] += len(citations)

        return techniques

    def create_discourse_profile(self, texts: List[str]) -> Dict[str, Any]:
        """Create a comprehensive discourse profile for a set of texts.

        Args:
            texts: Texts to analyze

        Returns:
            Comprehensive discourse profile
        """
        profile = {
            'patterns': self.analyze_discourse_patterns(texts),
            'argumentative_structures': self.analyze_argumentative_structures(texts),
            'rhetorical_strategies': self.analyze_rhetorical_strategies(texts),
            'narrative_frameworks': self.identify_narrative_frameworks(texts),
            'persuasive_techniques': self.analyze_persuasive_techniques(texts)
        }

        # Add summary statistics
        profile['summary'] = {
            'total_texts': len(texts),
            'avg_text_length': sum(len(text) for text in texts) / len(texts) if texts else 0,
            'total_patterns_identified': sum(pattern.frequency for pattern in profile['patterns'].values()) if profile['patterns'] else 0,
            'argumentative_structures_found': len(profile['argumentative_structures'])
        }

        return profile

    def compare_discourse_profiles(self, profile1: Dict[str, Any],
                                 profile2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two discourse profiles.

        Args:
            profile1: First discourse profile
            profile2: Second discourse profile

        Returns:
            Comparison results
        """
        comparison = {
            'pattern_differences': {},
            'rhetorical_differences': {},
            'structural_differences': {}
        }

        # Compare patterns
        patterns1 = set(profile1['patterns'].keys())
        patterns2 = set(profile2['patterns'].keys())

        comparison['pattern_differences'] = {
            'unique_to_first': patterns1 - patterns2,
            'unique_to_second': patterns2 - patterns1,
            'shared': patterns1 & patterns2
        }

        # Compare rhetorical strategies
        for strategy in profile1['rhetorical_strategies']:
            if strategy in profile2['rhetorical_strategies']:
                freq1 = profile1['rhetorical_strategies'][strategy]['frequency']
                freq2 = profile2['rhetorical_strategies'][strategy]['frequency']
                comparison['rhetorical_differences'][strategy] = {
                    'first': freq1,
                    'second': freq2,
                    'ratio': freq2 / freq1 if freq1 > 0 else float('inf')
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
            if key == 'patterns':
                serializable_profile[key] = {
                    pattern_type: {
                        'pattern_type': pattern.pattern_type,
                        'examples': pattern.examples,
                        'frequency': pattern.frequency,
                        'domains': list(pattern.domains),
                        'rhetorical_function': pattern.rhetorical_function
                    }
                    for pattern_type, pattern in value.items()
                }
            elif key == 'argumentative_structures':
                serializable_profile[key] = [
                    {
                        'claim': struct.claim,
                        'evidence': struct.evidence,
                        'warrant': struct.warrant,
                        'qualification': struct.qualification,
                        'discourse_markers': struct.discourse_markers
                    }
                    for struct in value
                ]
            else:
                serializable_profile[key] = value

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_profile, f, indent=2, ensure_ascii=False)
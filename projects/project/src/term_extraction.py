"""Terminology extraction for Ento-Linguistic analysis.

This module provides functionality for extracting, classifying, and analyzing
terminology used in entomological research, with focus on the six Ento-Linguistic domains.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field

try:
    from .text_analysis import TextProcessor
except ImportError:
    from text_analysis import TextProcessor


@dataclass
class Term:
    """Represents an extracted term with metadata.

    Attributes:
        text: The term text
        lemma: Lemmatized form
        domains: List of Ento-Linguistic domains this term belongs to
        frequency: Total frequency across corpus
        contexts: List of contextual usages
        pos_tags: Part-of-speech tags for the term
        confidence: Extraction confidence score
    """
    text: str
    lemma: str
    domains: List[str] = field(default_factory=list)
    frequency: int = 0
    contexts: List[str] = field(default_factory=list)
    pos_tags: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def add_context(self, context: str) -> None:
        """Add a usage context for this term.

        Args:
            context: Contextual usage example
        """
        if context not in self.contexts:
            self.contexts.append(context)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'text': self.text,
            'lemma': self.lemma,
            'domains': self.domains,
            'frequency': self.frequency,
            'contexts': self.contexts,
            'pos_tags': self.pos_tags,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Term':
        """Create from dictionary."""
        return cls(**data)


class TerminologyExtractor:
    """Extract and classify terminology from entomological texts.

    This class implements domain-specific terminology extraction algorithms
    tailored to the six Ento-Linguistic domains.
    """

    # Ento-Linguistic domain definitions with seed terms
    DOMAIN_SEEDS = {
        'unit_of_individuality': {
            'ant', 'nestmate', 'colony', 'superorganism', 'eusocial',
            'individual', 'collective', 'organism', 'holobiont', 'symbiont'
        },
        'behavior_and_identity': {
            'foraging', 'forager', 'worker', 'soldier', 'reproductive',
            'behavior', 'task', 'role', 'specialization', 'division of labor',
            'caste', 'polymorphism', 'behavioral repertoire'
        },
        'power_and_labor': {
            'caste', 'queen', 'worker', 'slave', 'parasite', 'host',
            'dominant', 'subordinate', 'hierarchy', 'control', 'authority',
            'exploitation', 'coercion', 'reproduction control'
        },
        'sex_and_reproduction': {
            'sex determination', 'sex differentiation', 'haplodiploidy',
            'diploid', 'haploid', 'gyne', 'male', 'female', 'reproduction',
            'mating', 'fertilization', 'parthenogenesis', 'queen'
        },
        'kin_and_relatedness': {
            'kin', 'relatedness', 'genetic relatedness', 'kin selection',
            'inclusive fitness', 'altruism', 'cooperation', 'family',
            'sibship', 'colony kin structure', 'relatedness coefficient'
        },
        'economics': {
            'resource', 'allocation', 'distribution', 'sharing', 'trade',
            'exchange', 'cost', 'benefit', 'investment', 'foraging efficiency',
            'resource economics', 'colony economy', 'optimal foraging'
        }
    }

    # Linguistic patterns for term extraction
    TERM_PATTERNS = [
        r'\b[a-z]+_[a-z]+\b',  # Underscore compounds
        r'\b[a-z]+-[a-z]+\b',  # Hyphenated compounds
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',  # Multi-word proper nouns
        r'\b[a-z]{4,}(?:\s+[a-z]{3,})+',  # Multi-word technical terms
    ]

    def __init__(self, text_processor: Optional[TextProcessor] = None):
        """Initialize terminology extractor.

        Args:
            text_processor: Text processor instance
        """
        self.text_processor = text_processor or TextProcessor()
        self.extracted_terms: Dict[str, Term] = {}

    def extract_terms(self, texts: List[str], min_frequency: int = 3) -> Dict[str, Term]:
        """Extract terminology from a collection of texts.

        Args:
            texts: List of input texts
            min_frequency: Minimum frequency for term inclusion

        Returns:
            Dictionary of extracted terms
        """
        # Process all texts
        all_tokens = []
        text_contexts = []

        for text in texts:
            tokens = self.text_processor.process_text(text, lemmatize=False)
            all_tokens.extend(tokens)
            text_contexts.append((text, tokens))

        # Count term frequencies
        term_counts = Counter(all_tokens)

        # Extract candidate terms
        candidate_terms = set()
        for token in all_tokens:
            if self._is_candidate_term(token):
                candidate_terms.add(token)

        # Create Term objects for candidates that meet frequency threshold
        for candidate in candidate_terms:
            if term_counts[candidate] >= min_frequency:
                lemma = self.text_processor.lemmatize_tokens([candidate])[0]
                term = Term(
                    text=candidate,
                    lemma=lemma,
                    frequency=term_counts[candidate]
                )

                # Classify domains
                term.domains = self.classify_term_domains(candidate)

                # Extract contexts
                self._extract_term_contexts(term, text_contexts)

                # Calculate confidence
                term.confidence = self._calculate_extraction_confidence(term)

                self.extracted_terms[candidate] = term

        return self.extracted_terms

    def _is_candidate_term(self, token: str) -> bool:
        """Check if token is a candidate for term extraction.

        Args:
            token: Token to evaluate

        Returns:
            True if token is a candidate term
        """
        # Skip very short or very long tokens
        if len(token) < 3 or len(token) > 50:
            return False

        # Skip pure numbers
        if token.isdigit():
            return False

        # Check for scientific patterns
        for pattern in self.TERM_PATTERNS:
            if re.match(pattern, token):
                return True

        # Check for domain-specific characteristics
        if '_' in token or '-' in token:
            return True

        # Check for compound words (CamelCase or multi-word)
        if re.match(r'[A-Z][a-z]+[A-Z]', token):  # CamelCase
            return True

        # Multi-word terms with scientific vocabulary
        scientific_words = {'eusocial', 'colony', 'behavior', 'foraging',
                          'reproduction', 'selection', 'evolution', 'genetic'}

        if any(word in token.lower() for word in scientific_words):
            return True

        return False

    def classify_term_domains(self, term: str) -> List[str]:
        """Classify term into Ento-Linguistic domains.

        Args:
            term: Term to classify

        Returns:
            List of domain names
        """
        domains = []
        term_lower = term.lower()

        # Direct seed term matching
        for domain, seeds in self.DOMAIN_SEEDS.items():
            if term_lower in seeds:
                domains.append(domain)
                continue

            # Fuzzy matching for compound terms
            term_words = set(term_lower.replace('_', ' ').replace('-', ' ').split())
            if term_words & seeds:  # Any overlap
                domains.append(domain)

        # Pattern-based classification
        if not domains:  # Only if no direct matches
            domains.extend(self._classify_by_pattern(term_lower))

        return list(set(domains))  # Remove duplicates

    def _classify_by_pattern(self, term: str) -> List[str]:
        """Classify term based on linguistic patterns.

        Args:
            term: Term to classify

        Returns:
            List of inferred domains
        """
        domains = []

        # Individuality patterns
        if any(word in term for word in ['individual', 'collective', 'organism', 'unit']):
            domains.append('unit_of_individuality')

        # Behavior patterns
        if any(word in term for word in ['behavior', 'task', 'role', 'foraging', 'specialization']):
            domains.append('behavior_and_identity')

        # Power patterns
        if any(word in term for word in ['caste', 'hierarchy', 'control', 'dominant', 'subordinate']):
            domains.append('power_and_labor')

        # Reproduction patterns
        if any(word in term for word in ['sex', 'reproduction', 'mating', 'fertilization']):
            domains.append('sex_and_reproduction')

        # Kin patterns
        if any(word in term for word in ['kin', 'relatedness', 'family', 'altruism']):
            domains.append('kin_and_relatedness')

        # Economic patterns
        if any(word in term for word in ['resource', 'allocation', 'cost', 'benefit', 'trade']):
            domains.append('economics')

        return domains

    def _extract_term_contexts(self, term: Term, text_contexts: List[Tuple[str, List[str]]],
                              window_size: int = 3) -> None:
        """Extract contextual usage examples for a term.

        Args:
            term: Term to extract contexts for
            text_contexts: List of (text, tokens) pairs
            window_size: Context window size in words
        """
        for text, tokens in text_contexts:
            for i, token in enumerate(tokens):
                if token == term.text:
                    # Extract context window
                    start = max(0, i - window_size)
                    end = min(len(tokens), i + window_size + 1)
                    context_tokens = tokens[start:end]
                    context = ' '.join(context_tokens)

                    # Highlight the term
                    highlighted_context = context.replace(
                        term.text,
                        f"**{term.text}**"
                    )

                    term.add_context(highlighted_context)

                    # Limit contexts per term
                    if len(term.contexts) >= 5:
                        break

    def _calculate_extraction_confidence(self, term: Term) -> float:
        """Calculate confidence score for term extraction.

        Args:
            term: Term to score

        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0

        # Domain classification confidence
        if term.domains:
            confidence += 0.4

        # Frequency-based confidence
        if term.frequency > 10:
            confidence += 0.3
        elif term.frequency > 5:
            confidence += 0.2
        else:
            confidence += 0.1

        # Linguistic pattern confidence
        if any(pattern in term.text for pattern in ['_', '-', ' ']):
            confidence += 0.2

        # Context availability
        if term.contexts:
            confidence += 0.1

        return min(confidence, 1.0)

    def get_domain_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each domain.

        Returns:
            Dictionary with domain statistics
        """
        domain_stats = defaultdict(lambda: {
            'term_count': 0,
            'total_frequency': 0,
            'avg_confidence': 0.0,
            'terms': []
        })

        for term in self.extracted_terms.values():
            for domain in term.domains:
                domain_stats[domain]['term_count'] += 1
                domain_stats[domain]['total_frequency'] += term.frequency
                domain_stats[domain]['avg_confidence'] += term.confidence
                domain_stats[domain]['terms'].append(term.text)

        # Calculate averages
        for stats in domain_stats.values():
            if stats['term_count'] > 0:
                stats['avg_confidence'] /= stats['term_count']

        return dict(domain_stats)

    def find_term_cooccurrences(self, term1: str, term2: str,
                               texts: List[str], window_size: int = 10) -> int:
        """Find co-occurrence frequency of two terms.

        Args:
            term1: First term
            term2: Second term
            texts: Texts to search
            window_size: Co-occurrence window size

        Returns:
            Number of co-occurrences
        """
        cooccurrences = 0

        for text in texts:
            tokens = self.text_processor.process_text(text, lemmatize=False)

            # Find positions of both terms
            term1_positions = [i for i, token in enumerate(tokens) if token == term1]
            term2_positions = [i for i, token in enumerate(tokens) if token == term2]

            # Check for co-occurrences within window
            for pos1 in term1_positions:
                for pos2 in term2_positions:
                    if abs(pos1 - pos2) <= window_size:
                        cooccurrences += 1
                        break

        return cooccurrences

    def export_terms_csv(self, filepath: str) -> None:
        """Export extracted terms to CSV file.

        Args:
            filepath: Path to output CSV file
        """
        import csv

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['term', 'lemma', 'domains', 'frequency', 'confidence', 'contexts']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for term in self.extracted_terms.values():
                writer.writerow({
                    'term': term.text,
                    'lemma': term.lemma,
                    'domains': ';'.join(term.domains),
                    'frequency': term.frequency,
                    'confidence': term.confidence,
                    'contexts': '|'.join(term.contexts[:3])  # Limit contexts for CSV
                })


def create_domain_seed_expansion(extractor: TerminologyExtractor,
                               corpus_terms: Dict[str, Term]) -> Dict[str, Set[str]]:
    """Expand domain seed terms using corpus analysis.

    Args:
        extractor: Terminology extractor instance
        corpus_terms: Terms extracted from corpus

    Returns:
        Expanded domain seed sets
    """
    expanded_seeds = {}

    for domain, original_seeds in extractor.DOMAIN_SEEDS.items():
        expanded_seeds[domain] = set(original_seeds)

        # Find corpus terms in this domain
        domain_terms = [term for term in corpus_terms.values() if domain in term.domains]

        # Add high-confidence, high-frequency terms
        for term in domain_terms:
            if term.confidence > 0.7 and term.frequency > 5:
                expanded_seeds[domain].add(term.text)

    return expanded_seeds
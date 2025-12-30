"""Conceptual mapping for Ento-Linguistic analysis.

This module provides functionality for mapping terminology to concepts,
identifying conceptual overlaps, and analyzing how terms structure scientific understanding.
"""
from __future__ import annotations

import re
from collections import defaultdict, Counter
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field

try:
    from .term_extraction import Term
except ImportError:
    from term_extraction import Term


@dataclass
class Concept:
    """Represents a conceptual category in Ento-Linguistic analysis.

    Attributes:
        name: Concept name
        description: Human-readable description
        terms: Set of associated terms
        domains: Ento-Linguistic domains this concept spans
        parent_concepts: Higher-level concepts this belongs to
        child_concepts: Lower-level concepts under this one
        confidence: Mapping confidence score
    """
    name: str
    description: str
    terms: Set[str] = field(default_factory=set)
    domains: Set[str] = field(default_factory=set)
    parent_concepts: Set[str] = field(default_factory=set)
    child_concepts: Set[str] = field(default_factory=set)
    confidence: float = 0.0

    def add_term(self, term: str) -> None:
        """Add a term to this concept.

        Args:
            term: Term to add
        """
        self.terms.add(term)

    def add_domain(self, domain: str) -> None:
        """Add a domain to this concept.

        Args:
            domain: Domain to add
        """
        self.domains.add(domain)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'terms': list(self.terms),
            'domains': list(self.domains),
            'parent_concepts': list(self.parent_concepts),
            'child_concepts': list(self.child_concepts),
            'confidence': self.confidence
        }


@dataclass
class ConceptMap:
    """Network of concepts and their relationships.

    Attributes:
        concepts: Dictionary of concept names to Concept objects
        term_to_concepts: Mapping from terms to their concepts
        concept_relationships: Edges between concepts with weights
    """
    concepts: Dict[str, Concept] = field(default_factory=dict)
    term_to_concepts: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    concept_relationships: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the map.

        Args:
            concept: Concept to add
        """
        self.concepts[concept.name] = concept

        # Update term-to-concept mapping
        for term in concept.terms:
            self.term_to_concepts[term].add(concept.name)

    def add_relationship(self, concept1: str, concept2: str, weight: float) -> None:
        """Add a relationship between concepts.

        Args:
            concept1: First concept name
            concept2: Second concept name
            weight: Relationship strength (0-1)
        """
        key = tuple(sorted([concept1, concept2]))
        self.concept_relationships[key] = weight

    def get_concept_terms(self, concept_name: str) -> Set[str]:
        """Get all terms associated with a concept.

        Args:
            concept_name: Name of concept

        Returns:
            Set of associated terms
        """
        if concept_name in self.concepts:
            return self.concepts[concept_name].terms
        return set()

    def get_term_concepts(self, term: str) -> Set[str]:
        """Get all concepts associated with a term.

        Args:
            term: Term to query

        Returns:
            Set of associated concept names
        """
        return self.term_to_concepts.get(term, set())

    def find_concept_overlaps(self) -> Dict[Tuple[str, str], Set[str]]:
        """Find overlapping terms between concepts.

        Returns:
            Dictionary mapping concept pairs to overlapping terms
        """
        overlaps = {}

        concept_names = list(self.concepts.keys())
        for i, concept1 in enumerate(concept_names):
            for concept2 in concept_names[i+1:]:
                terms1 = self.get_concept_terms(concept1)
                terms2 = self.get_concept_terms(concept2)

                overlap = terms1 & terms2
                if overlap:
                    key = tuple(sorted([concept1, concept2]))
                    overlaps[key] = overlap

        return overlaps


class ConceptualMapper:
    """Map terminology to conceptual structures.

    This class provides algorithms for organizing terminology into conceptual
    hierarchies and networks that reveal how language structures scientific understanding.
    """

    # Base conceptual framework for Ento-Linguistic analysis
    BASE_CONCEPTS = {
        'biological_individuality': {
            'description': 'Concepts related to what constitutes a biological individual',
            'domains': ['unit_of_individuality'],
            'key_terms': ['organism', 'individual', 'colony', 'superorganism', 'holobiont']
        },
        'social_organization': {
            'description': 'Principles of social organization and structure',
            'domains': ['power_and_labor', 'behavior_and_identity'],
            'key_terms': ['caste', 'hierarchy', 'division of labor', 'specialization']
        },
        'reproductive_biology': {
            'description': 'Reproductive systems and sex determination',
            'domains': ['sex_and_reproduction'],
            'key_terms': ['haplodiploidy', 'sex determination', 'parthenogenesis', 'mating']
        },
        'kinship_systems': {
            'description': 'Genetic and social relatedness structures',
            'domains': ['kin_and_relatedness'],
            'key_terms': ['relatedness', 'kin selection', 'inclusive fitness', 'altruism']
        },
        'resource_economics': {
            'description': 'Resource allocation and economic principles',
            'domains': ['economics'],
            'key_terms': ['resource allocation', 'foraging efficiency', 'cost-benefit', 'trade']
        },
        'behavioral_ecology': {
            'description': 'Behavioral adaptations and ecological contexts',
            'domains': ['behavior_and_identity', 'economics'],
            'key_terms': ['foraging', 'behavior', 'adaptation', 'optimization', 'fitness']
        }
    }

    def __init__(self):
        """Initialize conceptual mapper."""
        self.concept_map = ConceptMap()

    def build_concept_map(self, terms: Dict[str, Term]) -> ConceptMap:
        """Build a concept map from extracted terminology.

        Args:
            terms: Dictionary of extracted terms

        Returns:
            Populated concept map
        """
        # Initialize base concepts
        for concept_name, concept_data in self.BASE_CONCEPTS.items():
            concept = Concept(
                name=concept_name,
                description=concept_data['description']
            )

            # Add domains
            for domain in concept_data['domains']:
                concept.add_domain(domain)

            # Add initial key terms
            for term in concept_data['key_terms']:
                concept.add_term(term)

            self.concept_map.add_concept(concept)

        # Map extracted terms to concepts
        for term_text, term_obj in terms:
            self._map_term_to_concepts(term_obj)

        # Establish concept relationships
        self._build_concept_relationships()

        return self.concept_map

    def _map_term_to_concepts(self, term: Term) -> None:
        """Map a term to appropriate concepts.

        Args:
            term: Term to map
        """
        # Direct domain-based mapping
        for domain in term.domains:
            if domain == 'unit_of_individuality':
                self._add_term_to_concept(term.text, 'biological_individuality')
            elif domain in ['power_and_labor', 'behavior_and_identity']:
                self._add_term_to_concept(term.text, 'social_organization')
            elif domain == 'sex_and_reproduction':
                self._add_term_to_concept(term.text, 'reproductive_biology')
            elif domain == 'kin_and_relatedness':
                self._add_term_to_concept(term.text, 'kinship_systems')
            elif domain == 'economics':
                self._add_term_to_concept(term.text, 'resource_economics')

        # Cross-domain mapping for behavioral ecology
        if ('behavior_and_identity' in term.domains or
            'economics' in term.domains):
            self._add_term_to_concept(term.text, 'behavioral_ecology')

        # Semantic pattern-based mapping
        self._semantic_concept_mapping(term)

    def _add_term_to_concept(self, term: str, concept_name: str) -> None:
        """Add a term to a concept, creating the concept if needed.

        Args:
            term: Term to add
            concept_name: Concept name
        """
        if concept_name not in self.concept_map.concepts:
            # Create new concept if it doesn't exist
            concept = Concept(
                name=concept_name,
                description=f"Concept derived from term mapping: {concept_name}"
            )
            self.concept_map.add_concept(concept)

        self.concept_map.concepts[concept_name].add_term(term)

    def _semantic_concept_mapping(self, term: Term) -> None:
        """Map terms to concepts based on semantic patterns.

        Args:
            term: Term to map semantically
        """
        term_lower = term.text.lower()

        # Individuality concepts
        if any(word in term_lower for word in ['unit', 'entity', 'organism', 'individual']):
            self._add_term_to_concept(term.text, 'biological_individuality')

        # Social concepts
        if any(word in term_lower for word in ['social', 'group', 'collective', 'society']):
            self._add_term_to_concept(term.text, 'social_organization')

        # Reproductive concepts
        if any(word in term_lower for word in ['reproduce', 'mating', 'fertil', 'egg']):
            self._add_term_to_concept(term.text, 'reproductive_biology')

        # Kinship concepts
        if any(word in term_lower for word in ['kin', 'relative', 'family', 'sib']):
            self._add_term_to_concept(term.text, 'kinship_systems')

        # Economic concepts
        if any(word in term_lower for word in ['resource', 'cost', 'benefit', 'value']):
            self._add_term_to_concept(term.text, 'resource_economics')

        # Behavioral concepts
        if any(word in term_lower for word in ['behavior', 'action', 'response', 'adaptation']):
            self._add_term_to_concept(term.text, 'behavioral_ecology')

    def _build_concept_relationships(self) -> None:
        """Build relationships between concepts based on term overlaps."""
        overlaps = self.concept_map.find_concept_overlaps()

        for (concept1, concept2), overlapping_terms in overlaps.items():
            # Relationship strength based on overlap size
            overlap_ratio = len(overlapping_terms) / min(
                len(self.concept_map.get_concept_terms(concept1)),
                len(self.concept_map.get_concept_terms(concept2))
            )

            self.concept_map.add_relationship(concept1, concept2, overlap_ratio)

    def identify_conceptual_boundaries(self) -> Dict[str, Dict[str, Any]]:
        """Identify conceptual boundaries and overlaps between domains.

        Returns:
            Dictionary with boundary analysis
        """
        boundaries = {}

        # Analyze each concept
        for concept_name, concept in self.concept_map.concepts.items():
            # Find bridging terms (terms in multiple concepts)
            bridging_terms = set()
            for term in concept.terms:
                if len(self.concept_map.get_term_concepts(term)) > 1:
                    bridging_terms.add(term)

            # Calculate boundary strength
            boundary_strength = len(bridging_terms) / len(concept.terms) if concept.terms else 0

            boundaries[concept_name] = {
                'bridging_terms': bridging_terms,
                'boundary_strength': boundary_strength,
                'domain_spread': len(concept.domains),
                'connected_concepts': self._get_connected_concepts(concept_name)
            }

        return boundaries

    def _get_connected_concepts(self, concept_name: str) -> List[Tuple[str, float]]:
        """Get concepts connected to the given concept.

        Args:
            concept_name: Concept to analyze

        Returns:
            List of (connected_concept, weight) tuples
        """
        connected = []
        for (c1, c2), weight in self.concept_map.concept_relationships.items():
            if c1 == concept_name:
                connected.append((c2, weight))
            elif c2 == concept_name:
                connected.append((c1, weight))

        return sorted(connected, key=lambda x: x[1], reverse=True)

    def analyze_conceptual_hierarchy(self) -> Dict[str, Any]:
        """Analyze the hierarchical structure of concepts.

        Returns:
            Dictionary with hierarchy analysis
        """
        # Calculate concept centrality
        centrality = {}
        for concept_name in self.concept_map.concepts:
            connected_concepts = self._get_connected_concepts(concept_name)
            centrality[concept_name] = len(connected_concepts)

        # Identify core vs peripheral concepts
        centrality_values = list(centrality.values())
        if centrality_values:
            centrality_threshold = sum(centrality_values) / len(centrality_values)
            core_concepts = [c for c, cent in centrality.items() if cent > centrality_threshold]
            peripheral_concepts = [c for c, cent in centrality.items() if cent <= centrality_threshold]
        else:
            core_concepts = []
            peripheral_concepts = []

        return {
            'centrality_scores': centrality,
            'core_concepts': core_concepts,
            'peripheral_concepts': peripheral_concepts,
            'hierarchy_depth': self._calculate_hierarchy_depth()
        }

    def _calculate_hierarchy_depth(self) -> int:
        """Calculate the depth of the concept hierarchy.

        Returns:
            Maximum hierarchy depth
        """
        # Simple depth calculation based on parent-child relationships
        depths = {}
        for concept in self.concept_map.concepts.values():
            if not concept.parent_concepts:
                depths[concept.name] = 0
            else:
                # Approximate depth as number of parent relationships
                depths[concept.name] = len(concept.parent_concepts)

        return max(depths.values()) if depths else 0

    def detect_anthropomorphic_concepts(self) -> Dict[str, List[str]]:
        """Detect concepts that carry anthropomorphic assumptions.

        Returns:
            Dictionary mapping concept types to term lists
        """
        anthropomorphic_indicators = {
            'agency': ['choose', 'decide', 'prefer', 'select', 'opt'],
            'communication': ['communicate', 'signal', 'inform', 'warn'],
            'social_contract': ['cooperate', 'compete', 'negotiate', 'trade'],
            'cognition': ['recognize', 'identify', 'distinguish', 'know'],
            'hierarchy': ['superior', 'inferior', 'dominant', 'subordinate']
        }

        detected = defaultdict(list)

        for concept_name, concept in self.concept_map.concepts.items():
            for term in concept.terms:
                term_lower = term.lower()
                for category, indicators in anthropomorphic_indicators.items():
                    if any(indicator in term_lower for indicator in indicators):
                        detected[category].append(term)

        return dict(detected)

    def export_concept_map_json(self, filepath: str) -> None:
        """Export concept map to JSON file.

        Args:
            filepath: Path to output JSON file
        """
        import json

        data = {
            'concepts': {name: concept.to_dict() for name, concept in self.concept_map.concepts.items()},
            'term_mappings': {k: list(v) for k, v in self.concept_map.term_to_concepts.items()},
            'relationships': [{'concepts': list(k), 'weight': v}
                            for k, v in self.concept_map.concept_relationships.items()]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def find_concept_gaps(self, domain_terms: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Identify conceptual gaps where domains lack corresponding concepts.

        Args:
            domain_terms: Dictionary mapping domains to their terms

        Returns:
            Dictionary of gaps by domain
        """
        gaps = {}

        for domain, terms in domain_terms.items():
            mapped_terms = set()
            for term in terms:
                mapped_terms.update(self.concept_map.get_term_concepts(term))

            if not mapped_terms:
                gaps[domain] = terms
            else:
                # Find unmapped terms
                unmapped = []
                for term in terms:
                    if not self.concept_map.get_term_concepts(term):
                        unmapped.append(term)
                if unmapped:
                    gaps[domain] = unmapped

        return gaps
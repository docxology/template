"""Domain analysis for Ento-Linguistic research.

This module provides specialized analysis functions for each of the six
Ento-Linguistic domains, examining how terminology structures understanding
within specific conceptual areas.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field

try:
    from .term_extraction import Term
    from .text_analysis import TextProcessor, LinguisticFeatureExtractor
except ImportError:
    from term_extraction import Term
    from text_analysis import TextProcessor, LinguisticFeatureExtractor


@dataclass
class DomainAnalysis:
    """Results of domain-specific analysis.

    Attributes:
        domain_name: Name of the Ento-Linguistic domain
        key_terms: Most important terms in this domain
        term_patterns: Common linguistic patterns
        framing_assumptions: Identified framing assumptions
        conceptual_structure: How concepts are organized
        ambiguities: Identified ambiguities and their contexts
        recommendations: Suggestions for clearer communication
    """
    domain_name: str
    key_terms: List[str] = field(default_factory=list)
    term_patterns: Dict[str, int] = field(default_factory=dict)
    framing_assumptions: List[str] = field(default_factory=list)
    conceptual_structure: Dict[str, Any] = field(default_factory=dict)
    ambiguities: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class DomainAnalyzer:
    """Analyze terminology within specific Ento-Linguistic domains.

    This class provides domain-specific analysis methods that examine
    how terminology structures understanding within each of the six domains.
    """

    def __init__(self):
        """Initialize domain analyzer."""
        self.text_processor = TextProcessor()
        self.feature_extractor = LinguisticFeatureExtractor()

    def analyze_all_domains(self, terms: Dict[str, Term],
                          texts: List[str]) -> Dict[str, DomainAnalysis]:
        """Analyze all six Ento-Linguistic domains.

        Args:
            terms: Dictionary of extracted terms
            texts: Source texts for context

        Returns:
            Dictionary mapping domain names to analysis results

        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not isinstance(terms, dict):
            raise ValueError("terms must be a dictionary")
        if not isinstance(texts, list):
            raise ValueError("texts must be a list")
        if not terms:
            return {}  # Nothing to analyze

        domain_analyses = {}

        # Group terms by domain
        domain_terms = self._group_terms_by_domain(terms)

        # Analyze each domain
        domain_methods = {
            'unit_of_individuality': self._analyze_individuality_domain,
            'behavior_and_identity': self._analyze_behavior_domain,
            'power_and_labor': self._analyze_power_domain,
            'sex_and_reproduction': self._analyze_reproduction_domain,
            'kin_and_relatedness': self._analyze_kinship_domain,
            'economics': self._analyze_economics_domain
        }

        for domain_name, terms_list in domain_terms.items():
            if domain_name in domain_methods:
                analysis = domain_methods[domain_name](terms_list, texts)
                domain_analyses[domain_name] = analysis

        return domain_analyses

    def _group_terms_by_domain(self, terms: Dict[str, Term]) -> Dict[str, List[Term]]:
        """Group terms by their Ento-Linguistic domains.

        Args:
            terms: Dictionary of terms

        Returns:
            Dictionary mapping domain names to term lists
        """
        domain_groups = defaultdict(list)

        for term in terms.values():
            for domain in term.domains:
                domain_groups[domain].append(term)

        return dict(domain_groups)

    def _analyze_individuality_domain(self, terms: List[Term],
                                    texts: List[str]) -> DomainAnalysis:
        """Analyze the Unit of Individuality domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name='unit_of_individuality')

        # Key terms analysis
        term_texts = [term.text for term in terms]
        analysis.key_terms = self._extract_key_terms(term_texts, top_n=10)

        # Pattern analysis
        analysis.term_patterns = self._analyze_term_patterns(terms)

        # Framing assumptions
        analysis.framing_assumptions = [
            "Individuality exists on a single biological scale",
            "Colony-level traits are emergent rather than individual",
            "Superorganism concept implies loss of individual agency",
            "Nestmate recognition defines individual boundaries"
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            'scale_hierarchy': ['gene', 'cell', 'organism', 'colony', 'population'],
            'individuality_types': ['genetic', 'physiological', 'behavioral', 'social'],
            'boundary_concepts': ['recognition', 'kinship', 'cooperation', 'conflict']
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                'term': 'colony',
                'contexts': ['reproductive unit', 'behavioral entity', 'ecological unit'],
                'issue': 'Shifts meaning across biological scales'
            },
            {
                'term': 'individual',
                'contexts': ['nestmate', 'colony member', 'genetic individual'],
                'issue': 'Multiple biological scales of individuality'
            }
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify biological scale when using individuality terms",
            "Distinguish between genetic, physiological, and social individuality",
            "Use 'colony-level' vs 'individual-level' traits explicitly",
            "Avoid assuming single scale of biological organization"
        ]

        return analysis

    def _analyze_behavior_domain(self, terms: List[Term],
                               texts: List[str]) -> DomainAnalysis:
        """Analyze the Behavior and Identity domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name='behavior_and_identity')

        # Key terms
        term_texts = [term.text for term in terms]
        analysis.key_terms = self._extract_key_terms(term_texts, top_n=10)

        # Pattern analysis
        analysis.term_patterns = self._analyze_term_patterns(terms)

        # Framing assumptions
        analysis.framing_assumptions = [
            "Behavioral categories reflect discrete identities",
            "Task performance defines individual identity",
            "Behavioral specialization is fixed and heritable",
            "Foraging behavior indicates specialized role"
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            'identity_types': ['task-based', 'age-based', 'size-based', 'genetic'],
            'behavior_categories': ['foraging', 'nursing', 'defense', 'reproduction'],
            'plasticity_concepts': ['developmental', 'environmental', 'social']
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                'term': 'forager',
                'contexts': ['observed carrying food', 'genetically predisposed', 'temporarily assigned'],
                'issue': 'Identity vs behavior vs observation'
            },
            {
                'term': 'worker',
                'contexts': ['sterile female', 'non-reproductive adult', 'task-performing individual'],
                'issue': 'Reproductive status vs behavioral role'
            }
        ]

        # Recommendations
        analysis.recommendations = [
            "Distinguish between behavioral observations and identities",
            "Specify whether roles are fixed or plastic",
            "Use 'behavioral specialization' rather than 'caste identity'",
            "Avoid assuming heritability of behavioral roles"
        ]

        return analysis

    def _analyze_power_domain(self, terms: List[Term],
                            texts: List[str]) -> DomainAnalysis:
        """Analyze the Power & Labor domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name='power_and_labor')

        # Key terms
        term_texts = [term.text for term in terms]
        analysis.key_terms = self._extract_key_terms(term_texts, top_n=10)

        # Pattern analysis
        analysis.term_patterns = self._analyze_term_patterns(terms)

        # Framing assumptions
        analysis.framing_assumptions = [
            "Social organization mirrors human hierarchical structures",
            "Power relationships are analogous to human societies",
            "Labor division reflects inherent inequalities",
            "Queen dominance implies worker subordination"
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            'power_types': ['reproductive', 'behavioral', 'resource', 'spatial'],
            'hierarchy_levels': ['queen', 'major workers', 'minor workers', 'soldiers'],
            'control_mechanisms': ['chemical', 'behavioral', 'physical', 'genetic']
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                'term': 'caste',
                'contexts': ['morphological difference', 'behavioral role', 'social status'],
                'issue': 'Biological vs social category'
            },
            {
                'term': 'slave',
                'contexts': ['captured worker', 'social parasite', 'metaphorical usage'],
                'issue': 'Biological relationship vs human analogy'
            }
        ]

        # Recommendations
        analysis.recommendations = [
            "Use 'morphological caste' or 'behavioral caste' explicitly",
            "Avoid human social terms like 'slave' and 'parasite'",
            "Specify mechanisms of social control",
            "Use 'reproductive skew' rather than 'queen dominance'"
        ]

        return analysis

    def _analyze_reproduction_domain(self, terms: List[Term],
                                   texts: List[str]) -> DomainAnalysis:
        """Analyze the Sex & Reproduction domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name='sex_and_reproduction')

        # Key terms
        term_texts = [term.text for term in terms]
        analysis.key_terms = self._extract_key_terms(term_texts, top_n=10)

        # Pattern analysis
        analysis.term_patterns = self._analyze_term_patterns(terms)

        # Framing assumptions
        analysis.framing_assumptions = [
            "Sex determination follows binary human model",
            "Reproductive roles determine social status",
            "Mating systems analogous to human relationships",
            "Parental investment follows human patterns"
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            'sex_systems': ['haplodiploidy', 'environmental sex determination', 'genetic sex determination'],
            'reproductive_strategies': ['monogamy', 'polygyny', 'polyandry', 'clonal reproduction'],
            'mating_systems': ['monogyny', 'polygyny', 'pleometrosis', 'secondary monogyny']
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                'term': 'sex determination',
                'contexts': ['chromosomal', 'environmental', 'social'],
                'issue': 'Multiple mechanisms conflated'
            },
            {
                'term': 'female',
                'contexts': ['reproductive queen', 'sterile worker', 'developmental stage'],
                'issue': 'Reproductive capacity vs morphological sex'
            }
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify mechanism of sex determination",
            "Use 'reproductive female' vs 'morphological female'",
            "Avoid assuming binary sex determination",
            "Specify reproductive strategy explicitly"
        ]

        return analysis

    def _analyze_kinship_domain(self, terms: List[Term],
                              texts: List[str]) -> DomainAnalysis:
        """Analyze the Kin & Relatedness domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name='kin_and_relatedness')

        # Key terms
        term_texts = [term.text for term in terms]
        analysis.key_terms = self._extract_key_terms(term_texts, top_n=10)

        # Pattern analysis
        analysis.term_patterns = self._analyze_term_patterns(terms)

        # Framing assumptions
        analysis.framing_assumptions = [
            "Kinship follows human family structures",
            "Relatedness is primarily genetic",
            "Kin recognition requires genetic similarity",
            "Family relationships mirror human patterns"
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            'relatedness_types': ['genetic', 'phenotypic', 'environmental', 'social'],
            'kinship_mechanisms': ['recognition', 'discrimination', 'cooperation', 'conflict'],
            'relatedness_measures': ['coefficient', 'distance', 'similarity', 'correlation']
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                'term': 'kin',
                'contexts': ['genetic relatives', 'social affiliates', 'colony members'],
                'issue': 'Genetic vs social kinship'
            },
            {
                'term': 'family',
                'contexts': ['nuclear family', 'colony kin group', 'mating pair'],
                'issue': 'Human family structures vs insect groupings'
            }
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify type of relatedness (genetic, social, environmental)",
            "Use 'relatedness coefficient' for genetic measures",
            "Avoid 'family' for insect groupings",
            "Specify mechanisms of kin recognition"
        ]

        return analysis

    def _analyze_economics_domain(self, terms: List[Term],
                                texts: List[str]) -> DomainAnalysis:
        """Analyze the Economics domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name='economics')

        # Key terms
        term_texts = [term.text for term in terms]
        analysis.key_terms = self._extract_key_terms(term_texts, top_n=10)

        # Pattern analysis
        analysis.term_patterns = self._analyze_term_patterns(terms)

        # Framing assumptions
        analysis.framing_assumptions = [
            "Colony economics mirror human market systems",
            "Resource allocation follows market principles",
            "Costs and benefits analogous to human economics",
            "Optimization implies conscious decision-making"
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            'resource_types': ['food', 'space', 'information', 'social capital'],
            'allocation_mechanisms': ['competition', 'cooperation', 'division of labor', 'storage'],
            'economic_measures': ['efficiency', 'productivity', 'cost-benefit', 'optimization']
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                'term': 'trade',
                'contexts': ['resource exchange', 'trophallaxis', 'metaphorical usage'],
                'issue': 'Biological exchange vs economic metaphor'
            },
            {
                'term': 'cost',
                'contexts': ['energetic expenditure', 'risk', 'opportunity cost'],
                'issue': 'Multiple types of costs conflated'
            }
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify type of resource allocation mechanism",
            "Use 'resource exchange' rather than 'trade'",
            "Specify cost type (energetic, risk, opportunity)",
            "Avoid assuming conscious economic decision-making"
        ]

        return analysis

    def _extract_key_terms(self, term_texts: List[str], top_n: int = 10) -> List[str]:
        """Extract most important terms by frequency.

        Args:
            term_texts: List of term texts
            top_n: Number of top terms to return

        Returns:
            List of top terms
        """
        term_counts = Counter(term_texts)
        return [term for term, _ in term_counts.most_common(top_n)]

    def _analyze_term_patterns(self, terms: List[Term]) -> Dict[str, int]:
        """Analyze linguistic patterns in terms.

        Args:
            terms: List of terms to analyze

        Returns:
            Dictionary of pattern counts
        """
        patterns = Counter()

        for term in terms:
            # Compound words
            if '_' in term.text or '-' in term.text:
                patterns['compound'] += 1

            # Multi-word terms
            if ' ' in term.text:
                patterns['multi_word'] += 1

            # Capitalized terms
            if term.text[0].isupper():
                patterns['capitalized'] += 1

            # Scientific abbreviations
            if re.match(r'^[A-Z]{2,}$', term.text):
                patterns['abbreviation'] += 1

            # Number-containing terms
            if any(char.isdigit() for char in term.text):
                patterns['numeric'] += 1

        return dict(patterns)

    def generate_domain_report(self, analysis: DomainAnalysis) -> str:
        """Generate a human-readable report for domain analysis.

        Args:
            analysis: Domain analysis results

        Returns:
            Formatted report string
        """
        report = f"""
# {analysis.domain_name.replace('_', ' ').title()} Domain Analysis

## Key Terms
{', '.join(analysis.key_terms)}

## Term Patterns
{chr(10).join(f"- {pattern}: {count}" for pattern, count in analysis.term_patterns.items())}

## Framing Assumptions
{chr(10).join(f"- {assumption}" for assumption in analysis.framing_assumptions)}

## Ambiguities Identified
{chr(10).join(f"- **{amb['term']}**: {amb['issue']} (contexts: {', '.join(amb['contexts'])})" for amb in analysis.ambiguities)}

## Recommendations
{chr(10).join(f"- {rec}" for rec in analysis.recommendations)}
"""
        return report

    def compare_domains(self, analyses: Dict[str, DomainAnalysis]) -> Dict[str, Any]:
        """Compare patterns across domains.

        Args:
            analyses: Dictionary of domain analyses

        Returns:
            Comparison results
        """
        comparison = {
            'domain_sizes': {name: len(analysis.key_terms) for name, analysis in analyses.items()},
            'shared_assumptions': self._find_shared_assumptions(analyses),
            'cross_domain_ambiguities': self._find_cross_domain_issues(analyses)
        }

        return comparison

    def _find_shared_assumptions(self, analyses: Dict[str, DomainAnalysis]) -> List[str]:
        """Find assumptions shared across domains.

        Args:
            analyses: Domain analyses

        Returns:
            List of shared assumptions
        """
        all_assumptions = []
        for analysis in analyses.values():
            all_assumptions.extend(analysis.framing_assumptions)

        assumption_counts = Counter(all_assumptions)
        shared = [assumption for assumption, count in assumption_counts.items() if count > 1]

        return shared

    def _find_cross_domain_issues(self, analyses: Dict[str, DomainAnalysis]) -> List[Dict[str, Any]]:
        """Find issues that span multiple domains.

        Args:
            analyses: Domain analyses

        Returns:
            List of cross-domain issues
        """
        # This would identify terms or concepts that appear in multiple domains
        # with conflicting meanings - simplified implementation
        cross_domain_issues = [
            {
                'issue': 'Anthropomorphic framing across domains',
                'affected_domains': ['power_and_labor', 'behavior_and_identity', 'economics'],
                'description': 'Human social concepts applied to insect societies'
            }
        ]

        return cross_domain_issues
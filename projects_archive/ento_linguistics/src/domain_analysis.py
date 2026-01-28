"""Domain analysis for Ento-Linguistic research.

This module provides specialized analysis functions for each of the six
Ento-Linguistic domains, examining how terminology structures understanding
within specific conceptual areas.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

try:
    from .term_extraction import Term
    from .text_analysis import LinguisticFeatureExtractor, TextProcessor
except ImportError:
    from term_extraction import Term
    from text_analysis import LinguisticFeatureExtractor, TextProcessor


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
        frequency_stats: Statistical analysis of term frequencies
        cooccurrence_analysis: Term co-occurrence patterns
        ambiguity_metrics: Quantified ambiguity metrics
        confidence_scores: Confidence scores for framing assumptions
        conceptual_metrics: Quantitative metrics for conceptual structure
        statistical_significance: Statistical significance of term patterns
    """

    domain_name: str
    key_terms: List[str] = field(default_factory=list)
    term_patterns: Dict[str, int] = field(default_factory=dict)
    framing_assumptions: List[str] = field(default_factory=list)
    conceptual_structure: Dict[str, Any] = field(default_factory=dict)
    ambiguities: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    frequency_stats: Dict[str, Any] = field(default_factory=dict)
    cooccurrence_analysis: Dict[str, Any] = field(default_factory=dict)
    ambiguity_metrics: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    conceptual_metrics: Dict[str, Any] = field(default_factory=dict)
    statistical_significance: Dict[str, Any] = field(default_factory=dict)


class DomainAnalyzer:
    """Analyze terminology within specific Ento-Linguistic domains.

    This class provides domain-specific analysis methods that examine
    how terminology structures understanding within each of the six domains.
    """

    def __init__(self):
        """Initialize domain analyzer."""
        self.text_processor = TextProcessor()
        self.feature_extractor = LinguisticFeatureExtractor()

    def analyze_all_domains(
        self, terms: Dict[str, Term], texts: List[str]
    ) -> Dict[str, DomainAnalysis]:
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
            "unit_of_individuality": self._analyze_individuality_domain,
            "behavior_and_identity": self._analyze_behavior_domain,
            "power_and_labor": self._analyze_power_domain,
            "sex_and_reproduction": self._analyze_reproduction_domain,
            "kin_and_relatedness": self._analyze_kinship_domain,
            "economics": self._analyze_economics_domain,
        }

        for domain_name, terms_list in domain_terms.items():
            if domain_name in domain_methods:
                analysis = domain_methods[domain_name](terms_list, texts)

                # Add statistical analysis
                analysis.frequency_stats = self.analyze_term_frequency_distribution(
                    terms_list, texts
                )
                analysis.cooccurrence_analysis = self.analyze_term_cooccurrence(
                    terms_list, texts
                )
                analysis.ambiguity_metrics = self.quantify_ambiguity_metrics(
                    terms_list, texts
                )
                analysis.confidence_scores = self.generate_confidence_scores(
                    analysis.framing_assumptions, terms_list, texts
                )
                analysis.conceptual_metrics = self.quantify_conceptual_structure(
                    analysis.conceptual_structure, terms_list
                )
                analysis.statistical_significance = (
                    self.calculate_statistical_significance(analysis.term_patterns)
                )

                domain_analyses[domain_name] = analysis

        # Add cross-domain analysis
        if len(domain_analyses) > 1:
            cross_domain_analysis = self.analyze_cross_domain_overlap(
                domain_terms, terms
            )
            # Store in a special key
            domain_analyses["_cross_domain"] = cross_domain_analysis

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

    def _analyze_individuality_domain(
        self, terms: List[Term], texts: List[str]
    ) -> DomainAnalysis:
        """Analyze the Unit of Individuality domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name="unit_of_individuality")

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
            "Nestmate recognition defines individual boundaries",
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            "scale_hierarchy": ["gene", "cell", "organism", "colony", "population"],
            "individuality_types": ["genetic", "physiological", "behavioral", "social"],
            "boundary_concepts": ["recognition", "kinship", "cooperation", "conflict"],
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                "term": "colony",
                "contexts": [
                    "reproductive unit",
                    "behavioral entity",
                    "ecological unit",
                ],
                "issue": "Shifts meaning across biological scales",
            },
            {
                "term": "individual",
                "contexts": ["nestmate", "colony member", "genetic individual"],
                "issue": "Multiple biological scales of individuality",
            },
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify biological scale when using individuality terms",
            "Distinguish between genetic, physiological, and social individuality",
            "Use 'colony-level' vs 'individual-level' traits explicitly",
            "Avoid assuming single scale of biological organization",
        ]

        return analysis

    def _analyze_behavior_domain(
        self, terms: List[Term], texts: List[str]
    ) -> DomainAnalysis:
        """Analyze the Behavior and Identity domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name="behavior_and_identity")

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
            "Foraging behavior indicates specialized role",
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            "identity_types": ["task-based", "age-based", "size-based", "genetic"],
            "behavior_categories": ["foraging", "nursing", "defense", "reproduction"],
            "plasticity_concepts": ["developmental", "environmental", "social"],
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                "term": "forager",
                "contexts": [
                    "observed carrying food",
                    "genetically predisposed",
                    "temporarily assigned",
                ],
                "issue": "Identity vs behavior vs observation",
            },
            {
                "term": "worker",
                "contexts": [
                    "sterile female",
                    "non-reproductive adult",
                    "task-performing individual",
                ],
                "issue": "Reproductive status vs behavioral role",
            },
        ]

        # Recommendations
        analysis.recommendations = [
            "Distinguish between behavioral observations and identities",
            "Specify whether roles are fixed or plastic",
            "Use 'behavioral specialization' rather than 'caste identity'",
            "Avoid assuming heritability of behavioral roles",
        ]

        return analysis

    def _analyze_power_domain(
        self, terms: List[Term], texts: List[str]
    ) -> DomainAnalysis:
        """Analyze the Power & Labor domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name="power_and_labor")

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
            "Queen dominance implies worker subordination",
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            "power_types": ["reproductive", "behavioral", "resource", "spatial"],
            "hierarchy_levels": ["queen", "major workers", "minor workers", "soldiers"],
            "control_mechanisms": ["chemical", "behavioral", "physical", "genetic"],
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                "term": "caste",
                "contexts": [
                    "morphological difference",
                    "behavioral role",
                    "social status",
                ],
                "issue": "Biological vs social category",
            },
            {
                "term": "slave",
                "contexts": [
                    "captured worker",
                    "social parasite",
                    "metaphorical usage",
                ],
                "issue": "Biological relationship vs human analogy",
            },
        ]

        # Recommendations
        analysis.recommendations = [
            "Use 'morphological caste' or 'behavioral caste' explicitly",
            "Avoid human social terms like 'slave' and 'parasite'",
            "Specify mechanisms of social control",
            "Use 'reproductive skew' rather than 'queen dominance'",
        ]

        return analysis

    def _analyze_reproduction_domain(
        self, terms: List[Term], texts: List[str]
    ) -> DomainAnalysis:
        """Analyze the Sex & Reproduction domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name="sex_and_reproduction")

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
            "Parental investment follows human patterns",
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            "sex_systems": [
                "haplodiploidy",
                "environmental sex determination",
                "genetic sex determination",
            ],
            "reproductive_strategies": [
                "monogamy",
                "polygyny",
                "polyandry",
                "clonal reproduction",
            ],
            "mating_systems": [
                "monogyny",
                "polygyny",
                "pleometrosis",
                "secondary monogyny",
            ],
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                "term": "sex determination",
                "contexts": ["chromosomal", "environmental", "social"],
                "issue": "Multiple mechanisms conflated",
            },
            {
                "term": "female",
                "contexts": [
                    "reproductive queen",
                    "sterile worker",
                    "developmental stage",
                ],
                "issue": "Reproductive capacity vs morphological sex",
            },
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify mechanism of sex determination",
            "Use 'reproductive female' vs 'morphological female'",
            "Avoid assuming binary sex determination",
            "Specify reproductive strategy explicitly",
        ]

        return analysis

    def _analyze_kinship_domain(
        self, terms: List[Term], texts: List[str]
    ) -> DomainAnalysis:
        """Analyze the Kin & Relatedness domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name="kin_and_relatedness")

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
            "Family relationships mirror human patterns",
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            "relatedness_types": ["genetic", "phenotypic", "environmental", "social"],
            "kinship_mechanisms": [
                "recognition",
                "discrimination",
                "cooperation",
                "conflict",
            ],
            "relatedness_measures": [
                "coefficient",
                "distance",
                "similarity",
                "correlation",
            ],
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                "term": "kin",
                "contexts": [
                    "genetic relatives",
                    "social affiliates",
                    "colony members",
                ],
                "issue": "Genetic vs social kinship",
            },
            {
                "term": "family",
                "contexts": ["nuclear family", "colony kin group", "mating pair"],
                "issue": "Human family structures vs insect groupings",
            },
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify type of relatedness (genetic, social, environmental)",
            "Use 'relatedness coefficient' for genetic measures",
            "Avoid 'family' for insect groupings",
            "Specify mechanisms of kin recognition",
        ]

        return analysis

    def _analyze_economics_domain(
        self, terms: List[Term], texts: List[str]
    ) -> DomainAnalysis:
        """Analyze the Economics domain.

        Args:
            terms: Terms in this domain
            texts: Source texts

        Returns:
            Domain analysis results
        """
        analysis = DomainAnalysis(domain_name="economics")

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
            "Optimization implies conscious decision-making",
        ]

        # Conceptual structure
        analysis.conceptual_structure = {
            "resource_types": ["food", "space", "information", "social capital"],
            "allocation_mechanisms": [
                "competition",
                "cooperation",
                "division of labor",
                "storage",
            ],
            "economic_measures": [
                "efficiency",
                "productivity",
                "cost-benefit",
                "optimization",
            ],
        }

        # Ambiguities
        analysis.ambiguities = [
            {
                "term": "trade",
                "contexts": ["resource exchange", "trophallaxis", "metaphorical usage"],
                "issue": "Biological exchange vs economic metaphor",
            },
            {
                "term": "cost",
                "contexts": ["energetic expenditure", "risk", "opportunity cost"],
                "issue": "Multiple types of costs conflated",
            },
        ]

        # Recommendations
        analysis.recommendations = [
            "Specify type of resource allocation mechanism",
            "Use 'resource exchange' rather than 'trade'",
            "Specify cost type (energetic, risk, opportunity)",
            "Avoid assuming conscious economic decision-making",
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
            if "_" in term.text or "-" in term.text:
                patterns["compound"] += 1

            # Multi-word terms
            if " " in term.text:
                patterns["multi_word"] += 1

            # Capitalized terms
            if term.text[0].isupper():
                patterns["capitalized"] += 1

            # Scientific abbreviations
            if re.match(r"^[A-Z]{2,}$", term.text):
                patterns["abbreviation"] += 1

            # Number-containing terms
            if any(char.isdigit() for char in term.text):
                patterns["numeric"] += 1

        return dict(patterns)

    def generate_domain_report(self, analysis) -> str:
        """Generate a human-readable report for domain analysis.

        Args:
            analysis: Domain analysis results (DomainAnalysis object or dict)

        Returns:
            Formatted report string
        """
        # Handle both dict and DomainAnalysis object inputs
        if isinstance(analysis, dict):
            domain_name = analysis.get("domain_name", "unknown")
            key_terms = analysis.get("key_terms", [])
            term_patterns = analysis.get("term_patterns", {})
            framing_assumptions = analysis.get("framing_assumptions", [])
            ambiguities = analysis.get("ambiguities", [])
            recommendations = analysis.get("recommendations", [])
        else:
            # DomainAnalysis object
            domain_name = analysis.domain_name
            key_terms = analysis.key_terms
            term_patterns = analysis.term_patterns
            framing_assumptions = analysis.framing_assumptions
            ambiguities = analysis.ambiguities
            recommendations = analysis.recommendations

        report = f"""
# {domain_name.replace('_', ' ').title()} Domain Analysis

## Key Terms
{', '.join(key_terms)}

## Term Patterns
{chr(10).join(f"- {pattern}: {count}" for pattern, count in term_patterns.items())}

## Framing Assumptions
{chr(10).join(f"- {assumption}" for assumption in framing_assumptions)}

## Ambiguities Identified
{chr(10).join(f"- **{amb['term']}**: {amb['issue']} (contexts: {', '.join(amb['contexts'])})" for amb in ambiguities)}

## Recommendations
{chr(10).join(f"- {rec}" for rec in recommendations)}
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
            "domain_sizes": {
                name: len(analysis.key_terms) for name, analysis in analyses.items()
            },
            "shared_assumptions": self._find_shared_assumptions(analyses),
            "cross_domain_ambiguities": self._find_cross_domain_issues(analyses),
        }

        return comparison

    def _find_shared_assumptions(
        self, analyses: Dict[str, DomainAnalysis]
    ) -> List[str]:
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
        shared = [
            assumption for assumption, count in assumption_counts.items() if count > 1
        ]

        return shared

    def _find_cross_domain_issues(
        self, analyses: Dict[str, DomainAnalysis]
    ) -> List[Dict[str, Any]]:
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
                "issue": "Anthropomorphic framing across domains",
                "affected_domains": [
                    "power_and_labor",
                    "behavior_and_identity",
                    "economics",
                ],
                "description": "Human social concepts applied to insect societies",
            }
        ]

        return cross_domain_issues

    def analyze_term_frequency_distribution(
        self, terms: List[Term], texts: List[str]
    ) -> Dict[str, Any]:
        """Analyze term frequency distributions within domains.

        Args:
            terms: List of terms to analyze
            texts: Source texts for context

        Returns:
            Statistical analysis of term frequencies
        """
        from collections import Counter

        import numpy as np

        # Extract term frequencies
        term_freqs = [term.frequency for term in terms]
        term_texts = [term.text for term in terms]

        # Basic statistics
        if term_freqs:
            stats = {
                "mean_frequency": np.mean(term_freqs),
                "median_frequency": np.median(term_freqs),
                "std_frequency": np.std(term_freqs),
                "min_frequency": min(term_freqs),
                "max_frequency": max(term_freqs),
                "total_occurrences": sum(term_freqs),
                "unique_terms": len(term_freqs),
            }

            # Frequency distribution
            hist, bin_edges = np.histogram(term_freqs, bins="auto")
            stats["frequency_distribution"] = {
                "bins": bin_edges.tolist(),
                "counts": hist.tolist(),
            }

            # Most frequent terms
            sorted_terms = sorted(
                zip(term_texts, term_freqs), key=lambda x: x[1], reverse=True
            )
            stats["top_terms"] = [
                {"term": term, "frequency": freq} for term, freq in sorted_terms[:10]
            ]

        else:
            stats = {"error": "No terms provided for analysis"}

        return stats

    def analyze_term_cooccurrence(
        self, terms: List[Term], texts: List[str], window_size: int = 50
    ) -> Dict[str, Any]:
        """Analyze co-occurrence patterns between terms.

        Args:
            terms: List of terms to analyze
            texts: Source texts for context
            window_size: Size of co-occurrence window

        Returns:
            Co-occurrence analysis results
        """
        from collections import defaultdict

        import numpy as np

        term_texts = [term.text.lower() for term in terms]
        cooccurrence_matrix = defaultdict(lambda: defaultdict(int))

        # Build co-occurrence matrix
        for text in texts:
            words = text.lower().split()
            for i, word1 in enumerate(words):
                if word1 in term_texts:
                    # Look for co-occurring terms within window
                    start = max(0, i - window_size // 2)
                    end = min(len(words), i + window_size // 2 + 1)

                    for j in range(start, end):
                        if i != j:
                            word2 = words[j]
                            if word2 in term_texts:
                                cooccurrence_matrix[word1][word2] += 1

        # Convert to regular dict for JSON serialization
        cooccurrence_dict = {}
        for term1, cooccurs in cooccurrence_matrix.items():
            cooccurrence_dict[term1] = dict(cooccurs)

        # Calculate co-occurrence statistics
        total_cooccurrences = sum(
            sum(counts.values()) for counts in cooccurrence_matrix.values()
        )

        return {
            "cooccurrence_matrix": cooccurrence_dict,
            "total_cooccurrences": total_cooccurrences,
            "unique_term_pairs": len(cooccurrence_dict),
            "average_cooccurrences_per_term": (
                total_cooccurrences / len(term_texts) if term_texts else 0
            ),
        }

    def quantify_ambiguity_metrics(
        self, terms: List[Term], texts: List[str]
    ) -> Dict[str, Any]:
        """Quantify ambiguity metrics for terms in the domain.

        Args:
            terms: List of terms to analyze
            texts: Source texts for context

        Returns:
            Ambiguity quantification metrics
        """
        import re
        from collections import defaultdict

        ambiguity_scores = {}
        context_counts = defaultdict(lambda: defaultdict(int))

        for term in terms:
            term_text = term.text.lower()
            contexts = []

            # Find contexts where term appears
            for text in texts:
                # Simple context extraction around term
                sentences = re.split(r"[.!?]+", text)
                for sentence in sentences:
                    if term_text in sentence.lower():
                        # Extract context (simplified)
                        contexts.append(sentence.strip())

            # Calculate ambiguity metrics
            if contexts:
                # Context diversity (unique contexts / total contexts)
                unique_contexts = len(set(contexts))
                total_contexts = len(contexts)
                context_diversity = (
                    unique_contexts / total_contexts if total_contexts > 0 else 0
                )

                # Context length variation
                context_lengths = [len(ctx.split()) for ctx in contexts]
                length_variation = np.std(context_lengths) if context_lengths else 0

                ambiguity_scores[term_text] = {
                    "total_occurrences": total_contexts,
                    "unique_contexts": unique_contexts,
                    "context_diversity": context_diversity,
                    "context_length_variation": length_variation,
                    "ambiguity_score": context_diversity
                    * length_variation,  # Combined metric
                }

        # Overall domain ambiguity metrics
        if ambiguity_scores:
            domain_scores = list(ambiguity_scores.values())
            overall_metrics = {
                "average_context_diversity": np.mean(
                    [s["context_diversity"] for s in domain_scores]
                ),
                "average_ambiguity_score": np.mean(
                    [s["ambiguity_score"] for s in domain_scores]
                ),
                "max_ambiguity_score": max(
                    [s["ambiguity_score"] for s in domain_scores]
                ),
                "highly_ambiguous_terms": [
                    term
                    for term, score in ambiguity_scores.items()
                    if score["ambiguity_score"]
                    > np.mean([s["ambiguity_score"] for s in domain_scores])
                ],
            }
        else:
            overall_metrics = {"error": "No terms found for ambiguity analysis"}

        return {
            "term_ambiguity_scores": ambiguity_scores,
            "domain_metrics": overall_metrics,
        }

    def analyze_cross_domain_overlap(
        self, domain_terms: Dict[str, List[Term]], all_terms: Dict[str, Term]
    ) -> Dict[str, Any]:
        """Analyze overlap between terms across different domains.

        Args:
            domain_terms: Terms grouped by domain
            all_terms: All terms with their domain classifications

        Returns:
            Cross-domain overlap analysis
        """
        from collections import defaultdict

        # Build term-to-domains mapping
        term_domains = defaultdict(set)
        for term_text, term_obj in all_terms.items():
            if hasattr(term_obj, "domains") and term_obj.domains:
                term_domains[term_text] = set(term_obj.domains)

        # Calculate overlap statistics
        overlap_stats = defaultdict(dict)
        domain_pairs = []

        domain_names = list(domain_terms.keys())
        for i, domain1 in enumerate(domain_names):
            for j, domain2 in enumerate(domain_names):
                if i < j:  # Avoid duplicate pairs
                    pair_key = f"{domain1}_{domain2}"

                    # Find terms shared between domains
                    shared_terms = []
                    for term_text, domains in term_domains.items():
                        if domain1 in domains and domain2 in domains:
                            shared_terms.append(term_text)

                    overlap_stats[pair_key] = {
                        "shared_terms": shared_terms,
                        "shared_count": len(shared_terms),
                        "domain1_total": len(domain_terms[domain1]),
                        "domain2_total": len(domain_terms[domain2]),
                        "overlap_percentage": (
                            (
                                len(shared_terms)
                                / min(
                                    len(domain_terms[domain1]),
                                    len(domain_terms[domain2]),
                                )
                            )
                            * 100
                            if min(
                                len(domain_terms[domain1]), len(domain_terms[domain2])
                            )
                            > 0
                            else 0
                        ),
                    }

        # Overall statistics
        all_shared_terms = set()
        for stats in overlap_stats.values():
            all_shared_terms.update(stats["shared_terms"])

        return {
            "domain_pair_overlaps": dict(overlap_stats),
            "total_unique_shared_terms": len(all_shared_terms),
            "average_overlap_percentage": (
                np.mean(
                    [stats["overlap_percentage"] for stats in overlap_stats.values()]
                )
                if overlap_stats
                else 0
            ),
        }

    def calculate_statistical_significance(
        self,
        term_patterns: Dict[str, int],
        expected_patterns: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Calculate statistical significance for term patterns.

        Args:
            term_patterns: Observed term pattern frequencies
            expected_patterns: Expected pattern frequencies (optional)

        Returns:
            Statistical significance analysis
        """
        import numpy as np
        from scipy import stats

        if not term_patterns:
            return {"error": "No patterns provided"}

        # If no expected patterns, use uniform distribution
        if expected_patterns is None:
            total_patterns = sum(term_patterns.values())
            expected_patterns = {
                pattern: total_patterns / len(term_patterns)
                for pattern in term_patterns.keys()
            }

        # Chi-square test for pattern significance
        observed = list(term_patterns.values())
        expected = [
            expected_patterns.get(pattern, 0) for pattern in term_patterns.keys()
        ]

        try:
            chi2_stat, p_value = stats.chisquare(observed, expected)
            significant_patterns = [
                pattern
                for pattern, freq in term_patterns.items()
                if freq > expected_patterns.get(pattern, 0)
            ]

            return {
                "chi_square_statistic": chi2_stat,
                "p_value": p_value,
                "significant_patterns": significant_patterns,
                "significance_threshold": 0.05,
                "is_significant": p_value < 0.05,
                "effect_size": chi2_stat / sum(observed),  # Cramer's V approximation
            }
        except Exception as e:
            return {
                "error": f"Statistical analysis failed: {str(e)}",
                "observed_patterns": term_patterns,
            }

    def generate_confidence_scores(
        self, framing_assumptions: List[str], terms: List[Term], texts: List[str]
    ) -> Dict[str, float]:
        """Generate confidence scores for framing assumptions.

        Args:
            framing_assumptions: List of framing assumptions
            terms: Terms in the domain
            texts: Source texts

        Returns:
            Confidence scores for each assumption
        """
        confidence_scores = {}

        for assumption in framing_assumptions:
            # Simplified confidence scoring based on term relevance
            # In a full implementation, this would use NLP models
            assumption_keywords = assumption.lower().split()
            supporting_terms = 0

            for term in terms:
                term_words = term.text.lower().split()
                # Check for keyword overlap
                if any(keyword in term_words for keyword in assumption_keywords):
                    supporting_terms += 1

            # Confidence based on supporting evidence
            confidence = min(supporting_terms / len(terms) * 100, 100) if terms else 0
            confidence_scores[assumption] = confidence

        return confidence_scores

    def quantify_conceptual_structure(
        self, conceptual_structure: Dict[str, Any], terms: List[Term]
    ) -> Dict[str, Any]:
        """Quantify conceptual structure metrics.

        Args:
            conceptual_structure: Conceptual structure dictionary
            terms: Terms in the domain

        Returns:
            Quantitative metrics for conceptual structure
        """
        metrics = {}

        # Concept coverage - how many terms map to concepts
        total_concepts = 0
        for key, value in conceptual_structure.items():
            if isinstance(value, list):
                total_concepts += len(value)
            elif isinstance(value, dict):
                total_concepts += len(value)

        metrics["total_concepts"] = total_concepts
        metrics["terms_per_concept"] = (
            len(terms) / total_concepts if total_concepts > 0 else 0
        )

        # Concept diversity - number of different concept types
        concept_types = sum(
            1
            for value in conceptual_structure.values()
            if isinstance(value, (list, dict))
        )
        metrics["concept_types"] = concept_types

        # Structural complexity - nested levels
        def calculate_depth(obj, current_depth=0):
            if isinstance(obj, dict):
                return max(calculate_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                return current_depth + 1
            else:
                return current_depth

        metrics["structural_depth"] = calculate_depth(conceptual_structure)
        metrics["structural_complexity_score"] = (
            concept_types * metrics["structural_depth"]
        )

        return metrics

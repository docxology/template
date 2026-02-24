"""Analysis sub-package for Ento-Linguistic research.

Provides modules for discourse analysis, domain analysis, conceptual mapping,
term extraction, text analysis, statistics, semantic entropy, CACE scoring,
and performance metrics.
"""

from .discourse_analysis import (
    ArgumentativeStructure,
    DiscourseAnalyzer,
    DiscoursePattern,
)
from .discourse_patterns import (
    DISCOURSE_MARKERS,
    identify_patterns_in_text,
    extract_argumentative_structure,
)
from .rhetorical_analysis import (
    analyze_rhetorical_strategies,
    identify_narrative_frameworks,
    quantify_rhetorical_patterns,
    score_argumentative_structures,
    analyze_narrative_frequency,
)
from .persuasive_analysis import (
    analyze_persuasive_techniques,
    measure_persuasive_effectiveness,
    analyze_term_usage_context,
    track_conceptual_shifts,
    quantify_framing_effects,
)
from .domain_analysis import DomainAnalysis, DomainAnalyzer
from .conceptual_mapping import Concept, ConceptMap, ConceptualMapper
from .term_extraction import Term, TerminologyExtractor
from .text_analysis import LinguisticFeatureExtractor, TextProcessor
from .statistics import DescriptiveStats
from .semantic_entropy import (
    SemanticEntropyResult,
    calculate_semantic_entropy,
    calculate_corpus_entropy,
    get_high_entropy_terms,
    HIGH_ENTROPY_THRESHOLD,
)
from .cace_scoring import (
    CACEScore,
    evaluate_term_cace,
    compare_terms_cace,
    score_clarity,
    score_appropriateness,
    score_consistency,
    score_evolvability,
    ANTHROPOMORPHIC_TERMS,
)
from .performance import ConvergenceMetrics, ScalabilityMetrics

__all__ = [
    # discourse_analysis
    "ArgumentativeStructure",
    "DiscourseAnalyzer",
    "DiscoursePattern",
    # discourse_patterns
    "DISCOURSE_MARKERS",
    "identify_patterns_in_text",
    "extract_argumentative_structure",
    # rhetorical_analysis
    "analyze_rhetorical_strategies",
    "identify_narrative_frameworks",
    "quantify_rhetorical_patterns",
    "score_argumentative_structures",
    "analyze_narrative_frequency",
    # persuasive_analysis
    "analyze_persuasive_techniques",
    "measure_persuasive_effectiveness",
    "analyze_term_usage_context",
    "track_conceptual_shifts",
    "quantify_framing_effects",
    # domain_analysis
    "DomainAnalysis",
    "DomainAnalyzer",
    # conceptual_mapping
    "Concept",
    "ConceptMap",
    "ConceptualMapper",
    # term_extraction
    "Term",
    "TerminologyExtractor",
    # text_analysis
    "LinguisticFeatureExtractor",
    "TextProcessor",
    # statistics
    "DescriptiveStats",
    # semantic_entropy
    "SemanticEntropyResult",
    "calculate_semantic_entropy",
    "calculate_corpus_entropy",
    "get_high_entropy_terms",
    "HIGH_ENTROPY_THRESHOLD",
    # cace_scoring
    "CACEScore",
    "evaluate_term_cace",
    "compare_terms_cace",
    "score_clarity",
    "score_appropriateness",
    "score_consistency",
    "score_evolvability",
    "ANTHROPOMORPHIC_TERMS",
    # performance
    "ConvergenceMetrics",
    "ScalabilityMetrics",
]

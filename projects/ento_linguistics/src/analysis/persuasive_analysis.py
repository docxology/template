"""Persuasive technique and framing analysis for Ento-Linguistic research.

This module provides methods for analyzing persuasive techniques, framing effects,
conceptual shifts, and context-dependent term usage in entomological literature.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

try:
    from ..core.logging import get_logger
except (ImportError, ValueError):
    import logging

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

__all__ = [
    "analyze_persuasive_techniques",
    "measure_persuasive_effectiveness",
    "analyze_term_usage_context",
    "track_conceptual_shifts",
    "quantify_framing_effects",
]


def analyze_persuasive_techniques(texts: List[str]) -> Dict[str, Dict[str, Any]]:
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


def measure_persuasive_effectiveness(
    texts: List[str],
) -> Dict[str, Dict[str, Any]]:
    """Measure effectiveness of persuasive techniques.

    Args:
        texts: Texts to analyze

    Returns:
        Dictionary of persuasive technique effectiveness metrics
    """
    techniques = analyze_persuasive_techniques(texts)
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
            "effectiveness_rating": _rate_technique_effectiveness(technique_data),
            "success_examples": technique_data.get("examples", [])[:3],
            "usage_distribution": technique_data.get("distribution", {}),
        }

    return effectiveness_analysis


def analyze_term_usage_context(
    terms: List[str], texts: List[str]
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
                            "context_type": _classify_context_type(sentence, term),
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
                "usage_consistency": _calculate_usage_consistency(term_contexts),
                "context_examples": term_contexts[:5],  # Limit examples
            }

    return context_analysis


def track_conceptual_shifts(
    texts: List[str],
    time_periods: Optional[List[str]] = None,
    rhetorical_analyzer=None,
) -> Dict[str, Dict[str, Any]]:
    """Track how concepts shift in discourse over time or contexts.

    Args:
        texts: Texts to analyze
        time_periods: Optional time periods for temporal analysis
        rhetorical_analyzer: Callable for rhetorical strategy analysis

    Returns:
        Dictionary of conceptual shift analysis
    """
    if time_periods and len(time_periods) != len(texts):
        raise ValueError("time_periods must have same length as texts")

    # If no time periods provided, create sequential periods
    if not time_periods:
        time_periods = [f"period_{i}" for i in range(len(texts))]

    # Import here to avoid circular dependency
    from .rhetorical_analysis import analyze_rhetorical_strategies as _analyze_rhetorical

    analyze_fn = rhetorical_analyzer or _analyze_rhetorical

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
        current_patterns = analyze_fn(current_texts)
        next_patterns = analyze_fn(next_texts)

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
    texts: List[str],
    framing_concepts: Optional[List[str]] = None,
    rhetorical_analyzer=None,
    argumentative_analyzer=None,
) -> Dict[str, Dict[str, Any]]:
    """Quantify the impact of framing assumptions on discourse.

    Args:
        texts: Texts to analyze
        framing_concepts: Optional list of framing concepts to analyze
        rhetorical_analyzer: Callable for rhetorical strategy analysis
        argumentative_analyzer: Callable for argumentative structure analysis

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

    # Import here to avoid circular dependency
    from .rhetorical_analysis import analyze_rhetorical_strategies as _analyze_rhetorical

    analyze_rhet = rhetorical_analyzer or _analyze_rhetorical

    framing_analysis = {}

    for concept in framing_concepts:
        # Find texts that use this framing
        framed_texts = []
        framing_indicators = _get_framing_indicators(concept)

        for text in texts:
            if any(
                indicator.lower() in text.lower()
                for indicator in framing_indicators
            ):
                framed_texts.append(text)

        if framed_texts:
            # Analyze framing impact
            framing_strength = len(framed_texts) / len(texts)
            consistency_score = _calculate_framing_consistency(
                framed_texts, framing_indicators
            )

            # Analyze downstream effects
            downstream_patterns = analyze_rhet(framed_texts)

            # Use argumentative analyzer if provided
            argumentation_count = 0
            if argumentative_analyzer:
                argumentation_structures = argumentative_analyzer(framed_texts)
                argumentation_count = len(argumentation_structures)

            framing_analysis[concept] = {
                "framing_strength": framing_strength,
                "consistency_score": consistency_score,
                "affected_texts": len(framed_texts),
                "downstream_rhetorical_patterns": len(downstream_patterns),
                "argumentation_structures": argumentation_count,
                "framing_indicators_used": framing_indicators,
                "impact_score": framing_strength * consistency_score,
            }

    return framing_analysis


# --- Helper functions ---


def _classify_context_type(sentence: str, term: str) -> str:
    """Classify the context type of term usage."""
    sentence_lower = sentence.lower()

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


def _calculate_usage_consistency(contexts: List[Dict[str, Any]]) -> float:
    """Calculate consistency of term usage across contexts."""
    if len(contexts) < 2:
        return 1.0

    context_types = [ctx["context_type"] for ctx in contexts]
    most_common_type = max(set(context_types), key=context_types.count)
    consistency = context_types.count(most_common_type) / len(context_types)

    return consistency


def _get_framing_indicators(framing_concept: str) -> List[str]:
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
    framed_texts: List[str], indicators: List[str]
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


def _rate_technique_effectiveness(technique_data: Dict[str, Any]) -> str:
    """Rate the effectiveness of a persuasive technique."""
    impact = _calculate_technique_impact(technique_data)

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


def _calculate_technique_impact(technique_data: Dict[str, Any]) -> float:
    """Calculate impact score for persuasive technique."""
    frequency = technique_data.get("frequency", 0)
    context_count = len(technique_data.get("contexts", []))

    # Impact based on usage and context relevance
    impact = min((frequency + context_count) / 20, 1.0)

    return impact

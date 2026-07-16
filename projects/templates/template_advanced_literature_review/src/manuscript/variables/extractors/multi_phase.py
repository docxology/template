"""Multi-phase literature review variable extraction.

Extracts template variables specific to multi-phase systematic reviews.
"""

from __future__ import annotations

import logging
from typing import Any

from manuscript.variables.formatters import latex_number, percentage

logger = logging.getLogger(__name__)


def extract_phase_variables(ctx: Any) -> dict[str, Any]:
    """Extract variables from multi-phase search metadata."""
    variables: dict[str, Any] = {}

    # Load phase metadata
    phase_metadata = ctx.load_json("phase_metadata.json")
    if not phase_metadata:
        logger.info("phase_metadata.json not found; phase variables skipped")
        return variables

    phases = phase_metadata.get("phases", {})
    total_papers = phase_metadata.get("total_papers", 0)

    # Overall phase statistics
    variables["TOTAL_PHASES"] = latex_number(len(phases))
    variables["CORPUS_SIZE"] = latex_number(total_papers)

    # Phase-specific counts
    for i, (phase_id, phase_data) in enumerate(phases.items(), 1):
        phase_num = f"PHASE_{i}"
        variables[f"{phase_num}_NAME"] = phase_data.get("name", phase_id)
        variables[f"{phase_num}_PAPERS"] = latex_number(phase_data.get("papers_final", 0))
        variables[f"{phase_num}_QUERIES"] = latex_number(len(phase_data.get("queries_executed", [])))

        # LLM filter effectiveness
        papers_before_llm = phase_data.get("papers_after_deterministic_filters", 0)
        papers_after_llm = phase_data.get("papers_after_llm_filters", 0)
        if papers_before_llm > 0:
            filter_rate = (papers_before_llm - papers_after_llm) / papers_before_llm
            variables[f"{phase_num}_LLM_FILTER_RATE"] = percentage(filter_rate)

    # Cross-phase overlap analysis
    overlap_matrix = phase_metadata.get("phase_overlap", {})
    if overlap_matrix:
        jaccard_scores = []
        for phase1_data in overlap_matrix.values():
            for phase2_data in phase1_data.values():
                jaccard_scores.append(phase2_data.get("jaccard_similarity", 0))

        if jaccard_scores:
            avg_overlap = sum(jaccard_scores) / len(jaccard_scores)
            variables["CROSS_PHASE_OVERLAP_PCT"] = percentage(avg_overlap)

    # Citation validation results
    citation_validation = phase_metadata.get("citation_validation", {})
    if citation_validation:
        citation_rates = []
        for phase_data in citation_validation.values():
            rate = phase_data.get("citation_rate", 0)
            if rate > 0:
                citation_rates.append(rate)

        if citation_rates:
            avg_citation_rate = sum(citation_rates) / len(citation_rates)
            variables["CROSS_PHASE_CITATION_RATE"] = percentage(avg_citation_rate)

    return variables

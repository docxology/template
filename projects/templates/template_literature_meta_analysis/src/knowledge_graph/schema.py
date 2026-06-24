"""RDF schema definitions for the literature meta-analysis knowledge graph.

Defines namespace URIs, assertion type predicates, hypothesis category URIs,
and subfield URIs used throughout the knowledge graph construction and
querying pipeline.

Core Triple Patterns:
    Paper  --ns:asserts-->      Assertion
    Paper  --ns:cites-->        Paper
    Paper  --ns:belongsTo-->    Subfield
    Assertion --ns:supports-->  Hypothesis
    Assertion --ns:contradicts--> Hypothesis
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Base namespace URI for the meta-analysis ontology. Generic by default; override
# by editing this constant for a project-specific ontology host.
# (``AIF_NAMESPACE`` symbol name retained for backward-compatible imports.)
AIF_NAMESPACE: str = "http://example.org/litmeta/ontology/"

# Assertion types (predicate URIs)
ASSERTION_TYPES: dict[str, str] = {
    "asserts": f"{AIF_NAMESPACE}asserts",
    "cites": f"{AIF_NAMESPACE}cites",
    "belongsTo": f"{AIF_NAMESPACE}belongsTo",
    "supports": f"{AIF_NAMESPACE}supports",
    "contradicts": f"{AIF_NAMESPACE}contradicts",
}

# Default hypothesis category URIs — one per standard hypothesis
DEFAULT_HYPOTHESIS_CATEGORIES: dict[str, str] = {
    "PRIMARY_EFFICACY": f"{AIF_NAMESPACE}hypothesis/primary_efficacy",
    "OPTIMAL_PERFORMANCE": f"{AIF_NAMESPACE}hypothesis/optimal_performance",
    "MECHANISTIC_BASIS": f"{AIF_NAMESPACE}hypothesis/mechanistic_basis",
    "PROCESS_MODEL": f"{AIF_NAMESPACE}hypothesis/process_model",
    "SCALABILITY": f"{AIF_NAMESPACE}hypothesis/scalability",
    "CLINICAL_UTILITY": f"{AIF_NAMESPACE}hypothesis/clinical_utility",
    "BIOLOGICAL_BASIS": f"{AIF_NAMESPACE}hypothesis/biological_basis",
    "DOMAIN_GENERALIZATION": f"{AIF_NAMESPACE}hypothesis/domain_generalization",
}

# Module-level active categories (overridden by configure_hypothesis_categories)
HYPOTHESIS_CATEGORIES: dict[str, str] = dict(DEFAULT_HYPOTHESIS_CATEGORIES)


def configure_hypothesis_categories(hypothesis_ids: list[str]) -> dict[str, str]:
    """Rebuild HYPOTHESIS_CATEGORIES from a list of hypothesis IDs.

    Known IDs reuse their default URI; unknown IDs get a generated URI
    under the ``AIF_NAMESPACE``.

    Args:
        hypothesis_ids: List of hypothesis identifier strings.

    Returns:
        The updated HYPOTHESIS_CATEGORIES dict.
    """
    global HYPOTHESIS_CATEGORIES
    new_cats: dict[str, str] = {}
    for h_id in hypothesis_ids:
        if h_id in DEFAULT_HYPOTHESIS_CATEGORIES:
            new_cats[h_id] = DEFAULT_HYPOTHESIS_CATEGORIES[h_id]
        else:
            new_cats[h_id] = f"{AIF_NAMESPACE}hypothesis/{h_id.lower()}"
    HYPOTHESIS_CATEGORIES = new_cats
    logger.info(
        "Configured %d hypothesis categories: %s",
        len(HYPOTHESIS_CATEGORIES),
        list(HYPOTHESIS_CATEGORIES.keys()),
    )
    return HYPOTHESIS_CATEGORIES


# Domain URIs for classifying papers by research area (A/B/C taxonomy)
SUBFIELD_URIS: dict[str, str] = {
    "A1_formal": f"{AIF_NAMESPACE}subfield/A1_formal",
    "A2_philosophy": f"{AIF_NAMESPACE}subfield/A2_philosophy",
    "B_tools": f"{AIF_NAMESPACE}subfield/B_tools",
    "C1_neuroscience": f"{AIF_NAMESPACE}subfield/C1_neuroscience",
    "C2_robotics": f"{AIF_NAMESPACE}subfield/C2_robotics",
    "C3_language": f"{AIF_NAMESPACE}subfield/C3_language",
    "C4_psychiatry": f"{AIF_NAMESPACE}subfield/C4_psychiatry",
    "C5_biology": f"{AIF_NAMESPACE}subfield/C5_biology",
}

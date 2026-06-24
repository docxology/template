"""Hypothesis definitions and citation-weighted scoring.

Provides configurable hypothesis definitions, a citation-weighted
scoring function, bulk scoring, and temporal trend analysis.

Hypotheses can be loaded from a YAML config file via
``configure_hypotheses(config_path)`` or left at the default 8
domain-neutral fallback hypotheses.

Scoring Formula:
    score(H) = (SUM_support(log(1+citations) * confidence)
                - SUM_contradict(log(1+citations) * confidence))
               / SUM_all(log(1+citations) * confidence)

    Range: [-1.0, 1.0].  Returns 0.0 when the denominator is zero.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from literature.models import Paper
from knowledge_graph.nanopublication import Assertion
from knowledge_graph.schema import configure_hypothesis_categories

logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    """A scored hypothesis in the meta-analysis.

    Attributes:
        hypothesis_id: Key into ``HYPOTHESIS_CATEGORIES``.
        name: Short human-readable name.
        description: Full description of the hypothesis.
    """

    hypothesis_id: str
    name: str
    description: str


# A generic, domain-neutral default hypothesis set. These are FALLBACKS only —
# the real hypotheses for a given study come from the ``hypothesis_definitions``
# block of ``manuscript/config.yaml`` (the bundled default targets "modafinil").
STANDARD_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        "PRIMARY_EFFICACY",
        "Primary Efficacy",
        "The intervention reliably produces its primary intended effect",
    ),
    Hypothesis(
        "OPTIMAL_PERFORMANCE",
        "Optimal Performance",
        "The intervention performs optimally relative to its theoretical ceiling",
    ),
    Hypothesis(
        "MECHANISTIC_BASIS",
        "Mechanistic Basis",
        "The observed effect is explained by an identifiable underlying mechanism",
    ),
    Hypothesis(
        "PROCESS_MODEL",
        "Process Model",
        "A process-level model accounts for how the effect arises",
    ),
    Hypothesis(
        "SCALABILITY",
        "Scalability",
        "The approach scales to broader, more complex real-world contexts",
    ),
    Hypothesis(
        "CLINICAL_UTILITY",
        "Clinical Utility",
        "The intervention has demonstrable applied or clinical utility",
    ),
    Hypothesis(
        "BIOLOGICAL_BASIS",
        "Biological Basis",
        "The effect has a coherent biological or physical basis",
    ),
    Hypothesis(
        "DOMAIN_GENERALIZATION",
        "Domain Generalization",
        "Findings generalize beyond the original populations and settings",
    ),
]

# Module-level active hypotheses (overridden by configure_hypotheses)
HYPOTHESES: list[Hypothesis] = list(STANDARD_HYPOTHESES)


def load_hypotheses_from_config(config_path: Path) -> list[Hypothesis]:
    """Load hypothesis definitions from a YAML config file.

    Reads the ``hypothesis_definitions`` section of the config and
    constructs Hypothesis objects. Falls back to ``STANDARD_HYPOTHESES``
    if the section is missing or the file cannot be read.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        List of Hypothesis objects.
    """
    try:
        import yaml
    except ImportError:
        logger.warning("pyyaml not installed; cannot load hypothesis config")
        return list(STANDARD_HYPOTHESES)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, IOError) as exc:
        logger.warning("Cannot read config %s: %s", config_path, exc)
        return list(STANDARD_HYPOTHESES)

    project_cfg = data.get("project_config", {})
    hyp_defs = data.get("hypothesis_definitions", {}) or project_cfg.get("hypothesis_definitions", {})
    if not hyp_defs:
        logger.debug("No hypothesis_definitions in config; using defaults")
        return list(STANDARD_HYPOTHESES)

    hypotheses: list[Hypothesis] = []
    for h_key, h_def in hyp_defs.items():
        name = h_def.get("name", h_key)
        description = h_def.get("description", "")
        # Map H1..H8 keys to hypothesis_id format
        hyp_id = _config_key_to_id(h_key, name)
        hypotheses.append(Hypothesis(hyp_id, name, description))

    logger.info(
        "Loaded %d hypotheses from config: %s",
        len(hypotheses),
        [h.hypothesis_id for h in hypotheses],
    )
    return hypotheses


def _config_key_to_id(key: str, name: str) -> str:
    """Map a config key (e.g. 'H1') to a hypothesis_id.

    Checks if the key matches a known STANDARD_HYPOTHESES entry by
    ordinal position (H1→PRIMARY_EFFICACY, H2→OPTIMAL_PERFORMANCE, etc.).
    Falls back to uppercased name with spaces replaced by underscores.
    """
    ordinal_map = {f"H{i + 1}": h.hypothesis_id for i, h in enumerate(STANDARD_HYPOTHESES)}
    if key in ordinal_map:
        return ordinal_map[key]
    # Fallback: derive from name
    return name.upper().replace(" ", "_").replace("-", "_")


def config_key_to_hypothesis_id(key: str, name: str = "") -> str:
    """Public alias of :func:`_config_key_to_id`.

    Downstream consumers (e.g. the manuscript-variable layer) need the SAME
    config-key → internal-hypothesis-id mapping the KG scorer uses, so that an
    ``hypothesis_scores.json`` keyed by ``PRIMARY_EFFICACY`` can be looked up
    from a manuscript that references the config key ``H1``. Without this bridge
    the injected hypothesis-evidence table reads ``pending`` even after the
    knowledge-graph stage has scored every hypothesis.
    """
    return _config_key_to_id(key, name)


def configure_hypotheses(config_path: Optional[Path] = None) -> list[Hypothesis]:
    """Set the module-level HYPOTHESES from config or defaults.

    Call this before scoring to ensure the correct hypothesis set is
    active. If *config_path* is provided, hypotheses are loaded from
    the YAML file; otherwise ``STANDARD_HYPOTHESES`` is used.

    Also updates ``HYPOTHESIS_CATEGORIES`` in :mod:`knowledge_graph.schema`
    to reflect the configured hypotheses.

    Args:
        config_path: Optional path to the YAML config file.

    Returns:
        The active HYPOTHESES list.
    """
    global HYPOTHESES
    if config_path and Path(config_path).exists():
        HYPOTHESES = load_hypotheses_from_config(Path(config_path))
    else:
        HYPOTHESES = list(STANDARD_HYPOTHESES)

    # Sync schema categories to match active hypotheses
    configure_hypothesis_categories([h.hypothesis_id for h in HYPOTHESES])
    logger.info(
        "Active hypotheses: %d configured",
        len(HYPOTHESES),
    )
    return HYPOTHESES


def _weight(citation_count: int, confidence: float) -> float:
    """Compute the citation-weighted contribution of a single assertion.

    Args:
        citation_count: Number of citations for the source paper.
            Must be non-negative; negative values are clamped to 0.
        confidence: Confidence level of the assertion in [0.0, 1.0].

    Returns:
        ``log(1 + max(0, citation_count)) * confidence``
    """
    return math.log(1 + max(0, citation_count)) * confidence


def score_hypothesis(assertions: list[Assertion], hypothesis_id: str) -> float:
    """Compute the citation-weighted score for a single hypothesis.

    Formula::

        score(H) = (SUM_support(w) - SUM_contradict(w)) / SUM_all(w)

    where ``w = log(1 + citations) * confidence``.

    Only assertions whose ``hypothesis_id`` matches are considered.
    Returns 0.0 when there are no matching assertions or when the
    total weight is zero.

    Args:
        assertions: All assertions (will be filtered by hypothesis_id).
        hypothesis_id: Key from ``HYPOTHESIS_CATEGORIES`` to score.

    Returns:
        Score in the range ``[-1.0, 1.0]``.
    """
    relevant = [a for a in assertions if a.hypothesis_id == hypothesis_id]
    if not relevant:
        return 0.0

    support_sum = 0.0
    contradict_sum = 0.0
    total_sum = 0.0

    for a in relevant:
        w = _weight(a.citation_count, a.confidence)
        total_sum += w
        if a.assertion_type == "supports":
            support_sum += w
        elif a.assertion_type == "contradicts":
            contradict_sum += w
        # "neutral" assertions contribute to denominator but not numerator

    if total_sum == 0.0:
        return 0.0

    return (support_sum - contradict_sum) / total_sum


def score_all_hypotheses(assertions: list[Assertion]) -> dict[str, float]:
    """Score all configured hypotheses.

    Uses the currently active HYPOTHESES (set via ``configure_hypotheses``
    or defaulting to ``STANDARD_HYPOTHESES``).

    Args:
        assertions: All assertions across all hypotheses.

    Returns:
        Dictionary mapping hypothesis_id to its score in ``[-1.0, 1.0]``.
    """
    return {h.hypothesis_id: score_hypothesis(assertions, h.hypothesis_id) for h in HYPOTHESES}


def get_hypothesis_by_id(hypothesis_id: str) -> Optional[Hypothesis]:
    """Look up a standard hypothesis by its identifier.

    Args:
        hypothesis_id: Key from ``HYPOTHESIS_CATEGORIES``.

    Returns:
        The matching Hypothesis or ``None`` if not found.
    """
    for h in HYPOTHESES:
        if h.hypothesis_id == hypothesis_id:
            return h
    return None


def temporal_trend(
    assertions: list[Assertion],
    hypothesis_id: str,
    papers: list[Paper],
) -> dict[int, float]:
    """Compute the cumulative hypothesis score over time.

    For each year present in *papers*, computes the cumulative score
    using all assertions from papers published in that year or earlier.

    Args:
        assertions: All assertions (will be filtered by hypothesis_id).
        hypothesis_id: The hypothesis to trend.
        papers: Paper objects used to map ``assertion.paper_id`` to a year.

    Returns:
        Dictionary mapping year to cumulative score as of that year.
        Years without any relevant data are omitted.
    """
    # Build paper_id -> year lookup
    paper_year: dict[str, int] = {}
    for p in papers:
        if p.year is not None:
            paper_year[p.canonical_id] = p.year

    # Filter to relevant assertions and attach year
    relevant: list[tuple[int, Assertion]] = []
    for a in assertions:
        if a.hypothesis_id == hypothesis_id and a.paper_id in paper_year:
            relevant.append((paper_year[a.paper_id], a))

    if not relevant:
        return {}

    # Collect all years and sort
    years = sorted({yr for yr, _ in relevant})

    trend: dict[int, float] = {}
    for target_year in years:
        cumulative = [a for yr, a in relevant if yr <= target_year]
        trend[target_year] = score_hypothesis(cumulative, hypothesis_id)

    return trend

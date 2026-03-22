"""Ordered section scores and gap flags for handbook figures (testable, no I/O)."""

from __future__ import annotations

from typing import Any


def section_scores_with_gap_flags(
    metrics: dict[str, Any],
) -> tuple[list[str], list[float], list[bool], float]:
    """Return section ids, scores, gap membership, and threshold from a metrics dict.

    Gap flags are True when the section id appears in ``gap_section_ids`` from
    ``build_metrics_report`` (strictly below the synthesis gap threshold).

    Args:
        metrics: Output of ``build_metrics_report``.

    Returns:
        Parallel lists of section ids and scores (sorted by section id), boolean
        gap flags, and the numeric gap threshold.
    """
    thr = float(metrics["gap_threshold"])
    gaps = set(metrics["gap_section_ids"])
    scores_map = metrics["scores_by_section"]
    items = sorted(scores_map.items(), key=lambda x: x[0])
    labels = [k for k, _ in items]
    scores = [float(v) for _, v in items]
    flags = [k in gaps for k in labels]
    return labels, scores, flags, thr

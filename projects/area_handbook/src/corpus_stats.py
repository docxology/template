"""Aggregate counts and coverage helpers over a corpus (no I/O)."""

from __future__ import annotations

from collections import Counter

from .models import AreaCorpus


def evidence_counts_by_theme(corpus: AreaCorpus) -> dict[str, int]:
    """Count evidence rows per theme id."""
    return dict(Counter(e.theme for e in corpus.evidence))


def themes_without_evidence(corpus: AreaCorpus) -> tuple[str, ...]:
    """Theme ids defined in the corpus but never referenced by any evidence item."""
    defined = {t.id for t in corpus.themes}
    used = {e.theme for e in corpus.evidence}
    unused = sorted(defined - used)
    return tuple(unused)


def total_evidence_weight(corpus: AreaCorpus) -> float:
    """Sum of all evidence weights (can exceed 1.0 across the whole corpus)."""
    return sum(e.weight for e in corpus.evidence)

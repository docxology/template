"""Roll evidence into sections; score coverage and list gaps."""

from __future__ import annotations

from .models import AreaCorpus, EvidenceItem, HandbookSection, SynthesisResult
from .outline import build_handbook_outline

DEFAULT_GAP_THRESHOLD = 0.35


def _evidence_for_section(section: HandbookSection, corpus: AreaCorpus) -> tuple[EvidenceItem, ...]:
    allowed = set(section.theme_ids)
    return tuple(e for e in corpus.evidence if e.theme in allowed)


def section_coverage_score(evidence: tuple[EvidenceItem, ...]) -> float:
    """Sum of evidence weights capped at 1.0 (pure function for tests and reuse)."""
    if not evidence:
        return 0.0
    return min(1.0, sum(e.weight for e in evidence))


def synthesize(
    corpus: AreaCorpus,
    *,
    gap_threshold: float = DEFAULT_GAP_THRESHOLD,
) -> SynthesisResult:
    """Attach evidence to each handbook section and flag weak chapters.

    Args:
        corpus: Loaded area corpus.
        gap_threshold: Sections with coverage score strictly below this value are listed in ``gaps``.
    """
    if gap_threshold < 0.0 or gap_threshold > 1.0:
        raise ValueError(f"gap_threshold must be in [0, 1], got {gap_threshold}")

    sections = build_handbook_outline(corpus)
    evidence_by_section: dict[str, tuple[EvidenceItem, ...]] = {}
    scores: dict[str, float] = {}
    gaps: list[str] = []

    for sec in sections:
        ev = _evidence_for_section(sec, corpus)
        evidence_by_section[sec.section_id] = ev
        s = section_coverage_score(ev)
        scores[sec.section_id] = s
        if s < gap_threshold:
            gaps.append(sec.section_id)

    return SynthesisResult(
        corpus=corpus,
        sections=sections,
        evidence_by_section=evidence_by_section,
        gaps=tuple(gaps),
        scores=scores,
        gap_threshold=gap_threshold,
    )

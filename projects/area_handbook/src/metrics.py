"""JSON-serializable metrics for pipeline reports and figures."""

from __future__ import annotations

from typing import Any

from .corpus_stats import evidence_counts_by_theme, themes_without_evidence, total_evidence_weight
from .models import SynthesisResult


def build_metrics_report(synth: SynthesisResult) -> dict[str, Any]:
    """Flat dict safe for ``json.dump`` (used by analysis script and tests)."""
    c = synth.corpus
    thr = synth.gap_threshold
    covered = sum(1 for sid in synth.scores if synth.scores[sid] >= thr)
    total_sections = len(synth.sections)
    ratio = covered / total_sections if total_sections else 0.0
    score_vals = list(synth.scores.values())
    mean_score = sum(score_vals) / len(score_vals) if score_vals else 0.0
    max_score = max(score_vals) if score_vals else 0.0
    min_score = min(score_vals) if score_vals else 0.0
    by_theme = evidence_counts_by_theme(c)
    unused = themes_without_evidence(c)

    return {
        "area_id": c.area_id,
        "area_label": c.area_label,
        "corpus_version": c.version,
        "evidence_count": len(c.evidence),
        "theme_count": len(c.themes),
        "section_count": total_sections,
        "sections_covered": covered,
        "coverage_ratio": round(ratio, 4),
        "gap_threshold": round(thr, 4),
        "gap_count": len(synth.gaps),
        "gap_section_ids": list(synth.gaps),
        "scores_by_section": {k: round(v, 4) for k, v in sorted(synth.scores.items())},
        "mean_section_score": round(mean_score, 4),
        "max_section_score": round(max_score, 4),
        "min_section_score": round(min_score, 4),
        "evidence_count_by_theme": dict(sorted(by_theme.items())),
        "themes_without_evidence": list(unused),
        "total_evidence_weight": round(total_evidence_weight(c), 4),
    }

"""Prose analysis module — readability, structure, editorial quality.

Public API:

* :class:`ProseMetrics`, :func:`compute_metrics` — Flesch / FKGL / Gunning
  Fog readability scores.
* :class:`StructureReport`, :func:`analyze_structure` — heading outline,
  per-section word counts, depth / skipped-level checks.
* :class:`QualityReport`, :func:`analyze_quality` — passive-voice
  candidates, hedge words, citation density, long sentences.
* :class:`ManuscriptReport`, :func:`analyze_manuscript` — aggregate
  report across a manuscript directory.
* :func:`normalise_for_prose` — strip front-matter, fences, inline code,
  links — applied automatically by the higher-level helpers.
"""

from __future__ import annotations

from infrastructure.prose.analysis import (
    Heading,
    ProseMetrics,
    QualityReport,
    Section,
    StructureReport,
    analyze_quality,
    analyze_structure,
    compute_metrics,
    count_syllables,
    detect_hedge_words,
    detect_long_sentences,
    detect_passive_sentences,
    extract_citation_keys,
    is_complex_word,
    parse_headings,
    render_outline,
    split_paragraphs,
    split_sentences,
    tokenize_words,
)
from infrastructure.prose.markdown import (
    normalise_for_prose,
    read_manuscript_dir,
    strip_fences,
    strip_front_matter,
    strip_inline_code,
    strip_links_to_text,
)
from infrastructure.prose.report import (
    FileReport,
    ManuscriptReport,
    analyze_files,
    analyze_manuscript,
    analyze_text,
    write_report,
)

__all__ = [
    # metrics
    "ProseMetrics",
    "compute_metrics",
    "count_syllables",
    "is_complex_word",
    "split_paragraphs",
    "split_sentences",
    "tokenize_words",
    # structure
    "Heading",
    "Section",
    "StructureReport",
    "analyze_structure",
    "parse_headings",
    "render_outline",
    # quality
    "QualityReport",
    "analyze_quality",
    "detect_hedge_words",
    "detect_long_sentences",
    "detect_passive_sentences",
    "extract_citation_keys",
    # markdown helpers
    "normalise_for_prose",
    "read_manuscript_dir",
    "strip_front_matter",
    "strip_fences",
    "strip_inline_code",
    "strip_links_to_text",
    # report
    "FileReport",
    "ManuscriptReport",
    "analyze_text",
    "analyze_files",
    "analyze_manuscript",
    "write_report",
]

"""Area handbook: structured corpus to handbook markdown and metrics."""

from .corpus_io import CorpusValidationError, load_corpus, load_corpus_from_dict
from .corpus_stats import evidence_counts_by_theme, themes_without_evidence, total_evidence_weight
from .handbook_md import (
    build_evidence_by_theme_table_md,
    build_executive_summary_md,
    build_full_handbook_body,
    build_gap_report_md,
    build_glossary_md,
    build_toc_md,
    render_section_markdown,
)
from .metrics import build_metrics_report
from .models import (
    AreaCorpus,
    EvidenceItem,
    HandbookSection,
    SynthesisResult,
    Theme,
)
from .outline import HANDBOOK_TEMPLATE, build_handbook_outline
from .synthesis import DEFAULT_GAP_THRESHOLD, section_coverage_score, synthesize

__all__ = [
    "DEFAULT_GAP_THRESHOLD",
    "AreaCorpus",
    "CorpusValidationError",
    "EvidenceItem",
    "HandbookSection",
    "HANDBOOK_TEMPLATE",
    "SynthesisResult",
    "Theme",
    "build_evidence_by_theme_table_md",
    "build_executive_summary_md",
    "build_full_handbook_body",
    "build_gap_report_md",
    "build_glossary_md",
    "build_handbook_outline",
    "build_metrics_report",
    "build_toc_md",
    "evidence_counts_by_theme",
    "load_corpus",
    "load_corpus_from_dict",
    "render_section_markdown",
    "section_coverage_score",
    "synthesize",
    "themes_without_evidence",
    "total_evidence_weight",
]

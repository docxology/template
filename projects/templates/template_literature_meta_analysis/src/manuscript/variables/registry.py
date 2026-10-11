"""Variable extractor registry."""

from __future__ import annotations

from collections.abc import Callable

from template_literature_meta_analysis.manuscript.variables.context import ExtractContext
from template_literature_meta_analysis.manuscript.variables.extractors.analysis import extract_analysis
from template_literature_meta_analysis.manuscript.variables.extractors.citation import extract_citation
from template_literature_meta_analysis.manuscript.variables.extractors.config import extract_config_tokens
from template_literature_meta_analysis.manuscript.variables.extractors.hypotheses import extract_hypotheses
from template_literature_meta_analysis.manuscript.variables.extractors.reproducibility import extract_reproducibility
from template_literature_meta_analysis.manuscript.variables.extractors.subfields import extract_subfields
from template_literature_meta_analysis.manuscript.variables.extractors.temporal import extract_temporal

VariableExtractor = Callable[[ExtractContext], dict[str, str]]

EXTRACTORS: list[VariableExtractor] = [
    extract_config_tokens,
    extract_temporal,
    extract_citation,
    extract_subfields,
    extract_hypotheses,
    extract_analysis,
    extract_reproducibility,
]

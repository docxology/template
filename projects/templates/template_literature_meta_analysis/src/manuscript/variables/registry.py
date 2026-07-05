"""Variable extractor registry."""

from __future__ import annotations

from collections.abc import Callable

from manuscript.variables.context import ExtractContext
from manuscript.variables.extractors.analysis import extract_analysis
from manuscript.variables.extractors.citation import extract_citation
from manuscript.variables.extractors.config import extract_config_tokens
from manuscript.variables.extractors.hypotheses import extract_hypotheses
from manuscript.variables.extractors.subfields import extract_subfields
from manuscript.variables.extractors.temporal import extract_temporal

VariableExtractor = Callable[[ExtractContext], dict[str, str]]

EXTRACTORS: list[VariableExtractor] = [
    extract_config_tokens,
    extract_temporal,
    extract_citation,
    extract_subfields,
    extract_hypotheses,
    extract_analysis,
]

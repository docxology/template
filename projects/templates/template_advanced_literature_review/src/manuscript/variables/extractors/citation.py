"""Public boundary backed by the behavior-verified declared literature engine."""

from template_literature_meta_analysis.manuscript.variables.extractors.citation import (
    _empty_advanced as _empty_advanced,
)
from template_literature_meta_analysis.manuscript.variables.extractors.citation import (
    extract_citation as extract_citation,
)

__all__ = ["_empty_advanced", "extract_citation"]

"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.fulltext_assessment import (
    _PROVIDER_PATTERNS as _PROVIDER_PATTERNS,
)
from template_literature_meta_analysis.literature.fulltext_assessment import (
    _classify_provider as _classify_provider,
)
from template_literature_meta_analysis.literature.fulltext_assessment import (
    _provider_breakdown as _provider_breakdown,
)
from template_literature_meta_analysis.literature.fulltext_assessment import (
    assess_corpus as assess_corpus,
)

__all__ = ["_PROVIDER_PATTERNS", "_classify_provider", "_provider_breakdown", "assess_corpus"]

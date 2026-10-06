"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.corpus import (
    Corpus as Corpus,
)
from template_literature_meta_analysis.literature.corpus import (
    _preprint_rank as _preprint_rank,
)

__all__ = ["Corpus", "_preprint_rank"]

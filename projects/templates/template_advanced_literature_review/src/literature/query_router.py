"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.query_router import (
    _ARXIV_RE as _ARXIV_RE,
)
from template_literature_meta_analysis.literature.query_router import (
    _DOI_RE as _DOI_RE,
)
from template_literature_meta_analysis.literature.query_router import (
    ACADEMIC_PATTERNS as ACADEMIC_PATTERNS,
)
from template_literature_meta_analysis.literature.query_router import (
    ACADEMIC_SOURCE_ORDER as ACADEMIC_SOURCE_ORDER,
)
from template_literature_meta_analysis.literature.query_router import (
    INDUSTRY_PATTERNS as INDUSTRY_PATTERNS,
)
from template_literature_meta_analysis.literature.query_router import (
    INDUSTRY_SOURCE_ORDER as INDUSTRY_SOURCE_ORDER,
)
from template_literature_meta_analysis.literature.query_router import (
    MIXED_SOURCE_ORDER as MIXED_SOURCE_ORDER,
)
from template_literature_meta_analysis.literature.query_router import (
    PREPRINT_PATTERNS as PREPRINT_PATTERNS,
)
from template_literature_meta_analysis.literature.query_router import (
    PREPRINT_SOURCE_ORDER as PREPRINT_SOURCE_ORDER,
)
from template_literature_meta_analysis.literature.query_router import (
    QueryRoute as QueryRoute,
)
from template_literature_meta_analysis.literature.query_router import (
    QueryRouter as QueryRouter,
)

__all__ = [
    "ACADEMIC_PATTERNS",
    "ACADEMIC_SOURCE_ORDER",
    "INDUSTRY_PATTERNS",
    "INDUSTRY_SOURCE_ORDER",
    "MIXED_SOURCE_ORDER",
    "PREPRINT_PATTERNS",
    "PREPRINT_SOURCE_ORDER",
    "_ARXIV_RE",
    "_DOI_RE",
    "QueryRoute",
    "QueryRouter",
]

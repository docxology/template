"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.semantic_scholar import (
    CITATION_FIELDS as CITATION_FIELDS,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    MAX_RETRIES as MAX_RETRIES,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    PAPER_FIELDS as PAPER_FIELDS,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    RETRY_BASE_SECONDS as RETRY_BASE_SECONDS,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    S2_API_URL as S2_API_URL,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    S2_PAGE_SIZE as S2_PAGE_SIZE,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    _parse_s2_paper as _parse_s2_paper,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    _request_with_retry as _request_with_retry,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    get_citations as get_citations,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    get_paper_details as get_paper_details,
)
from template_literature_meta_analysis.literature.semantic_scholar import (
    search_semantic_scholar as search_semantic_scholar,
)

__all__ = [
    "CITATION_FIELDS",
    "MAX_RETRIES",
    "PAPER_FIELDS",
    "RETRY_BASE_SECONDS",
    "S2_API_URL",
    "S2_PAGE_SIZE",
    "_parse_s2_paper",
    "_request_with_retry",
    "get_citations",
    "get_paper_details",
    "search_semantic_scholar",
]

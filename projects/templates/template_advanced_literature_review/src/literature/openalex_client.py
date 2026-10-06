"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.openalex_client import (
    MAX_RETRIES as MAX_RETRIES,
)
from template_literature_meta_analysis.literature.openalex_client import (
    OPENALEX_API_URL as OPENALEX_API_URL,
)
from template_literature_meta_analysis.literature.openalex_client import (
    OPENALEX_PAGE_SIZE as OPENALEX_PAGE_SIZE,
)
from template_literature_meta_analysis.literature.openalex_client import (
    RETRY_BASE_SECONDS as RETRY_BASE_SECONDS,
)
from template_literature_meta_analysis.literature.openalex_client import (
    _parse_openalex_work as _parse_openalex_work,
)
from template_literature_meta_analysis.literature.openalex_client import (
    _reconstruct_abstract as _reconstruct_abstract,
)
from template_literature_meta_analysis.literature.openalex_client import (
    _request_with_retry as _request_with_retry,
)
from template_literature_meta_analysis.literature.openalex_client import (
    get_work_by_doi as get_work_by_doi,
)
from template_literature_meta_analysis.literature.openalex_client import (
    search_openalex as search_openalex,
)

__all__ = [
    "MAX_RETRIES",
    "OPENALEX_API_URL",
    "OPENALEX_PAGE_SIZE",
    "RETRY_BASE_SECONDS",
    "_parse_openalex_work",
    "_reconstruct_abstract",
    "_request_with_retry",
    "get_work_by_doi",
    "search_openalex",
]

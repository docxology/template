"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.crossref_client import (
    _TAG_RE as _TAG_RE,
)
from template_literature_meta_analysis.literature.crossref_client import (
    CROSSREF_API_URL as CROSSREF_API_URL,
)
from template_literature_meta_analysis.literature.crossref_client import (
    CROSSREF_PAGE_SIZE as CROSSREF_PAGE_SIZE,
)
from template_literature_meta_analysis.literature.crossref_client import (
    MAX_RETRIES as MAX_RETRIES,
)
from template_literature_meta_analysis.literature.crossref_client import (
    RETRY_BASE_SECONDS as RETRY_BASE_SECONDS,
)
from template_literature_meta_analysis.literature.crossref_client import (
    _extract_authors as _extract_authors,
)
from template_literature_meta_analysis.literature.crossref_client import (
    _extract_year as _extract_year,
)
from template_literature_meta_analysis.literature.crossref_client import (
    _first_str as _first_str,
)
from template_literature_meta_analysis.literature.crossref_client import (
    _parse_crossref_work as _parse_crossref_work,
)
from template_literature_meta_analysis.literature.crossref_client import (
    _request_with_retry as _request_with_retry,
)
from template_literature_meta_analysis.literature.crossref_client import (
    _strip_jats as _strip_jats,
)
from template_literature_meta_analysis.literature.crossref_client import (
    search_crossref as search_crossref,
)

__all__ = [
    "CROSSREF_API_URL",
    "CROSSREF_PAGE_SIZE",
    "MAX_RETRIES",
    "RETRY_BASE_SECONDS",
    "_TAG_RE",
    "_extract_authors",
    "_extract_year",
    "_first_str",
    "_parse_crossref_work",
    "_request_with_retry",
    "_strip_jats",
    "search_crossref",
]

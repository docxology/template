"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.sovietrxiv_client import (
    CHINARXIV_API_URL as CHINARXIV_API_URL,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    MAX_RETRIES as MAX_RETRIES,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    RETRY_BASE_SECONDS as RETRY_BASE_SECONDS,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    SOVIETRXIV_API_URL as SOVIETRXIV_API_URL,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    SOVIETRXIV_PAGE_SIZE as SOVIETRXIV_PAGE_SIZE,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    _extract_authors as _extract_authors,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    _extract_year as _extract_year,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    _parse_sovietrxiv_paper as _parse_sovietrxiv_paper,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    _request_with_retry as _request_with_retry,
)
from template_literature_meta_analysis.literature.sovietrxiv_client import (
    search_sovietrxiv as search_sovietrxiv,
)

__all__ = [
    "CHINARXIV_API_URL",
    "MAX_RETRIES",
    "RETRY_BASE_SECONDS",
    "SOVIETRXIV_API_URL",
    "SOVIETRXIV_PAGE_SIZE",
    "_extract_authors",
    "_extract_year",
    "_parse_sovietrxiv_paper",
    "_request_with_retry",
    "search_sovietrxiv",
]

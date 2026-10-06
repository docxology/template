"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.arxiv_client import (
    ARXIV_API_URL as ARXIV_API_URL,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    ARXIV_NS as ARXIV_NS,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    ARXIV_PAGE_SIZE as ARXIV_PAGE_SIZE,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    ATOM_NS as ATOM_NS,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    DEFAULT_RATE_LIMIT_SECONDS as DEFAULT_RATE_LIMIT_SECONDS,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    MAX_RETRIES as MAX_RETRIES,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    RETRY_BASE_SECONDS as RETRY_BASE_SECONDS,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    _fetch_page as _fetch_page,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    _parse_entry as _parse_entry,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    parse_arxiv_response as parse_arxiv_response,
)
from template_literature_meta_analysis.literature.arxiv_client import (
    search_arxiv as search_arxiv,
)

__all__ = [
    "ARXIV_API_URL",
    "ARXIV_NS",
    "ARXIV_PAGE_SIZE",
    "ATOM_NS",
    "DEFAULT_RATE_LIMIT_SECONDS",
    "MAX_RETRIES",
    "RETRY_BASE_SECONDS",
    "_fetch_page",
    "_parse_entry",
    "parse_arxiv_response",
    "search_arxiv",
]

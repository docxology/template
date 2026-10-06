"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.biorxiv_client import (
    BIORXIV_API_URL as BIORXIV_API_URL,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    BIORXIV_MAX_PAGES as BIORXIV_MAX_PAGES,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    BIORXIV_PAGE_SIZE as BIORXIV_PAGE_SIZE,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    BIORXIV_YEAR_MAX as BIORXIV_YEAR_MAX,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    BIORXIV_YEAR_MIN as BIORXIV_YEAR_MIN,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    _build_pdf_url as _build_pdf_url,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    _extract_authors as _extract_authors,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    _extract_year as _extract_year,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    _matches_query as _matches_query,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    _parse_biorxiv_paper as _parse_biorxiv_paper,
)
from template_literature_meta_analysis.literature.biorxiv_client import (
    search_biorxiv as search_biorxiv,
)

__all__ = [
    "BIORXIV_API_URL",
    "BIORXIV_MAX_PAGES",
    "BIORXIV_PAGE_SIZE",
    "BIORXIV_YEAR_MAX",
    "BIORXIV_YEAR_MIN",
    "_build_pdf_url",
    "_extract_authors",
    "_extract_year",
    "_matches_query",
    "_parse_biorxiv_paper",
    "search_biorxiv",
]

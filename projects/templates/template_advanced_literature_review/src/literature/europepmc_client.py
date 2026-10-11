"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.europepmc_client import (
    EUROPEPMC_API_URL as EUROPEPMC_API_URL,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    EUROPEPMC_MAX_PAGE_SIZE as EUROPEPMC_MAX_PAGE_SIZE,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    _extract_authors as _extract_authors,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    _extract_open_access as _extract_open_access,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    _extract_pdf_url as _extract_pdf_url,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    _extract_venue as _extract_venue,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    _extract_year as _extract_year,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    _parse_europepmc_result as _parse_europepmc_result,
)
from template_literature_meta_analysis.literature.europepmc_client import (
    search_europepmc as search_europepmc,
)

__all__ = [
    "EUROPEPMC_API_URL",
    "EUROPEPMC_MAX_PAGE_SIZE",
    "_extract_authors",
    "_extract_open_access",
    "_extract_pdf_url",
    "_extract_venue",
    "_extract_year",
    "_parse_europepmc_result",
    "search_europepmc",
]

"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.fulltext_download import (
    _BACKOFF_BASE as _BACKOFF_BASE,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    _BLANK_LINES_RE as _BLANK_LINES_RE,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    MAX_RETRIES as MAX_RETRIES,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    UNPAYWALL_API_URL as UNPAYWALL_API_URL,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    _parse_unpaywall as _parse_unpaywall,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    _request_with_retry as _request_with_retry,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    assess_fulltext_availability as assess_fulltext_availability,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    assess_fulltext_extraction as assess_fulltext_extraction,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    download_and_extract_fulltext as download_and_extract_fulltext,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    download_fulltext as download_fulltext,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    extract_figures as extract_figures,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    extract_fulltext_text as extract_fulltext_text,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    resolve_fulltext_url as resolve_fulltext_url,
)
from template_literature_meta_analysis.literature.fulltext_download import (
    safe_filename as safe_filename,
)

__all__ = [
    "MAX_RETRIES",
    "UNPAYWALL_API_URL",
    "_BACKOFF_BASE",
    "_BLANK_LINES_RE",
    "_parse_unpaywall",
    "_request_with_retry",
    "assess_fulltext_availability",
    "assess_fulltext_extraction",
    "download_and_extract_fulltext",
    "download_fulltext",
    "extract_figures",
    "extract_fulltext_text",
    "resolve_fulltext_url",
    "safe_filename",
]

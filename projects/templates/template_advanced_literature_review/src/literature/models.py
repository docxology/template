"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.models import (
    _DOI_RESOLVER_PREFIX as _DOI_RESOLVER_PREFIX,
)
from template_literature_meta_analysis.literature.models import (
    _NON_ALNUM_RE as _NON_ALNUM_RE,
)
from template_literature_meta_analysis.literature.models import (
    _PREPRINT_HINTS as _PREPRINT_HINTS,
)
from template_literature_meta_analysis.literature.models import (
    _WHITESPACE_RE as _WHITESPACE_RE,
)
from template_literature_meta_analysis.literature.models import (
    Author as Author,
)
from template_literature_meta_analysis.literature.models import (
    Citation as Citation,
)
from template_literature_meta_analysis.literature.models import (
    Paper as Paper,
)
from template_literature_meta_analysis.literature.models import (
    _normalize_author_signature as _normalize_author_signature,
)
from template_literature_meta_analysis.literature.models import (
    _normalize_text as _normalize_text,
)
from template_literature_meta_analysis.literature.models import (
    normalize_doi as normalize_doi,
)

__all__ = [
    "_DOI_RESOLVER_PREFIX",
    "_NON_ALNUM_RE",
    "_PREPRINT_HINTS",
    "_WHITESPACE_RE",
    "Author",
    "Citation",
    "Paper",
    "_normalize_author_signature",
    "_normalize_text",
    "normalize_doi",
]

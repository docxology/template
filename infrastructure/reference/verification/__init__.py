"""Reference-existence verification — a deterministic anti-hallucination gate.

Given the references a manuscript claims to cite (its ``.bib`` file), resolve
each one against Crossref / OpenAlex / arXiv and report whether the cited work
actually exists and whether its metadata matches. Offline-first: with network
disabled it consults only the persistent SQLite cache and reports ``unchecked``
rather than silently passing.

Public API:

* :class:`ReferenceResolver` — resolve a DOI / arXiv id / title to a record.
* :class:`ResolutionCache` — persistent SQLite cache of resolutions.
* :func:`verify_bibfile` / :func:`verify_database` / :func:`verify_entry` —
  classify cited references into :class:`VerificationStatus` outcomes.
* :class:`VerificationReport` / :class:`ReferenceVerdict` — results.

See :mod:`infrastructure.search.literature` for the discovery (search) side of
the literature workflow; this package is the verification side.
"""

from infrastructure.reference.verification.cache import DEFAULT_TTL_SECONDS, ResolutionCache
from infrastructure.reference.verification.models import (
    BLOCKING_STATUSES,
    ReferenceVerdict,
    VerificationReport,
    VerificationStatus,
)
from infrastructure.reference.verification.resolver import (
    ReferenceResolver,
    Resolution,
    normalize_doi,
    title_similarity,
)
from infrastructure.reference.verification.verifier import (
    extract_arxiv_id,
    parse_bib_year,
    verify_bibfile,
    verify_database,
    verify_entry,
)

__all__ = [
    "BLOCKING_STATUSES",
    "DEFAULT_TTL_SECONDS",
    "ReferenceResolver",
    "ReferenceVerdict",
    "Resolution",
    "ResolutionCache",
    "VerificationReport",
    "VerificationStatus",
    "extract_arxiv_id",
    "normalize_doi",
    "parse_bib_year",
    "title_similarity",
    "verify_bibfile",
    "verify_database",
    "verify_entry",
]

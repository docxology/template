"""Full-text availability assessment for literature corpora.

Pure (no-network, no-filesystem) summary of how much full text a corpus
could yield from its metadata alone — the "potential" view. The
"realized" view (how much text was actually downloaded and extracted to
disk) is the sibling function
:func:`literature.fulltext_download.assess_fulltext_extraction`, which
is filesystem-aware and kept separate so this function's pure
no-side-effect contract is not disturbed.

Produces a JSON-serializable dict with four dimensions:

1. **Abstract coverage** — how many papers have an abstract (the minimum
   text for analysis).
2. **Open-access status** — how many papers are OA / not OA / unknown.
3. **PDF availability** — how many papers have a direct ``pdf_url`` and
   what domains host them.
4. **Identifier coverage** — how many papers have each type of persistent
   identifier (DOI, arXiv, S2, OpenAlex), which determines which engines
   can contribute to cross-engine dedup.

And a fifth dimension, **fulltext format**, that classifies each paper by
what kind of full text is available: LaTeX source + PDF (arXiv papers),
publisher PDF only, or no fulltext at all. This maps directly to the
degradation path in the reproducibility assessment: papers with no
fulltext cannot have workflow graphs extracted.

Mirrors :mod:`literature.evaluation` in convention: a pure function over
a :class:`~literature.corpus.Corpus`, called from
``scripts/06_fulltext_assessment.py``.
"""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from literature.corpus import Corpus
from literature.models import Paper

# Known OA providers and their URL patterns for provider classification.
_PROVIDER_PATTERNS: dict[str, tuple[str, ...]] = {
    "arxiv": ("arxiv.org",),
    "biorxiv": ("biorxiv.org", "medrxiv.org"),
    "europepmc": ("europepmc.org",),
    "pubmed_central": ("ncbi.nlm.nih.gov/pmc",),
    "unpaywall": ("unpaywall.org",),
    "zenodo": ("zenodo.org",),
    "figshare": ("figshare.com",),
    "osf": ("osf.io",),
    "github": ("github.com",),
    "doi": ("doi.org",),
}


def _classify_provider(paper: Paper) -> str:
    """Classify a paper's full-text provider from its pdf_url and identifiers."""
    url = (paper.pdf_url or "").lower()
    for provider, patterns in _PROVIDER_PATTERNS.items():
        if any(p in url for p in patterns):
            return provider
    if paper.full_text_source:
        return str(paper.full_text_source)
    if paper.is_preprint:
        return "preprint"
    if paper.doi:
        return "publisher"
    return "unknown"


def _provider_breakdown(papers: list[Paper]) -> dict[str, int]:
    """Count papers by full-text provider classification."""
    counts: Counter[str] = Counter()
    for paper in papers:
        counts[_classify_provider(paper)] += 1
    return dict(counts.most_common())


def assess_corpus(corpus: Corpus) -> dict:
    """Assess full-text availability across *corpus*.

    Args:
        corpus: The corpus to assess.

    Returns:
        A dict with keys ``total_papers``, ``abstract_coverage``,
        ``open_access``, ``pdf_availability``, ``fulltext_source_breakdown``,
        ``pdf_domain_breakdown``, ``identifier_coverage``, and
        ``fulltext_format``. Never raises on missing fields.
    """
    papers: list[Paper] = corpus.papers
    total = len(papers)

    has_abstract = sum(1 for p in papers if p.abstract and p.abstract.strip())
    oa_true = sum(1 for p in papers if p.is_open_access is True)
    oa_false = sum(1 for p in papers if p.is_open_access is False)
    oa_unknown = sum(1 for p in papers if p.is_open_access is None)
    has_pdf = sum(1 for p in papers if p.pdf_url)

    source_counter: Counter[str] = Counter()
    for paper in papers:
        source_counter[paper.full_text_source or "none"] += 1

    domain_counter: Counter[str] = Counter()
    for paper in papers:
        if paper.pdf_url:
            try:
                domain_counter[urlparse(paper.pdf_url).netloc] += 1
            except ValueError:
                domain_counter["unknown"] += 1

    def pct(n: int) -> float:
        """Compute percentage of *total*, or 0.0 when total is zero."""
        return round(100.0 * n / total, 1) if total > 0 else 0.0

    return {
        "total_papers": total,
        "abstract_coverage": {
            "has_abstract": has_abstract,
            "no_abstract": total - has_abstract,
            "percent_with_abstract": pct(has_abstract),
        },
        "open_access": {
            "is_oa": oa_true,
            "not_oa": oa_false,
            "unknown": oa_unknown,
            "percent_oa": pct(oa_true),
        },
        "pdf_availability": {
            "has_pdf_url": has_pdf,
            "no_pdf_url": total - has_pdf,
            "percent_with_pdf": pct(has_pdf),
        },
        "fulltext_source_breakdown": dict(source_counter.most_common()),
        "pdf_domain_breakdown": dict(domain_counter.most_common(20)),
        "identifier_coverage": {
            "doi": sum(1 for p in papers if p.doi),
            "arxiv_id": sum(1 for p in papers if p.arxiv_id),
            "s2_id": sum(1 for p in papers if p.s2_id),
            "openalex_id": sum(1 for p in papers if p.openalex_id),
            "pmid": sum(1 for p in papers if p.pmid),
        },
        "fulltext_format": {
            "latex_source_and_pdf": sum(1 for p in papers if p.arxiv_id),
            "publisher_pdf_only": sum(1 for p in papers if p.pdf_url and not p.arxiv_id),
            "no_fulltext_available": sum(1 for p in papers if not p.pdf_url and not p.arxiv_id),
        },
        "provider_breakdown": _provider_breakdown(papers),
    }

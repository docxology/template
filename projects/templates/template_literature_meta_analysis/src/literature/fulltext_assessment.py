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
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from literature.corpus import Corpus
from literature.fulltext_download import safe_filename
from literature.models import Paper

FULLTEXT_INVENTORY_SCHEMA = "literature-meta-analysis/fulltext-inventory/1"

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


def _classify_provider(paper: Paper) -> str | None:
    """Classify the provider of a directly resolvable PDF, if one exists.

    A DOI or retrieval-engine provenance alone does not identify an available
    full-text provider. Requiring ``pdf_url`` keeps this metric from counting
    metadata-only Europe PMC/publisher records as realized provider coverage.
    """
    if not paper.pdf_url:
        return None
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
    """Count papers with direct PDF URLs by full-text provider."""
    counts: Counter[str] = Counter()
    for paper in papers:
        provider = _classify_provider(paper)
        if provider is not None:
            counts[provider] += 1
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
        source = paper.full_text_source if paper.pdf_url else None
        source_counter[source or "none"] += 1

    domain_counter: Counter[str] = Counter()
    for paper in papers:
        if paper.pdf_url:
            try:
                domain_counter[urlparse(paper.pdf_url).netloc] += 1
            except Exception:  # noqa: BLE001 -- safety net: unparseable URL counts as "unknown" domain
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


def build_fulltext_inventory(corpus: Corpus, fulltext_dir: Path | None = None) -> dict:
    """Build provider-aware full-text provenance and local artifact checksums.

    Provider metadata and local artifacts are deliberately separate: an OA flag
    or URL does not prove that a PDF was downloaded, and a local checksum does
    not prove a license. License fields are reported only when the source
    record declared them; they are never inferred from open-access status.

    Args:
        corpus: Corpus whose records should be inventoried.
        fulltext_dir: Optional directory containing downloaded ``.pdf`` files.
            Paths in the result are relative to this directory and therefore do
            not leak machine-specific absolute paths.
    """
    root = Path(fulltext_dir) if fulltext_dir is not None else None
    records: list[dict[str, object]] = []
    for paper in sorted(corpus.papers, key=lambda item: item.canonical_id):
        stem = safe_filename(paper.canonical_id)
        pdf_path = root / f"{stem}.pdf" if root is not None else None
        pdf_exists = bool(pdf_path and pdf_path.is_file())
        checksum: str | None = None
        size_bytes: int | None = None
        if pdf_exists and pdf_path is not None:
            content = pdf_path.read_bytes()
            checksum = hashlib.sha256(content).hexdigest()
            size_bytes = len(content)
        if pdf_exists:
            availability = "local_pdf"
        elif paper.pdf_url:
            availability = "remote_pdf_declared"
        else:
            availability = "unavailable"
        records.append(
            {
                "paper_id": paper.canonical_id,
                "provider": _classify_provider(paper),
                "pdf_url": paper.pdf_url,
                "open_access": paper.is_open_access,
                "license": paper.license,
                "license_url": paper.license_url,
                "license_status": "declared" if (paper.license or paper.license_url) else "unknown",
                "availability": availability,
                "local_pdf": f"{stem}.pdf" if pdf_exists else None,
                "size_bytes": size_bytes,
                "checksum_sha256": checksum,
            }
        )
    return {
        "schema_version": FULLTEXT_INVENTORY_SCHEMA,
        "scope": "provider metadata plus local downloaded PDF artifacts",
        "claim_boundary": (
            "Open-access status and URLs describe declared availability; only a "
            "local PDF checksum proves the bytes present in this output tree."
        ),
        "fulltext_root": "output/fulltext" if root is not None else None,
        "summary": {
            "total_records": len(records),
            "metadata_pdf_urls": sum(1 for record in records if record["pdf_url"]),
            "local_pdfs": sum(1 for record in records if record["availability"] == "local_pdf"),
            "declared_licenses": sum(1 for record in records if record["license_status"] == "declared"),
            "unknown_licenses": sum(1 for record in records if record["license_status"] == "unknown"),
        },
        "records": records,
    }

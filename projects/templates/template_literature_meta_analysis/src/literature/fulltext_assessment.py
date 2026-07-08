"""Full-text availability assessment for literature corpora."""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from literature.corpus import Corpus
from literature.models import Paper


def assess_corpus(corpus: Corpus) -> dict:
    """Assess full-text availability across *corpus*."""
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
            except Exception:  # noqa: BLE001 -- safety net: unparseable URL counts as "unknown" domain
                domain_counter["unknown"] += 1

    def pct(n: int) -> float:
        """Process pct."""
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
        },
        "fulltext_format": {
            "latex_source_and_pdf": sum(1 for p in papers if p.arxiv_id),
            "publisher_pdf_only": sum(1 for p in papers if p.pdf_url and not p.arxiv_id),
            "no_fulltext_available": sum(1 for p in papers if not p.pdf_url and not p.arxiv_id),
        },
    }

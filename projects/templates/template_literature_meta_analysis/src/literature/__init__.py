"""Multi-source literature retrieval and corpus management."""

from __future__ import annotations

from .models import Paper, Author, Citation
from .corpus import Corpus
from .query_router import QueryRouter, QueryRoute
from .arxiv_client import search_arxiv
from .semantic_scholar import search_semantic_scholar, get_paper_details, get_citations
from .openalex_client import search_openalex, get_work_by_doi

__all__ = [
    "Paper",
    "Author",
    "Citation",
    "Corpus",
    "QueryRouter",
    "QueryRoute",
    "search_arxiv",
    "search_semantic_scholar",
    "get_paper_details",
    "get_citations",
    "search_openalex",
    "get_work_by_doi",
]

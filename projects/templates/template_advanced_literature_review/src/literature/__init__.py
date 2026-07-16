"""Multi-source literature retrieval and corpus management."""

from __future__ import annotations

from .arxiv_client import search_arxiv
from .corpus import Corpus
from .models import Author, Citation, Paper
from .openalex_client import get_work_by_doi, search_openalex
from .query_router import QueryRoute, QueryRouter
from .semantic_scholar import get_citations, get_paper_details, search_semantic_scholar

__all__ = [
    "Author",
    "Citation",
    "Corpus",
    "Paper",
    "QueryRoute",
    "QueryRouter",
    "get_citations",
    "get_paper_details",
    "get_work_by_doi",
    "search_arxiv",
    "search_openalex",
    "search_semantic_scholar",
]

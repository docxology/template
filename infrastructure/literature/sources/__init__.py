"""Literature source adapters for academic databases.

This module provides unified access to various literature databases:
- arXiv: Preprint repository
- Semantic Scholar: Academic search engine
- Unpaywall: Open access PDF resolution
- bioRxiv/medRxiv: Biology and medicine preprints
- PubMed: Medical/biology literature (NCBI)
- Europe PMC: European biomedical literature
- CrossRef: DOI-based metadata and search
- OpenAlex: Open access academic search
- DBLP: Computer science bibliography

All sources implement a common interface for searching and retrieving papers.
"""
from infrastructure.literature.sources.base import (
    SearchResult,
    LiteratureSource,
    normalize_title,
    title_similarity,
)
from infrastructure.literature.sources.arxiv import ArxivSource
from infrastructure.literature.sources.semanticscholar import SemanticScholarSource
from infrastructure.literature.sources.unpaywall import UnpaywallSource, UnpaywallResult
from infrastructure.literature.sources.biorxiv import BiorxivSource
from infrastructure.literature.sources.pubmed import PubMedSource
from infrastructure.literature.sources.europepmc import EuropePMCSource
from infrastructure.literature.sources.crossref import CrossRefSource
from infrastructure.literature.sources.openalex import OpenAlexSource
from infrastructure.literature.sources.dblp import DBLPSource

__all__ = [
    # Base classes and utilities
    'SearchResult',
    'LiteratureSource',
    'normalize_title',
    'title_similarity',
    # Source implementations
    'ArxivSource',
    'SemanticScholarSource',
    'UnpaywallSource',
    'UnpaywallResult',
    'BiorxivSource',
    'PubMedSource',
    'EuropePMCSource',
    'CrossRefSource',
    'OpenAlexSource',
    'DBLPSource',
]


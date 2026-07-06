"""Re-export all built-in connector implementations."""

from __future__ import annotations

from infrastructure.search.connectors.impl.arxiv import ArxivConnector
from infrastructure.search.connectors.impl.biorxiv import BiorxivConnector
from infrastructure.search.connectors.impl.crossref import CrossrefConnector
from infrastructure.search.connectors.impl.europepmc import EuropePMCConnector
from infrastructure.search.connectors.impl.openalex import OpenAlexConnector
from infrastructure.search.connectors.impl.pdb import PDBConnector
from infrastructure.search.connectors.impl.semantic_scholar import SemanticScholarConnector
from infrastructure.search.connectors.impl.uniprot import UniProtConnector

#: All built-in connectors in canonical order.
_ALL_CONNECTORS = [
    OpenAlexConnector,
    ArxivConnector,
    SemanticScholarConnector,
    CrossrefConnector,
    EuropePMCConnector,
    BiorxivConnector,
    UniProtConnector,
    PDBConnector,
]

__all__ = [
    "ArxivConnector",
    "BiorxivConnector",
    "CrossrefConnector",
    "EuropePMCConnector",
    "OpenAlexConnector",
    "PDBConnector",
    "SemanticScholarConnector",
    "UniProtConnector",
    "_ALL_CONNECTORS",
]

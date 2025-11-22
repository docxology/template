"""Literature Search Module.

This module provides tools for searching scientific literature, downloading PDFs,
and managing references.
"""

from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.api import SearchResult

__all__ = ["LiteratureSearch", "LiteratureConfig", "SearchResult"]


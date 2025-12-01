"""Literature Search Module.

This module provides tools for searching scientific literature, downloading PDFs,
and managing references with comprehensive tracking.

Classes:
    LiteratureSearch: Main entry point for literature search functionality.
    LiteratureConfig: Configuration for literature search operations.
    SearchResult: Normalized search result from any source.
    PDFHandler: Handles PDF downloading and text extraction.
    ReferenceManager: Manages references and BibTeX generation.
    LibraryIndex: Manages JSON library index for paper tracking.
    LibraryEntry: Represents a paper in the library index.

Output Files:
    literature/references.bib - BibTeX entries
    literature/library.json - JSON index with full metadata
    literature/pdfs/ - Downloaded PDFs (named by citation key)
"""

from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.api import SearchResult
from infrastructure.literature.pdf_handler import PDFHandler
from infrastructure.literature.reference_manager import ReferenceManager
from infrastructure.literature.library_index import LibraryIndex, LibraryEntry

__all__ = [
    "LiteratureSearch",
    "LiteratureConfig",
    "SearchResult",
    "PDFHandler",
    "ReferenceManager",
    "LibraryIndex",
    "LibraryEntry",
]

"""Library management and indexing."""
from infrastructure.literature.library.index import LibraryIndex, LibraryEntry
from infrastructure.literature.library.stats import (
    get_library_statistics,
    format_library_stats_display,
)
from infrastructure.literature.library.references import ReferenceManager
from infrastructure.literature.library.clear import (
    clear_pdfs,
    clear_summaries,
    clear_library,
)

__all__ = [
    "LibraryIndex",
    "LibraryEntry",
    "get_library_statistics",
    "format_library_stats_display",
    "ReferenceManager",
    "clear_pdfs",
    "clear_summaries",
    "clear_library",
]



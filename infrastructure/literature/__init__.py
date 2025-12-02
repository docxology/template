"""Literature Search Module.

This module provides tools for searching scientific literature, downloading PDFs,
and managing references with comprehensive tracking.

Classes:
    LiteratureSearch: Main entry point for literature search functionality.
    LiteratureConfig: Configuration for literature search operations.
    SearchResult: Normalized search result from any source.
    UnpaywallResult: Result from Unpaywall API lookup.
    UnpaywallSource: Client for Unpaywall open access PDF resolution.
    PDFHandler: Handles PDF downloading and text extraction.
    ReferenceManager: Manages references and BibTeX generation.
    LibraryIndex: Manages JSON library index for paper tracking.
    LibraryEntry: Represents a paper in the library index.
    DownloadResult: Result of a PDF download attempt with status tracking.

New Modules (Thin Orchestrator Pattern):
    LiteratureWorkflow: High-level workflow orchestration.
    ProgressTracker: Progress persistence and resumability.
    PaperSummarizer: AI-powered paper summarization.
    SummaryQualityValidator: Summary quality validation.
    SummarizationResult: Summary generation result.
    ProgressEntry: Individual paper progress tracking.
    SummarizationProgress: Overall progress state.

Output Files:
    literature/references.bib - BibTeX entries
    literature/library.json - JSON index with full metadata
    literature/summarization_progress.json - Progress tracking
    literature/summaries/ - AI-generated summaries
    literature/pdfs/ - Downloaded PDFs (named by citation key)
"""

from infrastructure.literature.core import LiteratureSearch, DownloadResult
from infrastructure.literature.config import LiteratureConfig, BROWSER_USER_AGENTS
from infrastructure.literature.api import (
    SearchResult,
    UnpaywallResult,
    UnpaywallSource,
    ArxivSource,
    BiorxivSource,
)
from infrastructure.literature.pdf_handler import PDFHandler
from infrastructure.literature.reference_manager import ReferenceManager
from infrastructure.literature.library_index import LibraryIndex, LibraryEntry
from infrastructure.literature.workflow import LiteratureWorkflow, WorkflowResult
from infrastructure.literature.progress import ProgressTracker, ProgressEntry, SummarizationProgress
from infrastructure.literature.summarizer import PaperSummarizer, SummaryQualityValidator, SummarizationResult

__all__ = [
    # Original modules
    "LiteratureSearch",
    "LiteratureConfig",
    "BROWSER_USER_AGENTS",
    "SearchResult",
    "UnpaywallResult",
    "UnpaywallSource",
    "ArxivSource",
    "BiorxivSource",
    "PDFHandler",
    "ReferenceManager",
    "LibraryIndex",
    "LibraryEntry",
    "DownloadResult",
    # New thin orchestrator modules
    "LiteratureWorkflow",
    "WorkflowResult",
    "ProgressTracker",
    "ProgressEntry",
    "SummarizationProgress",
    "PaperSummarizer",
    "SummaryQualityValidator",
    "SummarizationResult",
]

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

Enhanced Modules (v2.0):
    StructuredLogger: Structured logging with JSON format and progress indicators.
    LiteratureReporter: Comprehensive reporting with JSON/CSV/HTML export.
    DomainDetector: Automatic domain detection for context-aware prompts.
    SummaryParser: Extract structured metadata from markdown summaries.
    PaperAnalyzer: Analyze paper structure and content characteristics.
    ContextBuilder: Build rich context for enhanced LLM prompts.

Output Files:
    data/references.bib - BibTeX entries
    data/library.json - JSON index with full metadata
    data/summarization_progress.json - Progress tracking
    data/summaries/ - AI-generated summaries
    data/pdfs/ - Downloaded PDFs (named by citation key)
    data/output/ - Generated reports and visualizations (JSON/CSV/HTML/PNG)
"""

# Core functionality
from infrastructure.literature.core import (
    LiteratureSearch,
    DownloadResult,
    LiteratureConfig,
    BROWSER_USER_AGENTS,
)
# Sources
from infrastructure.literature.sources import (
    SearchResult,
    UnpaywallResult,
    UnpaywallSource,
    ArxivSource,
    BiorxivSource,
)
# PDF handling
from infrastructure.literature.pdf import PDFHandler
# Library management
from infrastructure.literature.library import (
    LibraryIndex,
    LibraryEntry,
    ReferenceManager,
    get_library_statistics,
    format_library_stats_display,
)
# Workflow
from infrastructure.literature.workflow import (
    LiteratureWorkflow,
    WorkflowResult,
    ProgressTracker,
    ProgressEntry,
    SummarizationProgress,
)
# Summarization
from infrastructure.literature.summarization import (
    SummarizationEngine,
    PaperSummarizer,  # Alias for backward compatibility
    SummaryQualityValidator,
    SummarizationResult,
)
# LLM operations
from infrastructure.literature.llm import (
    PaperSelector,
    PaperSelectionConfig,
    LiteratureLLMOperations,
    LLMOperationResult,
)
# Reporting
from infrastructure.literature.reporting import LiteratureReporter

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
    "SummarizationEngine",
    "PaperSummarizer",  # Alias for backward compatibility
    "SummaryQualityValidator",
    "SummarizationResult",
    # NEW: Advanced literature operations
    "PaperSelector",
    "PaperSelectionConfig",
    "LiteratureLLMOperations",
    "LLMOperationResult",
    # Library statistics
    "get_library_statistics",
    "format_library_stats_display",
]

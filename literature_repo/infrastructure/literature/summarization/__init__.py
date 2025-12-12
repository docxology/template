"""Summarization module for literature processing.

This module provides comprehensive paper summarization with multi-stage
generation, quality validation, and context extraction. The system uses
intelligent PDF text processing with section prioritization, structured
context extraction, and automatic refinement based on validation feedback.

Classes:
    SummarizationEngine: Main interface for paper summarization with multi-stage refinement
    SummaryQualityValidator: Validates summary quality and detects issues
    SummarizationResult: Result container for summarization operations
    SummarizationContext: Structured context (internal use)
    ValidationResult: Result of summary validation
    run_summarize: Orchestrator function for summarization workflow

The module implements a multi-stage approach:
1. PDF text extraction with section prioritization
2. Structured context extraction (abstract, intro, conclusion, key terms)
3. Draft generation using enhanced prompts
4. Quality validation with detailed feedback
5. Automatic refinement addressing validation issues
"""

from infrastructure.literature.summarization.models import (
    SummarizationResult,
    SummarizationContext,
    SummarizationProgressEvent,
    ValidationResult,
)
from infrastructure.literature.summarization.core import SummarizationEngine
from infrastructure.literature.summarization.validator import SummaryQualityValidator
from infrastructure.literature.summarization.orchestrator import (
    run_summarize,
    run_extract_text,
    find_papers_needing_summary,
    find_papers_needing_extraction,
    get_library_analysis,
)
from infrastructure.literature.summarization.streaming import stream_with_progress

# Backward compatibility aliases
PaperSummarizer = SummarizationEngine

__all__ = [
    # Main classes
    "SummarizationEngine",
    "PaperSummarizer",  # Alias for backward compatibility
    "SummaryQualityValidator",
    "SummarizationResult",
    # Internal models (exported for advanced use)
    "SummarizationContext",
    "SummarizationProgressEvent",
    "ValidationResult",
    # Orchestration
    "run_summarize",
    "run_extract_text",
    "find_papers_needing_summary",
    "find_papers_needing_extraction",
    "get_library_analysis",
    # Streaming
    "stream_with_progress",
]

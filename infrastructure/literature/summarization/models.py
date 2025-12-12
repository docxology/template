"""Data models for summarization module.

This module defines all data structures used throughout the summarization
workflow, including results, context, and validation outcomes.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SummarizationResult:
    """Result of a paper summarization attempt.

    Contains the summary text, metadata, and quality metrics.

    Attributes:
        citation_key: Unique identifier for the paper.
        success: Whether summarization succeeded.
        summary_text: Generated summary text if successful.
        input_chars: Number of characters in extracted PDF text.
        input_words: Number of words in extracted PDF text.
        output_words: Number of words in generated summary.
        generation_time: Time taken for summarization in seconds.
        attempts: Number of attempts made.
        error: Error message if summarization failed.
        quality_score: Quality validation score (0.0 to 1.0).
        validation_errors: List of quality validation issues.
        summary_path: Path to the saved summary file if successful.
        skipped: Whether this summary was skipped because it already exists.
    """
    citation_key: str
    success: bool
    summary_text: Optional[str] = None
    input_chars: int = 0
    input_words: int = 0
    output_words: int = 0
    generation_time: float = 0.0
    attempts: int = 0
    error: Optional[str] = None
    quality_score: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    summary_path: Optional[Path] = None
    skipped: bool = False

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio (output/input words)."""
        return self.output_words / max(1, self.input_words)

    @property
    def words_per_second(self) -> float:
        """Calculate generation speed in words per second."""
        return self.output_words / max(0.001, self.generation_time)


@dataclass
class SummarizationContext:
    """Structured context for summarization.

    Contains extracted and prioritized sections from the paper to provide
    focused context for the LLM during summarization.

    Attributes:
        title: Paper title.
        abstract: Abstract text.
        introduction: Introduction section (first portion).
        conclusion: Conclusion section (last portion).
        key_terms: List of key terms extracted from title and abstract.
        equations: List of mathematical equations/formulations found.
        methods: Methodology section (optional).
        results: Results section (optional).
        discussion: Discussion section (optional).
        full_text: Full PDF text for reference.
    """
    title: str
    abstract: str
    introduction: str
    conclusion: str
    key_terms: List[str]
    equations: List[str]
    methods: Optional[str] = None
    results: Optional[str] = None
    discussion: Optional[str] = None
    full_text: str = ""

    def get_prioritized_text(self, max_chars: Optional[int] = None) -> str:
        """Get prioritized text combining key sections.
        
        Args:
            max_chars: Optional maximum characters to return.
            
        Returns:
            Prioritized text with key sections.
        """
        parts = []
        
        # Add title
        if self.title:
            parts.append(f"Title: {self.title}\n")
        
        # Add abstract
        if self.abstract:
            parts.append(f"Abstract:\n{self.abstract}\n")
        
        # Add introduction
        if self.introduction:
            parts.append(f"Introduction:\n{self.introduction}\n")
        
        # Add conclusion
        if self.conclusion:
            parts.append(f"Conclusion:\n{self.conclusion}\n")
        
        # Add key terms
        if self.key_terms:
            parts.append(f"Key Terms: {', '.join(self.key_terms[:10])}\n")
        
        text = "\n".join(parts)
        
        if max_chars and len(text) > max_chars:
            # Truncate while preserving structure
            return text[:max_chars] + "\n[... truncated ...]"
        
        return text


@dataclass
class ValidationResult:
    """Result of summary validation.

    Contains detailed validation results including specific issues,
    suggestions, and quality metrics.

    Attributes:
        is_valid: Whether summary passed validation.
        score: Quality score (0.0 to 1.0).
        errors: List of critical errors found.
        warnings: List of warnings (non-critical issues).
        missing_key_terms: List of key terms that should be mentioned.
        quote_count: Number of quotes/evidence found.
        repetition_issues: List of specific repetition problems.
        suggestions: List of suggestions for improvement.
    """
    is_valid: bool
    score: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_key_terms: List[str] = field(default_factory=list)
    quote_count: int = 0
    repetition_issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def has_hard_failure(self) -> bool:
        """Check if validation result indicates a hard failure.
        
        Hard failures are issues that should cause immediate rejection
        without retry: title mismatch, major hallucination, severe repetition.
        
        Returns:
            True if hard failure detected.
        """
        hard_failure_keywords = [
            "title mismatch",
            "major hallucination",
            "severe repetition",
        ]
        
        error_text = " ".join(self.errors).lower()
        return any(keyword in error_text for keyword in hard_failure_keywords)

    def get_refinement_guidance(self) -> str:
        """Get guidance text for refining the summary.
        
        Returns:
            Formatted guidance text with specific issues and suggestions.
        """
        guidance_parts = []
        
        if self.errors:
            guidance_parts.append("Critical Issues:")
            for error in self.errors:
                guidance_parts.append(f"  - {error}")
        
        if self.missing_key_terms:
            guidance_parts.append(f"\nMissing Key Terms: {', '.join(self.missing_key_terms[:10])}")
        
        if self.quote_count < 3:
            guidance_parts.append(f"\nInsufficient Evidence: Found {self.quote_count} quotes (need at least 3)")
        
        if self.repetition_issues:
            guidance_parts.append("\nRepetition Issues:")
            for issue in self.repetition_issues:
                guidance_parts.append(f"  - {issue}")
        
        if self.suggestions:
            guidance_parts.append("\nSuggestions:")
            for suggestion in self.suggestions:
                guidance_parts.append(f"  - {suggestion}")
        
        return "\n".join(guidance_parts)


@dataclass
class SummarizationProgressEvent:
    """Progress event for real-time summarization updates.
    
    Emitted at each stage of the summarization process to provide
    real-time feedback on progress, timing, and status.
    
    Attributes:
        citation_key: Unique identifier for the paper being processed.
        stage: Stage name ("pdf_extraction", "context_extraction", 
              "draft_generation", "validation", "refinement").
        status: Event status ("started", "completed", "failed").
        message: Optional human-readable message describing the event.
        metadata: Dictionary with additional metadata (timing, counts, etc.).
        timestamp: Unix timestamp when the event occurred.
    """
    citation_key: str
    stage: str  # "pdf_extraction", "context_extraction", "draft_generation", "validation", "refinement"
    status: str  # "started", "completed", "failed"
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

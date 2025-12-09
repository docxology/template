"""Literature paper summarization functionality.

This module provides comprehensive paper summarization capabilities,
including text extraction, quality validation, and AI-powered summary
generation with retry logic and hallucination detection.

Classes:
    PaperSummarizer: Main interface for paper summarization
    SummaryQualityValidator: Validates summary quality and detects issues
    SummarizationResult: Result container for summarization operations
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, TYPE_CHECKING

from infrastructure.core.logging_utils import get_logger, log_success
from infrastructure.core.exceptions import LLMConnectionError, FileOperationError
from infrastructure.literature.sources import SearchResult
from infrastructure.validation.pdf_validator import extract_text_from_pdf, PDFValidationError

if TYPE_CHECKING:
    from infrastructure.llm import LLMClient

logger = get_logger(__name__)


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


class SummaryQualityValidator:
    """Validates quality of generated paper summaries.

    Performs multiple quality checks including:
    - Length validation
    - Required section presence
    - Hallucination detection
    - Repetition analysis
    """

    def __init__(self, min_words: int = 200):
        """Initialize quality validator.

        Args:
            min_words: Minimum word count for valid summaries.
        """
        self.min_words = min_words

    def validate_summary(
        self,
        summary: str,
        pdf_text: str,
        citation_key: str
    ) -> Tuple[bool, float, List[str]]:
        """Validate summary quality comprehensively.

        Args:
            summary: Generated summary text.
            pdf_text: Original PDF text for comparison.
            citation_key: Citation key for logging.

        Returns:
            Tuple of (is_valid, quality_score, error_messages).
        """
        errors = []
        score = 1.0

        # Length check
        word_count = len(summary.split())
        if word_count < self.min_words:
            errors.append(f"Too short: {word_count} words (minimum {self.min_words})")
            score -= 0.5

        # Optional sections check - only log missing sections, don't penalize score
        # This makes the validator more lenient and focused on content quality rather than structure
        optional_sections = [
            ("Overview", ["### Overview", "### Summary", "### Introduction"]),
            ("Key Contributions", ["### Key Contributions", "### Contributions", "### Main Contributions"]),
            ("Methodology", ["### Methodology", "### Methods", "### Approach"]),
            ("Results", ["### Results", "### Findings", "### Outcomes"]),
            ("Limitations", ["### Limitations and Future Work", "### Limitations", "### Future Work", "### Discussion"])
        ]

        missing_sections = []
        for section_name, patterns in optional_sections:
            if not any(pattern in summary for pattern in patterns):
                missing_sections.append(section_name)

        # Only log missing sections as informational, don't penalize the score
        if missing_sections:
            logger.debug(f"Optional sections not found: {', '.join(missing_sections)} (not penalized)")

        # Repetition check
        if self._detect_repetition(summary):
            errors.append("Excessive repetition detected")
            score -= 0.2

        # Hallucination check
        is_hallucinated, hallucination_reason = self._detect_hallucination(summary, pdf_text)
        if is_hallucinated:
            errors.append(f"Hallucination detected: {hallucination_reason}")
            score -= 0.4

        # Off-topic content check
        off_topic_errors = self._detect_off_topic_content(summary)
        if off_topic_errors:
            errors.extend(off_topic_errors)
            score -= 0.1 * len(off_topic_errors)

        # Ensure score doesn't go below 0
        score = max(0.0, score)

        is_valid = len(errors) == 0
        return is_valid, score, errors

    def _detect_repetition(self, summary: str, threshold: float = 0.5) -> bool:
        """Detect excessive repetition in summary."""
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
        if len(sentences) < 5:
            return False

        seen = set()
        duplicates = 0
        for sent in sentences:
            sent_normalized = sent.lower()[:80]
            if sent_normalized in seen and len(sent_normalized) > 20:
                duplicates += 1
            seen.add(sent_normalized)

        repetition_ratio = duplicates / len(sentences) if sentences else 0
        return repetition_ratio > threshold

    def _detect_hallucination(self, summary: str, pdf_text: str) -> Tuple[bool, str]:
        """Detect potential hallucination by checking content against source."""
        hallucination_indicators = [
            (r"I'm happy to help", "AI assistant language"),
            (r"As an AI", "AI self-reference"),
            (r"I am an AI", "AI self-reference"),
            (r"as an artificial intelligence", "AI self-reference"),
            (r'\b(email|letter|correspondence)\b', "inappropriate content type"),
            (r'\bdear (sir|madam|professor)\b', "inappropriate greeting"),
            (r'\bhi\b.*\bthere\b', "inappropriate greeting"),
            (r"```python", "code in text summary"),
            (r"def \w+\(", "code in text summary"),
            (r"import \w+", "code in text summary"),
        ]

        summary_lower = summary.lower()
        pdf_lower = pdf_text.lower()

        for pattern, reason in hallucination_indicators:
            if re.search(pattern, summary_lower, re.IGNORECASE):
                # Check if pattern actually appears in source PDF
                if not re.search(pattern, pdf_lower, re.IGNORECASE):
                    return True, f"Content '{pattern}' not found in source PDF ({reason})"

        # Domain-specific checks for physics/math papers
        physics_indicators = [
            r'\b(collision|energy|speed.*sound|heavy.*ion|quark|gluon|QCD)\b',
            r'\b(velocity|momentum|temperature|pressure)\b',
            r'\b(beam|detector|experiment|measurement)\b'
        ]

        has_physics = any(re.search(p, pdf_lower) for p in physics_indicators)

        if has_physics:
            physics_in_summary = any(re.search(p, summary_lower) for p in physics_indicators)
            if not physics_in_summary:
                return True, "Physics paper summary lacks physics terminology"

        return False, ""

    def _detect_off_topic_content(self, summary: str) -> List[str]:
        """Detect off-topic or inappropriate content."""
        errors = []
        summary_lower = summary.lower()

        off_topic_patterns = [
            (r'\b(email|letter|correspondence)\b', "inappropriate content reference"),
            (r'\bdear (sir|madam|professor)\b', "inappropriate greeting"),
            (r'\bhi\b.*\bthere\b', "inappropriate greeting"),
            (r"I'm happy to help", "AI assistant language"),
            (r"As an AI", "AI self-reference"),
            (r"```python", "code content"),
            (r"Here is.*summary", "boilerplate text"),
        ]

        for pattern, reason in off_topic_patterns:
            if re.search(pattern, summary_lower, re.IGNORECASE):
                errors.append(f"Off-topic content: {reason}")

        return errors


class PaperSummarizer:
    """Main interface for paper summarization with quality validation.

    Orchestrates the complete summarization workflow including:
    - PDF text extraction
    - AI summary generation with retries
    - Quality validation and scoring
    - Progress tracking integration

    Attributes:
        llm_client: LLM client for summary generation.
        quality_validator: Quality validation instance.
        max_pdf_chars: Maximum characters to send to LLM.
    """

    def __init__(
        self,
        llm_client: "LLMClient",
        quality_validator: Optional[SummaryQualityValidator] = None,
        max_pdf_chars: int = 50000
    ):
        """Initialize paper summarizer.

        Args:
            llm_client: Configured LLM client for summary generation.
            quality_validator: Quality validator instance (created if None).
            max_pdf_chars: Maximum PDF characters to send to LLM.
        """
        self.llm_client = llm_client
        self.quality_validator = quality_validator or SummaryQualityValidator()
        self.max_pdf_chars = max_pdf_chars

    def summarize_paper(
        self,
        result: SearchResult,
        pdf_path: Path,
        max_retries: int = 2
    ) -> SummarizationResult:
        """Generate summary for a single paper with quality validation.

        Args:
            result: Search result with paper metadata.
            pdf_path: Path to PDF file.
            max_retries: Maximum retry attempts for generation.

        Returns:
            SummarizationResult with summary and metadata.
        """
        citation_key = pdf_path.stem
        start_time = time.time()

        # Extract text from PDF
        try:
            # Log file size for context before extraction
            file_size = pdf_path.stat().st_size
            logger.debug(f"Starting PDF text extraction for {pdf_path.name} ({file_size:,} bytes)")

            pdf_text = extract_text_from_pdf(pdf_path)
            if not pdf_text or len(pdf_text.strip()) < 100:
                logger.warning(f"PDF extraction yielded insufficient text: {len(pdf_text) if pdf_text else 0} chars, {len(pdf_text.split()) if pdf_text else 0} words from {pdf_path.name}")
                return SummarizationResult(
                    citation_key=citation_key,
                    success=False,
                    input_chars=len(pdf_text) if pdf_text else 0,
                    input_words=len(pdf_text.split()) if pdf_text else 0,
                    generation_time=time.time() - start_time,
                    attempts=1,
                    error="Insufficient text extracted from PDF (less than 100 characters)"
                )
        except PDFValidationError as e:
            logger.error(f"PDF text extraction failed for {pdf_path.name}: {e}")
            return SummarizationResult(
                citation_key=citation_key,
                success=False,
                input_chars=0,
                input_words=0,
                generation_time=time.time() - start_time,
                attempts=1,
                error=f"PDF extraction failed: {e}"
            )

        input_chars = len(pdf_text)
        input_words = len(pdf_text.split())

        logger.info(f"Extracted {input_chars:,} chars, {input_words:,} words from {pdf_path.name}")

        # Content analysis for logging
        physics_terms = ['collision', 'energy', 'quark', 'gluon', 'temperature', 'velocity']
        math_terms = ['convex', 'Brunn-Minkowski', 'function', 'nonnegative']

        has_physics = any(term in pdf_text.lower() for term in physics_terms)
        has_math = any(term in pdf_text.lower() for term in math_terms)

        if has_physics and has_math:
            logger.debug(f"PDF contains mixed physics/math content - quality validation enabled")
        elif has_physics:
            logger.debug("PDF appears physics-focused")
        elif has_math:
            logger.debug("PDF appears math-focused")

        # Generate summary with retries
        summary = None
        attempts = 0

        for attempt in range(max_retries + 1):
            attempts = attempt + 1
            try:
                summary = self._generate_summary(result, pdf_text)

                # Length check - primary acceptance criterion
                word_count = len(summary.split()) if summary else 0
                min_acceptable_words = 150  # Reasonable threshold for substantive content

                if word_count < min_acceptable_words:
                    logger.warning(f"Attempt {attempts}: Summary too short ({word_count} words, minimum {min_acceptable_words}), retrying...")
                    continue

                # Quality validation (now more lenient)
                is_valid, quality_score, validation_errors = self.quality_validator.validate_summary(
                    summary, pdf_text, citation_key
                )

                # Accept summaries that meet length requirements, even with minor quality issues
                # Only retry on critical issues (hallucination, severe repetition) or very low quality scores
                critical_issues = any(
                    "hallucination" in error.lower() or "excessive repetition" in error.lower()
                    for error in validation_errors
                )

                if not is_valid and critical_issues and quality_score < 0.3:
                    logger.warning(f"Attempt {attempts}: Critical quality issues - {', '.join(validation_errors)}")
                    if attempt < max_retries:
                        logger.info("Retrying summary generation...")
                        continue
                    else:
                        logger.warning(f"Max retries reached, accepting summary despite quality issues")
                        break
                else:
                    logger.info(f"Attempt {attempts}: Summary accepted ({word_count} words, score: {quality_score:.2f})")
                    break

            except LLMConnectionError as e:
                logger.error(f"LLM error (attempt {attempts}): {e}")
                if attempt == max_retries:
                    break

        generation_time = time.time() - start_time

        if not summary:
            return SummarizationResult(
                citation_key=citation_key,
                success=False,
                input_chars=input_chars,
                input_words=input_words,
                generation_time=generation_time,
                attempts=attempts,
                error="Summary generation failed after all retries"
            )

        output_words = len(summary.split())

        # Final quality check for reporting
        _, final_score, final_errors = self.quality_validator.validate_summary(
            summary, pdf_text, citation_key
        )

        return SummarizationResult(
            citation_key=citation_key,
            success=True,
            summary_text=summary,
            input_chars=input_chars,
            input_words=input_words,
            output_words=output_words,
            generation_time=generation_time,
            attempts=attempts,
            quality_score=final_score,
            validation_errors=final_errors
        )

    def _generate_summary(self, result: SearchResult, pdf_text: str) -> str:
        """Generate summary using LLM with paper-specific prompt."""
        from infrastructure.llm.templates import PaperSummarization

        # Truncate if too long
        if len(pdf_text) > self.max_pdf_chars:
            pdf_text = pdf_text[:self.max_pdf_chars] + "\n\n[... truncated for summarization ...]"

        # Create paper summarization prompt
        template = PaperSummarization()
        prompt = template.render(
            title=result.title,
            authors=', '.join(result.authors) if result.authors else 'Unknown',
            year=str(result.year) if result.year else 'Unknown',
            source=f"{result.source} ({result.venue or 'N/A'})",
            text=pdf_text
        )

        # Generate summary
        from infrastructure.llm import GenerationOptions
        options = GenerationOptions(
            temperature=0.3,  # Lower temperature for more consistent summaries
            max_tokens=2048
        )

        summary = self.llm_client.query(prompt, options=options, reset_context=True)
        return self._clean_summary_content(summary)

    def _clean_summary_content(self, summary: str) -> str:
        """Remove unwanted sections and content from summary."""
        lines = summary.split('\n')
        cleaned_lines = []
        skip_section = False

        unwanted_sections = [
            '### References',
            '### Citation',
            '### BibTex',
            '### Abstract',
            '### Keywords',
            '### Tags',
            '### Summary',
            'Note:',
            'Note: The above',
            'This summary was generated',
            'generated by an AI model'
        ]

        for line in lines:
            line_lower = line.lower().strip()
            # Check if this line starts an unwanted section
            if any(line_lower.startswith(unwanted.lower()) for unwanted in unwanted_sections):
                skip_section = True
                continue

            # Stop skipping when we hit a valid section header
            if line.startswith('### ') and skip_section:
                skip_section = False

            if not skip_section:
                cleaned_lines.append(line)

        cleaned = '\n'.join(cleaned_lines).strip()

        # Remove trailing disclaimers
        disclaimer_patterns = [
            r'Note:.*$',
            r'This summary.*$',
            r'generated by.*$'
        ]

        for pattern in disclaimer_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

        return cleaned.strip()

    def save_summary(
        self,
        result: SearchResult,
        summary_result: SummarizationResult,
        output_dir: Path
    ) -> Path:
        """Save summary to markdown file.

        Args:
            result: Search result with paper metadata.
            summary_result: Summarization result to save.
            output_dir: Directory for summary files.

        Returns:
            Path to saved summary file.

        Raises:
            FileOperationError: If saving fails.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        citation_key = summary_result.citation_key
        output_path = output_dir / f"{citation_key}_summary.md"

        # Build markdown content
        content = f"""# {result.title}

**Authors:** {', '.join(result.authors) if result.authors else 'Unknown'}

**Year:** {result.year or 'Unknown'}

**Source:** {result.source}

**Venue:** {result.venue or 'N/A'}

**DOI:** {result.doi or 'N/A'}

**PDF:** [{citation_key}.pdf](../pdfs/{citation_key}.pdf)

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

{summary_result.summary_text}

---

**Summary Statistics:**
- Input: {summary_result.input_words:,} words ({summary_result.input_chars:,} chars)
- Output: {summary_result.output_words:,} words
- Compression: {summary_result.compression_ratio:.2f}x
- Generation: {summary_result.generation_time:.1f}s ({summary_result.words_per_second:.1f} words/sec)
- Quality Score: {summary_result.quality_score:.2f}/1.0
- Attempts: {summary_result.attempts}

{f"**Quality Issues:** {', '.join(summary_result.validation_errors)}" if summary_result.validation_errors else "**Quality Check:** Passed"}
"""

        try:
            output_path.write_text(content)
            file_size = output_path.stat().st_size
            logger.info(f"Saved summary: {output_path.name} ({file_size:,} bytes) -> {output_path}")
            return output_path
        except Exception as e:
            raise FileOperationError(
                f"Failed to save summary: {e}",
                context={"path": str(output_path)}
            )

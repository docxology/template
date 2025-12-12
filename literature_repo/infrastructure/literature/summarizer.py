"""Literature paper summarization functionality.

**DEPRECATED**: This module is deprecated. Use `infrastructure.literature.summarization` 
module instead, which provides a modular, multi-stage summarization system with 
enhanced real-time logging and progress tracking.

The `PaperSummarizer` class is available as an alias (`PaperSummarizer = SummarizationEngine`)
in `infrastructure.literature.summarization` for backward compatibility.

This file is kept for backward compatibility but will be removed in a future version.

Classes:
    PaperSummarizer: Main interface for paper summarization (DEPRECATED)
    SummaryQualityValidator: Validates summary quality and detects issues (DEPRECATED)
    SummarizationResult: Result container for summarization operations (DEPRECATED)
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
    from infrastructure.llm.core.client import LLMClient

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
        citation_key: str,
        paper_title: Optional[str] = None
    ) -> Tuple[bool, float, List[str]]:
        """Validate summary quality comprehensively.

        Args:
            summary: Generated summary text.
            pdf_text: Original PDF text for comparison.
            citation_key: Citation key for logging.
            paper_title: Paper title for title matching validation (optional but recommended).

        Returns:
            Tuple of (is_valid, quality_score, error_messages).
        """
        errors = []
        score = 1.0

        # CRITICAL: Title matching check (if paper title provided)
        if paper_title:
            title_match, title_error = self._validate_title_match(summary, paper_title)
            if not title_match:
                errors.append(f"Title mismatch: {title_error}")
                score -= 0.8  # Severe penalty - wrong title is critical error
                logger.warning(f"Title mismatch detected for {citation_key}: {title_error}")

        # CRITICAL: Major hallucination check (wrong topic entirely)
        if paper_title:
            major_hallucination, hallucination_reason = self._detect_major_hallucination(
                summary, pdf_text, paper_title
            )
            if major_hallucination:
                errors.append(f"Major hallucination detected: {hallucination_reason}")
                score -= 0.9  # Critical error - summary about completely wrong topic
                logger.error(f"Major hallucination for {citation_key}: {hallucination_reason}")

        # Content topic matching check removed - term-based validation is unreliable

        # Quote presence check (warning, not critical)
        has_quotes, quote_count = self._validate_quotes_present(summary)
        if not has_quotes:
            errors.append(f"No quotes/evidence found (expected at least 3, found {quote_count})")
            score -= 0.2  # Moderate penalty - quotes are important but not critical

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

        # Severe repetition check (critical failure)
        has_severe_repetition, severe_repetition_reason = self._detect_severe_repetition(summary)
        if has_severe_repetition:
            errors.append(f"Severe repetition detected: {severe_repetition_reason}")
            score -= 1.0  # Critical penalty - severe repetition is a hard failure
        
        # Standard repetition check (now includes section, paragraph, and sentence level)
        has_section_repetition = self._detect_section_repetition(summary)
        has_paragraph_repetition = self._detect_paragraph_repetition(summary, threshold=0.5)  # Lowered threshold
        has_sentence_repetition = self._detect_sentence_repetition(summary)
        
        if has_section_repetition:
            errors.append("Section-level repetition detected (duplicate section headers)")
            score -= 0.5  # More severe penalty for section repetition
        elif has_paragraph_repetition:
            errors.append("Paragraph-level repetition detected")
            score -= 0.3  # Moderate penalty for paragraph repetition
        elif has_sentence_repetition:
            errors.append("Sentence-level repetition detected")
            score -= 0.2  # Lower penalty for sentence repetition

        # Hallucination check (general patterns)
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

    def _detect_sentence_repetition(self, summary: str, threshold: float = 0.5) -> bool:
        """Detect excessive sentence-level repetition in summary."""
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

    def _detect_section_repetition(self, summary: str) -> bool:
        """Detect duplicate section headers in summary.
        
        Returns True if the same section title appears multiple times.
        """
        # Extract all markdown headers (### and ##)
        header_pattern = re.compile(r'^#{2,3}\s+(.+)$', re.MULTILINE)
        headers = header_pattern.findall(summary)
        
        if len(headers) < 2:
            return False
        
        # Normalize headers (lowercase, strip)
        normalized_headers = [h.lower().strip() for h in headers]
        
        # Check for duplicates
        seen_headers = set()
        for header in normalized_headers:
            if header in seen_headers:
                logger.debug(f"Duplicate section detected: {header}")
                return True
            seen_headers.add(header)
        
        return False

    def _detect_paragraph_repetition(self, summary: str, threshold: float = 0.5) -> bool:
        """Detect near-duplicate paragraphs in summary.
        
        Args:
            summary: Summary text to check.
            threshold: Similarity threshold (0.0 to 1.0) for considering paragraphs duplicates.
                      Lowered from 0.8 to 0.5 for more aggressive detection.
            
        Returns:
            True if excessive paragraph repetition detected.
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in summary.split('\n\n') if p.strip() and len(p.strip()) > 50]
        
        if len(paragraphs) < 2:
            return False
        
        # Normalize paragraphs for comparison
        def normalize_text(text: str) -> str:
            """Normalize text for comparison."""
            # Lowercase, remove extra whitespace, remove punctuation
            text = text.lower()
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s]', '', text)
            return text.strip()
        
        normalized_paras = [normalize_text(p) for p in paragraphs]
        
        # Compare paragraphs for similarity
        duplicates = 0
        for i, para1 in enumerate(normalized_paras):
            for j, para2 in enumerate(normalized_paras[i+1:], start=i+1):
                # Calculate simple similarity (word overlap ratio)
                words1 = set(para1.split())
                words2 = set(para2.split())
                
                if len(words1) == 0 or len(words2) == 0:
                    continue
                
                intersection = words1.intersection(words2)
                union = words1.union(words2)
                
                if len(union) > 0:
                    similarity = len(intersection) / len(union)
                    if similarity > threshold:
                        duplicates += 1
                        logger.debug(f"Duplicate paragraph detected (similarity: {similarity:.2f})")
        
        # If more than 20% of paragraphs are duplicates, flag as excessive
        duplicate_ratio = duplicates / max(1, len(paragraphs))
        return duplicate_ratio > 0.2

    def _detect_severe_repetition(self, summary: str) -> Tuple[bool, str]:
        """Detect severe repetition patterns that indicate critical quality issues.
        
        Checks for:
        - Same sentence appearing 3+ times
        - Same 5+ word phrase appearing 5+ times
        - Paragraph similarity > 0.5 (more aggressive than standard check)
        
        Args:
            summary: Summary text to check.
            
        Returns:
            Tuple of (has_severe_repetition, reason).
        """
        def normalize_text(text: str) -> str:
            """Normalize text for comparison."""
            text = text.lower()
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s]', '', text)
            return text.strip()
        
        # Check for sentence repetition (same sentence 3+ times)
        sentences = [s.strip() for s in re.split(r'[.!?]+', summary) if s.strip() and len(s.strip()) > 20]
        if len(sentences) >= 3:
            normalized_sentences = [normalize_text(s) for s in sentences]
            sentence_counts = {}
            for sent in normalized_sentences:
                sentence_counts[sent] = sentence_counts.get(sent, 0) + 1
            
            for sent, count in sentence_counts.items():
                if count >= 3:
                    return True, f"Same sentence appears {count} times (severe repetition)"
        
        # Check for phrase repetition (same 5+ word phrase 5+ times)
        words = normalize_text(summary).split()
        if len(words) >= 5:
            phrases = []
            for i in range(len(words) - 4):
                phrase = ' '.join(words[i:i+5])
                phrases.append(phrase)
            
            phrase_counts = {}
            for phrase in phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
            
            for phrase, count in phrase_counts.items():
                if count >= 5:
                    return True, f"Same phrase appears {count} times (severe repetition)"
        
        # Check for paragraph repetition with lower threshold (0.5 instead of 0.8)
        paragraphs = [p.strip() for p in summary.split('\n\n') if p.strip() and len(p.strip()) > 50]
        if len(paragraphs) >= 2:
            normalized_paras = [normalize_text(p) for p in paragraphs]
            duplicates = 0
            for i, para1 in enumerate(normalized_paras):
                for j, para2 in enumerate(normalized_paras[i+1:], start=i+1):
                    words1 = set(para1.split())
                    words2 = set(para2.split())
                    if len(words1) > 0 and len(words2) > 0:
                        intersection = words1.intersection(words2)
                        union = words1.union(words2)
                        if len(union) > 0:
                            similarity = len(intersection) / len(union)
                            if similarity > 0.5:  # Lower threshold for severe repetition
                                duplicates += 1
            
            duplicate_ratio = duplicates / max(1, len(paragraphs))
            if duplicate_ratio > 0.3:  # More than 30% duplicates is severe
                return True, f"Severe paragraph repetition: {duplicate_ratio:.1%} of paragraphs are duplicates"
        
        return False, ""

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

        # Removed physics-specific check - it was causing false positives for non-physics papers
        # (e.g., active inference papers being flagged as physics papers)
        # General hallucination checks above are sufficient for detecting inappropriate content

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

    def _validate_title_match(self, summary: str, paper_title: str) -> Tuple[bool, str]:
        """Validate that summary correctly identifies the paper title.
        
        Args:
            summary: Generated summary text.
            paper_title: Expected paper title.
            
        Returns:
            Tuple of (is_match, error_message). is_match is True if title is correctly identified.
        """
        summary_lower = summary.lower()
        paper_title_lower = paper_title.lower()
        
        # Extract title from summary (usually in first few lines or after "#")
        # Look for title-like patterns in summary
        title_patterns = [
            r'^#\s+(.+)$',  # Markdown title
            r'^(.+?)\s*\n\s*\*\*Authors?\*\*',  # Title before Authors line
            r'^(.+?)\s*\n\s*---',  # Title before separator
        ]
        
        summary_title = None
        for pattern in title_patterns:
            match = re.search(pattern, summary, re.MULTILINE | re.IGNORECASE)
            if match:
                summary_title = match.group(1).strip()
                break
        
        # If no explicit title found, check if paper title appears in summary
        if not summary_title:
            # Check if paper title (or significant portion) appears in summary
            # Extract key words from paper title (3+ chars, not stop words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            title_words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', paper_title_lower) if w not in stop_words]
            
            if len(title_words) >= 3:
                # Check if at least 60% of key title words appear in summary
                words_in_summary = sum(1 for word in title_words if word in summary_lower)
                if words_in_summary / len(title_words) >= 0.6:
                    return True, ""  # Title words found, likely correct
            else:
                # Short title - check if exact title appears
                if paper_title_lower in summary_lower:
                    return True, ""
            
            return False, f"Paper title '{paper_title}' not found in summary"
        
        # Compare extracted title with paper title
        summary_title_lower = summary_title.lower()
        
        # Exact match
        if summary_title_lower == paper_title_lower:
            return True, ""
        
        # Check if summary title contains paper title or vice versa (for partial matches)
        if paper_title_lower in summary_title_lower or summary_title_lower in paper_title_lower:
            return True, ""  # Close enough match
        
        # Check word overlap (at least 70% of significant words match)
        title_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', paper_title_lower))
        summary_title_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', summary_title_lower))
        
        if title_words:
            overlap = len(title_words.intersection(summary_title_words)) / len(title_words)
            if overlap >= 0.7:
                return True, ""  # Good word overlap
        
        return False, f"Summary title '{summary_title}' does not match paper title '{paper_title}'"

    def _validate_quotes_present(self, summary: str) -> Tuple[bool, int]:
        """Validate that summary includes quoted evidence from the paper.
        
        Args:
            summary: Generated summary text.
            
        Returns:
            Tuple of (has_quotes, quote_count). has_quotes is True if at least 3 quotes found.
        """
        # Look for quote patterns: "text", 'text', [paraphrase], or "text" (section)
        quote_patterns = [
            r'"[^"]{20,200}"',  # Double quotes with substantial content
            r"'[^']{20,200}'",  # Single quotes
            r'\[[^\]]{20,200}\]',  # Brackets (paraphrases)
            r'"[^"]+"\s*\([^)]+\)',  # Quotes with citations
            r'As stated in [^:]+:\s*"[^"]+"',  # "As stated in X: 'quote'"
            r'According to [^:]+:\s*"[^"]+"',  # "According to X: 'quote'"
        ]
        
        quote_count = 0
        for pattern in quote_patterns:
            matches = re.findall(pattern, summary)
            quote_count += len(matches)
        
        has_quotes = quote_count >= 3
        return has_quotes, quote_count

    def _detect_major_hallucination(
        self,
        summary: str,
        pdf_text: str,
        paper_title: str
    ) -> Tuple[bool, str]:
        """Detect if summary is about completely wrong topic (major hallucination).
        
        This checks if the summary discusses topics that are completely unrelated
        to the paper, indicating the LLM summarized the wrong paper or hallucinated.
        
        FIXED: Only checks terms that ACTUALLY appear in title/abstract, not inferred domains.
        
        Args:
            summary: Generated summary text.
            pdf_text: Original PDF text.
            paper_title: Paper title for topic validation.
            
        Returns:
            Tuple of (is_major_hallucination, reason). is_major_hallucination is True if wrong topic detected.
        """
        summary_lower = summary.lower()
        pdf_lower = pdf_text.lower()
        title_lower = paper_title.lower()
        
        # Extract ACTUAL key terms from title and abstract (first 500 chars)
        # Don't infer domain from single word matches - use actual terms present
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'paper', 'presents', 'proposes', 'investigates', 'studies', 'examines', 'analyzes', 'discusses'}
        
        # Extract key terms from title (4+ char words, not stop words)
        title_key_terms = set(w for w in re.findall(r'\b[a-zA-Z]{4,}\b', title_lower) if w not in stop_words)
        
        # Extract key terms from abstract (first 500 chars)
        abstract_text = pdf_lower[:500]
        abstract_key_terms = set(w for w in re.findall(r'\b[a-zA-Z]{4,}\b', abstract_text) if w not in stop_words)
        
        # Combine actual key terms from paper
        actual_paper_terms = title_key_terms.union(abstract_key_terms)
        
        # Remove very common terms that aren't meaningful
        common_terms = {'that', 'with', 'from', 'this', 'which', 'their', 'there', 'these', 'those', 'would', 'could', 'should', 'might', 'about', 'using', 'based', 'through', 'within', 'between', 'during', 'while', 'where', 'when', 'what', 'how', 'why'}
        actual_paper_terms = {t for t in actual_paper_terms if t not in common_terms}
        
        if not actual_paper_terms:
            # Can't validate without key terms - skip this check
            return False, ""
        
        # Check if summary discusses terms NOT in paper (potential hallucination)
        summary_terms = set(w for w in re.findall(r'\b[a-zA-Z]{4,}\b', summary_lower) if w not in stop_words and w not in common_terms)
        
        # Find terms in summary that appear frequently but not in paper
        suspicious_terms = []
        for term in summary_terms:
            if term not in actual_paper_terms:
                summary_count = summary_lower.count(term)
                pdf_count = pdf_lower.count(term)
                # If term appears 3+ times in summary but 0 times in PDF, it's suspicious
                if summary_count >= 3 and pdf_count == 0:
                    suspicious_terms.append(term)
        
        if suspicious_terms:
            # Check if these suspicious terms form a coherent wrong domain
            # Common wrong domain patterns
            wrong_domain_patterns = {
                'nlp_cv': ['natural', 'language', 'processing', 'computer', 'vision', 'nlp', 'cv', 'neural', 'network', 'deep', 'learning', 'cnn', 'rnn', 'transformer'],
                'psychology': ['psychology', 'cognitive', 'behavioral', 'mental', 'psychological'],
                'physics': ['quantum', 'particle', 'collision', 'temperature', 'velocity', 'momentum'],
            }
            
            for domain_name, domain_terms in wrong_domain_patterns.items():
                domain_terms_in_suspicious = sum(1 for term in suspicious_terms if term in domain_terms)
                domain_terms_in_paper = sum(1 for term in domain_terms if term in actual_paper_terms)
                
                # If summary heavily discusses wrong domain (3+ terms) but paper doesn't
                if domain_terms_in_suspicious >= 3 and domain_terms_in_paper == 0:
                    return True, f"Summary discusses wrong domain ({domain_name}) with terms not in paper: {', '.join(suspicious_terms[:5])}"
        
        # Check if summary mentions key terms from paper
        paper_terms_in_summary = sum(1 for term in actual_paper_terms if term in summary_lower)
        paper_terms_in_pdf = len(actual_paper_terms)
        
        # If paper has many key terms but summary mentions very few, it's suspicious
        if paper_terms_in_pdf > 5:
            coverage = paper_terms_in_summary / paper_terms_in_pdf
            if coverage < 0.2:  # Less than 20% of key terms mentioned
                return True, f"Summary mentions only {coverage:.1%} of key terms from paper title/abstract"
        
        # Check if summary first sentence has low overlap with paper title
        summary_first_sent = summary_lower.split('.')[0][:200]
        summary_first_words = set(w for w in re.findall(r'\b[a-zA-Z]{4,}\b', summary_first_sent) if w not in stop_words and w not in common_terms)
        
        if title_key_terms:
            overlap = len(title_key_terms.intersection(summary_first_words)) / len(title_key_terms)
            if overlap < 0.2:  # Less than 20% word overlap (stricter than before)
                return True, f"Summary first sentence has very low word overlap with paper title ({overlap:.1%})"
        
        return False, ""


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
        max_pdf_chars: Optional[int] = None
    ):
        """Initialize paper summarizer.

        Args:
            llm_client: Configured LLM client for summary generation.
            quality_validator: Quality validator instance (created if None).
            max_pdf_chars: Maximum PDF characters to send to LLM. 
                          Defaults to 200000 (200K) or LLM_MAX_INPUT_LENGTH env var.
                          Set to 0 or None for unlimited (not recommended).
        """
        self.llm_client = llm_client
        self.quality_validator = quality_validator or SummaryQualityValidator()
        self._last_ref_info: Optional[Dict[str, Any]] = None  # Store ref_info for metadata
        
        # Get max_pdf_chars from parameter, environment variable, or default
        if max_pdf_chars is not None:
            self.max_pdf_chars = max_pdf_chars
        else:
            import os
            env_limit = os.getenv('LLM_MAX_INPUT_LENGTH')
            if env_limit:
                try:
                    self.max_pdf_chars = int(env_limit)
                except ValueError:
                    self.max_pdf_chars = 200000  # Default: 200K chars
            else:
                self.max_pdf_chars = 200000  # Default: 200K chars (increased from 50K)

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
        
        # Clear previous reference info
        self._last_ref_info = None

        # Extract text from PDF using prioritized processor
        try:
            # Log file size for context before extraction
            file_size = pdf_path.stat().st_size
            logger.debug(f"Starting PDF text extraction for {pdf_path.name} ({file_size:,} bytes)")

            # Use PDF processor for prioritized text extraction
            from infrastructure.literature.pdf_processor import PDFProcessor
            pdf_processor = PDFProcessor()
            prioritized_result = pdf_processor.extract_prioritized_text(
                pdf_path, self.max_pdf_chars
            )
            pdf_text = prioritized_result.text
            
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
            
            # Log section information
            if prioritized_result.truncation_occurred:
                logger.info(
                    f"PDF prioritized: {prioritized_result.original_length:,} -> {prioritized_result.final_length:,} chars. "
                    f"Sections included: {', '.join(prioritized_result.sections_included)}"
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
        
        # Analyze references before truncation
        ref_info = self._analyze_references(pdf_text)
        # Store for later use in metadata
        self._last_ref_info = ref_info
        
        # Check if truncation will occur
        will_truncate = (self.max_pdf_chars > 0 and input_chars > self.max_pdf_chars)
        truncation_pct = ((input_chars - self.max_pdf_chars) / input_chars * 100) if will_truncate else 0.0
        
        logger.info(
            f"Extracted {input_chars:,} chars, {input_words:,} words from {pdf_path.name}"
            + (f" (will truncate to {self.max_pdf_chars:,} chars, {truncation_pct:.1f}% removed)" if will_truncate else " (full paper loaded)")
        )
        
        if ref_info['count']:
            logger.info(f"Detected {ref_info['count']} references in PDF")
        elif ref_info['section_found']:
            logger.debug("References section found but count could not be determined")
        else:
            logger.debug("No references section detected in PDF text")

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
                summary = self._generate_summary(result, pdf_text, ref_info=ref_info)

                # Length check - primary acceptance criterion
                word_count = len(summary.split()) if summary else 0
                min_acceptable_words = 150  # Reasonable threshold for substantive content

                if word_count < min_acceptable_words:
                    logger.warning(f"Attempt {attempts}: Summary too short ({word_count} words, minimum {min_acceptable_words}), retrying...")
                    continue

                # Quality validation - pass paper title for title matching
                is_valid, quality_score, validation_errors = self.quality_validator.validate_summary(
                    summary, pdf_text, citation_key, paper_title=result.title
                )

                # Check for HARD FAILURES - these should never be accepted, even after retries
                hard_failures = any(
                    "title mismatch" in error.lower() or
                    "major hallucination" in error.lower() or
                    "severe repetition" in error.lower()
                    for error in validation_errors
                )

                if hard_failures:
                    # Hard failure - don't accept, fail immediately
                    hard_failure_errors = [e for e in validation_errors if any(
                        keyword in e.lower() for keyword in ["title mismatch", "major hallucination", "severe repetition"]
                    )]
                    logger.error(f"Attempt {attempts}: HARD FAILURE detected - {', '.join(hard_failure_errors)}")
                    logger.error("Summary will be rejected - hard failures cannot be retried")
                    # Continue to next attempt if available, but don't accept this summary
                    if attempt < max_retries:
                        logger.info("Retrying summary generation...")
                        continue
                    else:
                        # Max retries reached with hard failure - return failure
                        return SummarizationResult(
                            citation_key=citation_key,
                            success=False,
                            input_chars=input_chars,
                            input_words=input_words,
                            generation_time=time.time() - start_time,
                            attempts=attempts,
                            error=f"Hard failure after {attempts} attempts: {', '.join(hard_failure_errors)}"
                        )

                # Check for other critical issues (retryable)
                critical_issues = any(
                    "hallucination" in error.lower() or 
                    "repetition" in error.lower() or
                    "topic mismatch" in error.lower()
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

        # Final quality check for reporting - pass paper title for title matching
        _, final_score, final_errors = self.quality_validator.validate_summary(
            summary, pdf_text, citation_key, paper_title=result.title
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

    def _analyze_references(self, pdf_text: str) -> Dict[str, Any]:
        """Analyze references in PDF text.
        
        Args:
            pdf_text: Extracted PDF text.
            
        Returns:
            Dictionary with reference analysis:
            {
                'count': Optional[int] - Number of references found,
                'section_found': bool - Whether references section exists,
                'section_start': Optional[int] - Character position of references section
            }
        """
        ref_info = {
            'count': None,
            'section_found': False,
            'section_start': None
        }
        
        # Look for references section header
        ref_section_patterns = [
            r'^\s*(?:References?|Bibliography|Works\s+Cited)\s*$',
            r'^#+\s*(?:References?|Bibliography)',
            r'\\begin\{thebibliography\}',
            r'\\bibliography'
        ]
        
        for pattern in ref_section_patterns:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                ref_info['section_found'] = True
                ref_info['section_start'] = match.start()
                break
        
        # Count references using multiple patterns
        citation_patterns = [
            (r'\[(\d+)\]', lambda m: int(m.group(1))),  # [1], [2], etc.
            (r'\\cite\{[^}]+\}', lambda m: 1),  # \cite{key} - count occurrences
            (r'\\bibitem', lambda m: 1),  # \bibitem entries
        ]
        
        max_ref_num = 0
        citation_count = 0
        
        for pattern, extractor in citation_patterns:
            matches = list(re.finditer(pattern, pdf_text))
            if matches:
                if pattern == r'\[(\d+)\]':
                    # Extract numbers and find max
                    numbers = [int(m.group(1)) for m in matches if m.group(1).isdigit()]
                    if numbers:
                        max_ref_num = max(max_ref_num, max(numbers))
                else:
                    # Count occurrences
                    citation_count += len(matches)
        
        # Use max reference number if found, otherwise use citation count
        if max_ref_num > 0:
            ref_info['count'] = max_ref_num
        elif citation_count > 0:
            ref_info['count'] = citation_count
        
        return ref_info

    def _generate_summary(self, result: SearchResult, pdf_text: str, ref_info: Optional[Dict[str, Any]] = None) -> str:
        """Generate summary using LLM with paper-specific prompt and domain detection."""
        from infrastructure.llm.templates.research import PaperSummarization
        from infrastructure.literature.domain_detector import DomainDetector

        # PDF text is already processed by PDF processor with prioritization
        # No need to truncate again here - pdf_text is already optimized
        original_chars = len(pdf_text)
        logger.debug(f"PDF text loaded: {original_chars:,} chars (already prioritized by PDF processor)")

        # Detect domain for context-aware prompts
        domain_detector = DomainDetector()
        domain_result = domain_detector.detect_domain(
            text=pdf_text,
            title=result.title,
            abstract=result.abstract
        )
        
        # Get domain-specific instructions
        domain_instructions = domain_detector.get_domain_specific_instructions(domain_result.domain)
        
        logger.debug(f"Detected domain: {domain_result.domain.value} (confidence: {domain_result.confidence:.2f})")
        logger.debug(f"Detected paper type: {domain_result.paper_type.value} (confidence: {domain_result.type_confidence:.2f})")

        # Create paper summarization prompt with domain context and reference info
        template = PaperSummarization()
        prompt = template.render(
            title=result.title,
            authors=', '.join(result.authors) if result.authors else 'Unknown',
            year=str(result.year) if result.year else 'Unknown',
            source=f"{result.source} ({result.venue or 'N/A'})",
            text=pdf_text,
            domain=domain_result.domain.value if domain_result.confidence > 0.5 else None,
            domain_instructions=domain_instructions if domain_result.confidence > 0.5 else None,
            reference_count=ref_info.get('count') if ref_info else None,
            references_section_found=ref_info.get('section_found', False) if ref_info else False
        )

        # Generate summary with improved parameters for comprehensive, technically detailed summaries
        from infrastructure.llm.core.config import GenerationOptions
        options = GenerationOptions(
            temperature=0.45,  # Balanced for detailed content while maintaining consistency
            max_tokens=4000  # Increased significantly to allow for comprehensive, technically detailed summaries (600-1000 words)
        )

        summary = self.llm_client.query(prompt, options=options, reset_context=True)
        cleaned = self._clean_summary_content(summary)
        # Apply deduplication BEFORE validation so validation sees clean content
        deduplicated = self._deduplicate_summary(cleaned)
        logger.debug(f"Deduplication completed before validation (removed duplicates if any)")
        return deduplicated

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

    def _deduplicate_summary(self, summary: str) -> str:
        """Remove duplicate sections and paragraphs from summary.
        
        Uses more aggressive deduplication to handle cases like matsumoto2025active
        where entire sections are repeated multiple times.
        
        Args:
            summary: Summary text that may contain duplicates.
            
        Returns:
            Deduplicated summary text.
        """
        if not summary:
            return summary
        
        lines = summary.split('\n')
        deduplicated_lines = []
        seen_sections = {}  # Map normalized title -> (first_occurrence_index, content_hash)
        seen_paragraphs = set()
        current_section = None
        current_section_start = None
        current_paragraph = []
        removed_count = 0
        
        def normalize_text(text: str) -> str:
            """Normalize text for comparison."""
            text = text.lower()
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s]', '', text)
            return text.strip()
        
        def normalize_section_title(title: str) -> str:
            """Normalize section title for comparison (handle variations)."""
            title = title.lower().strip()
            # Handle common variations and combinations
            title = re.sub(r'^summary/?overview$', 'overview', title)
            title = re.sub(r'^overview/?summary$', 'overview', title)
            title = re.sub(r'^additional\s+information$', 'additional information', title)
            title = re.sub(r'^notes?$', 'notes', title)
            # Handle "Limitations/Discussion" vs "Limitations" vs "Discussion"
            if '/' in title:
                # Split and normalize each part
                parts = [p.strip() for p in title.split('/')]
                # Use the first significant part for comparison
                title = parts[0] if parts else title
            # Normalize common variations
            title = re.sub(r'^limitations\s*(?:and|/)\s*(?:future\s*work|discussion)$', 'limitations', title)
            title = re.sub(r'^discussion\s*(?:and|/)\s*(?:limitations|future\s*work)$', 'limitations', title)
            return title
        
        def hash_paragraph_content(para_text: str) -> str:
            """Create a hash of paragraph content for comparison."""
            normalized = normalize_text(para_text)
            # Use first 300 chars of normalized text as hash (increased for better detection)
            return normalized[:300]
        
        def paragraphs_similar(para1: str, para2: str, threshold: float = 0.5) -> bool:
            """Check if two paragraphs are similar (for more aggressive deduplication).
            
            Lowered threshold from 0.7 to 0.5 to catch more repetition cases.
            """
            norm1 = normalize_text(para1)
            norm2 = normalize_text(para2)
            
            if len(norm1) < 30 or len(norm2) < 30:
                return False
            
            # Word-based similarity
            words1 = set(norm1.split())
            words2 = set(norm2.split())
            
            if len(words1) == 0 or len(words2) == 0:
                return False
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if len(union) > 0:
                similarity = len(intersection) / len(union)
                return similarity > threshold
            
            return False
        
        # First pass: Remove repeated sentences (same sentence 2+ times)
        # Split into sentences while preserving structure
        sentence_pattern = r'([.!?]+)\s*'
        parts = re.split(sentence_pattern, summary)
        sentences_list = []
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                sentence = (parts[i] + parts[i+1]).strip()
                if sentence and len(sentence) > 20:
                    sentences_list.append(sentence)
        
        # Remove duplicate sentences
        seen_sentences = {}
        unique_sentences = []
        for sent in sentences_list:
            sent_normalized = normalize_text(sent)
            if sent_normalized not in seen_sentences:
                seen_sentences[sent_normalized] = True
                unique_sentences.append(sent)
            else:
                removed_count += 1
                logger.debug(f"Removed duplicate sentence: {sent[:50]}...")
        
        # Reconstruct summary from unique sentences
        if len(unique_sentences) < len(sentences_list):
            summary = ' '.join(unique_sentences)
            lines = summary.split('\n')
            logger.info(f"Removed {len(sentences_list) - len(unique_sentences)} duplicate sentences")
        else:
            lines = summary.split('\n')
        
        # Note: Phrase removal is complex and can break text structure
        # Sentence-level deduplication above is more important and effective
        # For severe phrase repetition, validation will catch it via _detect_severe_repetition
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a section header
            header_match = re.match(r'^(#{2,3})\s+(.+)$', line)
            if header_match:
                # Process previous paragraph before starting new section
                if current_paragraph:
                    para_text = '\n'.join(current_paragraph).strip()
                    para_hash = hash_paragraph_content(para_text)
                    
                    if para_hash and len(para_hash) > 30:
                        # Check for exact hash match first
                        if para_hash in seen_paragraphs:
                            removed_count += 1
                            logger.debug(f"Removed duplicate paragraph (exact match) in section: {current_section}")
                            current_paragraph = []
                            continue
                        
                        # Check for similar paragraphs (more aggressive deduplication)
                        is_duplicate = False
                        for seen_hash in seen_paragraphs:
                            # Reconstruct paragraph from hash is not possible, so check similarity differently
                            # Instead, we'll check similarity against current paragraph
                            pass  # Will check during final pass
                        
                        # If not duplicate, add it
                        seen_paragraphs.add(para_hash)
                        deduplicated_lines.extend(current_paragraph)
                        deduplicated_lines.append('')  # Preserve paragraph spacing
                    current_paragraph = []
                
                # Check for duplicate section
                section_title = header_match.group(2).strip()
                section_normalized = normalize_section_title(section_title)
                
                if section_normalized in seen_sections:
                    # This is a duplicate section - skip entire section content
                    removed_count += 1
                    logger.debug(f"Removed duplicate section: {section_title} (normalized: {section_normalized})")
                    
                    # Skip all lines until next section header or end
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if re.match(r'^#{2,3}\s+', next_line):
                            i -= 1  # Back up to process this header
                            break
                        i += 1
                    current_section = None
                    current_section_start = None
                else:
                    # New unique section - track it
                    seen_sections[section_normalized] = (len(deduplicated_lines), section_title)
                    current_section = section_title
                    current_section_start = len(deduplicated_lines)
                    deduplicated_lines.append(line)
                i += 1
                continue
            
            # Regular line - add to current paragraph
            current_paragraph.append(line)
            i += 1
        
        # Process final paragraph
        if current_paragraph:
            para_text = '\n'.join(current_paragraph).strip()
            para_hash = hash_paragraph_content(para_text)
            
            if para_hash and len(para_hash) > 30:
                if para_hash not in seen_paragraphs:
                    seen_paragraphs.add(para_hash)
                    deduplicated_lines.extend(current_paragraph)
                else:
                    removed_count += 1
                    logger.debug("Removed duplicate final paragraph")
        
        # Second pass: Check for similar paragraphs (more aggressive deduplication)
        # Re-parse to check paragraph similarity
        result_lines = deduplicated_lines
        final_lines = []
        seen_para_texts = []
        
        i = 0
        current_para_lines = []
        while i < len(result_lines):
            line = result_lines[i]
            
            # Check if this is a section header
            if re.match(r'^#{2,3}\s+', line):
                # Process accumulated paragraph
                if current_para_lines:
                    para_text = '\n'.join(current_para_lines).strip()
                    if para_text and len(para_text) > 50:
                        # Check if similar to any seen paragraph (lowered threshold to 0.5)
                        is_similar = False
                        for seen_para in seen_para_texts:
                            if paragraphs_similar(para_text, seen_para, threshold=0.5):
                                is_similar = True
                                removed_count += 1
                                logger.debug(f"Removed similar paragraph (similarity > 50%)")
                                break
                        
                        if not is_similar:
                            seen_para_texts.append(para_text)
                            final_lines.extend(current_para_lines)
                            final_lines.append('')
                    current_para_lines = []
                
                final_lines.append(line)
            else:
                current_para_lines.append(line)
            
            i += 1
        
        # Process final paragraph
        if current_para_lines:
            para_text = '\n'.join(current_para_lines).strip()
            if para_text and len(para_text) > 50:
                is_similar = False
                for seen_para in seen_para_texts:
                    if paragraphs_similar(para_text, seen_para, threshold=0.5):
                        is_similar = True
                        removed_count += 1
                        logger.debug("Removed similar final paragraph (similarity > 50%)")
                        break
                
                if not is_similar:
                    final_lines.extend(current_para_lines)
        
        if removed_count > 0:
            logger.info(f"Deduplication removed {removed_count} duplicate section(s)/paragraph(s)")
        
        result = '\n'.join(final_lines).strip()
        
        # Clean up excessive blank lines and trailing content
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Remove trailing incomplete sentences/paragraphs (common in truncated summaries)
        lines_result = result.split('\n')
        if lines_result and len(lines_result[-1].strip()) < 20 and not lines_result[-1].strip().endswith('.'):
            # Likely incomplete - remove last line
            result = '\n'.join(lines_result[:-1]).strip()
        
        return result

    def save_summary(
        self,
        result: SearchResult,
        summary_result: SummarizationResult,
        output_dir: Path,
        pdf_path: Optional[Path] = None
    ) -> Path:
        """Save summary to markdown file and metadata to JSON.

        Args:
            result: Search result with paper metadata.
            summary_result: Summarization result to save.
            output_dir: Directory for summary files.
            pdf_path: Path to PDF file (for metadata).

        Returns:
            Path to saved summary file.

        Raises:
            FileOperationError: If saving fails.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        citation_key = summary_result.citation_key
        output_path = output_dir / f"{citation_key}_summary.md"

        # Build clean markdown content (no statistics/metadata)
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
"""

        try:
            output_path.write_text(content, encoding='utf-8')
            file_size = output_path.stat().st_size
            logger.info(f"Saved summary: {output_path.name} ({file_size:,} bytes) -> {output_path}")
            
            # Save metadata to JSON
            self._save_summary_metadata(
                summary_result=summary_result,
                pdf_path=pdf_path,
                output_dir=output_dir
            )
            
            return output_path
        except Exception as e:
            raise FileOperationError(
                f"Failed to save summary: {e}",
                context={"path": str(output_path)}
            )
    
    def _save_summary_metadata(
        self,
        summary_result: SummarizationResult,
        pdf_path: Optional[Path],
        output_dir: Path
    ) -> None:
        """Save summary metadata to JSON file.
        
        Args:
            summary_result: Summarization result with statistics.
            pdf_path: Path to PDF file.
            output_dir: Directory for summary files (to determine metadata path).
        """
        from infrastructure.literature.summary_metadata import (
            SummaryMetadataManager,
            SummaryMetadata
        )
        
        try:
            # Determine metadata file path (in same directory as summaries)
            metadata_path = output_dir.parent / "summaries_metadata.json"
            manager = SummaryMetadataManager(metadata_path=metadata_path)
            
            # Get PDF size if available
            pdf_size_bytes = None
            pdf_relative_path = None
            if pdf_path and pdf_path.exists():
                pdf_size_bytes = pdf_path.stat().st_size
                # Store relative path from literature/ directory
                try:
                    pdf_relative_path = pdf_path.relative_to(output_dir.parent).as_posix()
                except ValueError:
                    pdf_relative_path = pdf_path.name
            
            # Check if truncation occurred
            truncated = False
            if hasattr(self, 'max_pdf_chars') and self.max_pdf_chars > 0:
                if summary_result.input_chars >= self.max_pdf_chars * 0.95:  # Within 5% of limit
                    truncated = True
            
            # Get reference count if available (from ref_info stored during summarization)
            reference_count = None
            if hasattr(self, '_last_ref_info') and self._last_ref_info:
                reference_count = self._last_ref_info.get('count')
            
            # Create metadata object
            metadata = SummaryMetadata(
                citation_key=summary_result.citation_key,
                input_words=summary_result.input_words,
                input_chars=summary_result.input_chars,
                output_words=summary_result.output_words,
                compression_ratio=summary_result.compression_ratio,
                generation_time=summary_result.generation_time,
                words_per_second=summary_result.words_per_second,
                quality_score=summary_result.quality_score,
                validation_errors=summary_result.validation_errors,
                attempts=summary_result.attempts,
                generated=time.strftime('%Y-%m-%d %H:%M:%S'),
                pdf_path=pdf_relative_path,
                pdf_size_bytes=pdf_size_bytes,
                truncated=truncated,
                reference_count=reference_count
            )
            
            # Save to JSON
            manager.add_metadata(metadata)
            logger.debug(f"Saved metadata for {summary_result.citation_key} to {metadata_path}")
            
        except Exception as e:
            logger.warning(f"Failed to save summary metadata: {e} (summary file still saved)")

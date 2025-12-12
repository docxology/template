"""Quality validation for paper summaries.

This module provides comprehensive validation of generated summaries,
detecting issues like hallucination, repetition, and topic mismatches.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.summarization.models import ValidationResult

logger = get_logger(__name__)


class SummaryQualityValidator:
    """Validates quality of generated paper summaries.

    Performs comprehensive quality checks:
    - Length validation (minimum word count)
    - Title matching (ensures summary identifies correct paper)
    - Hallucination detection (pattern-based: AI language, code snippets, inappropriate content)
    - Repetition analysis (sentence, paragraph, and section-level)
    - Quote presence validation
    
    Note: Term-based validation has been removed as it produced too many
    false positives. Validation now focuses on structural quality, repetition,
    and obvious hallucination patterns.
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
        
        Performs multiple validation checks and returns a quality score.
        Validation focuses on structural quality rather than term matching
        to avoid false positives.

        Args:
            summary: Generated summary text to validate.
            pdf_text: Original PDF text for comparison (used for title matching
                     and pattern-based hallucination detection).
            citation_key: Citation key for logging and error messages.
            paper_title: Paper title for title matching validation.
                        Recommended for accurate validation.

        Returns:
            Tuple of (is_valid, quality_score, error_messages):
            - is_valid: True if no errors found (score may still be low)
            - quality_score: Score from 0.0 to 1.0 (1.0 = perfect)
            - error_messages: List of validation error strings
            
        Validation Checks:
            - Title matching: Ensures summary correctly identifies the paper
            - Length: Minimum word count (default: 200 words)
            - Repetition: Detects severe sentence/paragraph repetition
            - Hallucination: Pattern-based detection (AI language, code, etc.)
            - Quotes: Validates presence of quoted evidence (warning only)
        """
        errors = []
        warnings = []
        score = 1.0

        # CRITICAL: Title matching check (if paper title provided)
        if paper_title:
            logger.debug(f"[{citation_key}] Validating title match...")
            title_match, title_error = self._validate_title_match(summary, paper_title)
            if not title_match:
                errors.append(f"Title mismatch: {title_error}")
                score -= 0.8  # Severe penalty - wrong title is critical error
                logger.warning(f"[{citation_key}] Title mismatch detected: {title_error}")
            else:
                logger.debug(f"[{citation_key}] Title match validated ✓")

        # Quote presence check (warning, not critical)
        has_quotes, quote_count = self._validate_quotes_present(summary)
        if not has_quotes:
            warnings.append(f"No quotes/evidence found (expected at least 3, found {quote_count})")
            score -= 0.2  # Moderate penalty - quotes are important but not critical

        # Length check
        word_count = len(summary.split())
        if word_count < self.min_words:
            errors.append(f"Too short: {word_count} words (minimum {self.min_words})")
            score -= 0.5

        # Optional sections check - only log missing sections, don't penalize score
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

        if missing_sections:
            logger.debug(f"Optional sections not found: {', '.join(missing_sections)} (not penalized)")

        # Severe repetition check (critical failure)
        logger.debug(f"[{citation_key}] Checking for severe repetition...")
        has_severe_repetition, severe_repetition_reason = self._detect_severe_repetition(summary)
        if has_severe_repetition:
            errors.append(f"Severe repetition detected: {severe_repetition_reason}")
            score -= 1.0  # Critical penalty - severe repetition is a hard failure
            logger.error(f"[{citation_key}] Severe repetition detected: {severe_repetition_reason}")
        else:
            logger.debug(f"[{citation_key}] No severe repetition detected ✓")
        
        # Standard repetition check
        has_section_repetition = self._detect_section_repetition(summary)
        has_paragraph_repetition = self._detect_paragraph_repetition(summary, threshold=0.5)
        has_sentence_repetition = self._detect_sentence_repetition(summary)
        
        repetition_issues = []
        if has_section_repetition:
            errors.append("Section-level repetition detected (duplicate section headers)")
            repetition_issues.append("Duplicate section headers found")
            score -= 0.5
        elif has_paragraph_repetition:
            errors.append("Paragraph-level repetition detected")
            repetition_issues.append("Similar paragraphs detected")
            score -= 0.3
        elif has_sentence_repetition:
            warnings.append("Sentence-level repetition detected")
            repetition_issues.append("Repeated sentences found")
            score -= 0.2

        # Hallucination check (general patterns)
        logger.debug(f"[{citation_key}] Checking for hallucination...")
        is_hallucinated, hallucination_reason = self._detect_hallucination(summary, pdf_text)
        if is_hallucinated:
            errors.append(f"Hallucination detected: {hallucination_reason}")
            score -= 0.4
            logger.warning(f"[{citation_key}] Hallucination detected: {hallucination_reason}")
        else:
            logger.debug(f"[{citation_key}] No hallucination detected ✓")

        # Off-topic content check
        off_topic_errors = self._detect_off_topic_content(summary)
        if off_topic_errors:
            errors.extend(off_topic_errors)
            score -= 0.1 * len(off_topic_errors)

        # Ensure score doesn't go below 0
        score = max(0.0, score)

        is_valid = len(errors) == 0
        
        # Log final validation summary
        if is_valid:
            logger.debug(f"[{citation_key}] Validation passed: score={score:.2f}, {quote_count} quotes")
        else:
            logger.debug(
                f"[{citation_key}] Validation failed: score={score:.2f}, "
                f"{len(errors)} errors, {len(warnings)} warnings, {quote_count} quotes"
            )
        
        return is_valid, score, errors

    def validate_summary_detailed(
        self,
        summary: str,
        pdf_text: str,
        citation_key: str,
        paper_title: Optional[str] = None,
        key_terms: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate summary and return detailed ValidationResult.

        Args:
            summary: Generated summary text.
            pdf_text: Original PDF text for comparison.
            citation_key: Citation key for logging.
            paper_title: Paper title for validation.
            key_terms: Optional list of key terms that should be mentioned.

        Returns:
            ValidationResult with detailed validation information.
        """
        is_valid, score, errors = self.validate_summary(summary, pdf_text, citation_key, paper_title)
        
        warnings = []
        missing_key_terms = []
        repetition_issues = []
        suggestions = []
        
        # Extract missing key terms if provided
        if key_terms:
            summary_lower = summary.lower()
            for term in key_terms:
                if term.lower() not in summary_lower:
                    missing_key_terms.append(term)
        
        # Extract quote count
        _, quote_count = self._validate_quotes_present(summary)
        
        # Extract repetition issues
        has_severe, severe_reason = self._detect_severe_repetition(summary)
        if has_severe:
            repetition_issues.append(severe_reason)
        
        # Generate suggestions
        if missing_key_terms:
            suggestions.append(f"Include key terms: {', '.join(missing_key_terms[:5])}")
        if quote_count < 3:
            suggestions.append("Add more quotes/evidence from the paper (at least 3)")
        if score < 0.5:
            suggestions.append("Review summary for accuracy and completeness")
        
        return ValidationResult(
            is_valid=is_valid,
            score=score,
            errors=errors,
            warnings=warnings,
            missing_key_terms=missing_key_terms,
            quote_count=quote_count,
            repetition_issues=repetition_issues,
            suggestions=suggestions
        )

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
        """Detect duplicate section headers in summary."""
        header_pattern = re.compile(r'^#{2,3}\s+(.+)$', re.MULTILINE)
        headers = header_pattern.findall(summary)
        
        if len(headers) < 2:
            return False
        
        normalized_headers = [h.lower().strip() for h in headers]
        seen_headers = set()
        for header in normalized_headers:
            if header in seen_headers:
                logger.debug(f"Duplicate section detected: {header}")
                return True
            seen_headers.add(header)
        
        return False

    def _detect_paragraph_repetition(self, summary: str, threshold: float = 0.5) -> bool:
        """Detect near-duplicate paragraphs in summary."""
        paragraphs = [p.strip() for p in summary.split('\n\n') if p.strip() and len(p.strip()) > 50]
        
        if len(paragraphs) < 2:
            return False
        
        def normalize_text(text: str) -> str:
            text = text.lower()
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s]', '', text)
            return text.strip()
        
        normalized_paras = [normalize_text(p) for p in paragraphs]
        duplicates = 0
        for i, para1 in enumerate(normalized_paras):
            for j, para2 in enumerate(normalized_paras[i+1:], start=i+1):
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
        
        duplicate_ratio = duplicates / max(1, len(paragraphs))
        return duplicate_ratio > 0.2

    def _sentence_similarity(self, sent1: str, sent2: str) -> float:
        """Calculate similarity between two sentences (0.0 to 1.0).
        
        Uses word overlap ratio as similarity metric.
        """
        def normalize_text(text: str) -> str:
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            return text.strip()
        
        words1 = set(normalize_text(sent1).split())
        words2 = set(normalize_text(sent2).split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _detect_severe_repetition(self, summary: str) -> Tuple[bool, str]:
        """Detect severe repetition patterns with similarity scoring."""
        def normalize_text(text: str) -> str:
            text = text.lower()
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s]', '', text)
            return text.strip()
        
        # Check for sentence repetition
        # Remove markdown headers first for better sentence detection
        summary_clean = re.sub(r'^#{1,6}\s+[^\n]+\n?', '', summary, flags=re.MULTILINE)
        # Split by all sentence delimiters together
        sentences = [s.strip() for s in re.split(r'[.!?]+', summary_clean) if s.strip() and len(s.strip()) > 15]
        
        if len(sentences) >= 3:
            # First check exact matches
            normalized_sentences = [normalize_text(s) for s in sentences]
            sentence_counts = {}
            for sent in normalized_sentences:
                sentence_counts[sent] = sentence_counts.get(sent, 0) + 1
            
            for sent, count in sentence_counts.items():
                if count >= 3:
                    return True, f"Same sentence appears {count} times (severe repetition)"
            
            # Then check for similar sentences (using similarity threshold 0.85)
            similar_groups = []
            for i, sent1 in enumerate(sentences):
                for j, sent2 in enumerate(sentences[i+1:], start=i+1):
                    similarity = self._sentence_similarity(sent1, sent2)
                    if similarity >= 0.85:  # 85% word overlap indicates near-duplicate
                        # Find or create group for this sentence
                        found_group = False
                        for group in similar_groups:
                            if any(self._sentence_similarity(sent1, gs) >= 0.85 for gs in group):
                                group.append(sent2)
                                found_group = True
                                break
                        if not found_group:
                            similar_groups.append([sent1, sent2])
            
            # Check if any group has 3+ similar sentences
            for group in similar_groups:
                if len(group) >= 3:
                    return True, f"Similar sentences appear {len(group)} times (severe repetition, similarity >= 0.85)"
        
        # Check for phrase repetition
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
        
        # Check for paragraph repetition
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
                            if similarity > 0.5:
                                duplicates += 1
            
            duplicate_ratio = duplicates / max(1, len(paragraphs))
            if duplicate_ratio > 0.3:
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
                if not re.search(pattern, pdf_lower, re.IGNORECASE):
                    return True, f"Content '{pattern}' not found in source PDF ({reason})"

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
        """Validate that summary correctly identifies the paper title."""
        summary_lower = summary.lower()
        paper_title_lower = paper_title.lower()
        
        title_patterns = [
            r'^#\s+(.+)$',
            r'^(.+?)\s*\n\s*\*\*Authors?\*\*',
            r'^(.+?)\s*\n\s*---',
        ]
        
        summary_title = None
        for pattern in title_patterns:
            match = re.search(pattern, summary, re.MULTILINE | re.IGNORECASE)
            if match:
                summary_title = match.group(1).strip()
                break
        
        if not summary_title:
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            title_words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', paper_title_lower) if w not in stop_words]
            
            if len(title_words) >= 3:
                words_in_summary = sum(1 for word in title_words if word in summary_lower)
                if words_in_summary / len(title_words) >= 0.6:
                    return True, ""
            else:
                if paper_title_lower in summary_lower:
                    return True, ""
            
            return False, f"Paper title '{paper_title}' not found in summary"
        
        summary_title_lower = summary_title.lower()
        
        if summary_title_lower == paper_title_lower:
            return True, ""
        
        if paper_title_lower in summary_title_lower or summary_title_lower in paper_title_lower:
            return True, ""
        
        # Filter stop words for better matching
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        title_words = set(w for w in re.findall(r'\b[a-zA-Z]{3,}\b', paper_title_lower) if w not in stop_words)
        summary_title_words = set(w for w in re.findall(r'\b[a-zA-Z]{3,}\b', summary_title_lower) if w not in stop_words)
        
        if title_words:
            overlap = len(title_words.intersection(summary_title_words)) / len(title_words)
            # Lower threshold to 0.5 to allow partial matches with good word overlap
            if overlap >= 0.5:
                return True, ""
        
        return False, f"Summary title '{summary_title}' does not match paper title '{paper_title}'"

    def _validate_quotes_present(self, summary: str) -> Tuple[bool, int]:
        """Validate that summary includes quoted evidence from the paper."""
        quote_patterns = [
            r'"[^"]{20,200}"',
            r"'[^']{20,200}'",
            r'\[[^\]]{20,200}\]',
            r'"[^"]+"\s*\([^)]+\)',
            r'As stated in [^:]+:\s*"[^"]+"',
            r'According to [^:]+:\s*"[^"]+"',
        ]
        
        quote_count = 0
        for pattern in quote_patterns:
            matches = re.findall(pattern, summary)
            quote_count += len(matches)
        
        has_quotes = quote_count >= 3
        return has_quotes, quote_count

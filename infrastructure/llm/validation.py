"""Output validation for LLM responses.

Provides comprehensive validation including:
- JSON validation and parsing
- Length and structure validation
- Citation extraction
- Formatting quality checks
- Repetition detection for LLM output loops
"""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any, Dict, Optional, Type, List, Tuple

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# Repetition Detection Functions
# =============================================================================

def detect_repetition(
    text: str,
    min_chunk_size: int = 100,
    similarity_threshold: float = 0.8,
    similarity_method: str = "hybrid",
) -> Tuple[bool, List[str], float]:
    """Detect repetitive content in LLM output with improved semantic detection.

    Uses hybrid similarity methods to better identify true repetition vs.
    conceptually similar but differently worded content.

    Args:
        text: The text to analyze
        min_chunk_size: Minimum characters for a chunk to be considered
        similarity_threshold: Threshold (0-1) above which chunks are considered duplicates
        similarity_method: Similarity method ("jaccard", "tfidf", "hybrid")

    Returns:
        Tuple of (has_repetition, list of repeated chunks, unique content ratio)
    """
    if not text or len(text) < min_chunk_size * 2:
        return False, [], 1.0

    # Split by common section markers with better pattern matching
    section_patterns = [
        r'\n### ',  # H3 headers
        r'\n## ',   # H2 headers
        r'\n# ',    # H1 headers
        r'\n\n\n',  # Triple newlines (section breaks)
    ]

    # Try each pattern to find the best split
    chunks = []
    for pattern in section_patterns:
        parts = re.split(pattern, text)
        valid_parts = [p.strip() for p in parts if len(p.strip()) >= min_chunk_size]
        if len(valid_parts) > len(chunks):
            chunks = valid_parts

    # Fallback: split by double newlines (paragraphs)
    if len(chunks) < 2:
        chunks = [p.strip() for p in text.split('\n\n') if len(p.strip()) >= min_chunk_size]

    if len(chunks) < 2:
        return False, [], 1.0

    # Normalize chunks for comparison
    normalized_chunks = [_normalize_for_comparison(c) for c in chunks]

    # Find duplicates using improved similarity methods
    duplicates = []
    seen_hashes = set()
    unique_count = 0

    # Use larger comparison window (400 chars instead of 200)
    for i, (chunk, normalized) in enumerate(zip(chunks, normalized_chunks)):
        chunk_hash = hash(normalized[:400])

        if chunk_hash in seen_hashes:
            duplicates.append(chunk[:100] + "..." if len(chunk) > 100 else chunk)
        else:
            seen_hashes.add(chunk_hash)
            unique_count += 1

    # Check for high semantic similarity using improved methods
    for i in range(len(normalized_chunks)):
        for j in range(i + 1, len(normalized_chunks)):
            similarity = _calculate_similarity(
                normalized_chunks[i],
                normalized_chunks[j],
                method=similarity_method
            )
            if similarity >= similarity_threshold:
                if chunks[j] not in duplicates:
                    duplicates.append(chunks[j][:100] + "..." if len(chunks[j]) > 100 else chunks[j])
                    logger.debug(
                        f"Semantic duplicate detected (similarity: {similarity:.2f}, "
                        f"method: {similarity_method})"
                    )

    unique_ratio = unique_count / len(chunks) if chunks else 1.0

    # More nuanced repetition detection
    has_repetition = (
        len(duplicates) >= 2 or  # Multiple duplicates found
        unique_ratio < 0.5 or    # Less than 50% unique content
        (len(duplicates) >= 1 and unique_ratio < 0.7)  # Single duplicate with low uniqueness
    )

    return has_repetition, duplicates[:5], unique_ratio  # Limit to 5 examples


def calculate_unique_content_ratio(text: str, chunk_size: int = 200) -> float:
    """Calculate the ratio of unique content vs total content.
    
    Uses a sliding window approach to detect repeated blocks.
    
    Args:
        text: The text to analyze
        chunk_size: Size of chunks to compare
        
    Returns:
        Ratio from 0.0 (all repeated) to 1.0 (all unique)
    """
    if not text or len(text) < chunk_size:
        return 1.0
    
    # Create overlapping chunks
    chunks = []
    step = chunk_size // 2  # 50% overlap
    for i in range(0, len(text) - chunk_size + 1, step):
        chunk = _normalize_for_comparison(text[i:i + chunk_size])
        chunks.append(chunk)
    
    if not chunks:
        return 1.0
    
    # Count unique chunks
    unique_chunks = set(chunks)
    
    return len(unique_chunks) / len(chunks)


def _normalize_for_comparison(text: str) -> str:
    """Normalize text for comparison by removing whitespace variations.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text for comparison
    """
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    # Remove common markdown formatting
    normalized = re.sub(r'[#*_`\[\]()]', '', normalized)
    # Remove numbers (often vary in repetitive content)
    normalized = re.sub(r'\d+', 'N', normalized)
    return normalized


def _calculate_similarity(text1: str, text2: str, method: str = "hybrid") -> float:
    """Calculate similarity between two texts using multiple methods.

    Uses a hybrid approach combining Jaccard similarity, TF-IDF cosine similarity,
    and sequence-based similarity for better semantic matching.

    Args:
        text1: First text
        text2: Second text
        method: Similarity method ("jaccard", "tfidf", "hybrid")

    Returns:
        Similarity ratio from 0.0 to 1.0
    """
    if not text1 or not text2:
        return 0.0

    # Normalize texts for comparison
    norm1 = _normalize_for_comparison(text1)
    norm2 = _normalize_for_comparison(text2)

    if method == "jaccard":
        return _jaccard_similarity(norm1, norm2)
    elif method == "tfidf":
        return _tfidf_cosine_similarity(norm1, norm2)
    else:  # hybrid
        jaccard_sim = _jaccard_similarity(norm1, norm2)
        tfidf_sim = _tfidf_cosine_similarity(norm1, norm2)
        sequence_sim = _sequence_similarity(norm1, norm2)

        # Weighted combination: favor TF-IDF and sequence similarity
        return 0.3 * jaccard_sim + 0.4 * tfidf_sim + 0.3 * sequence_sim


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity (word overlap)."""
    words1 = set(text1.split())
    words2 = set(text2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def _tfidf_cosine_similarity(text1: str, text2: str) -> float:
    """Calculate TF-IDF cosine similarity for semantic matching."""
    from collections import Counter
    import math

    # Tokenize and count
    words1 = Counter(text1.split())
    words2 = Counter(text2.split())

    if not words1 or not words2:
        return 0.0

    # Get all unique words
    all_words = set(words1.keys()) | set(words2.keys())

    # Calculate TF-IDF vectors (simplified: just TF for now, can be enhanced)
    vec1 = {word: words1.get(word, 0) for word in all_words}
    vec2 = {word: words2.get(word, 0) for word in all_words}

    # Cosine similarity
    dot_product = sum(vec1[word] * vec2[word] for word in all_words)
    norm1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
    norm2 = math.sqrt(sum(val ** 2 for val in vec2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def _sequence_similarity(text1: str, text2: str) -> float:
    """Calculate sequence-based similarity using n-gram overlap."""
    def get_ngrams(text: str, n: int = 3):
        """Get n-grams from text."""
        words = text.split()
        return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]

    ngrams1 = set(get_ngrams(text1, 3))
    ngrams2 = set(get_ngrams(text2, 3))

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2

    return len(intersection) / len(union) if union else 0.0


def deduplicate_sections(
    text: str,
    max_repetitions: int = 2,
    mode: str = "conservative",
    similarity_threshold: float = 0.85,
    min_content_preservation: float = 0.7
) -> str:
    """Remove repeated sections from LLM output with improved semantic detection.

    Uses configurable similarity thresholds and preservation rules to avoid
    removing valid content that happens to be conceptually similar.

    Args:
        text: The text to deduplicate
        max_repetitions: Maximum times a section can appear
        mode: Deduplication mode ("conservative", "balanced", "aggressive")
        similarity_threshold: Similarity threshold above which content is considered duplicate
        min_content_preservation: Minimum fraction of original content to preserve

    Returns:
        Deduplicated text with detailed logging
    """
    if not text:
        return text

    original_length = len(text)

    # Configure thresholds based on mode
    if mode == "conservative":
        similarity_threshold = max(similarity_threshold, 0.9)  # Very strict similarity
        max_repetitions = max(max_repetitions, 3)  # Allow more repetitions
    elif mode == "aggressive":
        similarity_threshold = min(similarity_threshold, 0.7)  # Looser similarity
        max_repetitions = min(max_repetitions, 1)  # Fewer repetitions
    # balanced uses provided values

    # Split by section headers (## or ###) with better pattern matching
    section_pattern = r'(^|\n)(#{2,3}\s+[^\n]+(?:\n|$))'
    parts = re.split(section_pattern, text)

    if len(parts) < 3:
        # Not enough sections to deduplicate, try paragraphs
        return _deduplicate_paragraphs(
            text, max_repetitions, similarity_threshold, min_content_preservation
        )

    # Track seen sections with semantic similarity
    seen_sections: Dict[str, Dict] = {}  # key -> {"count": int, "text": str}
    result_parts = []
    removed_count = 0

    i = 0
    while i < len(parts):
        part = parts[i]

        # Check if this is a header
        if re.match(r'#{2,3}\s+', part.strip()):
            # Get header and content (expanded window)
            header = part
            content = parts[i + 1] if i + 1 < len(parts) else ""

            # Use larger comparison window (500 chars instead of 200)
            comparison_text = header + content[:500]
            normalized = _normalize_for_comparison(comparison_text)

            # Check similarity against existing sections
            is_duplicate = False
            duplicate_key = None

            for existing_key, existing_data in seen_sections.items():
                similarity = _calculate_similarity(normalized, existing_key, method="hybrid")
                if similarity >= similarity_threshold:
                    existing_data["count"] += 1
                    if existing_data["count"] >= max_repetitions:
                        is_duplicate = True
                        duplicate_key = existing_key
                        logger.debug(
                            f"Duplicate section detected (similarity: {similarity:.2f}, "
                            f"count: {existing_data['count']})"
                        )
                    break

            if not is_duplicate:
                # Not a duplicate, add to seen sections
                seen_sections[normalized] = {"count": 1, "text": comparison_text}
                result_parts.append(part)
                if i + 1 < len(parts):
                    result_parts.append(parts[i + 1])
            else:
                removed_count += 1
                logger.debug(f"Removed duplicate section: {header.strip()[:50]}...")

            i += 2
        else:
            result_parts.append(part)
            i += 1

    result = ''.join(result_parts)

    # Apply content preservation rule
    if len(result) / original_length < min_content_preservation:
        logger.warning(
            f"Deduplication would remove too much content "
            f"({len(result)}/{original_length} = {len(result)/original_length:.1%}). "
            f"Using conservative fallback."
        )
        # Fallback to more conservative deduplication
        return deduplicate_sections(
            text, max_repetitions=max_repetitions + 1,
            mode="conservative", similarity_threshold=0.95,
            min_content_preservation=0.8
        )

    if removed_count > 0:
        logger.info(
            f"Deduplication removed {removed_count} duplicate sections "
            f"({original_length} → {len(result)} chars, "
            f"{len(result)/original_length:.1%} preserved)"
        )

    return result


def _deduplicate_paragraphs(
    text: str,
    max_repetitions: int,
    similarity_threshold: float,
    min_content_preservation: float
) -> str:
    """Deduplicate at paragraph level with semantic similarity."""
    paragraphs = text.split('\n\n')
    if len(paragraphs) < 3:
        return text

    original_length = len(text)
    seen_content: Dict[str, Dict] = {}
    result_paragraphs = []
    removed_count = 0

    for para in paragraphs:
        if not para.strip():
            result_paragraphs.append(para)
            continue

        normalized = _normalize_for_comparison(para)
        # Use larger comparison window for paragraphs
        key = normalized[:300] if len(normalized) > 300 else normalized

        # Check similarity against existing paragraphs
        is_duplicate = False
        for existing_key, existing_data in seen_content.items():
            similarity = _calculate_similarity(key, existing_key, method="hybrid")
            if similarity >= similarity_threshold:
                existing_data["count"] += 1
                if existing_data["count"] >= max_repetitions:
                    is_duplicate = True
                    logger.debug(
                        f"Duplicate paragraph detected (similarity: {similarity:.2f})"
                    )
                break

        if not is_duplicate:
            seen_content[key] = {"count": 1, "text": key}
            result_paragraphs.append(para)
        else:
            removed_count += 1

    result = '\n\n'.join(result_paragraphs)

    # Content preservation check
    if len(result) / original_length < min_content_preservation:
        logger.warning(
            f"Paragraph deduplication would remove too much content. "
            f"Skipping deduplication."
        )
        return text

    if removed_count > 0:
        logger.info(
            f"Paragraph deduplication removed {removed_count} duplicates "
            f"({original_length} → {len(result)} chars)"
        )

    return result


class OutputValidator:
    """Validates LLM outputs for quality and correctness."""

    @staticmethod
    def validate_json(content: str) -> Dict[str, Any]:
        """Validate and parse JSON output."""
        try:
            # Try to find JSON block if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValidationError(
                "LLM output is not valid JSON",
                context={"error": str(e), "content": content[:100]}
            )

    @staticmethod
    def validate_length(content: str, min_len: int = 0, max_len: Optional[int] = None) -> bool:
        """Validate output length."""
        length = len(content)
        if length < min_len:
            raise ValidationError(
                f"Output too short ({length} < {min_len})",
                context={"length": length}
            )
        if max_len and length > max_len:
            raise ValidationError(
                f"Output too long ({length} > {max_len})",
                context={"length": length}
            )
        return True

    @staticmethod
    def estimate_tokens(content: str) -> int:
        """Estimate token count (simple heuristic: 1 token ≈ 4 chars)."""
        return len(content) // 4

    @staticmethod
    def validate_short_response(content: str, max_tokens: int = 150) -> bool:
        """Validate short response format (< 150 tokens)."""
        tokens = OutputValidator.estimate_tokens(content)
        if tokens > max_tokens:
            logger.warning(
                f"Short response exceeds limit: {tokens} > {max_tokens} tokens"
            )
            return False
        return True

    @staticmethod
    def validate_long_response(content: str, min_tokens: int = 500) -> bool:
        """Validate long response format (> 500 tokens)."""
        tokens = OutputValidator.estimate_tokens(content)
        if tokens < min_tokens:
            logger.warning(
                f"Long response below minimum: {tokens} < {min_tokens} tokens"
            )
            return False
        return True

    @staticmethod
    def validate_structure(content: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate structured response against schema."""
        required_keys = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for key in required_keys:
            if key not in content:
                raise ValidationError(
                    f"Missing required field in structure: {key}",
                    context={"required": required_keys, "present": list(content.keys())}
                )
        
        # Type validation (basic)
        for key, value in content.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type and not OutputValidator._check_type(value, expected_type):
                    raise ValidationError(
                        f"Field '{key}' has wrong type",
                        context={"field": key, "expected": expected_type, "got": type(value).__name__}
                    )
        
        return True

    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        return isinstance(value, expected)

    @staticmethod
    def validate_citations(content: str) -> List[str]:
        """Extract and validate citations in content."""
        # Look for common citation patterns
        patterns = [
            r'\(([A-Z][a-z]+(?:\s+&\s+[A-Z][a-z]+)*\s+\d{4})\)',  # (Author Year)
            r'\[(\d+)\]',  # [1]
            r'@(\w+)',  # @key
        ]
        
        citations = []
        for pattern in patterns:
            citations.extend(re.findall(pattern, content))
        
        return citations

    @staticmethod
    def validate_formatting(content: str) -> bool:
        """Validate basic formatting quality."""
        issues = []
        
        # Check for excessive punctuation
        if "!!!" in content or "???" in content:
            issues.append("Excessive punctuation detected")
        
        # Check for common typos/issues
        if "  " in content:
            issues.append("Double spaces detected")
        
        if issues:
            logger.warning(f"Formatting issues: {', '.join(issues)}")
            return False
        
        return True

    @staticmethod
    def validate_complete(
        content: str,
        mode: str = "standard",
        schema: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Comprehensive validation based on mode."""
        if not content or not content.strip():
            raise ValidationError("Empty response")
        
        # Basic formatting check
        if not OutputValidator.validate_formatting(content):
            logger.warning("Response has formatting issues")
        
        # Mode-specific validation
        if mode == "short":
            return OutputValidator.validate_short_response(content)
        elif mode == "long":
            return OutputValidator.validate_long_response(content)
        elif mode == "structured" and schema:
            try:
                data = OutputValidator.validate_json(content)
                return OutputValidator.validate_structure(data, schema)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON for structured mode: {e}")
        
        return True

    @staticmethod
    def validate_no_repetition(
        content: str,
        max_allowed_ratio: float = 0.3,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate that response doesn't contain excessive repetition.
        
        Detects when LLM output gets stuck in a loop repeating content.
        
        Args:
            content: The response text to validate
            max_allowed_ratio: Maximum ratio of repeated content (0.0-1.0)
                              0.3 means at most 30% of content can be repeated
        
        Returns:
            Tuple of (is_valid, details dict with repetition info)
        """
        has_repetition, duplicates, unique_ratio = detect_repetition(content)
        
        details = {
            "has_repetition": has_repetition,
            "unique_ratio": unique_ratio,
            "duplicates_found": len(duplicates),
            "duplicate_samples": duplicates[:3],  # First 3 examples
        }
        
        # Calculate repetition ratio
        repetition_ratio = 1.0 - unique_ratio
        is_valid = repetition_ratio <= max_allowed_ratio
        
        if not is_valid:
            logger.warning(
                f"Excessive repetition detected: {repetition_ratio:.1%} repeated "
                f"(max allowed: {max_allowed_ratio:.1%})"
            )
        
        return is_valid, details

    @staticmethod
    def clean_repetitive_output(
        content: str,
        max_repetitions: int = 2,
    ) -> str:
        """Clean repetitive content from LLM output.
        
        Post-processing step to remove repeated sections/paragraphs.
        
        Args:
            content: The response text to clean
            max_repetitions: Maximum times a section can appear
            
        Returns:
            Cleaned text with repetitions removed
        """
        # Use balanced mode with lower content preservation threshold
        # since the purpose of this function is to aggressively clean repetition
        return deduplicate_sections(
            content, max_repetitions, mode="balanced", min_content_preservation=0.3
        )


# =============================================================================
# Review Quality Validation
# =============================================================================

# Off-topic detection patterns (indicates LLM confusion or hallucination)
# These patterns detect when the model is not reviewing the actual manuscript
OFF_TOPIC_PATTERNS_START = [
    # Email/letter formats (must be at start)
    r"^Re:\s",                        # Email reply format
    r"^Dear\s",                       # Letter format
    r"^To:\s",                        # Email header format
    r"^Subject:\s",                   # Email subject line
    r"^From:\s",                      # Email from header
    # Casual greetings at start (inappropriate for formal review)
    r"^Hi\s",                         # Casual greeting
    r"^Hello\s",                      # Casual greeting
    r"^Hey\s",                        # Very casual greeting
    r"^Hello!",                       # Casual with exclamation
    # Generic book/guide language at start (indicates hallucinated content)
    r"^This book is",                 # Generic book intro
    r"^This guide",                   # Generic guide intro
    r"^Chapter 1",                    # Chapter numbering (not manuscript)
    r"^Introduction\s*\n\s*This book", # Book intro pattern
]

OFF_TOPIC_PATTERNS_ANYWHERE = [
    # AI assistant refusal patterns (critical - indicates model can't process)
    r"I can't help",
    r"I cannot help",
    r"I'm unable to",
    r"I am unable to",
    r"I don't have access to",
    r"I cannot access",
    r"I'm not able to",
    # AI self-identification (indicates confusion)
    r"As an AI assistant",
    r"as a language model",
    r"I am an AI",
    r"I'm an AI assistant",
    r"I'm happy to help you with",
    r"I'm not sure if I can help",
    # External URLs (indicates external references, not manuscript content)
    r"https?://[^\s]+",               # Any URL
    # Generic book/guide language (indicates hallucinated content)
    r"this book provides",
    r"this guide explains",
    r"chapter \d+ deals with",
    r"chapter \d+ covers",
    r"the book is divided",
    r"this manual",
    # Code-focused responses when expecting prose
    r"^```python\n",                  # Code block at very start
    r"import pandas as pd\nimport",   # Multi-import block
    r"CMakeLists\.txt",               # Build system files
    r"\.cpp\b",                       # C++ file extensions
    r"\.hpp\b",                       # C++ header extensions
    # User requirement patterns (indicates form/registration confusion)
    r"must be a minimum of \d+ years",
    r"must have a valid email",
    r"must provide a.*phone number",
]

# Conversational AI phrases that indicate poor review quality
CONVERSATIONAL_PATTERNS = [
    r"based on the document you shared",
    r"based on the document you've shared",
    r"I'll give you a precise",
    r"I'll provide you",
    r"Let me know if",
    r"let me know your",
    r"I'd be happy to",
    r"I'll help you",
    r"if you'd like me to",
    r"tell me:",
    r"Need help\?",
    r"I'm here to",
    r"just say the word",
]

# Positive signals that indicate on-topic response (overrides off-topic detection)
ON_TOPIC_SIGNALS = [
    r"## overview",
    r"## key contributions",
    r"## methodology",
    r"## strengths",
    r"## weaknesses",
    r"## score",
    r"\*\*score:",
    r"## high priority",
    r"## recommendations",
    r"the manuscript",
    r"this research",
    r"the paper",
    r"the authors",
    r"the study",
]


def has_on_topic_signals(text: str) -> bool:
    """Check if response contains clear on-topic indicators.
    
    Args:
        text: Response text to check
        
    Returns:
        True if response has clear manuscript review signals
    """
    text_lower = text.lower()
    signals_found = 0
    for pattern in ON_TOPIC_SIGNALS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            signals_found += 1
    # If we find 2+ on-topic signals, it's clearly on-topic
    return signals_found >= 2


def detect_conversational_phrases(text: str) -> List[str]:
    """Detect conversational AI phrases in response text.
    
    Args:
        text: Response text to check
        
    Returns:
        List of conversational phrases found
    """
    text_lower = text.lower()
    phrases_found = []
    for pattern in CONVERSATIONAL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Extract a snippet of the matched text for logging
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                phrases_found.append(match.group(0)[:50])
    return phrases_found


def check_format_compliance(response: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Check response for format compliance issues.
    
    Simplified validation focusing on structural compliance only.
    Emojis and tables are allowed.
    
    Detects:
    - Conversational AI phrases (unprofessional for formal review)
    
    Args:
        response: The generated review text
        
    Returns:
        Tuple of (is_compliant, list of issues, details dict)
    """
    issues = []
    details: Dict[str, Any] = {
        "conversational_phrases": [],
    }
    
    # Check for conversational phrases (only format check we keep)
    phrases = detect_conversational_phrases(response)
    if phrases:
        details["conversational_phrases"] = phrases[:5]  # Limit to first 5
        # This is a warning, not a hard failure
        issues.append(f"Contains conversational AI phrases: {phrases[0][:30]}...")
    
    is_compliant = len(issues) == 0
    return is_compliant, issues, details


def is_off_topic(text: str) -> bool:
    """Check if response contains off-topic indicators.
    
    Uses a two-tier approach:
    1. Check for start-of-response patterns (strict)
    2. Check for anywhere patterns (must be strong signals)
    3. Override if clear on-topic signals are present
    
    Args:
        text: Response text to check
        
    Returns:
        True if response appears off-topic
    """
    # First check for on-topic signals - if present, not off-topic
    if has_on_topic_signals(text):
        return False
    
    text_lower = text.lower().strip()
    
    # Check start-of-response patterns
    for pattern in OFF_TOPIC_PATTERNS_START:
        if re.search(pattern, text_lower[:100], re.IGNORECASE | re.MULTILINE):
            return True
    
    # Check anywhere patterns (must be strong signals)
    for pattern in OFF_TOPIC_PATTERNS_ANYWHERE:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False


def validate_section_completeness(
    response: str,
    required_headers: List[str],
    flexible: bool = True
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate that all required sections are present in the response.
    
    Args:
        response: Response text to validate
        required_headers: List of required section headers (e.g., ["## Overview", "## Results"])
        flexible: If True, accepts semantic equivalents (e.g., "overview" matches "## Overview")
        
    Returns:
        Tuple of (is_complete, missing_sections, details)
    """
    found_headers = []
    missing_headers = []
    details: Dict[str, Any] = {
        "required": required_headers,
        "found": [],
        "missing": [],
    }
    
    response_lower = response.lower()
    
    for header in required_headers:
        # Extract header text without markdown
        header_text = header.replace("##", "").replace("#", "").strip().lower()
        
        # Check for exact match
        if header in response:
            found_headers.append(header)
            details["found"].append(header)
            continue
        
        # Check for flexible match
        if flexible:
            # Check for header text anywhere (case-insensitive)
            if header_text in response_lower:
                # Find the actual header used
                pattern = rf"#+\s*{re.escape(header_text)}"
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    found_headers.append(match.group(0))
                    details["found"].append(match.group(0))
                    continue
        
        missing_headers.append(header)
        details["missing"].append(header)
    
    is_complete = len(missing_headers) == 0
    return is_complete, missing_headers, details


def extract_structured_sections(response: str) -> Dict[str, str]:
    """Extract markdown sections from response into structured data.
    
    Args:
        response: Response text with markdown headers
        
    Returns:
        Dict mapping section headers to section content
    """
    sections: Dict[str, str] = {}
    
    # Pattern to match markdown headers (## Header or # Header)
    header_pattern = r'^(#{1,6})\s+(.+)$'
    
    lines = response.split('\n')
    current_header = None
    current_content: List[str] = []
    
    for line in lines:
        match = re.match(header_pattern, line)
        if match:
            # Save previous section
            if current_header:
                sections[current_header] = '\n'.join(current_content).strip()
            
            # Start new section
            current_header = match.group(2).strip()
            current_content = []
        else:
            if current_header:
                current_content.append(line)
    
    # Save last section
    if current_header:
        sections[current_header] = '\n'.join(current_content).strip()
    
    return sections


def validate_response_structure(
    response: str,
    required_headers: List[str],
    min_word_count: Optional[int] = None,
    max_word_count: Optional[int] = None,
    flexible_headers: bool = True
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Comprehensive structure validation for LLM responses.
    
    Args:
        response: Response text to validate
        required_headers: List of required section headers
        min_word_count: Minimum word count (optional)
        max_word_count: Maximum word count (optional)
        flexible_headers: If True, accepts semantic equivalents
        
    Returns:
        Tuple of (is_valid, issues, details)
    """
    issues: List[str] = []
    details: Dict[str, Any] = {
        "word_count": len(response.split()),
        "sections": {},
        "structure": {},
    }
    
    # Check word count
    word_count = details["word_count"]
    if min_word_count and word_count < min_word_count:
        issues.append(f"Word count too low: {word_count} < {min_word_count}")
    if max_word_count and word_count > max_word_count:
        issues.append(f"Word count too high: {word_count} > {max_word_count}")
    
    # Check section completeness
    is_complete, missing, section_details = validate_section_completeness(
        response, required_headers, flexible=flexible_headers
    )
    details["structure"] = section_details
    
    if not is_complete:
        issues.append(f"Missing sections: {', '.join(missing)}")
    
    # Extract sections
    sections = extract_structured_sections(response)
    details["sections"] = sections
    
    # Check section content (non-empty)
    for header in required_headers:
        header_text = header.replace("##", "").replace("#", "").strip().lower()
        found = False
        for section_header, content in sections.items():
            if header_text in section_header.lower():
                if len(content.strip()) < 50:  # Minimum content length
                    issues.append(f"Section '{section_header}' has insufficient content")
                found = True
                break
        if not found and not flexible_headers:
            issues.append(f"Section '{header}' not found or empty")
    
    is_valid = len(issues) == 0
    return is_valid, issues, details


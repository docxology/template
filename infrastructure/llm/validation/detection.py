"""Repetition detection and deduplication for LLM output validation.

Contains the core detection logic (detect_repetition, calculate_unique_content_ratio)
and section/paragraph deduplication (deduplicate_sections).
"""

from __future__ import annotations

import re
from typing import NamedTuple

from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.validation.similarity import (
    _calculate_similarity,
    _normalize_for_comparison,
)

logger = get_logger(__name__)


class RepetitionResult(NamedTuple):
    """Result of detect_repetition.

    NamedTuple is intentional: 7 call sites use positional unpacking
    (``found, examples, ratio = detect_repetition(text)``).
    """

    found: bool
    examples: list[str]
    unique_ratio: float


def calculate_unique_content_ratio(text: str, chunk_size: int = 200) -> float:
    """Calculate ratio of unique content in text.

    Args:
        text: Text to analyze
        chunk_size: Size of chunks to compare

    Returns:
        Ratio of unique content (0.0-1.0)
    """
    if not text or len(text) < chunk_size * 2:
        return 1.0

    # First try splitting by paragraphs/sections (double newlines)
    # This is better for detecting repeated sections
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) >= chunk_size // 2]

    if len(paragraphs) >= 2:
        # Use paragraphs as chunks if we have enough
        chunks = paragraphs
    else:
        # Fall back to fixed-size chunks
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    if len(chunks) < 2:
        return 1.0

    # Count unique chunks using normalized comparison
    normalized_chunks = [_normalize_for_comparison(c) for c in chunks]
    unique_chunks = set()

    for normalized in normalized_chunks:
        # Use first 200 chars as key for comparison
        key = normalized[:200] if len(normalized) > 200 else normalized
        unique_chunks.add(key)

    return len(unique_chunks) / len(chunks) if chunks else 1.0


def detect_repetition(
    text: str,
    min_chunk_size: int = 100,
    similarity_threshold: float = 0.8,
    similarity_method: str = "hybrid",
) -> RepetitionResult:
    """Detect repetitive content in LLM output with improved semantic detection.

    Uses hybrid similarity methods to better identify true repetition vs.
    conceptually similar but differently worded content.

    Args:
        text: The text to analyze
        min_chunk_size: Minimum characters for a chunk to be considered
        similarity_threshold: Threshold (0-1) above which chunks are considered duplicates
        similarity_method: Similarity method ("jaccard", "tfidf", "hybrid")

    Returns:
        RepetitionResult with fields: found, examples, unique_ratio.
        Supports positional unpacking: found, examples, ratio = detect_repetition(text)
    """
    if not text or len(text) < min_chunk_size * 2:
        return RepetitionResult(False, [], 1.0)

    # Split by common section markers with better pattern matching
    section_patterns = [
        r"\n### ",  # H3 headers
        r"\n## ",  # H2 headers
        r"\n# ",  # H1 headers
        r"\n\n\n",  # Triple newlines (section breaks)
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
        chunks = [p.strip() for p in text.split("\n\n") if len(p.strip()) >= min_chunk_size]

    if len(chunks) < 2:
        return RepetitionResult(False, [], 1.0)

    # Normalize chunks for comparison
    normalized_chunks = [_normalize_for_comparison(c) for c in chunks]

    # Find duplicates using improved similarity methods
    duplicates = []
    seen_hashes = set()
    unique_count = 0

    # Use larger comparison window (400 chars instead of 200)
    for _, (chunk, normalized) in enumerate(zip(chunks, normalized_chunks)):
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
                normalized_chunks[i], normalized_chunks[j], method=similarity_method
            )
            if similarity >= similarity_threshold:
                if chunks[j] not in duplicates:
                    duplicates.append(
                        chunks[j][:100] + "..." if len(chunks[j]) > 100 else chunks[j]
                    )

    # Calculate unique content ratio
    # For better detection, also check content without headers
    content_only = re.sub(r"^#{1,6}\s+[^\n]+\n?", "", text, flags=re.MULTILINE)
    unique_ratio = calculate_unique_content_ratio(content_only if content_only.strip() else text)

    has_repetition = len(duplicates) > 0 or unique_ratio < 0.7

    return RepetitionResult(has_repetition, duplicates, unique_ratio)


def _deduplicate_paragraphs(
    text: str,
    max_repetitions: int,
    similarity_threshold: float,
    min_content_preservation: float,
) -> str:
    """Deduplicate at paragraph level with semantic similarity."""
    paragraphs = text.split("\n\n")
    if len(paragraphs) < 3:
        return text

    original_length = len(text)
    seen_content: dict[str, dict] = {}
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
                    logger.debug(f"Duplicate paragraph detected (similarity: {similarity:.2f})")
                break

        if not is_duplicate:
            seen_content[key] = {"count": 1, "text": key}
            result_paragraphs.append(para)
        else:
            removed_count += 1

    result = "\n\n".join(result_paragraphs)

    # Content preservation check
    if len(result) / original_length < min_content_preservation:
        logger.warning(
            "Paragraph deduplication would remove too much content. Skipping deduplication."
        )
        return text

    if removed_count > 0:
        logger.info(
            f"Paragraph deduplication removed {removed_count} duplicates "
            f"({original_length} → {len(result)} chars)"
        )

    return result


def deduplicate_sections(
    text: str,
    max_repetitions: int = 2,
    mode: str = "conservative",
    similarity_threshold: float = 0.85,
    min_content_preservation: float = 0.7,
) -> str:
    """Remove repeated sections from LLM output with improved semantic detection.

    Uses configurable similarity thresholds and preservation rules to avoid
    removing valid content that happens to be conceptually similar.

    Args:
        text: The text to deduplicate
        max_repetitions: Maximum times a section can appear. Overridden by mode when
            mode is "conservative" (floor 3) or "aggressive" (ceiling 1).
        mode: Deduplication mode ("conservative", "balanced", "aggressive"). When not
            "balanced", mode overrides the caller-supplied similarity_threshold and
            max_repetitions to enforce preset bounds.
        similarity_threshold: Similarity threshold above which content is considered
            duplicate. Overridden by mode when mode is "conservative" (floor 0.9) or
            "aggressive" (ceiling 0.7). Pass mode="balanced" to use this value as-is.
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
    section_pattern = r"(^|\n)(#{2,3}\s+[^\n]+(?:\n|$))"
    parts = re.split(section_pattern, text)

    if len(parts) < 3:
        # Not enough sections to deduplicate, try paragraphs
        return _deduplicate_paragraphs(
            text, max_repetitions, similarity_threshold, min_content_preservation
        )

    # Track seen sections with semantic similarity
    seen_sections: dict[str, dict] = {}  # key -> {"count": int, "text": str}
    result_parts = []
    removed_count = 0

    i = 0
    while i < len(parts):
        part = parts[i]

        # Check if this is a header
        if re.match(r"#{2,3}\s+", part.strip()):
            # Get header and content (expanded window)
            header = part
            content = parts[i + 1] if i + 1 < len(parts) else ""

            # Use larger comparison window (500 chars instead of 200)
            comparison_text = header + content[:500]
            normalized = _normalize_for_comparison(comparison_text)

            # Check similarity against existing sections
            is_duplicate = False

            for existing_key, existing_data in seen_sections.items():
                similarity = _calculate_similarity(normalized, existing_key, method="hybrid")
                if similarity >= similarity_threshold:
                    existing_data["count"] += 1
                    if existing_data["count"] >= max_repetitions:
                        is_duplicate = True
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

    result = "".join(result_parts)

    # Apply content preservation rule
    if len(result) / original_length < min_content_preservation:
        logger.warning(
            f"Deduplication would remove too much content "
            f"({len(result)}/{original_length} = {len(result) / original_length:.1%}). "
            f"Using conservative fallback."
        )
        # Fallback to more conservative deduplication
        return deduplicate_sections(
            text,
            max_repetitions=max_repetitions + 1,
            mode="conservative",
            similarity_threshold=0.95,
            min_content_preservation=0.8,
        )

    if removed_count > 0:
        logger.info(
            f"Deduplication removed {removed_count} duplicate sections "
            f"({original_length} → {len(result)} chars, "
            f"{len(result) / original_length:.1%} preserved)"
        )

    return result

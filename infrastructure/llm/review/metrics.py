"""Metrics classes and calculations for LLM review generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ReviewMetrics:
    """Metrics for a single review generation."""
    input_chars: int = 0
    input_words: int = 0
    input_tokens_est: int = 0  # Estimated tokens (~4 chars/token)
    output_chars: int = 0
    output_words: int = 0
    output_tokens_est: int = 0
    generation_time_seconds: float = 0.0
    preview: str = ""  # First 150 chars of response


@dataclass
class ManuscriptMetrics:
    """Metrics for the manuscript input."""
    total_chars: int = 0
    total_words: int = 0
    total_tokens_est: int = 0
    truncated: bool = False
    truncated_chars: int = 0  # Chars after truncation (if any)


@dataclass
class SessionMetrics:
    """Complete metrics for the review session."""
    manuscript: ManuscriptMetrics = field(default_factory=ManuscriptMetrics)
    reviews: Dict[str, ReviewMetrics] = field(default_factory=dict)
    total_generation_time: float = 0.0
    model_name: str = ""
    max_input_length: int = 0
    warmup_tokens_per_sec: float = 0.0  # Performance from warmup step


@dataclass
class StreamingMetrics:
    """Metrics for streaming response generation."""
    chunk_count: int = 0
    total_chars: int = 0
    total_tokens_est: int = 0  # Estimated tokens (~4 chars/token)
    streaming_time_seconds: float = 0.0
    chunks_per_second: float = 0.0
    bytes_per_second: float = 0.0
    error_count: int = 0
    partial_response_saved: bool = False
    first_chunk_time: float = 0.0  # Time to first chunk
    last_chunk_time: float = 0.0  # Time of last chunk


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (approximately 4 characters per token).
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    return len(text) // 4











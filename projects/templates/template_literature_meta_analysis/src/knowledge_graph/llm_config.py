"""LLM extraction configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for the LLM-based extraction backend."""

    base_url: str = "http://localhost:11434"
    model: str = "gemma3:4b"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_delay: float = 2.0
    nanopub_path: str | None = None
    checkpoint_interval: int = 50
    max_papers: int | None = None
    min_confidence: float = 0.0

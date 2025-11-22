"""Configuration for LLM module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class LLMConfig:
    """Configuration for LLM interaction."""
    
    # Connection settings
    base_url: str = "http://localhost:11434"
    timeout: float = 60.0
    
    # Model settings
    default_model: str = "llama3"
    fallback_models: list[str] = field(default_factory=lambda: ["mistral", "phi3"])
    
    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    context_window: int = 4096
    
    # System prompt
    system_prompt: str = (
        "You are an expert research assistant. "
        "Provide clear, accurate, and scientifically rigorous responses. "
        "Cite sources when possible."
    )

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create configuration from environment variables."""
        return cls()


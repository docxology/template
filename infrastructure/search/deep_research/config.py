"""Configuration for deep research provider dispatch."""

from __future__ import annotations

import os
from dataclasses import dataclass


OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
OPENAI_MODEL_ENV = "OPENAI_DEEP_RESEARCH_MODEL"
GEMINI_AGENT_ENV = "GEMINI_DEEP_RESEARCH_AGENT"

DEFAULT_OPENAI_MODEL = "o3-deep-research"
DEFAULT_GEMINI_AGENT = "deep-research-preview-04-2026"


@dataclass(frozen=True)
class DeepResearchConfig:
    """Environment-backed deep research settings."""

    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    openai_model: str = DEFAULT_OPENAI_MODEL
    gemini_agent: str = DEFAULT_GEMINI_AGENT
    default_provider: str = "auto"

    @classmethod
    def from_env(cls) -> "DeepResearchConfig":
        return cls(
            openai_api_key=os.getenv(OPENAI_API_KEY_ENV),
            gemini_api_key=os.getenv(GEMINI_API_KEY_ENV),
            openai_model=os.getenv(OPENAI_MODEL_ENV, DEFAULT_OPENAI_MODEL),
            gemini_agent=os.getenv(GEMINI_AGENT_ENV, DEFAULT_GEMINI_AGENT),
        )

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)


__all__ = [
    "DEFAULT_GEMINI_AGENT",
    "DEFAULT_OPENAI_MODEL",
    "DeepResearchConfig",
    "GEMINI_AGENT_ENV",
    "GEMINI_API_KEY_ENV",
    "OPENAI_API_KEY_ENV",
    "OPENAI_MODEL_ENV",
]

"""Optional local-LLM filtering for literature-search results."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from literature.models import Paper

logger = logging.getLogger(__name__)


class LLMFilterEngine:
    """Engine for applying LLM-based content filters to papers."""

    def __init__(self, llm_config: dict[str, Any]):
        """Initialize the LLM filter engine from a config dict.

        Args:
            llm_config: Configuration with optional keys ``model``,
                ``base_url``, ``temperature``, ``timeout_seconds``, and
                ``max_retries``.
        """
        self.model: str = llm_config.get("model", "gemma3:4b")
        self.base_url: str = llm_config.get("base_url", "http://localhost:11434")
        self.temperature: float = llm_config.get("temperature", 0.1)
        self.timeout: int = llm_config.get("timeout_seconds", 120)
        self.max_retries: int = llm_config.get("max_retries", 3)

    def apply_filter(self, paper: Paper, filter_config: dict[str, Any]) -> str:
        """Apply an LLM filter to a paper's abstract. Returns the classification."""
        if not paper.abstract or not paper.abstract.strip():
            return "no_abstract"

        prompt = filter_config["prompt"].format(abstract=paper.abstract)

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": self.temperature},
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()
                answer = str(result.get("response", "")).strip().lower()

                # Clean up common single-label response punctuation without
                # altering punctuation inside a legitimate category name.
                answer = answer.strip(" \t\r\n\"'.")
                return answer

            except (requests.RequestException, ValueError, TypeError) as exc:
                logger.warning("LLM filter attempt %d failed: %s", attempt + 1, exc)
                if attempt == self.max_retries - 1:
                    return "error"
                time.sleep(2**attempt)

        return "error"


__all__ = ["LLMFilterEngine"]

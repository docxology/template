"""Text utility functions for LLM response processing."""

from __future__ import annotations

import re


def strip_thinking_tags(text: str) -> str:
    """Remove thinking tags from LLM responses.

    Some models (e.g., Qwen) output <think>...</think> tags before their
    actual response. Handles case-insensitive tags and malformed closers
    (e.g., </think> without a matching opener).

    Example:
        >>> text = "<think>Let me think about this...</think>The answer is 42."
        >>> strip_thinking_tags(text)
        'The answer is 42.'
    """
    if not text:
        return text

    # Remove <think>...</think> tags (case-insensitive, handles whitespace)
    # Pattern matches: <think>...</think>, <think >...</think>, <THINK>...</THINK>, etc.
    pattern = r"<think[^>]*>.*?</think>"
    result = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Also handle </think> without opening tag (malformed)
    result = re.sub(r"</think>", "", result, flags=re.IGNORECASE)

    # Clean up extra whitespace that might result
    result = result.strip()

    return result

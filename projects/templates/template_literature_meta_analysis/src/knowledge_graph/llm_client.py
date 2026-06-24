"""HTTP client and response parsing for Ollama LLM extraction."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from knowledge_graph.llm_config import LLMConfig
from knowledge_graph.llm_prompts import _SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def call_ollama(prompt: str, config: LLMConfig) -> tuple[str, dict[str, float | int]]:
    """Send *prompt* to Ollama ``/api/generate`` and return text + metadata."""
    url = f"{config.base_url}/api/generate"
    payload = {
        "model": config.model,
        "prompt": prompt,
        "system": _SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": config.temperature, "num_predict": config.max_tokens},
    }
    resp = requests.post(url, json=payload, timeout=config.timeout_seconds)
    resp.raise_for_status()
    data = resp.json()
    response_text = data.get("response", "")
    eval_duration_ns = data.get("eval_duration", 0)
    eval_count = data.get("eval_count", 0)
    eval_duration_s = eval_duration_ns / 1e9 if eval_duration_ns else 0
    tokens_per_s = (eval_count / eval_duration_s) if eval_duration_s > 0 else 0
    meta = {
        "prompt_chars": len(prompt),
        "response_chars": len(response_text),
        "eval_duration_s": round(eval_duration_s, 2),
        "tokens_per_s": round(tokens_per_s, 1),
        "eval_count": eval_count,
    }
    return response_text, meta


def parse_llm_response(raw: str) -> list[dict[str, Any]]:
    """Parse the LLM JSON array response, stripping fences when present."""
    text = raw.strip()
    if text.startswith("```"):
        first_newline = text.index("\n")
        text = text[first_newline + 1 :]
    if text.endswith("```"):
        text = text[:-3].rstrip()

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON array found in LLM response: {text[:200]}")

    json_str = text[start : end + 1]
    max_attempts = 2
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = json.loads(json_str)
            break
        except json.JSONDecodeError as exc:
            logger.debug("LLM raw response: %s", raw)
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2 * (2 ** (attempt - 1)))
            else:
                raise ValueError(
                    f"Failed to parse JSON from LLM response after {max_attempts} attempts: {exc}"
                ) from exc
    else:
        raise ValueError(f"Failed to parse JSON: {last_error}")

    if not isinstance(result, list):
        raise ValueError(f"Expected JSON array, got {type(result).__name__}")
    return result

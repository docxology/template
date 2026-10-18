"""Build :class:`LLMClient` instances that talk to the real Ollama daemon.

``tests/infra_tests/llm/conftest.py`` patches ``OLLAMA_HOST`` to ``pytest_httpserver`` for
most tests. Any test that needs the local daemon must use an explicit
``OllamaClientConfig`` (default ``base_url`` is ``http://localhost:11434``) and a known
model — this module centralizes that pattern for ``@pytest.mark.requires_ollama`` tests.
"""

from __future__ import annotations

import os

import pytest

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig
from infrastructure.llm.utils.ollama import preload_model, select_small_fast_model


def build_real_small_llm_client(
    *,
    auto_inject_system_prompt: bool = True,
    timeout: float = 30.0,
) -> LLMClient:
    """Return a preloaded client for the configured real daemon endpoint."""
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model_name = select_small_fast_model(base_url)
    if not model_name:
        pytest.fail("Expected an Ollama model after ensure_ollama_for_tests")
    ok, err = preload_model(model_name, base_url=base_url, timeout=10.0, retries=0, context_window=4096)
    if not ok:
        pytest.fail(f"Ollama model {model_name!r} failed to preload: {err}")
    return LLMClient(
        OllamaClientConfig(
            base_url=base_url,
            default_model=model_name,
            timeout=timeout,
            max_tokens=128,
            context_window=4096,
            fallback_models=[],
            request_retries=0,
            temperature=0.0,
            seed=42,
            auto_inject_system_prompt=auto_inject_system_prompt,
        )
    )

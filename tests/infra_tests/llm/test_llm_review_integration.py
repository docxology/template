"""Ollama-gated integration tests for LLM manuscript review."""

from __future__ import annotations

import pytest


@pytest.mark.requires_ollama
@pytest.mark.timeout(180)
class TestLLMReviewIntegration:
    """Integration tests requiring Ollama server."""

    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        pass

    def test_select_and_start_ollama_model(self):
        """Test Ollama model selection and startup."""
        from infrastructure.llm.utils.ollama import (
            get_available_model_info,
            is_ollama_running,
            select_best_model,
        )

        assert is_ollama_running() is True
        models = get_available_model_info()
        assert len(models) > 0
        model = select_best_model()
        assert model is not None
        assert isinstance(model, str)

    def test_generate_review_with_real_llm(self):
        """Test generating a review with real LLM."""
        from infrastructure.llm.review.generator import generate_llm_executive_summary as generate_executive_summary
        from infrastructure.llm.utils.ollama import is_ollama_running, preload_model, select_small_fast_model

        if not is_ollama_running():
            pytest.fail("Ollama server is not running (ensure_ollama_for_tests should have started it).")

        model = select_small_fast_model()
        if not model:
            pytest.fail("No Ollama models available.")

        ok, err = preload_model(model, timeout=10.0, retries=0)
        if not ok:
            pytest.fail(f"Ollama model {model!r} failed to preload: {err}")

        from infrastructure.llm.core.client import LLMClient
        from infrastructure.llm.core.config import OllamaClientConfig

        client = LLMClient(
            OllamaClientConfig(
                base_url="http://localhost:11434",
                default_model=model,
                timeout=60.0,
                auto_inject_system_prompt=True,
            )
        )
        test_text = "This is a brief manuscript to test actual LLM functionality."
        response, metrics = generate_executive_summary(client, test_text, model_name=model)

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

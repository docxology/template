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
        from infrastructure.llm.core.client import LLMClient

        from .real_ollama_client import build_real_small_llm_client

        client = build_real_small_llm_client(timeout=60.0)
        # This smoke proves real review generation and metrics at a finite size.
        client = LLMClient(client.config.with_overrides(long_max_tokens=128))
        test_text = "This is a brief manuscript to test actual LLM functionality."
        response, metrics = generate_executive_summary(
            client, test_text, model_name=client.config.default_model, temperature=0.0
        )

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)
        assert metrics.input_chars == len(test_text)
        assert metrics.output_chars == len(response)
        assert metrics.generation_time_seconds > 0

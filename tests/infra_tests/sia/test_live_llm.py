"""Tests for optional LLM feedback."""

from __future__ import annotations

from infrastructure.sia.live_llm import generate_improvement_markdown


def test_generate_improvement_markdown_empty_model():
    assert (
        generate_improvement_markdown(
            generation=2,
            metric_name="accuracy",
            metric_value=0.5,
            llm_model="",
        )
        is None
    )

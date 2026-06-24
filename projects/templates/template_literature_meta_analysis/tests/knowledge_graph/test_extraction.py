"""Expanded tests for knowledge_graph.extraction wrapper."""

from __future__ import annotations

import json

from pytest_httpserver import HTTPServer

from knowledge_graph.extraction import extract_assertions
from knowledge_graph.llm_extraction import LLMConfig
from literature.models import Paper


def _paper() -> Paper:
    return Paper(
        title="Active Inference",
        abstract="This paper supports the free energy principle.",
        authors=[],
        year=2023,
        doi="10.1234/test",
    )


def test_extract_assertions_via_httpserver(httpserver: HTTPServer) -> None:
    """Exercise extraction wrapper against a local Ollama-shaped HTTP stub."""
    response_payload = json.dumps(
        [
            {
                "hypothesis_id": "PRIMARY_EFFICACY",
                "direction": "supports",
                "confidence": 0.9,
                "reasoning": "Explicit FEP support in abstract.",
            }
        ]
    )
    httpserver.expect_request("/api/generate", method="POST").respond_with_data(
        json.dumps({"response": response_payload}),
        content_type="application/json",
    )
    config = LLMConfig(base_url=httpserver.url_for(""), model="gemma3:4b")
    assertions = extract_assertions([_paper()], llm_config=config)
    assert len(assertions) >= 1
    assert assertions[0].hypothesis_id == "PRIMARY_EFFICACY"


def test_extract_assertions_empty_papers() -> None:
    config = LLMConfig(base_url="http://localhost:11434", model="gemma3:4b")
    assert extract_assertions([], llm_config=config) == []

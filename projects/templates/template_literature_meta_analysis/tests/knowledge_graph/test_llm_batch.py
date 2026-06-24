"""Tests for knowledge_graph.llm_extraction — batch extraction and unified entry point."""

from __future__ import annotations

import json

from pytest_httpserver import HTTPServer

from knowledge_graph.extraction import extract_assertions
from knowledge_graph.llm_extraction import (
    LLMConfig,
    extract_assertions_llm,
)
from tests.knowledge_graph.llm_extraction_fixtures import (
    httpserver_base_url,
    make_paper,
    valid_llm_response,
)

_make_paper = make_paper
_valid_llm_response = valid_llm_response


class TestExtractAssertionsLLM:
    def test_batch_extraction(self, httpserver: HTTPServer):
        """Multiple papers processed sequentially."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
        )

        papers = [make_paper(doi=f"10.1234/p{i}") for i in range(3)]
        assertions = extract_assertions_llm(papers, config)

        # 3 papers × 3 non-irrelevant assertions each = 9
        assert len(assertions) == 9

    def test_papers_without_abstract_skipped(self, httpserver: HTTPServer):
        """Papers without abstracts are silently skipped."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
        )

        papers = [
            make_paper(abstract="", doi="10.1234/empty"),
            make_paper(doi="10.1234/with_abstract"),
        ]
        assertions = extract_assertions_llm(papers, config)

        # Only 1 paper processed (the one with abstract)
        assert len(assertions) == 3


# ---------------------------------------------------------------------------
# Test: unified entry point (extraction.py)
# ---------------------------------------------------------------------------


class TestExtractAssertions:
    def test_default_config(self, httpserver: HTTPServer):
        """Without explicit config, uses default LLMConfig."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
        )

        papers = [make_paper()]
        assertions = extract_assertions(papers, llm_config=config)
        assert len(assertions) == 3
        # LLM method produces assertions with "llm_" prefix
        assert all(a.assertion_id.startswith("llm_") for a in assertions)

    def test_custom_config(self, httpserver: HTTPServer):
        """Custom LLMConfig is forwarded correctly."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="custom-model",
            temperature=0.5,
            max_retries=1,
        )

        papers = [make_paper()]
        assertions = extract_assertions(papers, llm_config=config)
        assert len(assertions) == 3

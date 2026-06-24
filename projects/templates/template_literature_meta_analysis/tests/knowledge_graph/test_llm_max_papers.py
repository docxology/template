"""Tests for knowledge_graph.llm_extraction — max_papers cap."""

from __future__ import annotations

import json
import logging

from pytest_httpserver import HTTPServer

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


class TestMaxPapers:
    def test_max_papers_limits_extraction(self, httpserver: HTTPServer):
        """Setting max_papers stops extraction after that many papers."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            max_papers=2,
        )

        papers = [make_paper(doi=f"10.1234/p{i}") for i in range(5)]
        assertions = extract_assertions_llm(papers, config)

        # Only 2 papers processed × 3 assertions each = 6
        assert len(assertions) == 6

    def test_max_papers_none_processes_all(self, httpserver: HTTPServer):
        """max_papers=None (default) processes all papers."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            max_papers=None,
        )

        papers = [make_paper(doi=f"10.1234/p{i}") for i in range(4)]
        assertions = extract_assertions_llm(papers, config)

        # All 4 papers × 3 assertions = 12
        assert len(assertions) == 12

    def test_max_papers_with_resume(self, httpserver: HTTPServer, tmp_path):
        """max_papers counts only newly processed papers, not resumed ones."""
        from knowledge_graph.nanopublication import (
            Assertion,
            create_nanopub,
            serialize_nanopubs,
        )

        nanopub_path = tmp_path / "nanopublications.jsonl"
        existing = Assertion(
            assertion_id="llm_doi:10.1/a_PRIMARY_EFFICACY",
            paper_id="doi:10.1/a",
            claim="existing",
            assertion_type="supports",
            hypothesis_id="PRIMARY_EFFICACY",
            confidence=0.8,
            citation_count=3,
        )
        serialize_nanopubs(
            [create_nanopub(existing, attribution="test")],
            nanopub_path,
        )

        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            nanopub_path=str(nanopub_path),
            checkpoint_interval=100,
            max_papers=1,  # only process 1 NEW paper
        )

        papers = [
            make_paper(doi="10.1/a", title="Already done"),
            make_paper(doi="10.1/b", title="New 1"),
            make_paper(doi="10.1/c", title="New 2"),
        ]
        assertions = extract_assertions_llm(papers, config)

        # 1 from resumed + 3 from 1 new paper = 4
        assert len(assertions) == 4

    def test_max_papers_logs_limit(self, httpserver: HTTPServer, caplog):
        """When max_papers is set, a log message announces the limit."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            max_papers=2,
        )

        papers = [make_paper(doi=f"10.1234/p{i}") for i in range(5)]
        with caplog.at_level(logging.INFO, logger="knowledge_graph.llm_extraction"):
            extract_assertions_llm(papers, config)

        assert any("max_papers=2" in m for m in caplog.messages)
        assert any("stopping extraction early" in m for m in caplog.messages)

    def test_max_papers_zero_processes_none(self, httpserver: HTTPServer):
        """max_papers=0 means no papers are processed."""
        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            max_papers=0,
        )

        papers = [make_paper(doi="10.1234/p0")]
        assertions = extract_assertions_llm(papers, config)
        assert len(assertions) == 0

"""Tests for knowledge_graph.llm_extraction — nanopub resume."""

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


class TestNanopubResume:
    def test_resume_skips_processed(self, httpserver: HTTPServer, tmp_path):
        """Resume skips papers already in the nanopubs file."""
        from knowledge_graph.nanopublication import (
            Assertion,
            create_nanopub,
            serialize_nanopubs,
        )

        nanopub_path = tmp_path / "nanopublications.jsonl"

        # Paper with doi="10.1/a" will have canonical_id="doi:10.1/a"
        paper1_cid = "doi:10.1/a"
        existing_assertion = Assertion(
            assertion_id=f"llm_{paper1_cid}_PRIMARY_EFFICACY",
            paper_id=paper1_cid,
            claim="Pre-existing",
            assertion_type="supports",
            hypothesis_id="PRIMARY_EFFICACY",
            confidence=0.8,
            citation_count=3,
        )
        serialize_nanopubs(
            [create_nanopub(existing_assertion, attribution="test")],
            nanopub_path,
        )

        # Set up server for paper2 only
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
        )

        papers = [
            make_paper(doi="10.1/a", title="Paper 1"),
            make_paper(doi="10.1/b", title="Paper 2"),
        ]
        assertions = extract_assertions_llm(papers, config)
        # Should have 1 from existing nanopubs + 3 from paper2
        assert len(assertions) == 4

    def test_fresh_run_no_nanopub_file(self, httpserver: HTTPServer, tmp_path):
        """When no nanopub file exists, processes all papers."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        nanopub_path = tmp_path / "nanopublications.jsonl"
        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            nanopub_path=str(nanopub_path),
            checkpoint_interval=100,
        )

        papers = [make_paper(doi=f"10.1/{i}") for i in range(2)]
        assertions = extract_assertions_llm(papers, config)
        # 2 papers × 3 non-irrelevant assertions = 6
        assert len(assertions) == 6
        # Nanopub file should have been created
        assert nanopub_path.exists()

    def test_nanopub_file_updated_after_extraction(self, httpserver: HTTPServer, tmp_path):
        """After extraction, nanopub file on disk contains all results."""
        from knowledge_graph.nanopublication import deserialize_nanopubs

        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        nanopub_path = tmp_path / "nanopublications.jsonl"
        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            nanopub_path=str(nanopub_path),
            checkpoint_interval=100,
        )

        papers = [make_paper(doi="10.1/x")]
        extract_assertions_llm(papers, config)

        nanopubs = deserialize_nanopubs(nanopub_path)
        assert len(nanopubs) == 3  # 3 non-irrelevant
        assert all(np_obj.assertion.paper_id == "doi:10.1/x" for np_obj in nanopubs)

    def test_logs_nanopub_path_on_fresh_run(self, httpserver: HTTPServer, tmp_path, caplog):
        """Fresh run logs the nanopub output path."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        nanopub_path = tmp_path / "nanopublications.jsonl"
        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
            nanopub_path=str(nanopub_path),
            checkpoint_interval=100,
        )

        papers = [make_paper(doi="10.1/log")]
        with caplog.at_level(logging.INFO, logger="knowledge_graph.llm_extraction"):
            extract_assertions_llm(papers, config)

        # Should log persistence file path and completion path
        assert any("Nanopub persistence file" in m for m in caplog.messages)
        assert any("Nanopublications saved" in m for m in caplog.messages)
        assert any(str(nanopub_path) in m for m in caplog.messages)

    def test_logs_resume_info(self, httpserver: HTTPServer, tmp_path, caplog):
        """Resume run logs how many papers were already processed."""
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
        )

        papers = [
            make_paper(doi="10.1/a", title="Paper A"),
            make_paper(doi="10.1/b", title="Paper B"),
        ]
        with caplog.at_level(logging.INFO, logger="knowledge_graph.llm_extraction"):
            extract_assertions_llm(papers, config)

        assert any("Resuming" in m for m in caplog.messages)
        assert any("1 papers already processed" in m for m in caplog.messages)

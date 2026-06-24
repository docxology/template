"""Tests for knowledge_graph.llm_extraction — single-paper LLM assessment."""

from __future__ import annotations

import json

import pytest
from pytest_httpserver import HTTPServer

from knowledge_graph.llm_extraction import (
    LLMConfig,
    assess_paper_hypotheses,
)
from tests.knowledge_graph.llm_extraction_fixtures import (
    httpserver_base_url,
    make_paper,
    valid_llm_response,
)

_make_paper = make_paper
_valid_llm_response = valid_llm_response


class TestAssessPaperHypotheses:
    def test_successful_assessment(self, httpserver: HTTPServer):
        """LLM returns valid JSON → assertions are created correctly."""
        response_body = {
            "response": json.dumps(valid_llm_response()),
            "done": True,
        }
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(response_body)

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),  # strip trailing slash
            model="test-model",
            max_retries=1,
        )

        paper = make_paper()
        assertions = assess_paper_hypotheses(paper, config)

        # "irrelevant" entries are excluded → 3 should remain
        assert len(assertions) == 3

        # Check the supporting assertion
        fep = [a for a in assertions if a.hypothesis_id == "PRIMARY_EFFICACY"]
        assert len(fep) == 1
        assert fep[0].assertion_type == "supports"
        assert fep[0].confidence == 0.85
        assert fep[0].citation_count == 42

        # Check the contradicting assertion
        pc = [a for a in assertions if a.hypothesis_id == "PROCESS_MODEL"]
        assert len(pc) == 1
        assert pc[0].assertion_type == "contradicts"
        assert pc[0].confidence == 0.6

        # Check the neutral assertion
        mb = [a for a in assertions if a.hypothesis_id == "MECHANISTIC_BASIS"]
        assert len(mb) == 1
        assert mb[0].assertion_type == "neutral"

    def test_invalid_directions_skipped(self, httpserver: HTTPServer):
        """Unknown directions are silently skipped."""
        response_data = [
            {"hypothesis_id": "PRIMARY_EFFICACY", "direction": "maybe", "confidence": 0.5, "reasoning": "unsure"},
            {"hypothesis_id": "OPTIMAL_PERFORMANCE", "direction": "supports", "confidence": 0.7, "reasoning": "ok"},
        ]
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(
            {"response": json.dumps(response_data), "done": True}
        )

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
        )

        assertions = assess_paper_hypotheses(make_paper(), config)
        assert len(assertions) == 1
        assert assertions[0].hypothesis_id == "OPTIMAL_PERFORMANCE"

    def test_unknown_hypothesis_ids_skipped(self, httpserver: HTTPServer):
        """Hypothesis IDs not in the standard set are skipped."""
        response_data = [
            {"hypothesis_id": "MADE_UP_THING", "direction": "supports", "confidence": 0.9, "reasoning": "nope"},
        ]
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(
            {"response": json.dumps(response_data), "done": True}
        )

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
        )

        assertions = assess_paper_hypotheses(make_paper(), config)
        assert len(assertions) == 0

    def test_retries_on_parse_failure(self, httpserver: HTTPServer):
        """First response is garbage JSON, second is valid → succeeds."""
        # First request: bad response
        httpserver.expect_ordered_request("/api/generate", method="POST").respond_with_json(
            {"response": "Not valid JSON at all", "done": True}
        )

        # Second request: valid response
        httpserver.expect_ordered_request("/api/generate", method="POST").respond_with_json(
            {
                "response": json.dumps(valid_llm_response()),
                "done": True,
            }
        )

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=2,
            retry_delay=0.01,  # fast for tests
        )

        assertions = assess_paper_hypotheses(make_paper(), config)
        assert len(assertions) == 3  # 3 non-irrelevant

    def test_all_retries_exhausted_raises_runtime_error(self, httpserver: HTTPServer):
        """All retries fail → RuntimeError."""
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(
            {"response": "garbage", "done": True}
        )

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=2,
            retry_delay=0.01,
        )

        with pytest.raises(RuntimeError, match="failed after 2 retries"):
            assess_paper_hypotheses(make_paper(), config)

    def test_confidence_clamped(self, httpserver: HTTPServer):
        """Confidence values outside [0, 1] are clamped."""
        response_data = [
            {"hypothesis_id": "PRIMARY_EFFICACY", "direction": "supports", "confidence": 1.5, "reasoning": "high"},
            {
                "hypothesis_id": "OPTIMAL_PERFORMANCE",
                "direction": "contradicts",
                "confidence": -0.3,
                "reasoning": "low",
            },
        ]
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(
            {"response": json.dumps(response_data), "done": True}
        )

        config = LLMConfig(
            base_url=httpserver_base_url(httpserver),
            model="test-model",
            max_retries=1,
        )

        assertions = assess_paper_hypotheses(make_paper(), config)
        assert assertions[0].confidence == 1.0
        assert assertions[1].confidence == 0.0

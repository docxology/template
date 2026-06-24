"""Tests for knowledge_graph.llm_extraction — prompt construction and JSON parsing."""

from __future__ import annotations

import json

import pytest

from knowledge_graph.llm_extraction import (
    _parse_llm_response,
    build_prompt,
    _hypothesis_dicts,
)
from tests.knowledge_graph.llm_extraction_fixtures import (
    make_paper,
    valid_llm_response,
)

_make_paper = make_paper
_valid_llm_response = valid_llm_response


class TestBuildPrompt:
    def test_prompt_contains_paper_info(self):
        paper = make_paper()
        hypotheses = _hypothesis_dicts()
        prompt = build_prompt(paper, hypotheses)

        assert "Active Inference and Free Energy" in prompt
        assert "free energy principle" in prompt
        assert "PRIMARY_EFFICACY" in prompt
        assert "OPTIMAL_PERFORMANCE" in prompt
        assert "JSON array" in prompt

    def test_prompt_with_long_abstract(self):
        paper = make_paper(abstract="x" * 5000)
        prompt = build_prompt(paper, _hypothesis_dicts())
        assert len(prompt) > 5000

    def test_hypothesis_dicts_returns_all_eight(self):
        dicts = _hypothesis_dicts()
        assert len(dicts) == 8
        ids = {d["id"] for d in dicts}
        assert "PRIMARY_EFFICACY" in ids
        assert "DOMAIN_GENERALIZATION" in ids


# ---------------------------------------------------------------------------
# Test: JSON response parsing
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_clean_json_array(self):
        raw = json.dumps(valid_llm_response())
        result = _parse_llm_response(raw)
        assert len(result) == 8
        assert result[0]["hypothesis_id"] == "PRIMARY_EFFICACY"

    def test_json_with_markdown_fences(self):
        raw = "```json\n" + json.dumps(valid_llm_response()) + "\n```"
        result = _parse_llm_response(raw)
        assert len(result) == 8

    def test_json_with_surrounding_text(self):
        raw = "Here is the analysis:\n" + json.dumps(valid_llm_response()) + "\nEnd."
        result = _parse_llm_response(raw)
        assert len(result) == 8

    def test_no_json_raises_value_error(self):
        with pytest.raises(ValueError, match="No JSON array"):
            _parse_llm_response("This is just commentary with no JSON.")

    def test_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError, match="Failed to parse"):
            _parse_llm_response("[{invalid json}]")

    def test_non_array_raises_value_error(self):
        with pytest.raises(ValueError, match="No JSON array"):
            _parse_llm_response('{"key": "value"}')

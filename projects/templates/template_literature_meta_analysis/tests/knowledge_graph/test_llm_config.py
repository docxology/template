"""Tests for knowledge_graph.llm_extraction — LLMConfig defaults."""

from __future__ import annotations


from knowledge_graph.llm_extraction import (
    LLMConfig,
)
from tests.knowledge_graph.llm_extraction_fixtures import (
    make_paper,
    valid_llm_response,
)

_make_paper = make_paper
_valid_llm_response = valid_llm_response


class TestLLMConfig:
    def test_defaults(self):
        config = LLMConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.model == "gemma3:4b"
        assert config.temperature == 0.1
        assert config.max_retries == 3
        assert config.nanopub_path is None
        assert config.checkpoint_interval == 50
        assert config.max_papers is None

    def test_custom_values(self):
        config = LLMConfig(model="llama3:8b", temperature=0.5)
        assert config.model == "llama3:8b"
        assert config.temperature == 0.5

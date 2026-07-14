"""Tests for reproducibility.prompts — system prompt and build_prompt."""

from __future__ import annotations

from reproducibility.prompts import _SYSTEM_PROMPT, build_prompt


class TestSystemPrompt:
    def test_requests_json_array_no_markdown_fences(self) -> None:
        assert "JSON array" in _SYSTEM_PROMPT
        assert "no markdown fences" in _SYSTEM_PROMPT

    def test_documents_all_four_node_types(self) -> None:
        for node_type in ("source", "method", "experiment", "sink"):
            assert f'"{node_type}"' in _SYSTEM_PROMPT

    def test_documents_required_schema_keys(self) -> None:
        for key in (
            "node_id",
            "node_name",
            "node_type",
            "source_quote",
            "description",
            "reproducibility_rating",
            "rationale",
            "depends_on",
        ):
            assert f'"{key}"' in _SYSTEM_PROMPT

    def test_source_quote_is_mandatory_and_verbatim(self) -> None:
        assert "verbatim" in _SYSTEM_PROMPT

    def test_documents_rating_scale_one_to_four(self) -> None:
        assert "1 = missing info" in _SYSTEM_PROMPT
        assert "2 = partial specification" in _SYSTEM_PROMPT
        assert "3 = mostly specified" in _SYSTEM_PROMPT
        assert "4 = sufficient detail for independent reconstruction" in _SYSTEM_PROMPT

    def test_documents_depends_on_semantics(self) -> None:
        assert "depends_on" in _SYSTEM_PROMPT
        assert "this node's" in _SYSTEM_PROMPT


class TestBuildPrompt:
    def test_prompt_contains_title_and_fulltext(self) -> None:
        prompt = build_prompt("Active Inference and Free Energy", "We used dataset X and method Y.")
        assert "Active Inference and Free Energy" in prompt
        assert "We used dataset X and method Y." in prompt

    def test_prompt_requests_json_array(self) -> None:
        prompt = build_prompt("Some Title", "Some full text.")
        assert "JSON array" in prompt

    def test_prompt_with_long_fulltext(self) -> None:
        prompt = build_prompt("Title", "x" * 10000)
        assert len(prompt) > 10000

    def test_prompt_with_empty_fulltext(self) -> None:
        prompt = build_prompt("Title Only", "")
        assert "Title Only" in prompt
        assert "## Full text" in prompt

    def test_prompt_returns_str(self) -> None:
        prompt = build_prompt("T", "F")
        assert isinstance(prompt, str)

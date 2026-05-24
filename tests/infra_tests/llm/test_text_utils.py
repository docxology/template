"""Tests for infrastructure.llm.core._text_utils — coverage."""

from infrastructure.llm.core._text_utils import strip_thinking_tags


class TestStripThinkingTags:
    def test_no_tags(self):
        assert strip_thinking_tags("Hello world") == "Hello world"

    def test_empty_string(self):
        assert strip_thinking_tags("") == ""

    def test_basic_thinking_tags(self):
        text = "<think>reasoning here</think>The answer is 42."
        assert strip_thinking_tags(text) == "The answer is 42."

    def test_case_insensitive(self):
        text = "<THINK>caps reasoning</THINK>Result"
        assert strip_thinking_tags(text) == "Result"

    def test_multiline_thinking(self):
        text = "<think>\nLine 1\nLine 2\n</think>\nActual content"
        result = strip_thinking_tags(text)
        assert "Actual content" in result
        assert "<think>" not in result

    def test_only_thinking_tags(self):
        text = "<think>All thinking, no response</think>"
        assert strip_thinking_tags(text) == ""

    def test_malformed_closer_only(self):
        text = "Some text</think> more text"
        result = strip_thinking_tags(text)
        assert "Some text" in result
        assert "</think>" not in result
        assert "more text" in result

    def test_whitespace_cleanup(self):
        text = "  <think>thought</think>  result  "
        result = strip_thinking_tags(text)
        assert result == "result"

    def test_think_with_attributes(self):
        text = "<think lang='en'>thought</think>Answer"
        result = strip_thinking_tags(text)
        assert result == "Answer"

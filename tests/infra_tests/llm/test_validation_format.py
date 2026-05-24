"""Tests for infrastructure/llm/validation/format.py.

Covers: has_on_topic_signals, detect_conversational_phrases,
check_format_compliance, is_off_topic.

No mocks used -- all tests use real data and regex.
"""

from __future__ import annotations

from infrastructure.llm.validation.format import (
    has_on_topic_signals,
    detect_conversational_phrases,
    check_format_compliance,
    is_off_topic,
)


class TestHasOnTopicSignals:
    """Test has_on_topic_signals."""

    def test_manuscript_review_signals(self):
        text = "## Overview\n\nThe manuscript presents a novel approach.\n## Methodology\nGood methods."
        assert has_on_topic_signals(text) is True

    def test_no_signals(self):
        text = "Hello, how are you today? I am fine."
        assert has_on_topic_signals(text) is False

    def test_single_signal_not_enough(self):
        text = "The paper discusses something."
        assert has_on_topic_signals(text) is False

    def test_multiple_signals(self):
        text = "The manuscript is well-written. The authors demonstrate strong methodology."
        assert has_on_topic_signals(text) is True


class TestDetectConversationalPhrases:
    """Test detect_conversational_phrases."""

    def test_no_phrases(self):
        text = "## Overview\n\nThe manuscript presents rigorous methodology."
        phrases = detect_conversational_phrases(text)
        assert phrases == []

    def test_let_me_know(self):
        text = "Good paper. Let me know if you need more details."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) > 0

    def test_happy_to_help(self):
        text = "I'd be happy to provide further analysis."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) > 0

    def test_multiple_phrases(self):
        text = "I'll provide you a review. Let me know if you need changes."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 2


class TestCheckFormatCompliance:
    """Test check_format_compliance."""

    def test_compliant_response(self):
        response = "## Overview\n\nThe manuscript presents novel findings in climate science."
        is_compliant, issues, details = check_format_compliance(response)
        assert is_compliant is True
        assert issues == []

    def test_conversational_response(self):
        response = "I'd be happy to help review this. Let me know your thoughts."
        is_compliant, issues, details = check_format_compliance(response)
        assert is_compliant is False
        assert len(issues) > 0
        assert "conversational_phrases" in details

    def test_details_structure(self):
        response = "Professional review text."
        _, _, details = check_format_compliance(response)
        assert "conversational_phrases" in details


class TestIsOffTopic:
    """Test is_off_topic."""

    def test_on_topic_review(self):
        text = "## Overview\n\nThe manuscript presents a novel approach to data analysis.\n## Methodology\nStrong methods."
        assert is_off_topic(text) is False

    def test_email_format(self):
        text = "Dear Dr. Smith,\n\nThank you for your submission."
        assert is_off_topic(text) is True

    def test_ai_refusal(self):
        text = "I can't help with this request because I don't have access."
        assert is_off_topic(text) is True

    def test_ai_self_identification(self):
        text = "As an AI assistant, I'll review this paper."
        assert is_off_topic(text) is True

    def test_url_in_text(self):
        text = "Visit https://example.com for more information on this topic."
        assert is_off_topic(text) is True

    def test_on_topic_overrides_off_topic(self):
        # Has both on-topic signals and an off-topic pattern
        text = (
            "## Overview\n\nThe manuscript presents strong methodology.\n"
            "## Strengths\n\nThe research design is robust."
        )
        assert is_off_topic(text) is False

    def test_casual_greeting(self):
        text = "Hi there, let me review this paper for you."
        assert is_off_topic(text) is True

    def test_book_language(self):
        text = "This book is divided into several chapters covering the topic."
        assert is_off_topic(text) is True

    def test_code_focused(self):
        text = "```python\nimport pandas as pd\nimport numpy as np\n```"
        assert is_off_topic(text) is True

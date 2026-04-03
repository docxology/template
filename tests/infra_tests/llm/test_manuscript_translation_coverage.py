"""Tests for infrastructure/llm/templates/manuscript_translation.py.

Covers: ManuscriptTranslationAbstract.render, TRANSLATION_LANGUAGES.

No mocks used -- all tests use real template rendering with string data.
"""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.manuscript_translation import (
    ManuscriptTranslationAbstract,
    TRANSLATION_LANGUAGES,
)


class TestTranslationLanguages:
    """Test TRANSLATION_LANGUAGES constant."""

    def test_has_expected_languages(self):
        assert "zh" in TRANSLATION_LANGUAGES
        assert "hi" in TRANSLATION_LANGUAGES
        assert "ru" in TRANSLATION_LANGUAGES

    def test_values_are_strings(self):
        for code, name in TRANSLATION_LANGUAGES.items():
            assert isinstance(code, str)
            assert isinstance(name, str)


class TestManuscriptTranslationAbstract:
    """Test ManuscriptTranslationAbstract template."""

    def test_basic_render(self):
        template = ManuscriptTranslationAbstract()
        result = template.render(
            text="This paper presents findings in quantum computing.",
            target_language="Chinese (Simplified)",
        )
        assert "quantum computing" in result.lower()
        assert "Chinese" in result

    def test_render_with_max_tokens(self):
        template = ManuscriptTranslationAbstract()
        result = template.render(
            text="Abstract content.", target_language="Hindi", max_tokens=1500
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_no_text_raises(self):
        template = ManuscriptTranslationAbstract()
        with pytest.raises(LLMTemplateError):
            template.render(text=None, target_language="Russian")

    def test_render_no_target_language_raises(self):
        template = ManuscriptTranslationAbstract()
        with pytest.raises((LLMTemplateError, KeyError)):
            template.render(text="Content.", target_language=None)

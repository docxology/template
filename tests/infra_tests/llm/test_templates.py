import pytest

from infrastructure.llm.templates import (
    REVIEW_MIN_WORDS,
    TRANSLATION_LANGUAGES,
    LLMTemplateError,
    ManuscriptTranslationAbstract,
    SummarizeAbstract,
    get_template,
)


class TestGetTemplate:
    """Test template retrieval."""

    def test_get_template(self):
        tmpl = get_template("summarize_abstract")
        assert isinstance(tmpl, SummarizeAbstract)

    def test_get_template_invalid(self):
        with pytest.raises(LLMTemplateError):
            get_template("nonexistent")

    def test_get_translation_template(self):
        """Test retrieving translation template from registry."""
        tmpl = get_template("manuscript_translation_abstract")
        assert isinstance(tmpl, ManuscriptTranslationAbstract)


class TestSummarizeAbstract:
    """Test SummarizeAbstract template."""

    def test_render_success(self):
        tmpl = SummarizeAbstract()
        result = tmpl.render(text="Sample abstract")
        assert "Sample abstract" in result
        assert "summarize" in result

    def test_render_missing_var(self):
        tmpl = SummarizeAbstract()
        with pytest.raises(LLMTemplateError):
            tmpl.render()  # Missing 'text'


class TestManuscriptTranslationAbstract:
    """Test ManuscriptTranslationAbstract template."""

    def test_render_with_language(self):
        """Test template renders correctly with target language."""
        tmpl = ManuscriptTranslationAbstract()
        result = tmpl.render(text="Sample manuscript text", target_language="Chinese (Simplified)")

        assert "Sample manuscript text" in result
        assert "Chinese (Simplified)" in result
        assert "MANUSCRIPT BEGIN" in result
        assert "English Abstract" in result
        assert "Translation" in result

    def test_render_with_different_languages(self):
        """Test template works with all supported languages."""
        tmpl = ManuscriptTranslationAbstract()

        for lang_code, lang_name in TRANSLATION_LANGUAGES.items():
            result = tmpl.render(text="Test content", target_language=lang_name)
            assert lang_name in result
            assert "Test content" in result

    def test_render_missing_text(self):
        """Test template requires text variable."""
        tmpl = ManuscriptTranslationAbstract()
        with pytest.raises(LLMTemplateError):
            tmpl.render(target_language="Hindi")  # Missing 'text'

    def test_render_missing_language(self):
        """Test template requires target_language variable."""
        tmpl = ManuscriptTranslationAbstract()
        with pytest.raises(LLMTemplateError):
            tmpl.render(text="Sample text")  # Missing 'target_language'

    def test_template_structure(self):
        """Test template contains required structure elements."""
        tmpl = ManuscriptTranslationAbstract()
        result = tmpl.render(text="Content", target_language="Russian")

        # Check required instruction elements
        assert "MANUSCRIPT BEGIN" in result
        assert "MANUSCRIPT END" in result
        assert "TASK:" in result
        assert "REQUIREMENTS:" in result
        assert "200-400 word" in result
        assert "native script" in result


class TestTranslationLanguages:
    """Test TRANSLATION_LANGUAGES constant."""

    def test_contains_required_languages(self):
        """Test all required language codes are present."""
        assert "zh" in TRANSLATION_LANGUAGES
        assert "hi" in TRANSLATION_LANGUAGES
        assert "ru" in TRANSLATION_LANGUAGES

    def test_language_names(self):
        """Test language names are human-readable."""
        assert TRANSLATION_LANGUAGES["zh"] == "Chinese (Simplified)"
        assert TRANSLATION_LANGUAGES["hi"] == "Hindi"
        assert TRANSLATION_LANGUAGES["ru"] == "Russian"

    def test_all_languages_have_names(self):
        """Test all language codes map to non-empty names."""
        for code, name in TRANSLATION_LANGUAGES.items():
            assert isinstance(code, str)
            assert len(code) == 2  # ISO language codes
            assert isinstance(name, str)
            assert len(name) > 0


class TestReviewMinWords:
    """Test REVIEW_MIN_WORDS constant."""

    def test_translation_threshold_exists(self):
        """Test translation has a minimum word threshold."""
        assert "translation" in REVIEW_MIN_WORDS
        assert REVIEW_MIN_WORDS["translation"] > 0

    def test_translation_threshold_reasonable(self):
        """Test translation threshold is reasonable for abstract + translation."""
        # Should be enough for ~200 English + ~200 translation words
        assert REVIEW_MIN_WORDS["translation"] >= 300
        assert REVIEW_MIN_WORDS["translation"] <= 600


# Preserve original test functions for backward compatibility
def test_get_template():
    tmpl = get_template("summarize_abstract")
    assert isinstance(tmpl, SummarizeAbstract)


def test_get_template_invalid():
    with pytest.raises(LLMTemplateError):
        get_template("nonexistent")


def test_render_success():
    tmpl = SummarizeAbstract()
    result = tmpl.render(text="Sample abstract")
    assert "Sample abstract" in result
    assert "summarize" in result


def test_render_missing_var():
    tmpl = SummarizeAbstract()
    with pytest.raises(LLMTemplateError):
        tmpl.render()  # Missing 'text'


class TestAllRegisteredTemplates:
    """Parametrised tests that every entry in TEMPLATES works end-to-end."""

    _ALL_KEYS = [
        "summarize_abstract",
        "literature_review",
        "code_doc",
        "data_interpret",
        "paper_summarization",
        "manuscript_executive_summary",
        "manuscript_quality_review",
        "manuscript_methodology_review",
        "manuscript_improvement_suggestions",
        "manuscript_translation_abstract",
        "literature_review_synthesis",
        "science_communication_narrative",
        "comparative_analysis",
        "research_gap_identification",
        "citation_network_analysis",
    ]

    @pytest.mark.parametrize("key", _ALL_KEYS)
    def test_template_instantiates(self, key: str) -> None:
        from infrastructure.llm.templates import get_template, ResearchTemplate
        t = get_template(key)
        assert isinstance(t, ResearchTemplate)

    @pytest.mark.parametrize("key", _ALL_KEYS)
    def test_template_has_non_empty_str(self, key: str) -> None:
        from infrastructure.llm.templates import TEMPLATES
        t = TEMPLATES[key]()
        assert t.template_str, f"{key} has an empty template_str"

    def test_all_keys_present_in_registry(self) -> None:
        from infrastructure.llm.templates import TEMPLATES
        for key in self._ALL_KEYS:
            assert key in TEMPLATES, f"Key '{key}' missing from TEMPLATES registry"

    def test_registry_contains_no_extra_unknown_classes(self) -> None:
        from infrastructure.llm.templates import TEMPLATES, ResearchTemplate
        for name, cls in TEMPLATES.items():
            assert issubclass(cls, ResearchTemplate), f"{name} is not a ResearchTemplate subclass"


class TestResearchTemplateBase:
    """Test the ResearchTemplate base class directly."""

    def test_render_happy_path(self):
        from infrastructure.llm.templates.base import ResearchTemplate

        class _SimpleTemplate(ResearchTemplate):
            template_str = "Hello $name, your score is $score."

        result = _SimpleTemplate().render(name="Alice", score=42)
        assert result == "Hello Alice, your score is 42."

    def test_render_missing_variable_raises_llm_template_error(self):
        from infrastructure.llm.templates.base import ResearchTemplate
        from infrastructure.core.exceptions import LLMTemplateError

        class _TwoVarTemplate(ResearchTemplate):
            template_str = "A=$a B=$b"

        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            _TwoVarTemplate().render(a="only_one")

    def test_empty_template_renders_empty_string(self):
        from infrastructure.llm.templates.base import ResearchTemplate

        class _EmptyTemplate(ResearchTemplate):
            template_str = ""

        assert _EmptyTemplate().render() == ""

import pytest
from infrastructure.llm.templates import get_template, LLMTemplateError, SummarizeAbstract

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
        tmpl.render() # Missing 'text'


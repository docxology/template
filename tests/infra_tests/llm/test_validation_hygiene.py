from infrastructure.llm.validation import (
    clean_agent_output,
    citation_density,
    normalize_output_whitespace,
    strip_placeholder_tokens,
    validate_citation_density,
    validate_formatting,
)


def test_clean_agent_output_strips_placeholders_and_repetition() -> None:
    text = (
        "TODO: insert placeholder\n\n"
        "## Intro\n"
        "Introduction text.\n\n"
        "## Intro\n"
        "Introduction text.\n\n"
        "## Intro\n"
        "Introduction text.\n"
    )

    cleaned = clean_agent_output(text)

    assert "TODO" not in cleaned
    assert cleaned.count("## Intro") <= 2


def test_validate_citation_density_thresholds() -> None:
    text = "Alpha beta gamma delta (Smith 2020) [1] @key"
    ok, details = validate_citation_density(text, min_per_1000_words=100.0)

    assert ok is True
    assert details["citations_found"] == 3
    assert citation_density(text) > 0

    too_low, low_details = validate_citation_density("Alpha beta gamma delta.", min_per_1000_words=1.0)
    assert too_low is False
    assert low_details["citations_found"] == 0


def test_validate_citation_density_upper_bound() -> None:
    text = ("(Smith 2020) " * 40).strip()
    ok, details = validate_citation_density(text, max_per_1000_words=100.0)

    assert ok is False
    assert details["citation_density_per_1000_words"] > 100.0


def test_validate_formatting_flags_placeholders() -> None:
    assert validate_formatting("TODO: insert placeholder") is False


def test_strip_placeholder_tokens_normalizes_spacing() -> None:
    text = "Alpha  {{placeholder}}  beta\n\n"
    stripped = strip_placeholder_tokens(text)
    normalized = normalize_output_whitespace(stripped)

    assert "{{" not in stripped
    assert "Alpha" in normalized

"""Tests for font registration and the stylesheet."""

from __future__ import annotations

import os

from newspaper.typography import (
    Fonts,
    _try_register,
    build_stylesheet,
    register_fonts,
)


def test_register_fonts_always_returns_usable_names() -> None:
    fonts = register_fonts()
    assert isinstance(fonts, Fonts)
    for role in (fonts.display, fonts.display_bold, fonts.body, fonts.sans, fonts.sans_bold):
        assert isinstance(role, str) and role


def test_try_register_returns_none_for_missing_font() -> None:
    """No mocks: a real nonexistent path yields None, which triggers the base-14
    fallback in register_fonts. This is the cross-platform safety net (a Linux CI
    box without macOS system fonts hits exactly this path)."""
    assert _try_register([("NP-Nope", "/nonexistent/does-not-exist.ttf", 0)]) is None


def test_try_register_returns_none_when_ttfont_raises(tmp_path) -> None:
    """If the font file exists but TTFont loading raises, _try_register falls back
    to None rather than propagating the exception — covering the except branch."""
    # Create a real file (so os.path.exists passes) with garbage content.
    bad_font = tmp_path / "bad.ttf"
    bad_font.write_bytes(b"NOT A FONT FILE")
    result = _try_register([("NP-BadFont", str(bad_font), 0)])
    assert result is None


def test_stylesheet_builds_from_base14_fallback_fonts() -> None:
    """The base-14 fallback Fonts must yield a complete, usable stylesheet — proving
    rendering does not depend on any machine-specific font being present."""
    base14 = Fonts(
        display="Times-Roman",
        display_bold="Times-Bold",
        body="Times-Roman",
        body_bold="Times-Bold",
        body_italic="Times-Italic",
        body_bolditalic="Times-BoldItalic",
        sans="Helvetica",
        sans_bold="Helvetica-Bold",
    )
    ss = build_stylesheet(base14)
    assert ss["Body"] is not None and ss["Nameplate"] is not None


def test_sans_embeds_when_arial_present() -> None:
    """Regression guard: the sans role must use an embeddable TTF (Arial),
    not base-14 Helvetica, wherever Arial is available — base-14 fonts are not
    embedded and fail to rasterise under some PDF renderers."""
    if os.path.exists("/System/Library/Fonts/Supplemental/Arial.ttf"):
        assert register_fonts().sans == "NP-Sans"


def test_stylesheet_has_required_styles() -> None:
    ss = build_stylesheet(register_fonts())
    required = [
        "Nameplate",
        "Folio",
        "Kicker",
        "HeadlineLead",
        "HeadlinePrimary",
        "HeadlineSecondary",
        "Deck",
        "Byline",
        "Body",
        "BodyFirst",
        "PullQuote",
        "BoxTitle",
        "Caption",
        "Classified",
        "ClassifiedCat",
        "Tabular",
    ]
    for name in required:
        assert name in ss.byName, f"missing style {name}"


def test_headlines_do_not_split_words() -> None:
    ss = build_stylesheet(register_fonts())
    for name in ("HeadlineLead", "HeadlinePrimary", "HeadlineSecondary", "HeadlineMinor"):
        assert ss[name].splitLongWords == 0


def test_stylesheet_named_colors_are_darker_than_muted() -> None:
    """INK should be near-black and darker than MUTED — a sanity check on the
    newsprint palette constants."""
    from newspaper.typography import INK, MUTED

    ink_gray = (INK.red + INK.green + INK.blue) / 3
    muted_gray = (MUTED.red + MUTED.green + MUTED.blue) / 3
    assert ink_gray < muted_gray, "INK must be darker than MUTED"


def test_stylesheet_body_first_inherits_body() -> None:
    """BodyFirst must inherit from Body (used for the first paragraph in a story
    to get zero first-line indent) — this is the justified paragraph invariant."""
    ss = build_stylesheet(register_fonts())
    assert ss["BodyFirst"].parent == ss["Body"]


def test_stylesheet_all_named_styles_have_nonempty_font() -> None:
    """Every style in the stylesheet must have a non-empty fontName.

    This catches accidental Fonts() construction with empty-string roles.
    """
    ss = build_stylesheet(register_fonts())
    for name, style in ss.byName.items():
        assert getattr(style, "fontName", None), f"style {name!r} has no fontName"

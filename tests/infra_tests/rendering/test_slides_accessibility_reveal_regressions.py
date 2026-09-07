"""Regression tests for accessible Reveal navigation and rendered semantics."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import AccessibleSlidePolicy
from infrastructure.rendering._slides_accessibility_reveal import (
    _accessible_reveal_css,
    _add_interactive_keyboard_guard,
    _normalize_reveal_viewport,
    _rendered_title_only_headings,
    accessible_reveal_output_issues,
    enhance_accessible_reveal,
)
from infrastructure.rendering._slides_accessibility_reveal_controls import (
    disable_automatic_reveal_scroll,
    reveal_scroll_activation_issues,
    reveal_viewport_issues,
)


def _standalone_reveal(body: str) -> str:
    return (
        "<!doctype html><html><head>"
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, '
        'maximum-scale=1.0, user-scalable=no, minimal-ui">'
        "<title>Temporary deck</title>"
        '<link rel="stylesheet" href="https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css">'
        f'</head><body><div class="reveal"><div class="slides">{body}</div></div>'
        "<script>Reveal.initialize({keyboard: true});</script></body></html>"
    )


def test_reveal_viewport_normalization_restores_user_zoom() -> None:
    source = _standalone_reveal("").replace(
        "</head>",
        '<META NAME = viewport CONTENT="width=device-width, minimum-scale = 1">\n</HEAD>',
    )

    normalized = _normalize_reveal_viewport(source)

    assert normalized.count('name="viewport"') == 1
    assert 'content="width=device-width, initial-scale=1.0"' in normalized
    assert "user-scalable=no" not in normalized
    assert "maximum-scale=1" not in normalized
    assert "minimum-scale" not in normalized
    assert reveal_viewport_issues(normalized) == ()
    assert _normalize_reveal_viewport(normalized) == normalized


@pytest.mark.parametrize(
    "viewport",
    (
        '<meta name="viewport" content="user-scalable = NO">',
        "<meta NAME='viewport' content='user-scalable=0'>",
        '<meta name=viewport content="maximum-scale = 4">',
        '<meta name="viewport" content="minimum-scale=0.5">',
    ),
)
def test_reveal_viewport_validation_rejects_zoom_constraints(viewport: str) -> None:
    assert reveal_viewport_issues(f"<html><head>{viewport}</head></html>")


def test_reveal_viewport_validation_ignores_unrelated_data_attributes() -> None:
    viewport = (
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" '
        'data-obsolete-policy="user-scalable=no, maximum-scale=1">'
    )

    assert reveal_viewport_issues(viewport) == ()


def test_reveal_viewport_parsing_does_not_promote_attribute_text_to_attributes() -> None:
    source = (
        "<html><head>"
        '<meta data-note=\'name="viewport"\' content="source-marker">'
        '<meta name="viewport" data-note=\'content="user-scalable=no"\' '
        'content="width=device-width, initial-scale=1.0">'
        "</head><body></body></html>"
    )

    normalized = _normalize_reveal_viewport(source)

    assert '<meta data-note=\'name="viewport"\' content="source-marker">' in normalized
    assert normalized.count('<meta name="viewport"') == 1
    assert "source-marker" in normalized
    assert reveal_viewport_issues(normalized) == ()


def test_reveal_viewport_validation_reads_only_the_real_content_attribute() -> None:
    viewport = (
        '<meta name="viewport" data-note=\'content="user-scalable=no, maximum-scale=1"\' '
        'content="width=device-width, initial-scale=1.0">'
    )

    assert reveal_viewport_issues(viewport) == ()


def test_reveal_viewport_validation_rejects_missing_and_duplicate_metadata() -> None:
    assert reveal_viewport_issues("<html><head></head></html>") == ("Reveal viewport metadata is missing",)
    duplicate = (
        "<html><head>"
        '<meta name="viewport" content="width=device-width">'
        "<META NAME='VIEWPORT' CONTENT='initial-scale=1'>"
        "</head></html>"
    )
    assert "appears 2 times" in reveal_viewport_issues(duplicate)[0]
    assert reveal_viewport_issues('<meta name="viewport" content="">') == (
        "Reveal viewport content is missing or empty",
    )
    assert reveal_viewport_issues('<meta data-name="viewport" content="width=device-width">') == (
        "Reveal viewport metadata is missing",
    )
    assert reveal_viewport_issues('<meta name="viewport" content="width=1280">') == (
        "Reveal viewport content is not the canonical responsive declaration",
    )


def test_reveal_viewport_normalization_does_not_consume_data_name_attribute() -> None:
    source = (
        '<html><head><meta data-name="viewport" content="source-marker">'
        '<meta name="viewport" content=""></head><body></body></html>'
    )

    normalized = _normalize_reveal_viewport(source)

    assert '<meta data-name="viewport" content="source-marker">' in normalized
    assert normalized.count('<meta name="viewport"') == 1
    assert reveal_viewport_issues(normalized) == ()


def test_reveal_viewport_normalization_removes_the_whole_indented_source_line() -> None:
    source = (
        "<html><head>\n"
        '  <meta name="viewport" content="width=device-width">\n'
        "  <title>Deck</title>\n"
        "</head><body></body></html>"
    )

    normalized = _normalize_reveal_viewport(source)

    assert "\n  \n" not in normalized
    assert "\n  <title>Deck</title>" in normalized
    assert reveal_viewport_issues(normalized) == ()


def test_reveal_keyboard_guard_is_scoped_to_interactive_controls() -> None:
    guarded = _add_interactive_keyboard_guard(_standalone_reveal(""))

    assert guarded.count("data-template-interactive-keyboard-guard") == 1
    assert '".reveal summary, .reveal button' in guarded
    assert ".reveal input[type='checkbox']" in guarded
    assert 'event.key !== " "' in guarded
    assert "event.stopImmediatePropagation()" in guarded
    assert "control.click()" in guarded
    assert ".reveal a" not in guarded
    assert _add_interactive_keyboard_guard(guarded) == guarded


def test_reveal_automatic_scroll_scaling_is_disabled_deterministically() -> None:
    source = _standalone_reveal("")

    disabled = disable_automatic_reveal_scroll(source)

    assert disabled.count("scrollActivationWidth: null") == 1
    assert reveal_scroll_activation_issues(disabled) == ()
    assert disable_automatic_reveal_scroll(disabled) == disabled


def test_reveal_numeric_scroll_activation_is_normalized_and_duplicates_fail() -> None:
    numeric = _standalone_reveal("").replace(
        "Reveal.initialize({keyboard: true",
        "Reveal.initialize({scrollActivationWidth: 435, keyboard: true",
    )

    disabled = disable_automatic_reveal_scroll(numeric)

    assert "scrollActivationWidth: 435" not in disabled
    assert disabled.count("scrollActivationWidth: null") == 1
    assert reveal_scroll_activation_issues(disabled) == ()
    duplicate = disabled.replace(
        "keyboard: true",
        "scrollActivationWidth: null, keyboard: true",
    )
    assert reveal_scroll_activation_issues(duplicate) == ("Reveal scrollActivationWidth appears 2 times",)


def test_reveal_scroll_activation_ignores_settings_outside_the_initializer() -> None:
    source = _standalone_reveal("").replace(
        "<script>Reveal.initialize",
        "<!-- scrollActivationWidth: null --><script>Reveal.initialize",
    )

    disabled = disable_automatic_reveal_scroll(source)

    assert disabled.count("scrollActivationWidth: null") == 2
    assert reveal_scroll_activation_issues(disabled) == ()


def test_reveal_narrow_focus_controls_use_nonoverlapping_vertical_lanes() -> None:
    css = _accessible_reveal_css(AccessibleSlidePolicy())

    assert "@media (max-width: 32rem)" in css
    assert "html.reveal-full-page" in css
    assert "body.reveal-viewport" in css
    assert "overflow-y: auto" in css
    assert "main#main-content" in css
    assert "margin-block-start: 7.5rem" in css
    assert "main#main-content .reveal .slides" in css
    assert ".slides > section.present:not(.stack)" in css
    assert "transform: none !important" in css
    assert "zoom: 1 !important" in css
    assert "touch-action: pan-y pinch-zoom" in css
    assert "min-block-size: var(--template-figure-min-allocation-height)" in css
    assert "max-block-size: var(--template-figure-safe-max-height)" in css
    assert ".slide-reader-nav" in css
    assert "inset-block-start: max(4.25rem" in css
    assert "(max-height: 20rem)" in css
    assert "scroll-padding-block-start: 3.25rem" in css
    assert "scroll-padding-block-start: 7.25rem" in css
    assert "position: fixed" in css
    assert "body:has(.skip-link:focus) .slide-reader-nav" in css
    assert "margin-block-start: 3.25rem" in css
    assert "margin-block-start: 7.25rem" in css
    assert "scroll-margin-block-start: 3.25rem" in css
    assert "scroll-margin-block-start: 7.5rem" in css
    assert "min-block-size: calc(100dvh - 3.25rem)" in css
    assert "min-block-size: calc(100dvh - 7.25rem)" in css


def test_rendered_title_only_detection_ignores_dividers_and_script_text() -> None:
    content = (
        '<section class="slide prose-slide" aria-roledescription="slide">'
        "<h2>Missing theorem</h2><script>not visible</script></section>"
        '<section class="slide section-divider" aria-roledescription="slide">'
        "<h2>Intentional divider</h2></section>"
        '<section class="slide figure-led" aria-roledescription="slide">'
        '<h2>Visible figure</h2><figure><img src="figure.png" alt="Evidence"></figure></section>'
    )

    assert _rendered_title_only_headings(content) == ("Missing theorem",)


def test_rendered_title_only_detection_ignores_nonvisual_descendants() -> None:
    content = (
        '<section aria-roledescription="slide"><h2>Notes only</h2>'
        '<aside class="notes">Presenter note</aside></section>'
        '<section aria-roledescription="slide"><h2>Hidden only</h2>'
        "<div hidden><p>Not rendered</p></div></section>"
        '<section aria-roledescription="slide"><h2>Visually hidden only</h2>'
        '<p class="visually-hidden">Screen-reader title</p></section>'
        '<section aria-roledescription="slide"><h2>Empty figure only</h2>'
        "<figure></figure></section>"
        '<section aria-roledescription="slide"><h2>Visible figure</h2>'
        '<figure><img src="figure.png" alt="Evidence"></figure></section>'
    )

    assert _rendered_title_only_headings(content) == (
        "Notes only",
        "Hidden only",
        "Visually hidden only",
        "Empty figure only",
    )


def test_reveal_enhancement_normalizes_zoom_and_adds_keyboard_guard(tmp_path: Path) -> None:
    reveal = tmp_path / "deck_slides.html"
    reveal.write_text(
        _standalone_reveal('<section class="slide prose-slide"><h2>Evidence</h2><p>Visible body.</p></section>'),
        encoding="utf-8",
    )

    enhance_accessible_reveal(
        reveal,
        policy=AccessibleSlidePolicy(reader_href="../web/index.html"),
        registry_path=None,
    )
    rendered = reveal.read_text(encoding="utf-8")

    assert "user-scalable=no" not in rendered
    assert "maximum-scale=1" not in rendered
    assert "data-template-interactive-keyboard-guard" in rendered
    assert "scrollActivationWidth: null" in rendered
    assert accessible_reveal_output_issues(reveal) == ()


def test_reveal_enhancement_rejects_rendered_title_only_nondivider(tmp_path: Path) -> None:
    reveal = tmp_path / "deck_slides.html"
    reveal.write_text(
        _standalone_reveal('<section class="slide prose-slide"><h2>Dropped definition</h2></section>'),
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match=r"\[slides\.structure\.title-only-rendered\]"):
        enhance_accessible_reveal(
            reveal,
            policy=AccessibleSlidePolicy(reader_href="../web/index.html"),
            registry_path=None,
        )

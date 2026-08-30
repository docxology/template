"""Reveal.js semantics and accessibility post-processing for slide decks."""

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import AccessibleSlidePolicy
from infrastructure.rendering._web_postprocess import (
    enhance_accessibility,
    normalize_figure_paths,
    write_if_changed,
)


_SLIDE_OPEN_RE = re.compile(
    r"(?P<open><section\b(?P<attrs>[^>]*)>)(?P<spacing>\s*)"
    r"(?P<heading><h(?P<level>[1-6])\b(?P<heading_attrs>[^>]*)>.*?</h(?P=level)>)",
    flags=re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_STANDALONE_HTML_RE = re.compile(r"(?:<!doctype\s+html\b|<html(?:\s|>))", flags=re.IGNORECASE)
_ACCESSIBLE_REVEAL_MARKERS = (
    "data-template-accessible-slides",
    'aria-label="Presentation companion"',
    'aria-label="Presentation slides"',
    'aria-roledescription="slide"',
    "overflow-x: hidden",
)


def _set_html_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(
        rf"(?<!\S){re.escape(name)}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
        flags=re.IGNORECASE,
    )
    if pattern.search(tag):
        return pattern.sub(lambda _match: f'{name}="{escaped}"', tag, count=1)
    return tag[:-1].rstrip() + f' {name}="{escaped}">' if tag.endswith(">") else tag


def _reveal_semantics(content: str) -> str:
    """Name every Reveal slide from its first heading and add slide roles."""

    def replace(match: re.Match[str]) -> str:
        heading_tag = match.group("heading")
        identifier_match = re.search(
            r'(?<!\S)id\s*=\s*["\'](?P<id>[^"\']+)',
            match.group("heading_attrs"),
        )
        if identifier_match is None:
            heading_text = html.unescape(_TAG_RE.sub("", heading_tag)).strip()
            heading_id = "slide-heading-" + hashlib.sha256(heading_text.encode("utf-8")).hexdigest()[:12]
            updated_heading = _set_html_attribute(heading_tag, "id", heading_id)
        else:
            heading_id = identifier_match.group("id")
            updated_heading = heading_tag
        open_tag = _set_html_attribute(match.group("open"), "role", "group")
        open_tag = _set_html_attribute(open_tag, "aria-roledescription", "slide")
        open_tag = _set_html_attribute(open_tag, "aria-labelledby", heading_id)
        return f"{open_tag}{match.group('spacing')}{updated_heading}"

    updated = _SLIDE_OPEN_RE.sub(replace, content)
    unnamed_slide = re.search(
        r"<section\b(?=[^>]*(?<!\S)class\s*=\s*[\"'][^\"']*\bslide\b)[^>]*>"
        r"(?!\s*<h[1-6]\b)",
        updated,
        flags=re.IGNORECASE,
    )
    if unnamed_slide is not None:
        raise RenderingError(
            "[slides.structure.heading] Reveal slide has no semantic heading",
            context={"diagnostic_code": "slides.structure.heading"},
        )
    return updated


def _accessible_reveal_css(policy: AccessibleSlidePolicy) -> str:
    body_px = policy.body_font_pt * (4 / 3)
    title_px = policy.title_font_pt * (4 / 3)
    label_px = policy.figure_label_font_pt * (4 / 3)
    return f"""<style data-template-accessible-slides>
:root {{ --r-background-color: #ffffff; --r-main-color: #111111; --r-link-color: #004b87; }}
html, body {{ max-width: 100%; overflow-x: hidden; }}
.reveal {{ color: #111111; background: #ffffff; font-size: {body_px:.2f}px; }}
.reveal .slides section {{
  max-width: 100%; min-width: 0; overflow-wrap: anywhere;
  text-align: left; line-height: 1.35;
}}
.reveal h1, .reveal h2, .reveal h3 {{ color: #111111; font-size: {title_px:.2f}px; line-height: 1.15; }}
.reveal a {{ color: #004b87; text-decoration: underline; text-decoration-thickness: 0.11em; }}
.reveal a:focus-visible, .reveal button:focus-visible {{ outline: 4px solid #b34d00; outline-offset: 4px; }}
.reveal .table-scroll {{
  max-width: 100%; overflow-x: auto;
  overscroll-behavior-inline: contain; scrollbar-gutter: stable;
}}
.reveal .table-scroll:focus-visible {{ outline: 4px solid #b34d00; outline-offset: 4px; }}
.reveal table {{ max-width: 100%; min-width: 100%; width: max-content; font-size: inherit; border-collapse: collapse; }}
.reveal th, .reveal td {{ border: 2px solid #404040; padding: 0.25em 0.4em; }}
.reveal section.figure-led figure {{
  min-height: {policy.min_figure_area_percent}vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.reveal section.figure-led img {{
  display: block;
  width: 100% !important;
  height: calc({policy.min_figure_area_percent}vh - 5.5rem) !important;
  max-height: calc({policy.min_figure_area_percent}vh - 5.5rem);
  max-width: 100%;
  object-fit: contain;
  margin-inline: auto;
}}
.reveal figcaption, .reveal .slide-reader-link {{ font-size: {label_px:.2f}px; line-height: 1.3; }}
.slide-reader-nav {{
  position: fixed;
  inset-inline-end: 0.75rem;
  inset-block-start: 0.5rem;
  z-index: 30;
  background: #ffffff;
  border: 2px solid #111111;
  padding: 0.3rem 0.55rem;
}}
.skip-link {{
  position: fixed;
  inset-inline-start: 0.5rem;
  inset-block-start: -8rem;
  z-index: 100;
  background: #ffffff;
  color: #111111;
  border: 3px solid #111111;
  padding: 0.5rem;
}}
.skip-link:focus {{ inset-block-start: 0.5rem; }}
.figure-long-description {{
  font-size: {label_px:.2f}px; max-height: 35vh; max-width: 100%;
  overflow: auto; overflow-wrap: anywhere;
}}
.figure-exact-values {{ font-size: {label_px:.2f}px; max-width: 100%; overflow-wrap: anywhere; }}
@media (prefers-reduced-motion: reduce) {{ .reveal .slides section {{ transition: none !important; }} }}
@media (forced-colors: active) {{ .reveal th, .reveal td, .slide-reader-nav {{ border: 2px solid CanvasText; }} }}
</style>"""


def enhance_accessible_reveal(
    html_file: Path,
    *,
    policy: AccessibleSlidePolicy,
    registry_path: Path | None,
    language: str = "en",
) -> None:
    """Apply deterministic semantic, navigation, and visual-accessibility hooks."""

    # Reveal uses ``data-src`` for lazy loading while the shared publication
    # postprocessor intentionally matches ordinary HTML ``src`` attributes.
    # Accessible mode favors predictable native image semantics over lazy
    # loading and normalizes the attribute before applying the shared registry.
    initial = html_file.read_text(encoding="utf-8")
    initial = re.sub(r"(?<!\S)data-src\s*=", "src=", initial, flags=re.IGNORECASE)
    initial = normalize_figure_paths(initial)
    write_if_changed(html_file, initial)
    enhance_accessibility(html_file, language=language, registry_path=registry_path)
    content = html_file.read_text(encoding="utf-8")
    content = _reveal_semantics(content)
    if "data-template-accessible-slides" not in content:
        content = content.replace("</head>", _accessible_reveal_css(policy) + "\n</head>", 1)
    if '<nav class="slide-reader-nav"' not in content:
        reader_href = html.escape(policy.reader_href, quote=True)
        nav = (
            '<nav class="slide-reader-nav" aria-label="Presentation companion">'
            f'<a href="{reader_href}">Open canonical HTML manuscript</a></nav>'
        )
        content = re.sub(r"(<body\b[^>]*>)", rf"\1\n{nav}", content, count=1, flags=re.IGNORECASE)
    content = content.replace(
        '<div class="slides">',
        '<div class="slides" role="region" aria-label="Presentation slides">',
        1,
    )
    if not re.search(r"\bkeyboard\s*:\s*true\b", content):
        raise RenderingError(
            "[slides.accessibility.keyboard] Reveal.js keyboard navigation is not enabled",
            context={"source": str(html_file), "diagnostic_code": "slides.accessibility.keyboard"},
        )
    write_if_changed(html_file, content)


def accessible_reveal_output_issues(html_file: Path) -> tuple[str, ...]:
    """Return structural issues for one accessibility-enhanced Reveal deck."""

    try:
        if not html_file.is_file() or html_file.stat().st_size == 0:
            return ("file is missing or empty",)
        content = html_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return (f"file is not readable UTF-8: {exc}",)

    issues: list[str] = []
    if _STANDALONE_HTML_RE.search(content) is None:
        issues.append("document is not standalone HTML")
    issues.extend(
        f"missing accessible Reveal marker: {marker}" for marker in _ACCESSIBLE_REVEAL_MARKERS if marker not in content
    )
    if re.search(r"\bkeyboard\s*:\s*true\b", content) is None:
        issues.append("Reveal keyboard navigation is not enabled")
    return tuple(issues)

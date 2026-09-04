"""Reveal.js semantics and accessibility post-processing for slide decks."""

from __future__ import annotations

import hashlib
import html
import re
from collections.abc import Mapping
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import AccessibleSlidePolicy
from infrastructure.rendering._slides_accessibility_figures import (
    FIGURE_SAFE_BODY_MAX_HEIGHT_PERCENT_16_9,
    FIGURE_SAFE_BODY_MAX_WIDTH_PERCENT,
    REVEAL_LOGICAL_SLIDE_HEIGHT_PX,
)
from infrastructure.rendering._slides_accessibility_reveal_controls import (
    add_interactive_keyboard_guard as _add_interactive_keyboard_guard,
    disable_automatic_reveal_scroll as _disable_automatic_reveal_scroll,
    normalize_reveal_viewport as _normalize_reveal_viewport,
    rendered_title_only_headings as _rendered_title_only_headings,
    reveal_scroll_activation_issues,
    reveal_viewport_issues,
)
from infrastructure.rendering._slides_reveal_content import (
    activate_hardened_reveal_mathjax,
    promote_display_math_labels,
    resolve_reveal_cross_references,
    reveal_reference_and_math_issues,
)
from infrastructure.rendering._web_postprocess import (
    enhance_accessibility,
    harden_mathjax_script,
    normalize_figure_paths,
    write_if_changed,
)


_SLIDE_OPEN_RE = re.compile(
    r"(?P<open><section\b(?P<attrs>[^>]*)>)(?P<spacing>\s*)"
    r"(?P<heading_open><h(?P<level>[1-6])\b(?P<heading_attrs>[^>]*)>)"
    r"(?P<heading_body>.*?)"
    r"(?P<heading_close></h(?P=level)>)",
    flags=re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_STANDALONE_HTML_RE = re.compile(r"(?:<!doctype\s+html\b|<html(?:\s|>))", flags=re.IGNORECASE)
_READER_NAV_RE = re.compile(
    r"\s*<nav\b(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bslide-reader-nav\b)[^>]*>.*?</nav>\s*",
    flags=re.IGNORECASE | re.DOTALL,
)
_SKIP_LINK_RE = re.compile(
    r"<a\b(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bskip-link\b)"
    r"(?=[^>]*\bhref\s*=\s*(?:\"#main-content\"|'#main-content'))[^>]*>.*?</a>",
    flags=re.IGNORECASE | re.DOTALL,
)
_TITLE_RE = re.compile(r"<title\b[^>]*>.*?</title>", flags=re.IGNORECASE | re.DOTALL)
_MAIN_OPEN_RE = re.compile(r"<main\b[^>]*>", flags=re.IGNORECASE)
_HEADING_ID_RE = re.compile(r'(?<!\S)id\s*=\s*["\'](?P<id>[^"\']+)', flags=re.IGNORECASE)
_ACCESSIBLE_REVEAL_MARKERS = (
    "data-template-accessible-slides",
    'aria-label="Presentation companion"',
    'aria-label="Presentation slides"',
    'aria-roledescription="slide"',
    "dist/theme/white.css",
    "overflow-x: hidden",
    "data-template-interactive-keyboard-guard",
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

    seen_heading_ids: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        heading_open = match.group("heading_open")
        heading_body = match.group("heading_body")
        identifier_match = _HEADING_ID_RE.search(match.group("heading_attrs"))
        heading_text = " ".join(html.unescape(_TAG_RE.sub(" ", heading_body)).split())
        candidate_id = identifier_match.group("id") if identifier_match is not None else ""
        if not candidate_id or candidate_id in seen_heading_ids:
            digest = hashlib.sha256(heading_text.encode("utf-8")).hexdigest()[:12]
            base_id = f"slide-heading-{digest}"
            heading_id = base_id
            suffix = 2
            while heading_id in seen_heading_ids:
                heading_id = f"{base_id}-{suffix}"
                suffix += 1
            updated_heading_open = _set_html_attribute(heading_open, "id", heading_id)
        else:
            heading_id = candidate_id
            updated_heading_open = heading_open
        seen_heading_ids.add(heading_id)
        open_tag = _set_html_attribute(match.group("open"), "role", "group")
        open_tag = _set_html_attribute(open_tag, "aria-roledescription", "slide")
        open_tag = _set_html_attribute(open_tag, "aria-labelledby", heading_id)
        return f"{open_tag}{match.group('spacing')}{updated_heading_open}{heading_body}{match.group('heading_close')}"

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


def _first_slide_heading(content: str) -> str:
    """Return the first visible slide heading as plain, normalized text."""

    match = _SLIDE_OPEN_RE.search(content)
    if match is None:
        raise RenderingError(
            "[slides.structure.heading] Reveal deck has no authored slide heading",
            context={"diagnostic_code": "slides.structure.heading"},
        )
    heading = " ".join(html.unescape(_TAG_RE.sub(" ", match.group("heading_body"))).split())
    if not heading:
        raise RenderingError(
            "[slides.structure.heading] Reveal deck has an empty authored slide heading",
            context={"diagnostic_code": "slides.structure.heading"},
        )
    return heading


def _set_document_title_and_heading(content: str, heading: str) -> str:
    """Bind the browser title and document heading to authored slide text."""

    page_title = f"{heading} — presentation"
    escaped_title = html.escape(page_title)
    if _TITLE_RE.search(content):
        content = _TITLE_RE.sub(lambda _match: f"<title>{escaped_title}</title>", content, count=1)
    else:
        content = content.replace("</head>", f"<title>{escaped_title}</title>\n</head>", 1)

    # Pandoc emits h2 slide headings when the source has no explicit h1. Add a
    # single visually hidden document-level heading in that case so heading
    # navigation still exposes a page title without changing projected text.
    if re.search(r"<h1\b", content, flags=re.IGNORECASE) is None:
        digest = hashlib.sha256(page_title.encode("utf-8")).hexdigest()[:12]
        heading_id = f"presentation-title-{digest}"
        document_heading = f'<h1 id="{heading_id}" class="visually-hidden">{escaped_title}</h1>'

        def add_heading(match: re.Match[str]) -> str:
            main = _set_html_attribute(match.group(0), "aria-labelledby", heading_id)
            return f"{main}\n{document_heading}"

        content, replacements = _MAIN_OPEN_RE.subn(add_heading, content, count=1)
        if replacements != 1:
            raise RenderingError(
                "[slides.structure.main] Reveal deck has no main landmark for its document heading",
                context={"diagnostic_code": "slides.structure.main"},
            )
    return content


def _place_reader_navigation_after_skip_link(content: str, reader_href: str) -> str:
    """Make the skip link the first focusable body control."""

    content = _READER_NAV_RE.sub("\n", content)
    skip_match = _SKIP_LINK_RE.search(content)
    if skip_match is None:
        raise RenderingError(
            "[slides.accessibility.skip-link] Reveal deck has no main-content skip link",
            context={"diagnostic_code": "slides.accessibility.skip-link"},
        )
    nav = (
        '<nav class="slide-reader-nav" aria-label="Presentation companion">'
        f'<a href="{html.escape(reader_href, quote=True)}">Open canonical HTML manuscript</a></nav>'
    )
    return content[: skip_match.end()] + "\n" + nav + content[skip_match.end() :]


def _accessible_reveal_css(policy: AccessibleSlidePolicy) -> str:
    body_px = policy.body_font_pt * (4 / 3)
    title_px = policy.title_font_pt * (4 / 3)
    label_px = policy.figure_label_font_pt * (4 / 3)
    maximum_figure_height_px = REVEAL_LOGICAL_SLIDE_HEIGHT_PX * FIGURE_SAFE_BODY_MAX_HEIGHT_PERCENT_16_9 / 100
    return f"""<style data-template-accessible-slides>
:root {{ --r-background-color: #ffffff; --r-main-color: #111111; --r-link-color: #004b87; }}
html, body {{ max-width: 100%; overflow-x: hidden; }}
main#main-content {{ inline-size: 100%; block-size: 100vh; min-block-size: 100vh; }}
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
  display: flex;
  flex-direction: column;
  justify-content: center;
  /* Reveal scales its 960×700 logical canvas to the viewport. Keep figure
     geometry in that canvas so narrow viewports do not scale ``vh`` twice. */
  max-block-size: {maximum_figure_height_px:g}px;
}}
/* The minimum is an allocation floor carried independently from the
   title/footer-safe maximum; neither value asserts literal ink coverage. */
.reveal section.figure-led img.accessible-max-fit-image {{
  height: var(--template-figure-safe-max-height) !important;
  min-height: var(--template-figure-min-allocation-height);
  max-height: var(--template-figure-safe-max-height);
  max-width: 100%;
  object-fit: contain;
}}
.reveal section.figure-led img.accessible-max-fit-image:not(.accessible-multi-image-panel) {{
  display: block;
  width: {FIGURE_SAFE_BODY_MAX_WIDTH_PERCENT}% !important;
  margin-inline: auto;
}}
.reveal section.figure-led img.accessible-max-fit-image.accessible-multi-image-panel {{
  display: inline-block;
  vertical-align: middle;
  margin-inline: 0;
}}
.reveal figcaption, .reveal .slide-reader-link {{ font-size: {label_px:.2f}px; line-height: 1.3; }}
.slide-reader-nav {{
  position: fixed;
  inset-inline-end: max(0.75rem, env(safe-area-inset-right));
  inset-block-start: max(0.5rem, env(safe-area-inset-top));
  z-index: 30;
  background: #ffffff;
  border: 2px solid #111111;
  padding: 0.3rem 0.55rem;
  box-sizing: border-box;
  max-inline-size: calc(100vw - 1rem);
  overflow-wrap: anywhere;
}}
.skip-link {{
  position: fixed;
  inset-inline-start: max(0.5rem, env(safe-area-inset-left));
  inset-block-start: -8rem;
  z-index: 100;
  background: #ffffff;
  color: #111111;
  border: 3px solid #111111;
  padding: 0.5rem;
  box-sizing: border-box;
  max-inline-size: calc(100vw - 1rem);
  overflow-wrap: anywhere;
}}
.skip-link:focus {{ inset-block-start: max(0.5rem, env(safe-area-inset-top)); }}
.visually-hidden {{
  position: absolute !important; inline-size: 1px !important; block-size: 1px !important;
  padding: 0 !important; margin: -1px !important; overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important; white-space: nowrap !important; border: 0 !important;
}}
.figure-long-description {{
  font-size: {label_px:.2f}px; max-height: 35vh; max-width: 100%;
  overflow: auto; overflow-wrap: anywhere;
}}
.figure-exact-values {{ font-size: {label_px:.2f}px; max-width: 100%; overflow-wrap: anywhere; }}
@media (max-width: 32rem) {{
  /* Reveal ordinarily fits a fixed 960 x 700 canvas by transforming each
     active section.  At narrow reader widths that projection transform
     compounds CSS reflow and makes nominal 28/20/16-point text physically
     unreadable.  This media query keeps Reveal's active-slide and keyboard
     state machine, but lays out the current slide as an unscaled document. */
  html.reveal-full-page,
  body.reveal-viewport {{
    inline-size: 100%;
    block-size: auto;
    min-block-size: 100%;
    overflow-x: hidden;
    overflow-y: auto;
  }}
  main#main-content {{
    block-size: auto;
    min-block-size: calc(100vh - 7.5rem);
    min-block-size: calc(100dvh - 7.5rem);
    margin-block-start: 7.5rem;
    scroll-margin-block-start: 7.5rem;
  }}
  main#main-content .reveal {{
    position: relative;
    inset: auto;
    inline-size: 100%;
    block-size: auto !important;
    min-block-size: inherit;
    overflow: visible !important;
    touch-action: pan-y pinch-zoom;
  }}
  main#main-content .reveal .slides {{
    position: relative !important;
    inset: auto !important;
    inline-size: 100% !important;
    block-size: auto !important;
    min-block-size: inherit;
    margin: 0 !important;
    padding: 0;
    overflow: visible;
    pointer-events: auto;
    perspective: none;
    transform: none !important;
    zoom: 1 !important;
  }}
  main#main-content .reveal .slides > section.stack.present {{
    display: block !important;
    position: relative !important;
    inset: auto !important;
    inline-size: 100% !important;
    block-size: auto !important;
    min-block-size: inherit;
    margin: 0 !important;
    padding: 0 !important;
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
  }}
  main#main-content .reveal .slides > section.present:not(.stack),
  main#main-content .reveal .slides > section.stack.present > section.present {{
    display: block !important;
    position: relative !important;
    inset: auto !important;
    inline-size: 100% !important;
    block-size: auto !important;
    min-block-size: inherit;
    margin: 0 !important;
    padding: clamp(0.75rem, 3vw, 1.25rem) !important;
    box-sizing: border-box !important;
    opacity: 1 !important;
    transform: none !important;
    transform-origin: center !important;
    transition: none !important;
  }}
  main#main-content .reveal pre,
  main#main-content .reveal mjx-container[display="true"] {{
    max-inline-size: 100%;
    overflow-x: auto;
    overflow-y: hidden;
  }}
  main#main-content .reveal section.figure-led figure {{
    inline-size: 100%;
    margin-inline: 0;
  }}
  main#main-content .reveal section.figure-led img.accessible-max-fit-image {{
    /* These are logical-canvas pixels in projection mode.  With the narrow
       transform removed they become readable CSS-pixel allocation bounds;
       keep the source-owned floor/max variables instead of substituting vh. */
    min-block-size: var(--template-figure-min-allocation-height);
    max-block-size: var(--template-figure-safe-max-height);
  }}
  .slide-reader-nav {{
    inset-inline: max(0.5rem, env(safe-area-inset-left));
    inset-block-start: max(4.25rem, calc(env(safe-area-inset-top) + 4.25rem));
  }}
}}
@media (max-width: 32rem) and (max-height: 20rem) {{
  body {{ scroll-padding-block-start: 3.25rem; }}
  body:has(.skip-link:focus) {{ scroll-padding-block-start: 7.25rem; }}
  .slide-reader-nav {{
    position: fixed;
    inset-inline: max(0.5rem, env(safe-area-inset-left));
    inset-block-start: max(0.5rem, env(safe-area-inset-top));
    margin: 0;
  }}
  body:has(.skip-link:focus) .slide-reader-nav,
  .skip-link:focus + .slide-reader-nav {{
    inset-block-start: max(4.5rem, calc(env(safe-area-inset-top) + 4.5rem));
  }}
  main#main-content {{
    block-size: auto;
    min-block-size: calc(100vh - 3.25rem);
    min-block-size: calc(100dvh - 3.25rem);
    margin-block-start: 3.25rem;
    scroll-margin-block-start: 3.25rem;
  }}
  body:has(.skip-link:focus) main#main-content,
  .skip-link:focus ~ main#main-content {{
    min-block-size: calc(100vh - 7.25rem);
    min-block-size: calc(100dvh - 7.25rem);
    margin-block-start: 7.25rem;
  }}
}}
@media (prefers-reduced-motion: reduce) {{ .reveal .slides section {{ transition: none !important; }} }}
@media (forced-colors: active) {{ .reveal th, .reveal td, .slide-reader-nav {{ border: 2px solid CanvasText; }} }}
</style>"""


def enhance_accessible_reveal(
    html_file: Path,
    *,
    policy: AccessibleSlidePolicy,
    registry_path: Path | None,
    language: str = "en",
    label_numbers: Mapping[str, str] | None = None,
    strict_cross_deck_refs: bool = False,
) -> None:
    """Apply deterministic semantic, navigation, and visual-accessibility hooks."""

    # Reveal uses ``data-src`` for lazy loading while the shared publication
    # postprocessor intentionally matches ordinary HTML ``src`` attributes.
    # Accessible mode favors predictable native image semantics over lazy
    # loading and normalizes the attribute before applying the shared registry.
    initial = html_file.read_text(encoding="utf-8")
    initial = re.sub(r"(?<!\S)data-src\s*=", "src=", initial, flags=re.IGNORECASE)
    initial = normalize_figure_paths(initial)
    initial = activate_hardened_reveal_mathjax(initial)
    initial = promote_display_math_labels(initial)
    initial = resolve_reveal_cross_references(
        initial,
        label_numbers,
        strict=strict_cross_deck_refs,
    )
    write_if_changed(html_file, initial)
    harden_mathjax_script(html_file)
    enhance_accessibility(html_file, language=language, registry_path=registry_path)
    content = html_file.read_text(encoding="utf-8")
    content = _normalize_reveal_viewport(content)
    content = _disable_automatic_reveal_scroll(content)
    content = _reveal_semantics(content)
    authored_heading = _first_slide_heading(content)
    content = _set_document_title_and_heading(content, authored_heading)
    if "data-template-accessible-slides" not in content:
        content = content.replace("</head>", _accessible_reveal_css(policy) + "\n</head>", 1)
    content = _place_reader_navigation_after_skip_link(content, policy.reader_href)
    content = _add_interactive_keyboard_guard(content)
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
    title_only = _rendered_title_only_headings(content)
    if title_only:
        raise RenderingError(
            "[slides.structure.title-only-rendered] Reveal emitted a non-divider slide with no visible body",
            context={
                "source": str(html_file),
                "diagnostic_code": "slides.structure.title-only-rendered",
                "headings": list(title_only),
            },
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
    issues.extend(reveal_viewport_issues(content))
    issues.extend(reveal_scroll_activation_issues(content))
    if "data-template-interactive-keyboard-guard" not in content:
        issues.append("Reveal interactive-control keyboard guard is missing")
    if re.search(r"</h[1-6]\s+[^>]*>", content, flags=re.IGNORECASE):
        issues.append("Reveal heading attributes appear on a closing tag")
    if re.search(r"<h1\b", content, flags=re.IGNORECASE) is None:
        issues.append("Reveal deck has no document-level h1")
    title_match = _TITLE_RE.search(content)
    if title_match is None or ".pandoc.accessible" in title_match.group(0):
        issues.append("Reveal document title is missing or exposes a temporary build filename")
    skip_match = _SKIP_LINK_RE.search(content)
    nav_match = _READER_NAV_RE.search(content)
    if skip_match is None or nav_match is None or skip_match.start() > nav_match.start():
        issues.append("Reveal skip link is not the first presentation navigation control")
    ids = [match.group("id") for match in _HEADING_ID_RE.finditer(content)]
    for labelled_by in re.findall(
        r'<section\b[^>]*\baria-roledescription\s*=\s*["\']slide["\'][^>]*'
        r'\baria-labelledby\s*=\s*["\']([^"\']+)["\']',
        content,
        flags=re.IGNORECASE,
    ):
        if ids.count(labelled_by) != 1:
            issues.append(f"Reveal slide aria-labelledby does not resolve exactly once: {labelled_by}")
    for heading in _rendered_title_only_headings(content):
        issues.append(f"Reveal non-divider slide has no visible body: {heading}")
    issues.extend(reveal_reference_and_math_issues(content))
    return tuple(issues)

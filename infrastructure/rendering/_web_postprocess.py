"""HTML transformations and compatibility exports for web post-processing.

Asset injection and repository link resolution live in narrow leaf modules;
existing web and slide renderers retain their imports through this module.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._figure_alt_registry import (
    FigureAltRecord,
    FigureAltRegistry,
    rendered_figure_filename,
    require_record_alt,
)
from infrastructure.rendering._html_attributes import (
    html_attribute_assignment_pattern as _html_attribute_assignment_pattern,
)
from infrastructure.rendering._web_figure_details import apply_figure_long_description
from infrastructure.rendering._web_io import write_if_changed as write_if_changed
from infrastructure.rendering._web_assets import (
    MATHJAX_URL as MATHJAX_URL,
    _MATHJAX_INTEGRITY as _MATHJAX_INTEGRITY,
    _MATHJAX_FONT_URL as _MATHJAX_FONT_URL,
    _MATHJAX_DYNAMIC_PREFIX as _MATHJAX_DYNAMIC_PREFIX,
    _MATHJAX_CONFIG_MARKER as _MATHJAX_CONFIG_MARKER,
    _MATHJAX_CONFIG_SCRIPT as _MATHJAX_CONFIG_SCRIPT,
    _FAVICON_MARKER as _FAVICON_MARKER,
    _FAVICON_LINK as _FAVICON_LINK,
    _FAVICON_PNG as _FAVICON_PNG,
    _FAVICON_ICO as _FAVICON_ICO,
    SHARED_DESIGN_TOKENS_CSS as SHARED_DESIGN_TOKENS_CSS,
    harden_mathjax_script as harden_mathjax_script,
    embed_favicon as embed_favicon,
    write_favicon_file as write_favicon_file,
    embed_css as embed_css,
)
from infrastructure.rendering._web_links import (
    _ANCHOR_HREF_RE as _ANCHOR_HREF_RE,
    _PASSTHROUGH_HREF_SCHEMES as _PASSTHROUGH_HREF_SCHEMES,
    _PUBLIC_POOL_ROOTS as _PUBLIC_POOL_ROOTS,
    repository_root_for as repository_root_for,
    _repository_code_url as _repository_code_url,
    _url_suffix as _url_suffix,
    _reject_non_public_pool_target as _reject_non_public_pool_target,
    _resolve_repository_href_target as _resolve_repository_href_target,
    _quoted_relative_path as _quoted_relative_path,
    _web_relative_target as _web_relative_target,
    _renderer_figure_asset_target as _renderer_figure_asset_target,
    rewrite_repository_links as rewrite_repository_links,
    deployed_web_link_issues as deployed_web_link_issues,
)


def normalize_figure_paths(content: str) -> str:
    """Rewrite manuscript figure paths for files emitted under ``output/web``."""
    return (
        content.replace("../../output/figures/", "../figures/")
        .replace("../output/figures/", "../figures/")
        .replace("output/figures/", "../figures/")
    )


def normalize_figure_paths_in_file(html_file: Path) -> None:
    """Rewrite manuscript figure paths in ``html_file`` for the ``output/web`` layout, in place."""
    content = html_file.read_text(encoding="utf-8")
    write_if_changed(html_file, normalize_figure_paths(content))


_FIGURE_RE = re.compile(
    r"<figure\b(?P<attrs>[^>]*)>(?P<body>.*?)</figure>",
    flags=re.IGNORECASE | re.DOTALL,
)
_IMAGE_RE = re.compile(r"<img\b(?P<attrs>[^>]*)>", flags=re.IGNORECASE | re.DOTALL)
_TABLE_RE = re.compile(
    r"<table\b(?P<attrs>[^>]*)>(?P<body>.*?)</table>",
    flags=re.IGNORECASE | re.DOTALL,
)


def _html_attribute(attributes: str, name: str) -> str | None:
    match = _html_attribute_assignment_pattern(name).search(attributes)
    if match is None:
        return None
    return html.unescape(match.group("double") or match.group("single") or match.group("bare") or "")


def _has_html_attribute(attributes: str, name: str) -> bool:
    return _html_attribute_assignment_pattern(name).search(attributes) is not None


def _replace_html_attribute(tag: str, name: str, value: str) -> str:
    """Replace or insert an HTML attribute with a literal escaped value.

    ``re.sub`` treats string replacements as backreference templates; LaTeX
    fragments such as ``\\Omega`` in alt text raise ``re.error: bad escape``
    unless the replacement is a callable.
    """
    escaped = html.escape(value, quote=True)
    pattern = _html_attribute_assignment_pattern(name)

    def literal(_match: re.Match[str]) -> str:
        return f'{name}="{escaped}"'

    if pattern.search(tag):
        return pattern.sub(literal, tag, count=1)
    if name == "alt":
        insert_at = tag.rfind("/>")
        if insert_at < 0:
            insert_at = tag.rfind(">")
        return tag[:insert_at].rstrip() + f' alt="{escaped}" ' + tag[insert_at:]
    raise RenderingError(f"Rendered registry figure is missing an image {name}")


def _set_image_alt(image_tag: str, alt_text: str) -> str:
    return _replace_html_attribute(image_tag, "alt", alt_text)


def _set_image_source(image_tag: str, source: str) -> str:
    return _replace_html_attribute(image_tag, "src", source)


def _exact_render_record(
    registry: FigureAltRegistry,
    *,
    label: str | None,
    filename: str | None,
) -> FigureAltRecord | None:
    filename_records = registry.by_filename(filename)
    if len(filename_records) > 1:
        raise RenderingError(
            f"Rendered figure path maps to multiple registry records: {filename}",
            context={"registry": str(registry.path)},
        )
    if label is None:
        if not filename_records:
            return None
        raise RenderingError(
            f"Rendered figure label/path mismatch: unlabeled != {filename_records[0].label}",
            context={"registry": str(registry.path), "rendered_filename": filename},
        )
    label_record = registry.by_label(label)
    if label_record is not None:
        if label_record.filename != filename:
            raise RenderingError(
                f"Rendered figure path does not match registry record for {label_record.label}",
                context={
                    "registry": str(registry.path),
                    "registry_filename": label_record.filename,
                    "rendered_filename": filename,
                },
            )
        return label_record
    if not filename_records:
        return None
    filename_record = filename_records[0]
    if label != filename_record.label:
        raise RenderingError(
            f"Rendered figure label/path mismatch: {label} != {filename_record.label}",
            context={"registry": str(registry.path), "rendered_filename": filename},
        )
    return filename_record


def replace_figure_alts(content: str, *, registry_path: Path | None = None) -> str:
    """Apply exact registry alt text without deriving alternatives from captions.

    A registry record is consumed only when the rendered ``figure`` label and
    image path agree with it. Present-but-blank registry alternatives and
    label/path disagreements raise instead of silently retaining Pandoc's
    caption-derived ``alt``. Unregistered figures retain a non-empty authored
    alternative. A cross-reference-labelled figure with a blank alternative is
    non-decorative by construction and therefore also fails closed.
    """
    registry = FigureAltRegistry.load_optional(registry_path or Path("__absent_figure_registry__.json"))

    def _figure(match: re.Match[str]) -> str:
        figure_attrs = match.group("attrs")
        body = match.group("body")
        image_match = _IMAGE_RE.search(body)
        if image_match is None:
            return match.group(0)
        image_tag = image_match.group(0)
        label = _html_attribute(figure_attrs, "id")
        source = _html_attribute(image_match.group("attrs"), "src")
        filename = rendered_figure_filename(source) if source is not None else None
        record = _exact_render_record(registry, label=label, filename=filename)
        if record is not None:
            alt_text = require_record_alt(record, rendered_target=str(registry.path))
            updated_image = _set_image_alt(image_tag, alt_text)
            if record.filename is None:  # Defensive: registry parsing requires this.
                raise RenderingError(f"Figure registry record is missing a filename: {record.label}")
            updated_image = _set_image_source(updated_image, f"../figures/{record.filename}")
            updated_image, disclosure = apply_figure_long_description(updated_image, record)
            updated_body = body[: image_match.start()] + updated_image + body[image_match.end() :]
            if disclosure and "figure-long-description" not in updated_body:
                updated_body += disclosure
            return f"<figure{figure_attrs}>{updated_body}</figure>"

        authored_alt = _html_attribute(image_match.group("attrs"), "alt")
        if label is not None and label.startswith("fig:") and not (authored_alt and authored_alt.strip()):
            raise RenderingError(
                f"Rendered non-decorative figure has blank authored alt text: {label}",
                context={"registry": str(registry.path), "rendered_filename": filename},
            )
        return match.group(0)

    content = _FIGURE_RE.sub(_figure, content)

    def _explicit_image_alt(match: re.Match[str]) -> str:
        attributes = match.group("attrs")
        if _has_html_attribute(attributes, "alt"):
            return match.group(0)
        source = _html_attribute(attributes, "src")
        filename = rendered_figure_filename(source) if source is not None else None
        records = registry.by_filename(filename)
        if len(records) > 1:
            raise RenderingError(
                f"Unlabelled rendered image maps to multiple registry records: {filename}",
                context={"registry": str(registry.path)},
            )
        if len(records) == 1 and records[0].filename is not None:
            # Markdown ``![](...)`` is an explicitly decorative reuse. Pandoc
            # omits the attribute entirely, so restore the authored empty-alt
            # semantic without repeating the canonical labelled figure's long
            # description to screen-reader users.
            image_tag = _set_image_alt(match.group(0), "")
            return _set_image_source(image_tag, f"../figures/{records[0].filename}")
        raise RenderingError(
            "Rendered image is missing authored alt text and has no exact registry record",
            context={"registry": str(registry.path), "rendered_filename": filename},
        )

    return _IMAGE_RE.sub(_explicit_image_alt, content)


def enhance_accessibility(
    html_file: Path,
    *,
    language: str = "en",
    registry_path: Path | None = None,
) -> None:
    """Apply accessibility enhancements to ``html_file`` in place.

    Sets the ``<html lang>`` attribute when missing, removes ``aria-hidden``
    from ``<figcaption>`` elements, applies exact source-owned figure-registry
    alt text where available, wraps body content in a ``<main>`` landmark with
    a skip link, and writes the result only if the content changed.
    """
    content = html_file.read_text(encoding="utf-8")
    if not re.search(r"<html\b[^>]*\blang=", content, flags=re.IGNORECASE):
        content = re.sub(
            r"<html\b",
            f'<html lang="{html.escape(language, quote=True)}"',
            content,
            count=1,
            flags=re.IGNORECASE,
        )
    content = re.sub(
        r"(<figcaption\b[^>]*)\saria-hidden=(?:\"true\"|'true')",
        r"\1",
        content,
        flags=re.IGNORECASE,
    )
    content = replace_figure_alts(content, registry_path=registry_path)
    content = wrap_responsive_tables(content)
    if not re.search(r"<main\b", content, flags=re.IGNORECASE):
        main_open = '<main id="main-content" tabindex="-1">'
        toc_pattern = r'(?P<toc><nav\b[^>]*\bid=["\']TOC["\'][^>]*>.*?</nav>)'
        if re.search(toc_pattern, content, flags=re.IGNORECASE | re.DOTALL):
            content = re.sub(
                toc_pattern,
                rf"\g<toc>\n{main_open}",
                content,
                count=1,
                flags=re.IGNORECASE | re.DOTALL,
            )
        else:
            content = re.sub(r"(<body\b[^>]*>)", rf"\1\n{main_open}", content, count=1, flags=re.IGNORECASE)
        content = re.sub(r"</body>", "</main>\n</body>", content, count=1, flags=re.IGNORECASE)
    if not re.search(r"<a\b[^>]*\bhref=(?:\"#main-content\"|'#main-content')", content, flags=re.IGNORECASE):
        content = re.sub(
            r"(<body\b[^>]*>)",
            r'\1\n<a class="skip-link" href="#main-content">Skip to main content</a>',
            content,
            count=1,
            flags=re.IGNORECASE,
        )
    write_if_changed(html_file, content)


def wrap_responsive_tables(content: str) -> str:
    """Confine wide tables to labelled keyboard-scrollable containers."""

    def _table(match: re.Match[str]) -> str:
        attributes = match.group("attrs")
        if _has_html_attribute(attributes, "data-responsive-table"):
            return match.group(0)
        body = match.group("body")
        caption_match = re.search(
            r"<caption\b[^>]*>(?P<caption>.*?)</caption>",
            body,
            flags=re.IGNORECASE | re.DOTALL,
        )
        caption = html.unescape(re.sub(r"<[^>]+>", " ", caption_match.group("caption"))) if caption_match else ""
        context = " ".join(caption.split())
        if len(context) > 120:
            context = context[:117].rstrip() + "…"
        accessible_name = f"Scrollable table: {context}" if context else "Scrollable data table"
        table = f'<table{attributes} data-responsive-table="true">{body}</table>'
        return (
            '<div class="table-scroll" role="region" tabindex="0" '
            f'aria-label="{html.escape(accessible_name, quote=True)}">{table}</div>'
        )

    return _TABLE_RE.sub(_table, content)


def add_responsive_image_variants(html_file: Path) -> None:
    """Wrap images with available ``_mobile`` companion files in ``<picture>`` responsive sources, in place."""
    content = html_file.read_text(encoding="utf-8")

    def _image(match: re.Match[str]) -> str:
        tag = match.group(0)
        source = _html_attribute(tag, "src")
        if source is None:
            return tag
        source_path = Path(source)
        if source_path.stem.endswith("_mobile"):
            return tag
        mobile_source = str(source_path.with_name(source_path.stem + "_mobile" + source_path.suffix))
        if not (html_file.parent / mobile_source).resolve().is_file():
            return tag
        return (
            '<picture><source media="(max-width: 600px)" '
            f'srcset="{html.escape(mobile_source, quote=True)}">{tag}</picture>'
        )

    write_if_changed(html_file, re.sub(r"<img\b[^>]*>", _image, content, flags=re.IGNORECASE))


def add_full_resolution_figure_links(html_file: Path) -> None:
    """Make each rendered figure image a visible, keyboard-accessible full-size link.

    Publication figures are intentionally high-resolution so axes, annotations,
    and uncertainty marks remain inspectable.  A responsive HTML layout can
    legitimately reduce them to a reading-column width, however.  This
    post-processing pass preserves that in-page layout while giving every
    ``<figure>`` image an explicit route to the original asset.  It is
    idempotent and leaves author-supplied image links alone.
    """

    content = html_file.read_text(encoding="utf-8")
    figure_re = re.compile(
        r"(?P<open><figure\b[^>]*>)(?P<body>.*?)(?P<close></figure>)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    image_re = re.compile(r"<img\b(?P<attrs>[^>]*)>", flags=re.IGNORECASE | re.DOTALL)

    def _link_name(figure_body: str, image_attributes: str) -> str:
        caption_match = re.search(
            r"<figcaption\b[^>]*>(?P<caption>.*?)</figcaption>",
            figure_body,
            flags=re.IGNORECASE | re.DOTALL,
        )
        caption = html.unescape(re.sub(r"<[^>]+>", " ", caption_match.group("caption"))) if caption_match else ""
        accessible_context = " ".join(caption.split()) or (_html_attribute(image_attributes, "alt") or "").strip()
        accessible_context = re.sub(r"\\(?:\(|\)|\[|\])", "", accessible_context)
        if not accessible_context:
            raise RenderingError(
                "Rendered figure cannot receive a contextual full-size link without a caption or alternative",
            )
        numbered_caption = re.match(
            r"Figure\s+(?P<number>[^:]+):\s*(?P<title>.+)",
            accessible_context,
            flags=re.IGNORECASE,
        )
        number = numbered_caption.group("number").strip() if numbered_caption is not None else None
        title_source = numbered_caption.group("title").strip() if numbered_caption is not None else accessible_context
        sentence = re.match(r"(?P<title>.+?[.!?])(?:\s|$)", title_source)
        title = sentence.group("title").strip() if sentence is not None else title_source
        if len(title) > 88:
            boundary = re.search(r"(?:;|\s+—|\s+while\b|\s+and\b|\s+for\b|\s+\()", title[36:])
            if boundary is not None:
                title = title[: 36 + boundary.start()].rstrip(" ,.;:")
        if len(title) > 96:
            title = title[:93].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
        prefix = f"Open full-size Figure {number}" if number is not None else "Open full-size figure"
        return f"{prefix}, {title}"

    def _figure(match: re.Match[str]) -> str:
        figure_body = match.group("body")
        if "figure-full-size-link" in figure_body:
            return match.group(0)
        # Do not introduce a nested link when the author already supplied a
        # destination for the figure image.
        if re.search(r"<a\b[^>]*>.*?<img\b", figure_body, flags=re.IGNORECASE | re.DOTALL):
            return match.group(0)

        def _image(image_match: re.Match[str]) -> str:
            source = _html_attribute(image_match.group("attrs"), "src")
            if not source:
                return image_match.group(0)
            href = html.escape(source, quote=True)
            link_name = _link_name(figure_body, image_match.group("attrs"))
            escaped_link_name = html.escape(link_name, quote=True)
            return (
                '<a class="figure-full-size-link" '
                f'href="{href}" target="_blank" rel="noopener" '
                f'aria-label="{escaped_link_name}">'
                f"{image_match.group(0)}"
                '<span class="figure-full-size-label" aria-hidden="true">'
                "Open full-size figure</span></a>"
            )

        return match.group("open") + image_re.sub(_image, figure_body) + match.group("close")

    write_if_changed(html_file, figure_re.sub(_figure, content))

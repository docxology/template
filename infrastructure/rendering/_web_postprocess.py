"""Deterministic post-processing for rendered HTML artifacts."""

from __future__ import annotations

import base64
import html
import re
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import yaml

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._figure_alt_registry import (
    FigureAltRecord,
    FigureAltRegistry,
    rendered_figure_filename,
    require_record_alt,
)
from infrastructure.rendering._web_figure_details import apply_figure_long_description

logger = get_logger(__name__)

MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"
_MATHJAX_INTEGRITY = "sha384-2BWc4dVaHADUocwKrUrK9u3iDwHxVMKXWEcoRmUkXYSFKhAsgVAYClu9ydNuo5Oz"
_MATHJAX_FONT_URL = "https://cdn.jsdelivr.net/npm/@mathjax/mathjax-newcm-font@4.0.0/chtml/woff2"
_MATHJAX_DYNAMIC_PREFIX = "https://cdn.jsdelivr.net/npm/@mathjax/mathjax-newcm-font@4.0.0/chtml/dynamic"
_MATHJAX_CONFIG_MARKER = "data-template-mathjax-config"
_MATHJAX_CONFIG_SCRIPT = f"""<script {_MATHJAX_CONFIG_MARKER}>
window.MathJax = window.MathJax || {{}};
window.MathJax.chtml = Object.assign({{}}, window.MathJax.chtml, {{
  fontURL: "{_MATHJAX_FONT_URL}",
  dynamicPrefix: "{_MATHJAX_DYNAMIC_PREFIX}"
}});
window.normalizeTemplateMathJaxAria = function () {{
  document.querySelectorAll("mjx-speech[aria-roledescription]").forEach(function (node) {{
    var roleDescription = node.getAttribute("aria-roledescription") || "";
    if (/[\u0080-\u009f]/.test(roleDescription)) {{
      node.setAttribute("aria-roledescription", "mathematical expression");
    }}
  }});
}};
window.MathJax.startup = Object.assign({{}}, window.MathJax.startup, {{
  ready: function () {{
    window.MathJax.startup.defaultReady();
    window.MathJax.startup.promise.then(window.normalizeTemplateMathJaxAria);
  }}
}});
</script>"""
_FAVICON_MARKER = "data-template-favicon"
_FAVICON_LINK = f'<link {_FAVICON_MARKER} rel="icon" href="favicon.ico">'
_FAVICON_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAALUlEQVR4nGNgGAWjYBSMglEwCkbBqBkFo2AUjIJRMApGwSgYBaNgFIwCABj7ABHX+aOtAAAAAElFTkSuQmCC"
)
_FAVICON_ICO = (
    b"\x00\x00\x01\x00\x01\x00"
    + bytes([16, 16, 0, 0])
    + b"\x01\x00\x20\x00"
    + len(_FAVICON_PNG).to_bytes(4, "little")
    + (22).to_bytes(4, "little")
    + _FAVICON_PNG
)

SHARED_DESIGN_TOKENS_CSS = """:root {
  --brand-1: #5b6ee0;
  --web-bg: #f8f8f8;
  --web-surface: #ffffff;
  --web-text: #2c3e50;
  --web-border: #bdc3c7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --brand-1: #7e8ce8;
    --web-bg: #0f1420;
    --web-surface: #161c2b;
    --web-text: #e6eaf2;
    --web-border: #2a3447;
  }
}
.theorem-box {
  border-left: 4px solid var(--brand-1);
  background: var(--web-surface);
  padding: 0.6em 1em;
  margin: 1.1em 0;
  border-radius: 0 4px 4px 0;
}
.theorem-box.definition { border-left-style: dashed; }
.theorem-box > p:first-child { margin-top: 0; }
.theorem-box > p:last-child { margin-bottom: 0; }
.figure-long-description {
  border: 1px solid var(--web-border);
  border-radius: 4px;
  margin-block: 0.75rem;
  padding: 0.5rem 0.75rem;
}
.figure-long-description > summary { cursor: pointer; font-weight: 700; }
.figure-long-description > p { max-width: 80ch; }"""

_ANCHOR_HREF_RE = re.compile(
    r"(?P<prefix><a\b[^>]*?(?<!\S)href\s*=\s*)(?P<quote>[\"'])(?P<href>.*?)(?P=quote)",
    flags=re.IGNORECASE | re.DOTALL,
)
_PASSTHROUGH_HREF_SCHEMES = frozenset({"http", "https", "mailto", "tel"})
_PUBLIC_POOL_ROOTS = frozenset({"projects", "fonds", "rules", "tools"})


def repository_root_for(path: Path) -> Path:
    """Return the enclosing public repository root for a web render.

    A source or output path outside this checkout is deliberately rejected. In
    particular, private sidecar projects must never cause their authored links
    to be rewritten against the public repository.
    """

    candidates: list[Path] = []
    resolved = path.resolve(strict=False)
    directory = resolved if resolved.is_dir() else resolved.parent
    for candidate in (directory, *directory.parents):
        if candidate not in candidates:
            candidates.append(candidate)
    for candidate in candidates:
        citation = candidate / "CITATION.cff"
        if (
            resolved.is_relative_to(candidate)
            and citation.is_file()
            and not citation.is_symlink()
            and (candidate / "infrastructure").is_dir()
            and (candidate / "projects" / "templates").is_dir()
        ):
            return candidate.resolve(strict=True)
    raise RenderingError(
        f"Could not locate public repository root for web source: {path}",
        context={"source": str(path)},
    )


def _repository_code_url(repository_root: Path) -> str:
    """Read and validate the canonical repository URL from ``CITATION.cff``."""

    citation = repository_root / "CITATION.cff"
    if citation.is_symlink() or not citation.is_file():
        raise RenderingError(f"Repository citation metadata is missing or unsafe: {citation}")
    try:
        payload = yaml.safe_load(citation.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise RenderingError(f"Could not read repository citation metadata: {citation}") from exc
    repository_code = payload.get("repository-code") if isinstance(payload, dict) else None
    if not isinstance(repository_code, str):
        raise RenderingError(f"CITATION.cff is missing repository-code: {citation}")
    parsed = urlsplit(repository_code)
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() != "github.com"
        or len([part for part in parsed.path.split("/") if part]) != 2
        or parsed.query
        or parsed.fragment
    ):
        raise RenderingError(f"CITATION.cff repository-code is not a canonical GitHub HTTPS URL: {repository_code}")
    return repository_code.rstrip("/")


def _url_suffix(query: str, fragment: str) -> str:
    return (f"?{query}" if query else "") + (f"#{fragment}" if fragment else "")


def _reject_non_public_pool_target(relative_path: Path) -> None:
    parts = relative_path.parts
    if parts and parts[0] in _PUBLIC_POOL_ROOTS and (len(parts) < 2 or parts[1] != "templates"):
        raise RenderingError(f"Web link targets non-public repository content: {relative_path.as_posix()}")


def _resolve_repository_href_target(
    href_path: str,
    *,
    html_file: Path,
    repository_root: Path,
    source_files: tuple[Path, ...] = (),
) -> tuple[Path, bool]:
    """Resolve one local href from Pandoc or a renderer postprocessor."""

    decoded = unquote(href_path)
    if "\x00" in decoded or "\\" in decoded:
        raise RenderingError(f"Web link contains an unsafe local path: {href_path}")
    lexical = Path(decoded)
    if lexical.is_absolute():
        raise RenderingError(f"Web link contains an unsupported absolute filesystem path: {href_path}")

    # Pandoc preserves authored paths in the HTML. Prefer the output-page
    # interpretation for renderer-owned assets, then the source directory for
    # authored manuscript links, and finally a checkout-relative path used by
    # generated links.
    page_candidate = html_file.parent / lexical
    candidate_paths: list[Path] = [page_candidate]
    candidate_paths.extend(source.parent / lexical for source in source_files)
    candidate_paths.append(repository_root / lexical)

    page_target: Path | None = None
    source_targets: list[Path] = []
    root_target: Path | None = None
    for index, candidate in enumerate(candidate_paths):
        try:
            if not candidate.exists():
                continue
            target = candidate.resolve(strict=True)
        except OSError:
            continue
        if index == 0:
            page_target = target
        elif index < len(candidate_paths) - 1:
            if target not in source_targets:
                source_targets.append(target)
        else:
            root_target = target

    if page_target is not None:
        target = page_target
    elif len(source_targets) > 1:
        raise RenderingError(
            f"Web link resolves to multiple manuscript targets: {href_path}",
            context={"page": str(html_file), "targets": [str(path) for path in source_targets]},
        )
    elif source_targets:
        target = source_targets[0]
    elif root_target is not None:
        target = root_target
    else:
        raise RenderingError(
            f"Web link target does not exist: {href_path}",
            context={"page": str(html_file)},
        )

    web_root = html_file.parent.resolve(strict=True)
    if page_target is not None:
        try:
            page_target.relative_to(web_root)
        except ValueError:
            pass
        else:
            return page_target, page_target.is_dir()

    root = repository_root.resolve(strict=True)
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise RenderingError(
            f"Web link escapes the public repository: {href_path}",
            context={"page": str(html_file), "target": str(target)},
        ) from exc
    _reject_non_public_pool_target(relative)
    return target, target.is_dir()


def _quoted_relative_path(path: Path) -> str:
    """Quote a repository or web-relative path for an HTML URL."""

    return quote(path.as_posix(), safe="/-._~")


def _web_relative_target(html_file: Path, target: Path) -> str | None:
    """Return a deployed-web-relative target when ``target`` is local HTML."""

    try:
        relative = target.relative_to(html_file.parent.resolve(strict=True))
    except ValueError:
        return None
    return _quoted_relative_path(relative)


def rewrite_repository_links(
    html_file: Path,
    *,
    repository_root: Path,
    rendered_sources: Mapping[Path, str],
) -> None:
    """Rewrite local anchors into deployed pages or canonical repository URLs.

    Pandoc preserves authored relative paths in the HTML. Links to renderer-
    owned pages stay inside ``output/web``; links to manuscript source files
    are mapped to their rendered page when available; every other public
    repository target becomes a deterministic GitHub ``main`` URL. Unsafe or
    nonexistent targets fail instead of surviving as broken deployed links.
    """

    root = repository_root.resolve(strict=True)
    repository_code = _repository_code_url(root)
    source_files = tuple(source.resolve(strict=True) for source in rendered_sources)
    mapped_sources = {
        source.resolve(strict=True): Path(output_name) for source, output_name in rendered_sources.items()
    }
    for output_name in mapped_sources.values():
        if output_name.is_absolute() or ".." in output_name.parts:
            raise RenderingError(f"Rendered web page name is unsafe: {output_name}")
    content = html_file.read_text(encoding="utf-8")

    def _rewrite(match: re.Match[str]) -> str:
        raw_href = html.unescape(match.group("href"))
        parsed = urlsplit(raw_href)
        scheme = parsed.scheme.lower()
        if scheme in _PASSTHROUGH_HREF_SCHEMES:
            return match.group(0)
        if scheme or parsed.netloc:
            raise RenderingError(f"Web link uses an unsupported URI scheme: {raw_href}")
        if not parsed.path or parsed.path.startswith("/"):
            return match.group(0)

        target, is_directory = _resolve_repository_href_target(
            parsed.path,
            html_file=html_file,
            repository_root=root,
            source_files=source_files,
        )
        suffix = _url_suffix(parsed.query, parsed.fragment)
        local_web_target = _web_relative_target(html_file, target)
        mapped = mapped_sources.get(target)
        if local_web_target is not None:
            replacement = local_web_target
        elif mapped is not None:
            replacement = _quoted_relative_path(mapped)
        else:
            relative = target.relative_to(root)
            encoded = _quoted_relative_path(relative)
            if not encoded:
                replacement = repository_code + ("/" if parsed.path.endswith("/") else "")
            else:
                route = "tree" if is_directory else "blob"
                replacement = f"{repository_code}/{route}/main/{encoded}"
                if is_directory and parsed.path.endswith("/"):
                    replacement += "/"
        escaped = html.escape(replacement + suffix, quote=True)
        return f"{match.group('prefix')}{match.group('quote')}{escaped}{match.group('quote')}"

    write_if_changed(html_file, _ANCHOR_HREF_RE.sub(_rewrite, content))


def deployed_web_link_issues(web_dir: Path) -> tuple[str, ...]:
    """Return fail-closed issues for renderer-owned deployed HTML anchors."""

    try:
        root = web_dir.resolve(strict=True)
    except OSError as exc:
        return (f"web output directory is unreadable: {web_dir}: {exc}",)
    pages = [root / "index.html", *sorted(root.glob("*__*.html"))]
    issues: list[str] = []
    for page in pages:
        if not page.is_file() or page.is_symlink():
            issues.append(f"renderer-owned web page is missing or unsafe: {page}")
            continue
        try:
            content = page.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(f"renderer-owned web page is unreadable: {page}: {exc}")
            continue
        for match in _ANCHOR_HREF_RE.finditer(content):
            raw_href = html.unescape(match.group("href"))
            parsed = urlsplit(raw_href)
            scheme = parsed.scheme.lower()
            if scheme in _PASSTHROUGH_HREF_SCHEMES or (not parsed.path and not parsed.netloc):
                continue
            if scheme or parsed.netloc:
                issues.append(f"{page.name}: unsupported href scheme: {raw_href}")
                continue
            if parsed.path.startswith("/"):
                continue
            decoded = unquote(parsed.path)
            if "\x00" in decoded or "\\" in decoded:
                issues.append(f"{page.name}: unsafe local href: {raw_href}")
                continue
            candidate = page.parent / decoded
            try:
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(root)
            except (OSError, ValueError):
                issues.append(f"{page.name}: local href leaves output/web or is missing: {raw_href}")
    return tuple(issues)


def write_if_changed(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` only when it differs from the current file content.

    Writes via a temporary file and atomic ``replace`` so the output is never
    left in a partially-written state. No-op when the content is unchanged,
    preserving mtime and avoiding spurious diffs.
    """
    if content == path.read_text(encoding="utf-8"):
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


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


def _html_attribute_assignment_pattern(name: str) -> re.Pattern[str]:
    """Return an exact HTML attribute assignment pattern for ``name``.

    HTML attributes in renderer output are separated by whitespace.  A regex
    word boundary is insufficient here because ``-`` is not a word character,
    so ``\balt`` also matches the suffix of ``data-fig-alt`` (and ``\bsrc``
    matches ``data-src``).  Requiring the attribute to begin at the start of
    the provided fragment or immediately after whitespace keeps lookup and
    replacement on the real attribute.
    """
    return re.compile(
        rf"(?<!\S){re.escape(name)}\s*=\s*(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)'|(?P<bare>[^\s>]+))",
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
        if not accessible_context:
            return "Open full-size figure"
        if len(accessible_context) > 140:
            accessible_context = accessible_context[:137].rstrip() + "…"
        return f"Open full-size figure: {accessible_context}"

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


def harden_mathjax_script(html_file: Path) -> None:
    """Add SRI integrity and crossorigin attributes to the MathJax CDN script tag and inject the config script."""
    content = html_file.read_text(encoding="utf-8")
    if MATHJAX_URL not in content:
        return
    script_re = re.compile(r'(<script(?=[^>]*(?<!\S)src="' + re.escape(MATHJAX_URL) + r'")[^>]*)></script>')

    def _replace(match: re.Match[str]) -> str:
        tag = match.group(1)
        if not _has_html_attribute(tag, "integrity"):
            tag += f' integrity="{_MATHJAX_INTEGRITY}"'
        if not _has_html_attribute(tag, "crossorigin"):
            tag += ' crossorigin="anonymous"'
        script = f"{tag}></script>"
        return script if _MATHJAX_CONFIG_MARKER in content else f"{_MATHJAX_CONFIG_SCRIPT}\n{script}"

    write_if_changed(html_file, script_re.sub(_replace, content, count=1))


def embed_favicon(html_file: Path) -> None:
    """Insert a marked ``<link>`` favicon reference before ``</head>`` in ``html_file`` if absent."""
    content = html_file.read_text(encoding="utf-8")
    if _FAVICON_MARKER in content:
        return
    if "</head>" not in content:
        logger.warning("Could not find </head> tag in HTML, favicon not embedded")
        return
    write_if_changed(html_file, content.replace("</head>", f"\n{_FAVICON_LINK}\n</head>", 1))


def write_favicon_file(output_dir: Path) -> None:
    """Write the embedded ``favicon.ico`` file into ``output_dir``, logging a warning on failure."""
    try:
        (output_dir / "favicon.ico").write_bytes(_FAVICON_ICO)
    except OSError as exc:
        logger.warning("Failed to write favicon.ico: %s", exc)


def embed_css(html_file: Path, css_file: Path) -> None:
    """Embed the shared design tokens and renderer CSS into ``html_file``."""
    try:
        if not css_file.exists():
            logger.warning("CSS file not found: %s, skipping CSS embedding", css_file)
            return
        css_content = SHARED_DESIGN_TOKENS_CSS + "\n" + css_file.read_text(encoding="utf-8")
        content = html_file.read_text(encoding="utf-8")
        style_tag = f"\n<style>\n{css_content}\n</style>\n"
        if "</head>" in content:
            updated = content.replace("</head>", style_tag + "</head>", 1)
        elif "<head>" in content:
            updated = content.replace("<head>", "<head>" + style_tag, 1)
        else:
            logger.warning("Could not find <head> tag in HTML, CSS not embedded")
            return
        write_if_changed(html_file, updated)
        logger.debug("Embedded CSS from %s into %s", css_file.name, html_file.name)
    except OSError as exc:
        logger.warning("Failed to embed CSS: %s", exc)

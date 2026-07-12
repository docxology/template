"""Deterministic post-processing for rendered HTML artifacts."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

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
.theorem-box > p:last-child { margin-bottom: 0; }"""


def write_if_changed(path: Path, content: str) -> None:
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
    content = html_file.read_text(encoding="utf-8")
    write_if_changed(html_file, normalize_figure_paths(content))


def replace_figure_alts(content: str) -> str:
    """Replace generated image alt text with a concise plain-text caption."""

    def _figure(match: re.Match[str]) -> str:
        block = match.group(0)
        caption_match = re.search(
            r"<figcaption\b[^>]*>(?P<caption>.*?)</figcaption>",
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if caption_match is None:
            return block
        caption = re.sub(r"<[^>]+>", " ", caption_match.group("caption"))
        caption = html.unescape(caption)
        replacements = {
            "delta": "delta",
            "pi": "pi",
            "sqrt": "square root",
            "approx": "approximately",
            "times": "times",
        }
        caption = re.sub(r"\\([A-Za-z]+)", lambda tex: replacements.get(tex.group(1), tex.group(1)), caption)
        caption = re.sub(r"\\[()\[\]]", "", caption)
        caption = re.sub(r"[${}]+", "", caption)
        caption = re.sub(r"\s+", " ", caption).strip()
        sentence = re.split(r"(?<=[.!?])\s+", caption, maxsplit=1)[0]
        concise = sentence[:240].rstrip()
        if len(sentence) > 240:
            concise = concise.rsplit(" ", 1)[0] + "…"
        escaped = html.escape(concise, quote=True)
        return re.sub(
            r"(<img\b[^>]*\balt=)(?:\"[^\"]*\"|'[^']*')",
            rf'\1"{escaped}"',
            block,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

    return re.sub(r"<figure\b[^>]*>.*?</figure>", _figure, content, flags=re.IGNORECASE | re.DOTALL)


def enhance_accessibility(html_file: Path, *, language: str = "en") -> None:
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
    content = replace_figure_alts(content)
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
    content = html_file.read_text(encoding="utf-8")

    def _image(match: re.Match[str]) -> str:
        tag = match.group(0)
        src_match = re.search(r'\bsrc="([^"]+)"', tag, flags=re.IGNORECASE)
        if src_match is None:
            return tag
        source_path = Path(src_match.group(1))
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


def harden_mathjax_script(html_file: Path) -> None:
    content = html_file.read_text(encoding="utf-8")
    if MATHJAX_URL not in content:
        return
    script_re = re.compile(r'(<script(?=[^>]*\bsrc="' + re.escape(MATHJAX_URL) + r'")[^>]*)></script>')

    def _replace(match: re.Match[str]) -> str:
        tag = match.group(1)
        if "integrity=" not in tag:
            tag += f' integrity="{_MATHJAX_INTEGRITY}"'
        if "crossorigin=" not in tag:
            tag += ' crossorigin="anonymous"'
        script = f"{tag}></script>"
        return script if _MATHJAX_CONFIG_MARKER in content else f"{_MATHJAX_CONFIG_SCRIPT}\n{script}"

    write_if_changed(html_file, script_re.sub(_replace, content, count=1))


def embed_favicon(html_file: Path) -> None:
    content = html_file.read_text(encoding="utf-8")
    if _FAVICON_MARKER in content:
        return
    if "</head>" not in content:
        logger.warning("Could not find </head> tag in HTML, favicon not embedded")
        return
    write_if_changed(html_file, content.replace("</head>", f"\n{_FAVICON_LINK}\n</head>", 1))


def write_favicon_file(output_dir: Path) -> None:
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

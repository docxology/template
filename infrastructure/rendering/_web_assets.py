"""Pinned web assets, design tokens, and deterministic HTML asset injection."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._html_attributes import (
    html_attribute_assignment_pattern as _html_attribute_assignment_pattern,
    remove_html_attribute_assignment,
    remove_unquoted_whitespace_only_lines,
)
from infrastructure.rendering._web_io import write_if_changed

# Keep the existing diagnostic namespace for callers and log consumers.
logger = get_logger("infrastructure.rendering._web_postprocess")

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
var templateMathOutput = window.MathJax.output || {{}};
window.MathJax.output = Object.assign({{}}, templateMathOutput, {{
  displayOverflow: "linebreak",
  linebreaks: Object.assign({{}}, templateMathOutput.linebreaks, {{
    inline: true,
    width: "100%",
    lineleading: 0.5
  }})
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
.figure-long-description > p { max-width: 80ch; overflow-wrap: anywhere; }
.figure-exact-values { max-width: 80ch; overflow-wrap: anywhere; }
code { overflow-wrap: anywhere; word-break: break-word; }
pre {
  max-width: 100%;
  overflow: visible;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  word-break: break-word;
}
pre code { overflow-wrap: inherit; white-space: inherit; word-break: inherit; }
div.sourceCode { max-width: 100%; overflow: visible; }
pre.sourceCode { background: #2c3e50; color: #ecf0f1; }
pre.sourceCode code,
pre.sourceCode code span { color: inherit; }
pre > code.sourceCode { white-space: pre-wrap; }
pre > code.sourceCode > span {
  display: block;
  max-width: 100%;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  word-break: break-word;
}
mjx-container[display="true"] { max-width: 100%; overflow: visible; }
.table-scroll {
  max-width: 100%;
  overflow-x: auto;
  overscroll-behavior-inline: contain;
  scrollbar-gutter: stable;
}
.table-scroll:focus-visible {
  outline: 3px solid var(--brand-1);
  outline-offset: 3px;
}
.table-scroll > table { margin-block: 0; min-width: 100%; width: max-content; }"""


def harden_mathjax_script(html_file: Path) -> None:
    """Normalize the pinned MathJax loader and inject its shared config.

    The URL is an executable dependency boundary: one page gets exactly one
    loader, with exactly the reviewed SRI digest and anonymous CORS mode.
    Existing, incorrect, or duplicate attributes are not trusted merely
    because they use an ``integrity``-shaped value.
    """
    content = html_file.read_text(encoding="utf-8")
    if MATHJAX_URL not in content:
        return
    config_re = re.compile(
        r"<script\b(?=[^>]*\b" + re.escape(_MATHJAX_CONFIG_MARKER) + r"\b)[^>]*>.*?</script>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    config_line_re = re.compile(
        r"^[ \t]*<script\b(?=[^>]*\b" + re.escape(_MATHJAX_CONFIG_MARKER) + r"\b)[^>]*>.*?</script>[ \t]*(?:\r?\n|$)",
        flags=re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    content = config_line_re.sub("", content)
    content = config_re.sub("", content)
    script_re = re.compile(r"<script\b(?P<attrs>[^>]*)>.*?</script>", flags=re.IGNORECASE | re.DOTALL)
    matched_loader = False

    def _replace(match: re.Match[str]) -> str:
        nonlocal matched_loader
        attributes = match.group("attrs")
        sources = [
            html.unescape(item.group("double") or item.group("single") or item.group("bare") or "")
            for item in _html_attribute_assignment_pattern("src").finditer(attributes)
        ]
        if not any(
            source == MATHJAX_URL or source.startswith((f"{MATHJAX_URL}?", f"{MATHJAX_URL}#")) for source in sources
        ):
            return match.group(0)
        if matched_loader:
            return ""
        matched_loader = True
        for attribute in ("src", "integrity", "crossorigin"):
            attributes = remove_html_attribute_assignment(attributes, attribute)
        attributes = remove_unquoted_whitespace_only_lines(attributes)
        attributes = attributes.rstrip()
        attributes += (
            f' src="{html.escape(MATHJAX_URL, quote=True)}" integrity="{_MATHJAX_INTEGRITY}" crossorigin="anonymous"'
        )
        script = f"<script{attributes}></script>"
        return f"{_MATHJAX_CONFIG_SCRIPT}\n{script}"

    write_if_changed(html_file, script_re.sub(_replace, content))


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

"""Pinned web assets, design tokens, and deterministic HTML asset injection."""

from __future__ import annotations

import base64
import html
import re
import secrets
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._html_attributes import (
    html_attribute_assignment_pattern as _html_attribute_assignment_pattern,
    remove_html_attribute_assignment,
    remove_unquoted_whitespace_only_lines,
)
from infrastructure.rendering._web_io import write_if_changed
from infrastructure.rendering._web_font_assets import source_web_font_script

# Keep the existing diagnostic namespace for callers and log consumers.
logger = get_logger("infrastructure.rendering._web_postprocess")

MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"

MATHJAX_INTEGRITY = _MATHJAX_INTEGRITY = "sha384-2BWc4dVaHADUocwKrUrK9u3iDwHxVMKXWEcoRmUkXYSFKhAsgVAYClu9ydNuo5Oz"

MATHJAX_FONT_URL = _MATHJAX_FONT_URL = "https://cdn.jsdelivr.net/npm/@mathjax/mathjax-newcm-font@4.0.0/chtml/woff2"

MATHJAX_DYNAMIC_PREFIX = _MATHJAX_DYNAMIC_PREFIX = (
    "https://cdn.jsdelivr.net/npm/@mathjax/mathjax-newcm-font@4.0.0/chtml/dynamic"
)

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
    var measuredWidth = document.documentElement.clientWidth;
    var reflowQueued = false;
    window.MathJax.startup.defaultReady();
    window.templateMathJaxReflowPromise = window.MathJax.startup.promise.then(
      window.normalizeTemplateMathJaxAria
    );
    function reflowDisplayMath() {{
      if (reflowQueued || document.documentElement.clientWidth === measuredWidth) return;
      reflowQueued = true;
      window.templateMathJaxReflowPromise = window.templateMathJaxReflowPromise
        .catch(function () {{ /* A later resize may retry a failed render. */ }})
        .then(async function () {{
          var width = document.documentElement.clientWidth;
          try {{
            // MathJax 4 MathItem.STATE.METRICS = 110. The default RERENDER
            // state retains old container metrics and cannot reflow on zoom.
            await window.MathJax.startup.document.rerenderPromise(110);
            window.normalizeTemplateMathJaxAria();
            window.templateMathJaxReflowError = null;
          }} catch (error) {{
            window.templateMathJaxReflowError = String(error);
            console.error("MathJax viewport reflow failed", error);
            throw error;
          }} finally {{
            measuredWidth = width;
            reflowQueued = false;
          }}
        }})
        .then(reflowDisplayMath);
      // Keep failure observable to callers without an unhandled rejection.
      window.templateMathJaxReflowPromise.catch(function () {{}});
    }}
    window.addEventListener("resize", reflowDisplayMath);
    // Also cover a resize that happened during the initial asynchronous render.
    window.templateMathJaxReflowPromise.then(reflowDisplayMath);
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
    target = output_dir / "favicon.ico"
    try:
        if target.is_symlink():
            raise OSError("refusing to follow a planted favicon.ico symlink")
        temporary = output_dir / f".favicon-{secrets.token_hex(12)}.tmp"
        try:
            temporary.write_bytes(_FAVICON_ICO)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
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
        style_tag = f"\n<style>\n{css_content}\n</style>\n" + source_web_font_script()
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


def install_local_mathjax_assets(html_file: Path, *, repo_root: Path) -> None:
    """Publish the source-declared exact npm runtime closure for offline reading.

    The opt-in mode fails if declared versions, lock identities, installed package
    identities, or the existing reviewed loader SRI differ. It never downloads.
    """
    import hashlib
    import json

    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined

    declarations = json.loads(read_bytes_confined(repo_root, repo_root / "package.json", max_bytes=1024 * 1024))
    lock = json.loads(read_bytes_confined(repo_root, repo_root / "package-lock.json", max_bytes=8 * 1024 * 1024))
    expected = {"mathjax": "4.0.0", "@mathjax/mathjax-newcm-font": "4.0.0"}
    for name, version in expected.items():
        if (
            declarations.get("dependencies", {}).get(name) or declarations.get("devDependencies", {}).get(name)
        ) != version:
            raise ValueError("offline MathJax requires source-declared exact npm dependencies")
        item = lock.get("packages", {}).get(f"node_modules/{name}", {})
        if item.get("version") != version or not str(item.get("integrity", "")).startswith("sha512-"):
            raise ValueError("offline MathJax requires exact integrity-bound npm lock entries")
    target = html_file.parent / "assets" / "mathjax-4.0.0"
    packages = repo_root / "node_modules"
    loader = read_bytes_confined(repo_root, packages / "mathjax" / "tex-chtml.js", max_bytes=4 * 1024 * 1024)
    sri = "sha384-" + base64.b64encode(hashlib.sha384(loader).digest()).decode()
    if sri != MATHJAX_INTEGRITY:
        raise ValueError("offline MathJax loader differs from reviewed source-owned SRI")
    manifest: dict[str, object] = {
        "schema_version": "template-local-mathjax-assets-v1",
        "package_lock_sha256": hashlib.sha256((repo_root / "package-lock.json").read_bytes()).hexdigest(),
        "packages": expected,
        "files": [],
    }
    rows: list[dict[str, str]] = []
    for name, version in expected.items():
        original = packages / name
        metadata = json.loads(read_bytes_confined(repo_root, original / "package.json", max_bytes=1024 * 1024))
        if metadata.get("name") != name or metadata.get("version") != version:
            raise ValueError("installed offline MathJax package identity differs")
        files = (
            sorted(original.rglob("*"))
            if name == "mathjax"
            else sorted((original / "chtml").rglob("*")) + [original / "chtml.js", original / "package.json"]
        )
        for source in files:
            if source.is_symlink():
                raise ValueError("offline MathJax assets refuse symlinks")
            if not source.is_file():
                continue
            relative = source.relative_to(original)
            asset_bytes = read_bytes_confined(repo_root, source, max_bytes=8 * 1024 * 1024)
            destination = target / ("mathjax" if name == "mathjax" else "newcm") / relative
            destination.relative_to(repo_root)
            for ancestor in (destination.parent, *destination.parent.parents):
                if ancestor == repo_root.parent:
                    break
                if ancestor.is_symlink():
                    raise ValueError("offline asset publication refuses symlink ancestors")
            destination.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_bytes_confined(repo_root, destination, asset_bytes)
            rows.append(
                {
                    "path": destination.relative_to(html_file.parent).as_posix(),
                    "sha256": hashlib.sha256(asset_bytes).hexdigest(),
                    "package": name,
                }
            )
    manifest["files"] = rows
    manifest_file = target / "asset-manifest.json"
    atomic_write_bytes_confined(
        repo_root, manifest_file, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    )
    content = html_file.read_text(encoding="utf-8")
    replacements = {
        MATHJAX_URL: "assets/mathjax-4.0.0/mathjax/tex-chtml.js",
        MATHJAX_FONT_URL: "assets/mathjax-4.0.0/newcm/chtml/woff2",
        MATHJAX_DYNAMIC_PREFIX: "assets/mathjax-4.0.0/newcm/chtml/dynamic",
    }
    for original_url, local_url in replacements.items():
        content = content.replace(original_url, local_url)
    # MathJax component and font resolution remains relative to this local page.
    content = content.replace(
        "window.MathJax = window.MathJax || {};",
        "window.MathJax = window.MathJax || {};\n"
        "window.MathJax.loader = Object.assign({}, window.MathJax.loader, "
        '{paths: {mathjax: "assets/mathjax-4.0.0/mathjax"}});',
    )
    write_if_changed(html_file, content)

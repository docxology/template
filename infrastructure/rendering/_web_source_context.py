"""Deterministic source boundaries and exact slices of canonical Pandoc HTML.

These markers carry ownership only. Pandoc's actual whole-document filters own
all numbering and citation semantics; no HTML labels or references are inferred.
"""

from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._paper_frontmatter import compose_frontmatter
from infrastructure.rendering._web_postprocess import _HTML_ATTRIBUTE_TOKEN_RE
from infrastructure.rendering.manuscript_hydration_replay import combine_held_manuscripts

WEB_SOURCE_ALGORITHM = "web-renderer-source-context-v2"
WEB_PAPER_SOURCE_ALGORITHM = "web-renderer-paper-source-context-v2"
_VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)
_EXTRA_RAW_TEXT = frozenset({"textarea", "title", "xmp", "iframe", "noembed", "noframes", "plaintext"})


def source_context_tokens(bodies: tuple[bytes, ...]) -> tuple[tuple[str, str], ...]:
    """Bind ordinal ownership to the complete ordered bytes, not filenames/IDs."""
    digest = hashlib.sha256()
    for body in bodies:
        digest.update(len(body).to_bytes(8, "big"))
        digest.update(body)
    prefix = "template-web-source-" + digest.hexdigest() + "-"
    if any(prefix.encode() in body for body in bodies):
        raise RenderingError("Manuscript collides with its reserved web source boundary namespace")
    return tuple((f"{prefix}{index}-start", f"{prefix}{index}-end") for index in range(len(bodies)))


def compose_web_source_context(
    bodies: tuple[bytes, ...],
    frontmatter_count: int = 0,
    *,
    boundary_bodies: tuple[bytes, ...] | None = None,
) -> str:
    """Frame every source while retaining Pandoc's whole-document YAML metadata.

    Raw HTML comments survive formalism, Crossref and citeproc without adding
    containers to their AST. Frontmatter keeps its original enclosing layout.
    """
    if (
        not bodies
        or not 0 <= frontmatter_count <= len(bodies)
        or not any(body.strip().removeprefix(b"\xef\xbb\xbf") for body in bodies)
    ):
        raise RenderingError("Web source context requires a complete nonempty ordered manuscript")
    if boundary_bodies is not None and len(boundary_bodies) != len(bodies):
        raise RenderingError("Web source context annotation changed its complete input roster")
    tokens = source_context_tokens(bodies if boundary_bodies is None else boundary_bodies)
    annotated = []
    for body, (start, end) in zip(bodies, tokens, strict=True):
        text = body.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        prefix = f"```{{=html}}\n<!--{start}-->\n```\n\n"
        annotated.append((prefix + text.rstrip() + f"\n\n```{{=html}}\n<!--{end}-->\n```\n").encode())
    held = tuple(annotated)
    if frontmatter_count:
        return compose_frontmatter(held, frontmatter_count, "\n---\n\n")
    return combine_held_manuscripts(held, separator="\n---\n\n").decode()


class _SourceDocument(HTMLParser):
    """Locate only real body/boundary tokens; never reserialize authored HTML."""

    def __init__(self, content: str, tokens: tuple[tuple[str, str], ...]) -> None:
        super().__init__(convert_charrefs=False)
        self.expected = {token for pair in tokens for token in pair}
        self.markers: dict[str, tuple[int, int, tuple[tuple[str, str], ...]]] = {}
        self.stack: list[tuple[str, str]] = []
        self.template_depth = 0
        self.body_start: int | None = None
        self.body_end: int | None = None
        self.lines = [0]
        self.lines.extend(index + 1 for index, character in enumerate(content) if character == "\n")
        self.feed(content)
        self.close()

    def _offset(self) -> int:
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        raw = self.get_starttag_text()
        if raw is None:
            raise RenderingError("Canonical HTML element has no original start tag")
        if tag in _EXTRA_RAW_TEXT:
            self.set_cdata_mode(tag)
        if tag == "template":
            self.template_depth += 1
        if tag == "body" and not self.template_depth:
            if self.body_start is not None:
                raise RenderingError("Canonical HTML has multiple body elements")
            self.body_start = self._offset() + len(raw)
            self.stack = []
        elif self.body_start is not None and self.body_end is None and tag not in _VOID:
            self.stack.append((tag, raw))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # HTML's self-closing flag does not close nonvoid elements, notably template.
        self.handle_starttag(tag, attrs)
        if tag in {"script", "style"}:
            self.set_cdata_mode(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "template" and self.template_depth:
            self.template_depth -= 1
        if self.body_start is None or self.body_end is not None:
            return
        if tag == "body" and not self.template_depth:
            self.body_end = self._offset()
        else:
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    del self.stack[index:]
                    break
                if self.stack[index][0] == "template":
                    break

    def handle_comment(self, data: str) -> None:
        if data not in self.expected or self.template_depth:
            return
        if self.body_start is None or self.body_end is not None or data in self.markers:
            raise RenderingError("Canonical HTML has an invalid or repeated source boundary")
        offset = self._offset()
        self.markers[data] = (offset, offset + len(data) + 7, tuple(self.stack))


def _reopen_ancestor(tag: str, raw: str) -> str:
    """Retain layout, not a second ownership claim for an ancestor's anchor."""
    removals = [
        (match.start(), match.end())
        for match in _HTML_ATTRIBUTE_TOKEN_RE.finditer(raw, len(tag) + 1)
        if match.group("name").lower() == "id" or (tag == "a" and match.group("name").lower() == "name")
    ]
    for first, last in reversed(removals):
        raw = raw[:first] + raw[last:]
    return raw


def split_canonical_html(content: str, bodies: tuple[bytes, ...]) -> tuple[str, tuple[str, ...]]:
    """Return marker-free index and source-owned pages with the identical shell.

    Generated title/TOC content, bibliography and footnotes stay in index;
    the existing exact fragment router supplies their cross-page destinations.
    Ancestor markup is retained for authored raw HTML and paper frontmatter.
    Script, code and template contents are copied unchanged, not interpreted as
    boundaries. Missing/changed boundaries fail closed rather than guessing.
    """
    tokens = source_context_tokens(bodies)
    document = _SourceDocument(content, tokens)
    if document.body_start is None or document.body_end is None:
        raise RenderingError("Canonical HTML lacks a complete body")
    expected = [token for pair in tokens for token in pair]
    if set(document.markers) != set(expected):
        raise RenderingError("Canonical HTML did not retain every ordered source boundary")
    ordered = [document.markers[token] for token in expected]
    if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
        raise RenderingError("Canonical HTML reordered source boundaries")
    prefix, suffix = content[: document.body_start], content[document.body_end :]
    pages = []
    for start, end in tokens:
        first, ancestors = document.markers[start][1], document.markers[start][2]
        last, _, closing = document.markers[end]
        pages.append(
            prefix
            + "".join(_reopen_ancestor(tag, raw) for tag, raw in ancestors)
            + content[first:last]
            + "".join(f"</{tag}>" for tag, _ in reversed(closing))
            + suffix
        )
    parts = []
    cursor = 0
    for first, last, _ in ordered:
        parts.append(content[cursor:first])
        cursor = last
    parts.append(content[cursor:])
    return "".join(parts), tuple(pages)


def project_source_context_ast(ast: bytes, bodies: tuple[bytes, ...], source_index: int | None = None) -> bytes:
    """Select exact ordered RawBlock boundaries in the real resolved AST.

    This projection never resolves a citation or reconstructs a text label. The
    complete parser result remains the custody record; the selected blocks carry
    their original attributes, citation structures and globally resolved values.
    """
    if source_index is not None and not 0 <= source_index < len(bodies):
        raise RenderingError("Source AST projection has an invalid source ordinal")
    document = json.loads(ast)
    tokens = source_context_tokens(bodies)
    expected = [token for pair in tokens for token in pair]
    markers = {f"<!--{token}-->": token for token in expected}
    seen = []
    selected = []
    current: int | None = None
    for block in document["blocks"]:
        raw = block.get("c")
        token = (
            markers.get(raw[1].strip())
            if block.get("t") == "RawBlock" and isinstance(raw, list) and raw[0] == "html"
            else None
        )
        if token is not None:
            seen.append(token)
            if token.endswith("-start"):
                current = next(index for index, pair in enumerate(tokens) if pair[0] == token)
            else:
                current = None
        elif source_index is None or current == source_index:
            selected.append(block)
    if seen != expected:
        raise RenderingError("Resolved source AST did not retain every ordered ownership boundary")
    document["blocks"] = selected
    if source_index is not None and source_index:
        # Only the first source owns whole-document YAML metadata.
        document["meta"] = {}
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()

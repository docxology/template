"""Well-formedness repair for raw-HTML damage in Pandoc EPUB XHTML members.

Raw HTML fragments in source markdown — unclosed void elements (``<br>``,
``<img ...>``), stray ``<`` characters in text, mismatched close tags, and
``--`` sequences inside HTML comments — pass through Pandoc's writers verbatim
as raw HTML. The EPUB chapter documents that receive them are then not
well-formed XML, so package validation (and every real-world reader) rejects
the whole EPUB even though only one passage is damaged.

:func:`sanitize_epub_xhtml` rewrites only the members that fail XML parsing;
members that already parse are passed through byte-for-byte, so a
correctly-formed package is never touched. Repairs are minimal and semantic:

- HTML void elements are re-emitted in XHTML self-closing form (``<br>`` becomes
  ``<br />``), which is what Pandoc itself emits for its own line breaks.
- Text and attribute values are XML-escaped (``&`` and ``<``, ``"`` in values).
- Comments containing ``--`` (forbidden by XML) have the run converted to a
  single hyphen followed by a space; HTML comments are not reader-visible
  content, so this is lossless for the rendered book.
- A close tag that does not match the innermost open element closes the
  intervening open elements first; a close tag with no matching open element is
  dropped; elements still open at end of input are closed there. This is the
  standard HTML5-style recovery, applied only where the strict XML parse
  already failed.
- Text and attribute values are XML-escaped (``&`` and ``<``, ``"`` in values),
  and code points XML cannot represent (raw control bytes in text or comments)
  are dropped.

Tag-name case is preserved from the raw source token so embedded SVG
(``<clipPath>``, ``<linearGradient>``) survives; SVG attribute names keep their
source spelling for the same reason. If a member still fails XML parsing after
repair the rewritten package fails validation downstream, exactly as an
unsanitized package would — the sanitizer never marks a damaged package valid.
"""

from __future__ import annotations

import os
import stat
import re
import tempfile
import zipfile
from html import entities as html_entities
from html.parser import HTMLParser
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._epub_package_validation import (
    MAX_EPUB_XML_MEMBER_BYTES,
    _preflight_members,
)

logger = get_logger(__name__)

# HTML5 void elements: never have content, must be self-closed in XML.
_VOID_ELEMENTS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)

_XHTML_MEMBER_SUFFIXES = (".xhtml", ".html")


_INVALID_XML_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _xml_safe(value: str) -> str:
    """Drop code points XML 1.0 cannot represent (e.g. raw control bytes)."""
    return _INVALID_XML_CONTROL.sub("", value)


def _escape_text(value: str) -> str:
    """Escape text data for XML character content."""
    return _xml_safe(value).replace("&", "&amp;").replace("<", "&lt;")


def _escape_attribute(value: str) -> str:
    """Escape one attribute value for XML double-quoted serialization."""
    return _xml_safe(value).replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def _named_entity_charref(name: str) -> str | None:
    """Return the numeric XML character reference for one HTML entity name."""
    codepoint = html_entities.entitydefs.get(name)
    if isinstance(codepoint, str) and len(codepoint) == 1:
        return f"&#{ord(codepoint)};"
    return None


def _sanitize_comment_text(data: str) -> str:
    """Return XML-safe comment text.

    XML forbids ``--`` anywhere inside a comment and a trailing ``-`` before
    the closing delimiter. Hyphen runs are repaired to a space-separated
    single hyphen so the comment stays human-readable, and code points XML
    cannot represent (raw control bytes) are dropped. The result equals the
    input byte-for-byte when the comment was already XML-safe.
    """
    repaired = _xml_safe(re.sub(r"--+", "- -", data))
    if repaired.endswith("-"):
        repaired += " "
    return repaired


def _repair_xhtml(payload: str) -> str:
    """Return a well-formed XML serialization of one XHTML document payload."""

    class _RepairingParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=False)
            self.out: list[str] = []
            self.open_stack: list[str] = []

        # -- structure -------------------------------------------------------
        def handle_decl(self, decl: str) -> None:
            self.out.append(f"<!{decl}>")

        def handle_pi(self, data: str) -> None:
            self.out.append(f"<?{data}>")

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            self._emit_start(tag, attrs, void=tag in _VOID_ELEMENTS)

        def handle_comment(self, data: str) -> None:
            self.out.append(f"<!--{_sanitize_comment_text(data)}-->")

        def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            self._emit_start(tag, attrs, void=True)

        def handle_endtag(self, tag: str) -> None:
            if tag in self.open_stack:
                while True:
                    open_tag = self.open_stack.pop()
                    self.out.append(f"</{open_tag}>")
                    if open_tag == tag:
                        break
            # A close tag with no matching open element is dropped.

        def close(self) -> None:
            super().close()
            while self.open_stack:
                self.out.append(f"</{self.open_stack.pop()}>")

        # -- content ---------------------------------------------------------
        def handle_data(self, data: str) -> None:
            self.out.append(_escape_text(data))

        def handle_entityref(self, name: str) -> None:
            charref = _named_entity_charref(name)
            self.out.append(charref if charref is not None else f"&amp;{name};")

        def handle_charref(self, name: str) -> None:
            self.out.append(f"&#{name};")

        # -- helpers ---------------------------------------------------------
        def _emit_start(self, tag: str, attrs: list[tuple[str, str | None]], *, void: bool) -> None:
            rendered_attrs = []
            for name, value in attrs:
                if value is None:
                    rendered_attrs.append(f'{name}=""')
                else:
                    rendered_attrs.append(f'{name}="{_escape_attribute(value)}"')
            attr_text = "".join(f" {part}" for part in rendered_attrs)
            # HTMLParser lowercases tag names; restore the source spelling so
            # embedded SVG (clipPath, linearGradient, ...) survives rewriting.
            raw = self.get_starttag_text() or ""
            case_match = re.match(r"<\s*([^\s/>]+)", raw)
            emitted_tag = case_match.group(1) if case_match else tag
            self.out.append(f"<{emitted_tag}{attr_text}{' /' if void else ''}>")
            if not void:
                self.open_stack.append(tag)

    parser = _RepairingParser()
    parser.feed(payload)
    parser.close()
    return "".join(parser.out)


def _repair_xhtml_bytes(payload: bytes) -> bytes | None:
    """Return repaired bytes for one member, or ``None`` if it already parses."""
    try:
        import defusedxml.ElementTree as safe_et
        from defusedxml.common import DefusedXmlException
    except ImportError as exc:  # pragma: no cover - exercised only without defusedxml
        raise ValueError("EPUB XHTML sanitization requires the 'defusedxml' package") from exc
    try:
        safe_et.fromstring(payload)
        return None
    except (DefusedXmlException, safe_et.ParseError, UnicodeError):
        pass
    return _repair_xhtml(payload.decode("utf-8", errors="replace")).encode("utf-8")


def sanitize_epub_xhtml(epub_path: Path) -> list[str]:
    """Rewrite every non-well-formed XHTML member of *epub_path* in place.

    Members that already parse as XML are copied byte-for-byte. Returns the
    sorted names of the members that were repaired; a package with no damage
    is not rewritten at all.

    Raises:
        ValueError: the archive cannot be preflighted safely.
        OSError: the archive cannot be read or replaced.
    """
    if epub_path.is_symlink():
        raise ValueError(f"refusing to rewrite EPUB through symlink: {epub_path}")
    original_mode = stat.S_IMODE(epub_path.stat().st_mode)
    repaired: list[str] = []
    temporary_path: Path | None = None
    try:
        with zipfile.ZipFile(epub_path) as source:
            infos = _preflight_members(source.infolist())
            payloads: dict[str, bytes] = {}
            for name, info in infos.items():
                if not name.endswith(_XHTML_MEMBER_SUFFIXES):
                    continue
                if info.file_size > MAX_EPUB_XML_MEMBER_BYTES:
                    raise ValueError(f"EPUB XHTML member exceeds size limit: {name}")
                original = source.read(info)
                fixed = _repair_xhtml_bytes(original)
                if fixed is None:
                    payloads[name] = original
                else:
                    payloads[name] = fixed
                    repaired.append(name)
            if not repaired:
                return []
            with tempfile.NamedTemporaryFile(
                prefix=f".{epub_path.name}.",
                suffix=".sanitize",
                dir=epub_path.parent,
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
            with zipfile.ZipFile(temporary_path, "w") as destination:
                destination.comment = source.comment
                for info in source.infolist():
                    if info.filename in payloads:
                        payload: bytes = payloads[info.filename]
                    else:
                        payload = source.read(info)
                    destination.writestr(info, payload)
        assert temporary_path is not None
        temporary_path.chmod(original_mode)
        os.replace(temporary_path, epub_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    logger.info("  Sanitized %d malformed EPUB XHTML member(s): %s", len(repaired), ", ".join(sorted(repaired)))
    return sorted(repaired)


__all__ = ["sanitize_epub_xhtml"]

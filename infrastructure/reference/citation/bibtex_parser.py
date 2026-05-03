"""Minimal hand-rolled BibTeX parser.

We deliberately avoid the heavyweight ``bibtexparser`` dependency: the only
dialects we need to read are (a) what our own writer emits and (b) the
exemplar ``projects/template_code_project/manuscript/references.bib`` style. Both are
covered by a simple state machine that:

* Skips ``@comment{...}`` blocks (collected as the database preamble).
* Treats ``@string`` / ``@preamble`` directives as pass-through (we record the
  raw text but do not expand string concatenations).
* Reads ``@type{key, field = value, ...}`` records, where ``value`` is either
  ``{braced text}`` (with balanced nesting) or ``"quoted text"`` or a bare
  numeric literal.

The parser is forgiving about whitespace, trailing commas, and unknown entry
types — the goal is round-tripping, not strict validation.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from infrastructure.reference.citation.escape import unescape_latex
from infrastructure.reference.citation.models import BibDatabase, BibEntry


class BibParseError(ValueError):
    """Raised when the parser encounters a malformed BibTeX construct."""


_VERBATIM_FIELDS: frozenset[str] = frozenset(
    {"year", "volume", "number", "month", "edition", "isbn", "issn", "doi", "url"}
)


class _Reader:
    __slots__ = ("text", "pos")

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.text)

    def peek(self) -> str:
        return self.text[self.pos] if not self.eof() else ""

    def advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def skip_ws_and_comments(self) -> None:
        while not self.eof():
            ch = self.peek()
            if ch.isspace():
                self.pos += 1
                continue
            if ch == "%":  # line comment (BibTeX-style)
                while not self.eof() and self.peek() != "\n":
                    self.pos += 1
                continue
            break

    def expect(self, ch: str) -> None:
        if self.eof() or self.peek() != ch:
            ctx = self.text[max(0, self.pos - 20) : self.pos + 20]
            raise BibParseError(f"Expected {ch!r} at pos {self.pos} near: …{ctx}…")
        self.pos += 1

    def read_identifier(self) -> str:
        start = self.pos
        while not self.eof():
            ch = self.peek()
            if ch.isalnum() or ch in "_-:.+/'":
                self.pos += 1
            else:
                break
        if start == self.pos:
            return ""
        return self.text[start : self.pos]

    def read_braced(self) -> str:
        """Read a ``{...}`` value with balanced brace nesting."""
        self.expect("{")
        depth = 1
        start = self.pos
        while not self.eof() and depth > 0:
            ch = self.advance()
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return self.text[start : self.pos - 1]
        raise BibParseError(f"Unterminated braced value starting at pos {start}")

    def read_quoted(self) -> str:
        self.expect('"')
        start = self.pos
        while not self.eof():
            ch = self.advance()
            if ch == "\\" and not self.eof():  # escape next char
                self.pos += 1
                continue
            if ch == '"':
                return self.text[start : self.pos - 1]
        raise BibParseError(f"Unterminated quoted value starting at pos {start}")

    def read_number(self) -> str:
        start = self.pos
        while not self.eof() and self.peek().isdigit():
            self.pos += 1
        return self.text[start : self.pos]


def _parse_value(reader: _Reader) -> str:
    reader.skip_ws_and_comments()
    if reader.eof():
        raise BibParseError("Unexpected EOF while reading field value")
    ch = reader.peek()
    if ch == "{":
        return reader.read_braced()
    if ch == '"':
        return reader.read_quoted()
    if ch.isdigit():
        return reader.read_number()
    # Bare identifier (e.g. @string macro). Read greedily; do not expand.
    ident = reader.read_identifier()
    if not ident:
        raise BibParseError(f"Unrecognised value at pos {reader.pos}")
    return ident


def _parse_entry(reader: _Reader) -> BibEntry | tuple[str, str] | None:
    """Parse one ``@…{…}`` block.

    Returns:
        BibEntry for normal entries, ``("comment", text)`` for ``@comment``
        blocks, ``("string", text)`` / ``("preamble", text)`` for those
        directives, or ``None`` if EOF is reached before another ``@``.
    """
    reader.skip_ws_and_comments()
    if reader.eof():
        return None
    if reader.peek() != "@":
        # Skip stray text between entries (BibTeX permits free-form text).
        while not reader.eof() and reader.peek() != "@":
            reader.pos += 1
        if reader.eof():
            return None
    reader.expect("@")
    type_name = reader.read_identifier().lower()
    if not type_name:
        raise BibParseError(f"Missing entry type at pos {reader.pos}")
    reader.skip_ws_and_comments()

    if type_name == "comment":
        # ``@comment{...}`` — capture body verbatim.
        if reader.peek() == "{":
            body = reader.read_braced()
            return ("comment", body.strip("\n"))
        # Or ``@comment ...`` to end-of-line; treat as pass-through.
        start = reader.pos
        while not reader.eof() and reader.peek() != "\n":
            reader.pos += 1
        return ("comment", reader.text[start : reader.pos].strip())

    if type_name in {"string", "preamble"}:
        if reader.peek() == "{":
            body = reader.read_braced()
        elif reader.peek() == "(":
            reader.advance()
            depth = 1
            start = reader.pos
            while not reader.eof() and depth > 0:
                ch = reader.advance()
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
            body = reader.text[start : reader.pos - 1]
        else:
            body = ""
        return (type_name, body.strip())

    # Normal entry: @type{key, field = value, ...}
    if reader.peek() == "(":
        # Some BibTeX dialects allow parens.
        reader.advance()
        closer = ")"
    else:
        reader.expect("{")
        closer = "}"

    reader.skip_ws_and_comments()
    citation_key = reader.read_identifier()
    if not citation_key:
        raise BibParseError(f"Missing citation key at pos {reader.pos}")

    fields: "OrderedDict[str, str]" = OrderedDict()
    reader.skip_ws_and_comments()
    while not reader.eof() and reader.peek() == ",":
        reader.advance()  # consume comma
        reader.skip_ws_and_comments()
        if reader.eof() or reader.peek() == closer:
            break
        field_name = reader.read_identifier()
        if not field_name:
            raise BibParseError(f"Expected field name at pos {reader.pos}")
        reader.skip_ws_and_comments()
        reader.expect("=")
        value = _parse_value(reader)
        if field_name.lower() not in _VERBATIM_FIELDS:
            value = unescape_latex(value)
        fields[field_name] = value
        reader.skip_ws_and_comments()

    reader.skip_ws_and_comments()
    if not reader.eof() and reader.peek() == closer:
        reader.advance()
    return BibEntry(entry_type=type_name, citation_key=citation_key, fields=fields)


def parse_bibtex(text: str) -> BibDatabase:
    """Parse *text* into a :class:`BibDatabase`.

    Comment blocks are concatenated into the database's preamble (joined with
    blank lines) so that round-tripping preserves provenance notes such as
    the one at the top of ``projects/template_code_project/manuscript/references.bib``.
    """
    reader = _Reader(text)
    db = BibDatabase()
    comments: list[str] = []
    while True:
        result = _parse_entry(reader)
        if result is None:
            break
        if isinstance(result, BibEntry):
            db.add(result)
        elif isinstance(result, tuple) and result[0] == "comment":
            comments.append(result[1])
        # @string / @preamble are silently dropped — we don't need them.
    if comments:
        db.preamble = "\n\n".join(c.strip() for c in comments if c.strip())
    return db


def parse_bibfile(path: Path | str, *, encoding: str = "utf-8") -> BibDatabase:
    """Read and parse a ``.bib`` file from *path*."""
    return parse_bibtex(Path(path).read_text(encoding=encoding))

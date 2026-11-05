"""Safe-width normalization for accessible Beamer tables emitted by Pandoc."""

from __future__ import annotations

import re

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH


_TABLE_MARKER = "% template-accessible-table-inset"
_LONGTABLE_BEGIN_RE = re.compile(r"\\begin\{longtable\}")
_LONGTABLE_END_RE = re.compile(r"\\end\{longtable\}")
_FIRST_TABLE_RULE_RE = re.compile(r"^[ \t]*\\(?:toprule|hline)\b", flags=re.MULTILINE)
_VERBATIM_ENVIRONMENT_RE = re.compile(
    r"\\begin\{(?P<environment>verbatim\*?|Verbatim|lstlisting|minted)\}.*?"
    r"\\end\{(?P=environment)\}",
    flags=re.DOTALL,
)
_INLINE_VERB_RE = re.compile(r"\\verb\*?(?P<delimiter>[^\w\s]).*?(?P=delimiter)", flags=re.DOTALL)


def _commented_at(text: str, position: int) -> bool:
    """Return whether one TeX token follows an unescaped percent on its line."""

    line_start = text.rfind("\n", 0, position) + 1
    for index in range(line_start, position):
        if text[index] != "%":
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= line_start and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return True
    return False


def _protected_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Return verbatim spans whose literal examples must remain byte-identical."""

    spans = [
        *(match.span() for match in _VERBATIM_ENVIRONMENT_RE.finditer(text)),
        *(match.span() for match in _INLINE_VERB_RE.finditer(text)),
    ]
    return tuple(sorted(spans))


def _inside_spans(position: int, spans: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= position < end for start, end in spans)


def _table_preamble_error(message: str, *, table_index: int) -> RenderingError:
    return RenderingError(
        f"[slides.geometry.table-preamble] {message}",
        context={
            "diagnostic_code": "slides.geometry.table-preamble",
            "table_index": table_index,
        },
        suggestions=[
            "Render semantic Markdown tables through the accessible Pandoc-AST path.",
            "Keep complete or unusually structured tables in the linked canonical HTML manuscript.",
        ],
    )


def inset_accessible_longtables(tex_content: str) -> tuple[str, int]:
    r"""Confine each generated ``longtable`` to the frame body width.

    Pandoc evaluates a table's ``\linewidth`` after ``longtable`` has reset it
    to the projection canvas.  At the start of a generated continuation frame,
    Beamer can also leave the pre-environment ``\linewidth`` at ``\paperwidth``
    until a preceding body paragraph or anchor establishes paragraph geometry.
    ``\textwidth`` remains the stable frame-body width in both contexts, so the
    owned table length is captured from it instead.  Only the generated column
    preamble is rewritten; cell-local ``\linewidth`` values (notably Pandoc's
    header minipages) remain local to their columns.  Archive rendering does
    not call this opt-in transform.
    """

    pieces: list[str] = []
    cursor = 0
    changed = 0
    table_index = 0
    protected = _protected_spans(tex_content)
    for begin in _LONGTABLE_BEGIN_RE.finditer(tex_content):
        if (
            begin.start() < cursor
            or _inside_spans(begin.start(), protected)
            or _commented_at(tex_content, begin.start())
        ):
            continue
        table_index += 1
        end = _LONGTABLE_END_RE.search(tex_content, begin.end())
        if end is None or _inside_spans(end.start(), protected) or _commented_at(tex_content, end.start()):
            raise _table_preamble_error("accessible longtable has no matching visible end", table_index=table_index)

        body = tex_content[begin.end() : end.start()]
        first_rule = _FIRST_TABLE_RULE_RE.search(body)
        if first_rule is None:
            raise _table_preamble_error(
                "accessible longtable has no generated top-rule boundary",
                table_index=table_index,
            )
        preamble = body[: first_rule.start()]
        prior = tex_content[max(cursor, begin.start() - 320) : begin.start()]
        if ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH in preamble:
            if _TABLE_MARKER not in prior:
                raise _table_preamble_error(
                    "accessible table width macro appeared outside the owned normalization wrapper",
                    table_index=table_index,
                )
            pieces.append(tex_content[cursor : end.end()])
            cursor = end.end()
            continue
        if r"\linewidth" not in preamble:
            raise _table_preamble_error(
                "accessible longtable column preamble does not expose a frame-width expression",
                table_index=table_index,
            )

        normalized_preamble = preamble.replace(r"\linewidth", ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH)
        normalized_body = normalized_preamble + body[first_rule.start() :]
        pieces.extend(
            (
                tex_content[cursor : begin.start()],
                _TABLE_MARKER + "\n",
                "\\begingroup\n",
                f"\\setlength{{{ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH}}}{{\\textwidth}}%\n",
                "\\setlength{\\LTleft}{\\fill}%\n",
                "\\setlength{\\LTright}{\\fill}%\n",
                begin.group(0),
                normalized_body,
                end.group(0),
                "\n\\endgroup",
            )
        )
        cursor = end.end()
        changed += 1
    pieces.append(tex_content[cursor:])
    return "".join(pieces), changed


__all__ = ["inset_accessible_longtables"]

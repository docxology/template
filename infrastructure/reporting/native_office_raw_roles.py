"""Independent finite source roles for native Office raw occurrences.

Only exact syntax observed in the configured native source lanes is admitted.
Visible prose, equations and unknown raw syntax can never become comments.
Only a single complete HTML comment ending at its first ``-->`` or ``--!>``
terminator is nonvisible; empty-abrupt openings and trailing raw content remain
unsupported.
"""

from __future__ import annotations

import re
from typing import Any

from infrastructure.reporting.native_office_source_coverage import scientific_source_occurrences

_COMPACT = (
    "\\thispagestyle{empty}\n\\setlength{\\parskip}{0pt}\n\\setlength{\\itemsep}{0pt}\n\\begin{samepage}\n\\scriptsize"
)
_END_BEGIN = "% transmission-end-bookend\n\\clearpage\n" + _COMPACT


def _html_comment_body(text: str) -> str | None:
    """Return only one complete comment, ending at its first closing token."""
    if not text.startswith("<!--") or text.startswith(("<!-->", "<!--->")):
        return None
    ending = min(
        ((offset, marker) for marker in ("-->", "--!>") if (offset := text.find(marker, 4)) >= 0),
        default=None,
    )
    if ending is None or ending[0] + len(ending[1]) != len(text):
        return None
    return text[4 : ending[0]]


def office_raw_source_roles(ast: bytes) -> tuple[dict[str, Any], ...]:
    """Classify each raw occurrence without excusing source content loss."""
    import json

    roles = []
    for occurrence in scientific_source_occurrences(ast):
        if occurrence.kind not in {"RawBlock", "RawInline"}:
            continue
        raw = json.loads(occurrence.content_json)
        role: dict[str, Any] = {
            "source_occurrence": occurrence.ordinal,
            "content_sha256": occurrence.content_sha256,
            "kind": "unsupported",
        }
        if isinstance(raw, list) and len(raw) == 2 and all(isinstance(value, str) for value in raw):
            format_name, text = raw
            text = text.strip()
            comment = _html_comment_body(text) if format_name == "html" else None
            if comment is not None:
                description = re.fullmatch(r"\s*alt:\s*(.*?)\s*", comment, re.DOTALL)
                role.update(
                    kind="image-alternative" if description else "nonvisible-comment",
                    text=" ".join(description[1].split()) if description else text,
                )
            elif format_name in {"tex", "latex"}:
                equation = re.fullmatch(
                    r"\\begin\{equation\}\s*\\label\{([\w:_-]+)\}\s*(.*?)\s*\\end\{equation\}", text, re.DOTALL
                )
                heading = re.fullmatch(
                    r"\\(section|subsection|subsubsection)\*\{([^{}]+)\}(?:\\label\{([\w:_-]+)\})?", text
                )
                if equation and "\\label" not in equation[2] and "\\begin{equation}" not in equation[2]:
                    role.update(kind="equation", label=equation[1], expression=equation[2])
                elif heading:
                    role.update(
                        kind="heading",
                        level={"section": 1, "subsection": 2, "subsubsection": 3}[heading[1]],
                        text=heading[2],
                        label=heading[3] or "",
                    )
                elif text in {"\\newpage", "\\clearpage"}:
                    role.update(kind="page-break", count=1)
                elif text in {_COMPACT, _END_BEGIN}:
                    role.update(
                        kind="compact-start",
                        page_breaks=int(text == _END_BEGIN),
                        size_half_points=14,
                        zero_spacing=True,
                        keep_together=True,
                        empty_page_style=True,
                    )
                elif text in {"\\end{samepage}", "\\end{samepage}\n\\newpage"}:
                    role.update(kind="compact-end", page_breaks=int(text.endswith("\\newpage")))
        roles.append(role)
    return tuple(roles)

"""Pandoc conversion pitfall checks for markdown manuscripts."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
from infrastructure.validation.content.diagnostic_codes import MarkdownCode
from infrastructure.validation.content.markdown_strip import strip_code_and_math

PANDOC_BARE_PIPE_PATTERN = re.compile(r"(?<![\\$`])\|(\w+)\|(?![$`])")
PANDOC_TABLE_ESCAPED_PIPE_PATTERN = re.compile(r"\\\|")

NON_RENDERED_MANUSCRIPT_FILES: frozenset[str] = frozenset({"AGENTS.md", "README.md", "preamble.md"})


def validate_pandoc_pitfalls(md_paths: list[str], repo_root: str | Path) -> list[DiagnosticEvent]:
    """Flag markdown patterns Pandoc converts to LaTeX ``\\mid`` in text mode."""
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []

    for path in md_paths:
        path_obj = Path(path)
        if path_obj.name in NON_RENDERED_MANUSCRIPT_FILES:
            continue
        text = path_obj.read_text(encoding="utf-8")
        try:
            rel: str | Path = path_obj.relative_to(repo_root_path)
        except ValueError:
            rel = path_obj
        rel_str = str(rel)

        prose = strip_code_and_math(text)
        for m in PANDOC_BARE_PIPE_PATTERN.finditer(prose):
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_PANDOC_MID",
                    message=(
                        f"Bare pipe pattern '|{m.group(1)}|' in prose will be "
                        f"converted by Pandoc to '\\mid {m.group(1)}\\mid{{}}', "
                        "which fails to render U+2223 in text mode."
                    ),
                    code=MarkdownCode.PANDOC_BARE_PIPE,
                    file_path=rel_str,
                    fix_suggestion=(
                        f"Wrap the span in inline math (e.g. '$|{m.group(1)}|$' "
                        f"or '${{|}}{m.group(1)}{{|}}$') so the macro renders "
                        "through the math font."
                    ),
                )
            )

        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if not stripped.startswith("|"):
                continue
            line_no_math = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)", "", line)
            line_no_math = re.sub(r"`[^`]+`", "", line_no_math)
            if not PANDOC_TABLE_ESCAPED_PIPE_PATTERN.search(line_no_math):
                continue
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_PANDOC_MID",
                    message=(
                        f"Escaped pipe '\\|' in table cell (line {line_no}) "
                        "is rendered by Pandoc as '\\mid', which fails to "
                        "render U+2223 in text mode."
                    ),
                    code=MarkdownCode.PANDOC_TABLE_ESCAPED_PIPE,
                    file_path=rel_str,
                    fix_suggestion=(
                        "Replace the cell content with inline math, e.g. '$P(\\text{A} \\mid \\text{B})$'."
                    ),
                )
            )
    return problems

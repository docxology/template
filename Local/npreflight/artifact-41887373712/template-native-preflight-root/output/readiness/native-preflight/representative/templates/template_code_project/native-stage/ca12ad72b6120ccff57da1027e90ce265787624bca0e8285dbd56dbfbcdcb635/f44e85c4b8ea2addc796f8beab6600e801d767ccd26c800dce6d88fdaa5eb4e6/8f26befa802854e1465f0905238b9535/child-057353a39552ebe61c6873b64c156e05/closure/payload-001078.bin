"""Markdown mathematical equation validation."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
from infrastructure.validation.content.diagnostic_codes import MarkdownCode
from infrastructure.validation.content.markdown_strip import strip_markdown_code_regions
from infrastructure.validation.content.validator_refs import text_without_fenced_code


def _has_invalid_dollar_display_math(text: str) -> bool:
    """Return true for inline, nested, or unbalanced ``$$`` delimiters."""
    text = strip_markdown_code_regions(text)
    open_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if "$$" not in stripped:
            continue

        delimiter_count = stripped.count("$$")
        if stripped == "$$" or re.fullmatch(r"\$\$\s+\{#eq:[A-Za-z0-9_-]+(?:\s+[^}]*)?\}", stripped):
            open_block = not open_block
            continue

        if (
            not open_block
            and delimiter_count == 2
            and stripped.startswith("$$")
            and stripped.endswith("$$")
            and stripped[2:-2].strip()
        ):
            continue

        return True
    return open_block


def validate_math(md_paths: list[str], repo_root: str | Path) -> list[DiagnosticEvent]:
    """Validate mathematical equation formatting and labeling."""
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []
    eq_block = re.compile(r"\\begin\{equation\}([\s\S]*?)\\end\{equation\}", re.MULTILINE)
    label_pattern = re.compile(r"\\label\{([^}]+)\}")
    seen_labels: set[str] = set()
    for path in md_paths:
        text = Path(path).read_text(encoding="utf-8")
        try:
            rel: str | Path = Path(path).relative_to(repo_root_path)
        except ValueError:
            rel = path

        rel_str = str(rel)

        if _has_invalid_dollar_display_math(text):
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_MATH",
                    message="Use isolated $$ display blocks; inline or unbalanced $$ is not allowed",
                    code=MarkdownCode.MATH_DOLLAR_DISPLAY,
                    file_path=rel_str,
                    fix_suggestion=("Put display math on its own line(s), for example $$x = y$$ or a paired $$ block."),
                )
            )
        if "\\[" in text or "\\]" in text:
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_MATH",
                    message="Use equation environment instead of \\[ \\]",
                    code=MarkdownCode.MATH_BRACKET_DISPLAY,
                    file_path=rel_str,
                    fix_suggestion="Replace \\[...\\] with \\begin{equation}...\\end{equation}",
                )
            )
        _eq_scan_text = re.sub(r"`+[^`\n]*`+", "", text_without_fenced_code(text))
        for m in eq_block.finditer(_eq_scan_text):
            block = m.group(1)
            labels_in_block = label_pattern.findall(block)
            if not labels_in_block:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.WARNING,
                        category="MARKDOWN_MATH",
                        message="Equation missing \\label{...}",
                        code=MarkdownCode.MATH_LABEL_MISSING,
                        file_path=rel_str,
                        fix_suggestion="Add a \\label{eq_name} inside the \\begin{equation} block.",
                    )
                )
            else:
                for lab in labels_in_block:
                    if lab in seen_labels:
                        problems.append(
                            DiagnosticEvent(
                                severity=DiagnosticSeverity.ERROR,
                                category="MARKDOWN_MATH",
                                message=f"Duplicate equation label '{{{lab}}}' found",
                                code=MarkdownCode.MATH_LABEL_DUPLICATE,
                                file_path=rel_str,
                                fix_suggestion="Rename one of the labels to be unique.",
                            )
                        )
                    seen_labels.add(lab)
    return problems

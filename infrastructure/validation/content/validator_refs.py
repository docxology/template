"""Markdown cross-reference and link validation."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
from infrastructure.validation.content.diagnostic_codes import MarkdownCode
from infrastructure.validation.content.markdown_strip import strip_fences

EQ_REF_PATTERN = re.compile(r"\\eqref\{([^}]+)\}")
INTERNAL_LINK_PATTERN = re.compile(r"\(#([^\)]+)\)")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
BARE_URL_PATTERN = re.compile(r"(?<!\]\()https?://\S+")


def text_without_fenced_code(text: str) -> str:
    """Remove triple-backtick and tilde-fenced code blocks."""
    return strip_fences(text)


def validate_refs(
    md_paths: list[str], repo_root: str | Path, labels: set[str], anchors: set[str]
) -> list[DiagnosticEvent]:
    """Validate cross-references, internal links, and external URLs."""
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []
    for path in md_paths:
        text = Path(path).read_text(encoding="utf-8")
        try:
            rel: str | Path = Path(path).relative_to(repo_root_path)
        except ValueError:
            rel = path

        rel_str = str(rel)
        text_wo_fences = text_without_fenced_code(text)
        for ref in EQ_REF_PATTERN.findall(text_wo_fences):
            if ref not in labels:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.ERROR,
                        category="MARKDOWN_REF",
                        message=f"Missing equation label for \\eqref{{{ref}}}",
                        code=MarkdownCode.REF_EQUATION_MISSING,
                        file_path=rel_str,
                        fix_suggestion=f"Verify that '\\label{{{ref}}}' exists in an equation block.",
                    )
                )
        for link in INTERNAL_LINK_PATTERN.findall(text_wo_fences):
            if link not in anchors and link not in labels:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.ERROR,
                        category="MARKDOWN_LINK",
                        message=f"Missing anchor/label for internal link (#{link})",
                        code=MarkdownCode.LINK_ANCHOR_MISSING,
                        file_path=rel_str,
                        fix_suggestion=f"Provide a heading anchor '{{#{link}}}' or equation label.",
                    )
                )
        text_no_code = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
        text_no_code = re.sub(r"`[^`]+`", "", text_no_code)
        for m in BARE_URL_PATTERN.finditer(text_no_code):
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_LINK",
                    message=f"Bare URL found: '{m.group(0)}'",
                    code=MarkdownCode.LINK_BARE_URL,
                    file_path=rel_str,
                    fix_suggestion="Wrap the URL in a Markdown link with informative text: [link text](url)",
                )
            )
        for m in LINK_PATTERN.finditer(text):
            label = m.group(1).strip()
            url = m.group(2).strip()
            if label == url or label.lower().startswith("http") or "/" in label:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.WARNING,
                        category="MARKDOWN_LINK",
                        message=f"Non-informative link text for {url}",
                        code=MarkdownCode.LINK_BAD_TEXT,
                        file_path=rel_str,
                        fix_suggestion=f"Replace '{label}' with descriptive text about the link destination.",
                    )
                )
    return problems

"""Shared markdown stripping helpers for content validators."""

from __future__ import annotations

import re


def strip_fences(text: str) -> str:
    """Remove triple-backtick and tilde-fenced code blocks."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"~~~[\s\S]*?~~~", "", text)
    return text


def strip_inline_code(text: str) -> str:
    """Remove inline code spans and indented code blocks."""
    text = re.sub(r"`[^`\n]+`", "", text)
    text = re.sub(
        r"(?:\A|\n)(?:[ ]{4,}|\t)[^\n]*(?:\n(?:[ ]{4,}|\t)[^\n]*)*",
        "\n",
        text,
    )
    return text


def strip_math(text: str) -> str:
    """Remove common LaTeX and dollar-delimited math regions."""
    text = re.sub(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}[\s\S]*?\\end\{\1\}", "", text)
    text = re.sub(r"\\\([\s\S]*?\\\)", "", text)
    text = re.sub(r"\\\[[\s\S]*?\\\]", "", text)
    text = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)", "", text)
    return text


def strip_markdown_code_regions(text: str) -> str:
    """Remove fenced and inline code before style-scanning prose/math."""
    return strip_inline_code(strip_fences(text))


def strip_code_and_math(text: str) -> str:
    """Remove code and math regions before pitfall/citation scans."""
    return strip_math(strip_markdown_code_regions(text))


__all__ = [
    "strip_code_and_math",
    "strip_fences",
    "strip_inline_code",
    "strip_markdown_code_regions",
    "strip_math",
]

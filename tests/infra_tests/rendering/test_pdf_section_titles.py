"""Tests for PDF section-title bookmark sanitization."""

from __future__ import annotations

from infrastructure.rendering._pdf_section_titles import sanitize_texorpdfstring


def test_sanitize_texorpdfstring_rewrites_bookmark_only() -> None:
    source = r"\section{\texorpdfstring{$F[q_\lambda]$}{F\textbackslash{}[q\_\lambda\]}}"

    result, count = sanitize_texorpdfstring(source)

    assert count == 1
    assert r"\texorpdfstring{$F[q_\lambda]$}" in result
    assert r"\textbackslash" not in result
    assert r"\_" not in result


def test_sanitize_texorpdfstring_strips_remaining_latex_macros() -> None:
    source = r"\subsection{\texorpdfstring{\textit{Expected Free Energy}}{\textit{Expected} \alpha}}"

    result, count = sanitize_texorpdfstring(source)

    assert count == 1
    assert r"{\textit{Expected Free Energy}}" in result
    assert "{Expected alpha}" in result


def test_sanitize_texorpdfstring_reports_zero_when_already_plain() -> None:
    source = r"\section{\texorpdfstring{Visible}{Plain bookmark}}"

    result, count = sanitize_texorpdfstring(source)

    assert result == source
    assert count == 0

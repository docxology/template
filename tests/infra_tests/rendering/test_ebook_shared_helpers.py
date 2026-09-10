"""Shared DOCX/EPUB/MOBI helper-function edge-case tests (split from test_docx_epub_fallbacks.py)."""

from __future__ import annotations


class TestSharedHelperFunctions:
    """Tests for _truncate_error_context and _process_output_text helpers.

    These helpers are duplicated across docx_renderer, epub_renderer, and
    mobi_renderer. The existing per-module test files cover them individually;
    here we verify they behave identically across modules (shared contract).
    """

    def test_truncate_error_context_empty_all_modules(self) -> None:
        """All three modules return the same placeholder for empty input."""
        from infrastructure.rendering.docx_renderer import _truncate_error_context as docx_trunc
        from infrastructure.rendering.epub_renderer import _truncate_error_context as epub_trunc
        from infrastructure.rendering.mobi_renderer import _truncate_error_context as mobi_trunc

        for func in (docx_trunc, epub_trunc, mobi_trunc):
            assert func("") == "no stderr captured"
            assert func("   ") == "no stderr captured"

    def test_truncate_error_context_long_all_modules(self) -> None:
        """All three modules truncate to 500 characters."""
        from infrastructure.rendering.docx_renderer import _truncate_error_context as docx_trunc
        from infrastructure.rendering.epub_renderer import _truncate_error_context as epub_trunc
        from infrastructure.rendering.mobi_renderer import _truncate_error_context as mobi_trunc

        long_text = "x" * 600
        for func in (docx_trunc, epub_trunc, mobi_trunc):
            result = func(long_text)
            assert len(result) == 500

    def test_process_output_text_none_all_modules(self) -> None:
        """All three modules return empty string for None input."""
        from infrastructure.rendering.docx_renderer import _process_output_text as docx_proc
        from infrastructure.rendering.epub_renderer import _process_output_text as epub_proc
        from infrastructure.rendering.mobi_renderer import _process_output_text as mobi_proc

        for func in (docx_proc, epub_proc, mobi_proc):
            assert func(None) == ""

    def test_process_output_text_bytes_all_modules(self) -> None:
        """All three modules decode bytes to string."""
        from infrastructure.rendering.docx_renderer import _process_output_text as docx_proc
        from infrastructure.rendering.epub_renderer import _process_output_text as epub_proc
        from infrastructure.rendering.mobi_renderer import _process_output_text as mobi_proc

        for func in (docx_proc, epub_proc, mobi_proc):
            assert func(b"hello") == "hello"

    def test_process_output_text_invalid_utf8_all_modules(self) -> None:
        """All three modules use errors='replace' for invalid UTF-8."""
        from infrastructure.rendering.docx_renderer import _process_output_text as docx_proc
        from infrastructure.rendering.epub_renderer import _process_output_text as epub_proc
        from infrastructure.rendering.mobi_renderer import _process_output_text as mobi_proc

        for func in (docx_proc, epub_proc, mobi_proc):
            result = func(b"\xff\xfe")
            assert isinstance(result, str)
            assert len(result) > 0

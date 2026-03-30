"""Tests for infrastructure/documentation/generate_glossary_cli.py.

Tests glossary CLI generation utilities using real files.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.documentation.generate_glossary_cli import _ensure_glossary_file


class TestEnsureGlossaryFile:
    """Test _ensure_glossary_file helper."""

    def test_creates_file_when_missing(self, tmp_path):
        """Test that _ensure_glossary_file creates a glossary file when it doesn't exist."""
        glossary_path = tmp_path / "manuscript" / "98_symbols_glossary.md"

        _ensure_glossary_file(glossary_path)

        assert glossary_path.exists()
        content = glossary_path.read_text(encoding="utf-8")
        assert "# API Symbols Glossary" in content
        assert "<!-- BEGIN: AUTO-API-GLOSSARY -->" in content
        assert "<!-- END: AUTO-API-GLOSSARY -->" in content

    def test_does_not_overwrite_existing_file(self, tmp_path):
        """Test that _ensure_glossary_file does NOT overwrite an existing file."""
        glossary_path = tmp_path / "existing_glossary.md"
        original_content = "# My Custom Glossary\n\nCustom content.\n"
        glossary_path.write_text(original_content, encoding="utf-8")

        _ensure_glossary_file(glossary_path)

        # File content should be unchanged
        assert glossary_path.read_text(encoding="utf-8") == original_content

    def test_creates_parent_directories(self, tmp_path):
        """Test that _ensure_glossary_file creates parent directories if needed."""
        deep_path = tmp_path / "a" / "b" / "c" / "glossary.md"

        _ensure_glossary_file(deep_path)

        assert deep_path.exists()
        assert deep_path.parent.exists()

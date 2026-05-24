"""Tests for infrastructure/documentation/generate_glossary_cli.py.

Tests glossary CLI generation utilities using real files.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

from infrastructure.documentation.generate_glossary_cli import (
    _ensure_glossary_file,
    _repo_root,
    main,
)


class TestRepoRoot:
    """Test _repo_root helper."""

    def test_returns_path(self):
        """Should return a Path object."""
        result = _repo_root()
        assert isinstance(result, Path)


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

        assert glossary_path.read_text(encoding="utf-8") == original_content

    def test_creates_parent_directories(self, tmp_path):
        """Test that _ensure_glossary_file creates parent directories if needed."""
        deep_path = tmp_path / "a" / "b" / "c" / "glossary.md"

        _ensure_glossary_file(deep_path)

        assert deep_path.exists()
        assert deep_path.parent.exists()


class TestMainFunction:
    """Test main function with real args."""

    def test_main_with_custom_args(self, tmp_path):
        """Should run main with src_dir and glossary_md args."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def hello():\n    pass\n")

        glossary = tmp_path / "manuscript" / "glossary.md"
        glossary.parent.mkdir(parents=True)

        old_argv = sys.argv
        try:
            sys.argv = ["generate_glossary_cli.py", str(src_dir), str(glossary)]
            result = main()
            assert result == 0
            assert glossary.exists()
        finally:
            sys.argv = old_argv

    def test_main_with_no_args_uses_defaults(self):
        """Should run main with default args (may use repo structure)."""
        old_argv = sys.argv
        try:
            sys.argv = ["generate_glossary_cli.py"]
            result = main()
            assert result == 0
        finally:
            sys.argv = old_argv

    def test_main_with_empty_src(self, tmp_path):
        """Should handle empty src directory."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        glossary = tmp_path / "glossary.md"

        old_argv = sys.argv
        try:
            sys.argv = ["generate_glossary_cli.py", str(src_dir), str(glossary)]
            result = main()
            assert result == 0
        finally:
            sys.argv = old_argv

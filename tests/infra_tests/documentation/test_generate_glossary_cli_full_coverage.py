"""Tests for infrastructure/documentation/generate_glossary_cli.py.

Covers: _ensure_glossary_file, main, _repo_root.

No mocks used — all tests use real files and real function calls.
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
    """Test _ensure_glossary_file creation."""

    def test_creates_new_file(self, tmp_path):
        """Should create glossary file when it doesn't exist."""
        glossary = tmp_path / "glossary.md"
        _ensure_glossary_file(glossary)
        assert glossary.exists()
        content = glossary.read_text()
        assert "API Symbols Glossary" in content
        assert "AUTO-API-GLOSSARY" in content

    def test_skips_existing_file(self, tmp_path):
        """Should not overwrite existing file."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text("existing content")
        _ensure_glossary_file(glossary)
        assert glossary.read_text() == "existing content"

    def test_creates_parent_dirs(self, tmp_path):
        """Should create parent directories."""
        glossary = tmp_path / "nested" / "deep" / "glossary.md"
        _ensure_glossary_file(glossary)
        assert glossary.exists()


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

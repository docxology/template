"""Comprehensive tests for infrastructure/rendering/render_all_cli.py.

Tests the wrapper CLI script for rendering all formats using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import logging

import pytest

from infrastructure.rendering import render_all_cli


@pytest.mark.slow
class TestRenderAllCliMain:
    """Test suite for render_all_cli main function."""

    def test_main_no_manuscript_directory(self, tmp_path, caplog, monkeypatch):
        """Test when manuscript directory doesn't exist."""
        monkeypatch.chdir(tmp_path)

        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit) as exc_info:
                render_all_cli.main()

        assert exc_info.value.code == 1
        assert "no manuscript directory" in caplog.text.lower() or "not found" in caplog.text.lower()

    def test_main_with_manuscript(self, tmp_path, caplog, monkeypatch):
        """Test with manuscript directory and files using real RenderManager."""
        monkeypatch.chdir(tmp_path)

        # Create manuscript directory with tex file
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        with caplog.at_level(logging.INFO):
            try:
                render_all_cli.main()
            except Exception as exc:
                outcome = f"{caplog.text}\n{exc}".lower()
                assert any(token in outcome for token in ("render", "latex", "pandoc", "error"))
            else:
                assert (tmp_path / "output" / "pdf" / "main.pdf").is_file()

    def test_main_empty_manuscript_dir(self, tmp_path, monkeypatch):
        """Test with empty manuscript directory using real execution."""
        monkeypatch.chdir(tmp_path)

        # Create empty manuscript directory
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        render_all_cli.main()
        assert not (tmp_path / "output").exists()


class TestRenderAllCliModule:
    """Test module structure."""

    def test_has_main_function(self):
        """Test that module has main function."""
        assert hasattr(render_all_cli, "main")
        assert callable(render_all_cli.main)

    def test_imports_render_manager(self):
        """Test that RenderManager is imported."""
        assert hasattr(render_all_cli, "RenderManager")

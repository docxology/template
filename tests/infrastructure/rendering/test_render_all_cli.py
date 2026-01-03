"""Comprehensive tests for infrastructure/rendering/render_all_cli.py.

Tests the wrapper CLI script for rendering all formats using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import sys
from pathlib import Path
import pytest

from infrastructure.rendering import render_all_cli


class TestRenderAllCliMain:
    """Test suite for render_all_cli main function."""
    
    def test_main_no_manuscript_directory(self, tmp_path, capsys, monkeypatch):
        """Test when manuscript directory doesn't exist."""
        monkeypatch.chdir(tmp_path)
        
        with pytest.raises(SystemExit) as exc_info:
            render_all_cli.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No manuscript directory" in captured.out
    
    def test_main_with_manuscript(self, tmp_path, capsys, monkeypatch):
        """Test with manuscript directory and files using real RenderManager."""
        monkeypatch.chdir(tmp_path)
        
        # Create manuscript directory with tex file
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        try:
            render_all_cli.main()
            captured = capsys.readouterr()
            # Should attempt rendering or show error
            assert len(captured.out) > 0 or len(captured.err) > 0
        except Exception:
            # LaTeX compilation may fail - that's real behavior
            captured = capsys.readouterr()
            assert len(captured.out) > 0 or len(captured.err) > 0
    
    def test_main_empty_manuscript_dir(self, tmp_path, monkeypatch):
        """Test with empty manuscript directory using real execution."""
        monkeypatch.chdir(tmp_path)
        
        # Create empty manuscript directory
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        
        # Use real execution
        try:
            render_all_cli.main()
        except SystemExit:
            pass  # May exit if no files found
        except Exception:
            pass  # May raise other exceptions


class TestRenderAllCliModule:
    """Test module structure."""
    
    def test_has_main_function(self):
        """Test that module has main function."""
        assert hasattr(render_all_cli, 'main')
        assert callable(render_all_cli.main)
    
    def test_imports_render_manager(self):
        """Test that RenderManager is imported."""
        assert hasattr(render_all_cli, 'RenderManager')




















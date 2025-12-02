"""Comprehensive tests for infrastructure/rendering/render_all_cli.py.

Tests the wrapper CLI script for rendering all formats.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
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
        """Test with manuscript directory and files."""
        monkeypatch.chdir(tmp_path)
        
        # Create manuscript directory with tex file
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").write_text("\\documentclass{article}")
        
        mock_manager = MagicMock()
        mock_manager.render_all.return_value = [
            tmp_path / "output" / "main.pdf",
            tmp_path / "output" / "main.html"
        ]
        
        with patch.object(render_all_cli, 'RenderManager', return_value=mock_manager):
            render_all_cli.main()
        
        captured = capsys.readouterr()
        assert "Rendering" in captured.out
        mock_manager.render_all.assert_called()
    
    def test_main_empty_manuscript_dir(self, tmp_path, monkeypatch):
        """Test with empty manuscript directory."""
        monkeypatch.chdir(tmp_path)
        
        # Create empty manuscript directory
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        
        mock_manager = MagicMock()
        
        with patch.object(render_all_cli, 'RenderManager', return_value=mock_manager):
            render_all_cli.main()
        
        # Should not call render_all if no tex files
        mock_manager.render_all.assert_not_called()


class TestRenderAllCliModule:
    """Test module structure."""
    
    def test_has_main_function(self):
        """Test that module has main function."""
        assert hasattr(render_all_cli, 'main')
        assert callable(render_all_cli.main)
    
    def test_imports_render_manager(self):
        """Test that RenderManager is imported."""
        assert hasattr(render_all_cli, 'RenderManager')




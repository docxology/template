"""Comprehensive tests for infrastructure/rendering/cli.py.

Tests the CLI interface for rendering operations.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.rendering import cli


class TestRenderPdfCommand:
    """Test suite for render_pdf_command."""
    
    def test_render_pdf_basic(self, tmp_path, capsys):
        """Test basic PDF rendering."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        args = argparse.Namespace(source=str(tex_file))
        
        mock_manager = MagicMock()
        mock_manager.render_pdf.return_value = tmp_path / "output.pdf"
        
        with patch.object(cli, 'RenderManager', return_value=mock_manager):
            cli.render_pdf_command(args)
        
        captured = capsys.readouterr()
        assert "Rendering PDF" in captured.out
        assert "Generated" in captured.out
    
    def test_render_pdf_nonexistent_source(self, tmp_path, capsys):
        """Test PDF rendering with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.tex"))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_pdf_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestRenderAllCommand:
    """Test suite for render_all_command."""
    
    def test_render_all_basic(self, tmp_path, capsys):
        """Test rendering all formats."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        args = argparse.Namespace(source=str(tex_file))
        
        mock_outputs = [
            tmp_path / "output.pdf",
            tmp_path / "output.html",
            tmp_path / "slides.pdf"
        ]
        mock_manager = MagicMock()
        mock_manager.render_all.return_value = mock_outputs
        
        with patch.object(cli, 'RenderManager', return_value=mock_manager):
            cli.render_all_command(args)
        
        captured = capsys.readouterr()
        assert "Rendering all formats" in captured.out
        assert captured.out.count("Generated") >= 3
    
    def test_render_all_nonexistent_source(self, tmp_path, capsys):
        """Test render all with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.tex"))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_all_command(args)
        assert exc_info.value.code == 1


class TestRenderSlidesCommand:
    """Test suite for render_slides_command."""
    
    def test_render_slides_beamer(self, tmp_path, capsys):
        """Test Beamer slide rendering."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide 1\n\n## Content")
        
        args = argparse.Namespace(source=str(md_file), format="beamer")
        
        mock_manager = MagicMock()
        mock_manager.render_slides.return_value = tmp_path / "slides.pdf"
        
        with patch.object(cli, 'RenderManager', return_value=mock_manager):
            cli.render_slides_command(args)
        
        captured = capsys.readouterr()
        assert "beamer" in captured.out
        assert "Generated" in captured.out
    
    def test_render_slides_revealjs(self, tmp_path, capsys):
        """Test reveal.js slide rendering."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide 1")
        
        args = argparse.Namespace(source=str(md_file), format="revealjs")
        
        mock_manager = MagicMock()
        mock_manager.render_slides.return_value = tmp_path / "slides.html"
        
        with patch.object(cli, 'RenderManager', return_value=mock_manager):
            cli.render_slides_command(args)
        
        captured = capsys.readouterr()
        assert "revealjs" in captured.out
    
    def test_render_slides_default_format(self, tmp_path, capsys):
        """Test slides with default format (beamer)."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")
        
        args = argparse.Namespace(source=str(md_file), format=None)
        
        mock_manager = MagicMock()
        mock_manager.render_slides.return_value = tmp_path / "slides.pdf"
        
        with patch.object(cli, 'RenderManager', return_value=mock_manager):
            cli.render_slides_command(args)
        
        mock_manager.render_slides.assert_called_once()
        call_kwargs = mock_manager.render_slides.call_args[1]
        assert call_kwargs['format'] == 'beamer'
    
    def test_render_slides_nonexistent_source(self, tmp_path, capsys):
        """Test slides with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.md"), format="beamer")
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_slides_command(args)
        assert exc_info.value.code == 1


class TestRenderWebCommand:
    """Test suite for render_web_command."""
    
    def test_render_web_basic(self, tmp_path, capsys):
        """Test basic web rendering."""
        md_file = tmp_path / "document.md"
        md_file.write_text("# Document\n\nContent here.")
        
        args = argparse.Namespace(source=str(md_file))
        
        mock_manager = MagicMock()
        mock_manager.render_web.return_value = tmp_path / "document.html"
        
        with patch.object(cli, 'RenderManager', return_value=mock_manager):
            cli.render_web_command(args)
        
        captured = capsys.readouterr()
        assert "Rendering web output" in captured.out
        assert "Generated" in captured.out
    
    def test_render_web_nonexistent_source(self, tmp_path, capsys):
        """Test web rendering with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.md"))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_web_command(args)
        assert exc_info.value.code == 1


class TestMainCli:
    """Test suite for main CLI entry point."""
    
    def test_main_with_pdf_command(self, tmp_path, capsys):
        """Test main with pdf subcommand."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}")
        
        mock_manager = MagicMock()
        mock_manager.render_pdf.return_value = tmp_path / "output.pdf"
        
        with patch('sys.argv', ['cli.py', 'pdf', str(tex_file)]):
            with patch.object(cli, 'RenderManager', return_value=mock_manager):
                cli.main()
        
        captured = capsys.readouterr()
        assert "Rendering PDF" in captured.out
    
    def test_main_with_all_command(self, tmp_path, capsys):
        """Test main with all subcommand."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}")
        
        mock_manager = MagicMock()
        mock_manager.render_all.return_value = [tmp_path / "out.pdf"]
        
        with patch('sys.argv', ['cli.py', 'all', str(tex_file)]):
            with patch.object(cli, 'RenderManager', return_value=mock_manager):
                cli.main()
        
        captured = capsys.readouterr()
        assert "Rendering all formats" in captured.out
    
    def test_main_with_slides_command(self, tmp_path, capsys):
        """Test main with slides subcommand."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")
        
        mock_manager = MagicMock()
        mock_manager.render_slides.return_value = tmp_path / "slides.pdf"
        
        with patch('sys.argv', ['cli.py', 'slides', str(md_file)]):
            with patch.object(cli, 'RenderManager', return_value=mock_manager):
                cli.main()
        
        captured = capsys.readouterr()
        assert "Rendering slides" in captured.out
    
    def test_main_with_web_command(self, tmp_path, capsys):
        """Test main with web subcommand."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Doc")
        
        mock_manager = MagicMock()
        mock_manager.render_web.return_value = tmp_path / "doc.html"
        
        with patch('sys.argv', ['cli.py', 'web', str(md_file)]):
            with patch.object(cli, 'RenderManager', return_value=mock_manager):
                cli.main()
        
        captured = capsys.readouterr()
        assert "Rendering web output" in captured.out
    
    def test_main_without_command(self, capsys):
        """Test main without any subcommand."""
        with patch('sys.argv', ['cli.py']):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 1
    
    def test_main_with_exception(self, tmp_path, capsys):
        """Test main when command raises an exception."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}")
        
        with patch('sys.argv', ['cli.py', 'pdf', str(tex_file)]):
            with patch.object(cli, 'RenderManager', side_effect=Exception("Render error")):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()
                assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err
    
    def test_main_slides_with_format_option(self, tmp_path, capsys):
        """Test main with slides format option."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")
        
        mock_manager = MagicMock()
        mock_manager.render_slides.return_value = tmp_path / "slides.html"
        
        with patch('sys.argv', ['cli.py', 'slides', str(md_file), '--format', 'revealjs']):
            with patch.object(cli, 'RenderManager', return_value=mock_manager):
                cli.main()
        
        mock_manager.render_slides.assert_called_once()
        call_kwargs = mock_manager.render_slides.call_args[1]
        assert call_kwargs['format'] == 'revealjs'


class TestCliModuleStructure:
    """Test CLI module structure and imports."""
    
    def test_module_has_main_function(self):
        """Test that cli module has main function."""
        assert hasattr(cli, 'main')
        assert callable(cli.main)
    
    def test_module_has_command_functions(self):
        """Test that cli module has command functions."""
        assert hasattr(cli, 'render_pdf_command')
        assert hasattr(cli, 'render_all_command')
        assert hasattr(cli, 'render_slides_command')
        assert hasattr(cli, 'render_web_command')
    
    def test_imports_render_manager(self):
        """Test that RenderManager is imported."""
        assert hasattr(cli, 'RenderManager')





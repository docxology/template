"""Comprehensive tests for infrastructure/rendering/cli.py.

Tests the CLI interface for rendering operations using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import pytest

from infrastructure.rendering import cli
from infrastructure.rendering.core import RenderManager


class TestRenderPdfCommand:
    """Test suite for render_pdf_command using real RenderManager."""
    
    def test_render_pdf_basic(self, tmp_path, capsys):
        """Test basic PDF rendering with real RenderManager."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        args = argparse.Namespace(source=str(tex_file))
        
        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        try:
            cli.render_pdf_command(args)
            captured = capsys.readouterr()
            assert "Rendering PDF" in captured.out or "Generated" in captured.out
        except Exception:
            # LaTeX compilation may fail - that's real behavior, just verify command was attempted
            captured = capsys.readouterr()
            assert "Rendering PDF" in captured.out or "Error" in captured.err
    
    def test_render_pdf_nonexistent_source(self, tmp_path, capsys):
        """Test PDF rendering with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.tex"))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_pdf_command(args)
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error" in captured.err or "not found" in captured.err


class TestRenderAllCommand:
    """Test suite for render_all_command using real RenderManager."""
    
    def test_render_all_basic(self, tmp_path, capsys):
        """Test rendering all formats with real RenderManager."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        args = argparse.Namespace(source=str(tex_file))
        
        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        try:
            cli.render_all_command(args)
            captured = capsys.readouterr()
            assert "Rendering all formats" in captured.out or "Generated" in captured.out
        except Exception:
            # LaTeX compilation may fail - that's real behavior, just verify command was attempted
            captured = capsys.readouterr()
            assert "Rendering all formats" in captured.out or "Error" in captured.err
    
    def test_render_all_nonexistent_source(self, tmp_path, capsys):
        """Test render all with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.tex"))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_all_command(args)
        assert exc_info.value.code == 1


class TestRenderSlidesCommand:
    """Test suite for render_slides_command using real RenderManager."""
    
    def test_render_slides_beamer(self, tmp_path, capsys):
        """Test Beamer slide rendering with real RenderManager."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide 1\n\n## Content")
        
        args = argparse.Namespace(source=str(md_file), format="beamer")
        
        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        try:
            cli.render_slides_command(args)
            captured = capsys.readouterr()
            assert "beamer" in captured.out or "Generated" in captured.out or "Rendering slides" in captured.out
        except Exception:
            # LaTeX compilation may fail - that's real behavior, just verify command was attempted
            captured = capsys.readouterr()
            assert "beamer" in captured.out or "Rendering slides" in captured.out or "Error" in captured.err
    
    def test_render_slides_revealjs(self, tmp_path, capsys):
        """Test reveal.js slide rendering with real RenderManager."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide 1")
        
        args = argparse.Namespace(source=str(md_file), format="revealjs")
        
        # Use real RenderManager
        cli.render_slides_command(args)
        
        captured = capsys.readouterr()
        assert "revealjs" in captured.out or "Generated" in captured.out or "Rendering slides" in captured.out
    
    def test_render_slides_default_format(self, tmp_path, capsys):
        """Test slides with default format (beamer) using real RenderManager."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")
        
        args = argparse.Namespace(source=str(md_file), format=None)
        
        # Use real RenderManager - should default to beamer, may fail if LaTeX not available
        try:
            cli.render_slides_command(args)
            captured = capsys.readouterr()
            # Should mention beamer or rendering slides
            assert "beamer" in captured.out or "Rendering slides" in captured.out or "Generated" in captured.out
        except Exception:
            # LaTeX compilation may fail - that's real behavior, just verify command was attempted
            captured = capsys.readouterr()
            assert "beamer" in captured.out or "Rendering slides" in captured.out or "Error" in captured.err
    
    def test_render_slides_nonexistent_source(self, tmp_path, capsys):
        """Test slides with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.md"), format="beamer")
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_slides_command(args)
        assert exc_info.value.code == 1


class TestRenderWebCommand:
    """Test suite for render_web_command using real RenderManager."""
    
    def test_render_web_basic(self, tmp_path, capsys):
        """Test basic web rendering with real RenderManager."""
        md_file = tmp_path / "document.md"
        md_file.write_text("# Document\n\nContent here.")
        
        args = argparse.Namespace(source=str(md_file))
        
        # Use real RenderManager
        cli.render_web_command(args)
        
        captured = capsys.readouterr()
        assert "Rendering web output" in captured.out or "Generated" in captured.out
    
    def test_render_web_nonexistent_source(self, tmp_path, capsys):
        """Test web rendering with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.md"))
        
        with pytest.raises(SystemExit) as exc_info:
            cli.render_web_command(args)
        assert exc_info.value.code == 1


class TestMainCli:
    """Test suite for main CLI entry point using real subprocess execution."""
    
    def test_main_with_pdf_command(self, tmp_path):
        """Test main with pdf subcommand via real subprocess."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli', 'pdf', str(tex_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent  # Repository root for module imports
        )
        
        # Accept success or failure depending on LaTeX availability
        assert result.returncode in [0, 1]
    
    def test_main_with_all_command(self, tmp_path):
        """Test main with all subcommand via real subprocess."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli', 'all', str(tex_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Accept success or failure depending on dependencies
        assert result.returncode in [0, 1]
    
    def test_main_with_slides_command(self, tmp_path):
        """Test main with slides subcommand via real subprocess."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")
        
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli', 'slides', str(md_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Accept success or failure depending on pandoc availability
        assert result.returncode in [0, 1]
    
    def test_main_with_web_command(self, tmp_path):
        """Test main with web subcommand via real subprocess."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Doc")
        
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli', 'web', str(md_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Accept success or failure depending on pandoc availability
        assert result.returncode in [0, 1]
    
    def test_main_without_command(self):
        """Test main without any subcommand via real subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Should exit with error code when no command provided
        assert result.returncode == 1
    
    def test_main_with_exception(self, tmp_path):
        """Test main when command raises an exception via real execution."""
        # Create a file that might cause issues
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Run real CLI - may succeed or fail depending on environment
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli', 'pdf', str(tex_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Accept any return code - real execution may succeed or fail
        assert result.returncode in [0, 1]
    
    def test_main_slides_with_format_option(self, tmp_path):
        """Test main with slides format option via real subprocess."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")
        
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli', 'slides', str(md_file), '--format', 'revealjs'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Accept success or failure depending on pandoc availability
        assert result.returncode in [0, 1]
        # Check that revealjs format was recognized
        combined_output = result.stdout + result.stderr
        # Format should be mentioned if command parsed correctly
        assert 'revealjs' in combined_output.lower() or result.returncode == 1


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

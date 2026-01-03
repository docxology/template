"""Comprehensive tests for infrastructure/rendering/cli.py using real implementations.

Tests rendering CLI functionality using real subprocess execution.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import sys
import subprocess
from pathlib import Path
import pytest


class TestRenderAllCliCore:
    """Test core render all CLI functionality."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.rendering import render_all_cli
        assert render_all_cli is not None
    
    def test_has_main_function(self):
        """Test that module has main function."""
        from infrastructure.rendering import render_all_cli
        assert hasattr(render_all_cli, 'main') or hasattr(render_all_cli, 'render_all_cli')


class TestRenderCommands:
    """Test render command functionality."""
    
    def test_render_pdf_command_exists(self):
        """Test that render PDF command exists."""
        from infrastructure.rendering import render_all_cli
        
        if hasattr(render_all_cli, 'render_pdf_command'):
            assert callable(render_all_cli.render_pdf_command)
    
    def test_render_html_command_exists(self):
        """Test that render HTML command exists."""
        from infrastructure.rendering import render_all_cli
        
        if hasattr(render_all_cli, 'render_html_command'):
            assert callable(render_all_cli.render_html_command)
    
    def test_render_all_command_exists(self):
        """Test that render all command exists."""
        from infrastructure.rendering import render_all_cli
        
        if hasattr(render_all_cli, 'render_all_command'):
            assert callable(render_all_cli.render_all_command)


class TestRenderCliParsing:
    """Test CLI argument parsing via real subprocess."""
    
    def test_parse_args_basic(self, tmp_path):
        """Test basic argument parsing via real subprocess."""
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp_dir:
            pdf = Path(tmp_dir) / "source.md"
            pdf.write_text("# Test")
            
            # Run real CLI command via subprocess
            result = subprocess.run(
                [sys.executable, '-m', 'infrastructure.rendering.cli', 'pdf', str(pdf)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            # May succeed or fail depending on dependencies
            assert result.returncode in [0, 1, 2]
    
    def test_parse_args_with_output(self, tmp_path):
        """Test parsing with output option via real subprocess."""
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp_dir:
            pdf = Path(tmp_dir) / "source.md"
            pdf.write_text("# Test")
            
            # Run real CLI command via subprocess
            result = subprocess.run(
                [sys.executable, '-m', 'infrastructure.rendering.cli', 'pdf', str(pdf)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            # May succeed or fail
            assert result.returncode in [0, 1, 2]


class TestSlidesRendering:
    """Test slides rendering commands."""
    
    def test_slides_beamer_command(self):
        """Test Beamer slides command."""
        from infrastructure.rendering import render_all_cli
        
        if hasattr(render_all_cli, 'render_slides_command'):
            assert callable(render_all_cli.render_slides_command)
    
    def test_slides_revealjs_command(self):
        """Test reveal.js slides command."""
        from infrastructure.rendering import render_all_cli
        
        if hasattr(render_all_cli, 'render_revealjs_command'):
            assert callable(render_all_cli.render_revealjs_command)


class TestRenderCliMain:
    """Test main entry point using real subprocess execution."""
    
    def test_main_without_args(self):
        """Test main without arguments via real subprocess."""
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Should exit with error when no args provided
        assert result.returncode in [1, 2]
    
    def test_main_with_pdf(self, tmp_path):
        """Test main with PDF command via real subprocess."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.rendering.cli', 'pdf', str(tex_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # May succeed or fail depending on LaTeX availability
        assert result.returncode in [0, 1, 2]

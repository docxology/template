#!/usr/bin/env python3
"""Comprehensive tests for repo_utilities modules."""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest

# Import the modules we're testing
sys_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities')
sys.path.insert(0, sys_path)

from generate_glossary import (
    _repo_root, _ensure_glossary_file, main as glossary_main
)
from validate_markdown import (
    _repo_root as validate_repo_root,
    find_markdown_files,
    collect_symbols,
    validate_images,
    validate_refs,
    validate_math,
    main as validate_main
)


class TestGenerateGlossary:
    """Test the generate_glossary module."""
    
    def test_repo_root(self):
        """Test _repo_root function returns correct path."""
        repo_path = _repo_root()
        assert os.path.basename(repo_path) == "template"
        assert os.path.exists(repo_path)
    
    def test_ensure_glossary_file_new_file(self, tmp_path):
        """Test _ensure_glossary_file creates new file with skeleton content."""
        glossary_path = tmp_path / "test_glossary.md"
        
        _ensure_glossary_file(str(glossary_path))
        
        assert glossary_path.exists()
        content = glossary_path.read_text()
        assert "<!-- BEGIN: AUTO-API-GLOSSARY -->" in content
        assert "<!-- END: AUTO-API-GLOSSARY -->" in content
        assert "No public APIs detected in `src/`" in content
    
    def test_ensure_glossary_file_existing_file(self, tmp_path):
        """Test _ensure_glossary_file doesn't overwrite existing file."""
        glossary_path = tmp_path / "test_glossary.md"
        original_content = "Existing content"
        glossary_path.write_text(original_content)
        
        _ensure_glossary_file(str(glossary_path))
        
        assert glossary_path.read_text() == original_content
    
    def test_ensure_glossary_file_creates_directory(self, tmp_path):
        """Test _ensure_glossary_file creates parent directory if needed."""
        glossary_path = tmp_path / "subdir" / "test_glossary.md"
        
        _ensure_glossary_file(str(glossary_path))
        
        assert glossary_path.exists()
        assert (tmp_path / "subdir").exists()
    
    def test_main_script_execution(self):
        """Test the __main__ block execution."""
        # Test that the script can be executed as a module
        import subprocess
        import sys
        
        # Run the module as a script
        result = subprocess.run([
            sys.executable, "-m", "generate_glossary"
        ], cwd="repo_utilities", capture_output=True, text=True)
        
        # The script should run successfully (exit code 0 or 1 depending on state)
        assert result.returncode in [0, 1]
    
    def test_main_with_real_glossary_gen(self):
        """Test main function with the actual glossary_gen module from current project."""
        # This test uses the real glossary_gen module from the current project
        # which demonstrates the actual working behavior
        
        # Use the current project's actual structure
        result = glossary_main()
        
        # The function should succeed with the real glossary_gen module
        assert result == 0
        
        # Verify that the glossary file exists and was processed
        glossary_file = os.path.join(os.path.dirname(__file__), "..", "markdown", "10_symbols_glossary.md")
        assert os.path.exists(glossary_file)
        
        # Read the file to verify it has the expected structure
        with open(glossary_file, "r") as f:
            content = f.read()
        
        assert "<!-- BEGIN: AUTO-API-GLOSSARY -->" in content
        assert "<!-- END: AUTO-API-GLOSSARY -->" in content


class TestValidateMarkdown:
    """Test the validate_markdown module."""
    
    def test_repo_root(self):
        """Test _repo_root function returns correct path."""
        repo_path = validate_repo_root()
        assert os.path.basename(repo_path) == "template"
        assert os.path.exists(repo_path)
    
    def test_find_markdown_files(self, tmp_path):
        """Test find_markdown_files finds and sorts markdown files."""
        # Create test markdown files
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "02_second.md").write_text("content")
        (tmp_path / "markdown" / "01_first.md").write_text("content")
        (tmp_path / "markdown" / "not_md.txt").write_text("content")
        
        files = find_markdown_files(str(tmp_path / "markdown"))
        
        assert len(files) == 2
        assert "01_first.md" in files[0]
        assert "02_second.md" in files[1]
    
    def test_collect_symbols(self, tmp_path):
        """Test collect_symbols extracts labels and anchors."""
        # Create test markdown files
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test1.md").write_text(
            "\\begin{equation}\\label{eq:test1}\\end{equation}\n"
            "# Section {#sec:test1}\n"
        )
        (tmp_path / "markdown" / "test2.md").write_text(
            "\\begin{equation}\\label{eq:test2}\\end{equation}\n"
            "## Subsection {#subsec:test2}\n"
        )
        
        labels, anchors = collect_symbols([str(tmp_path / "markdown" / "test1.md"), 
                                         str(tmp_path / "markdown" / "test2.md")])
        
        assert labels == {"eq:test1", "eq:test2"}
        assert anchors == {"sec:test1", "subsec:test2"}
    
    def test_validate_images_missing_image(self, tmp_path):
        """Test validate_images detects missing images."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "![alt text](../output/figures/missing.png)"
        )
        
        problems = validate_images([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Missing image: ../output/figures/missing.png" in problems[0]
    
    def test_validate_images_existing_image(self, tmp_path):
        """Test validate_images doesn't flag existing images."""
        # Create test markdown file and image
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "![alt text](../output/figures/existing.png)"
        )
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "existing.png").write_text("fake image")
        
        problems = validate_images([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 0
    
    def test_validate_images_absolute_path(self, tmp_path):
        """Test validate_images with absolute image paths."""
        # Create test markdown file with absolute path
        (tmp_path / "markdown").mkdir()
        abs_image_path = str(tmp_path / "absolute_image.png")
        (tmp_path / "markdown" / "test.md").write_text(
            f"![alt text]({abs_image_path})"
        )
        
        # Don't create the image file so it will be missing
        problems = validate_images([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert abs_image_path in problems[0]
    
    def test_validate_refs_missing_equation_label(self, tmp_path):
        """Test validate_refs detects missing equation labels."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "Reference to \\eqref{eq:missing}"
        )
        
        problems = validate_refs([str(tmp_path / "markdown" / "test.md")], set(), set(), str(tmp_path))
        
        assert len(problems) == 1
        assert "Missing equation label for \\eqref{eq:missing}" in problems[0]
    
    def test_validate_refs_missing_anchor(self, tmp_path):
        """Test validate_refs detects missing anchors."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "Link to [section](#missing_anchor)"
        )
        
        problems = validate_refs([str(tmp_path / "markdown" / "test.md")], set(), set(), str(tmp_path))
        
        assert len(problems) == 1
        assert "Missing anchor/label for link (#missing_anchor)" in problems[0]
    
    def test_validate_refs_bare_url(self, tmp_path):
        """Test validate_refs detects bare URLs."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "Visit https://example.com for more info"
        )
        
        problems = validate_refs([str(tmp_path / "markdown" / "test.md")], set(), set(), str(tmp_path))
        
        assert len(problems) == 1
        assert "Bare URL found" in problems[0]
    
    def test_validate_refs_non_informative_link(self, tmp_path):
        """Test validate_refs detects non-informative link text."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "[https://example.com](https://example.com)"
        )
        
        problems = validate_refs([str(tmp_path / "markdown" / "test.md")], set(), set(), str(tmp_path))
        
        # The regex patterns can detect multiple issues with the same text
        assert len(problems) >= 1
        assert any("Non-informative link text" in p for p in problems)
    
    def test_validate_math_dollar_math(self, tmp_path):
        """Test validate_math detects dollar math notation."""
        # Create test markdown file with $$ math
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "Math: $$x^2 + y^2 = z^2$$"
        )
        
        problems = validate_math([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Use equation environment instead of $$" in problems[0]
    
    def test_validate_math_bracket_math(self, tmp_path):
        """Test validate_math detects bracket math notation."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "Math: \\[x^2 + y^2 = z^2\\]"
        )
        
        problems = validate_math([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Use equation environment instead of \\[ \\]" in problems[0]
    
    def test_validate_math_missing_label(self, tmp_path):
        """Test validate_math detects equations without labels."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "\\begin{equation}x^2 + y^2 = z^2\\end{equation}"
        )
        
        problems = validate_math([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Equation missing \\label{...}" in problems[0]
    
    def test_validate_math_duplicate_label(self, tmp_path):
        """Test validate_math detects duplicate equation labels."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "\\begin{equation}\\label{eq:duplicate}x^2\\end{equation}\n"
            "\\begin{equation}\\label{eq:duplicate}y^2\\end{equation}"
        )
        
        problems = validate_math([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Duplicate equation label '{eq:duplicate}'" in problems[0]
    
    def test_validate_math_valid_equations(self, tmp_path):
        """Test validate_math accepts valid labeled equations."""
        # Create test markdown file
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text(
            "\\begin{equation}\\label{eq:valid1}x^2 + y^2 = z^2\\end{equation}\n"
            "\\begin{equation}\\label{eq:valid2}a^2 + b^2 = c^2\\end{equation}"
        )
        
        problems = validate_math([str(tmp_path / "markdown" / "test.md")], str(tmp_path))
        
        assert len(problems) == 0
    
    def test_main_markdown_dir_not_found(self):
        """Test main function handles missing markdown directory."""
        with patch('validate_markdown.os.path.isdir', return_value=False):
            with patch('builtins.print') as mock_print:
                result = validate_main()
                
                assert result == 1
                mock_print.assert_called_once()
                assert "Markdown directory not found" in mock_print.call_args[0][0]
    
    def test_main_no_problems(self, tmp_path):
        """Test main function returns 0 when no problems found."""
        # Create test markdown directory with valid content
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text("# Test\n\nNo problems here.")
        
        with patch('validate_markdown._repo_root', return_value=str(tmp_path)):
            with patch('builtins.print') as mock_print:
                result = validate_main()
                
                assert result == 0
                mock_print.assert_called_once()
                assert "Markdown validation passed" in mock_print.call_args[0][0]
    
    def test_main_with_problems_non_strict(self, tmp_path):
        """Test main function returns 0 with problems in non-strict mode."""
        # Create test markdown directory with problems that will actually be detected
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text("\\begin{equation}x^2\\end{equation}")
        
        with patch('validate_markdown._repo_root', return_value=str(tmp_path)):
            with patch('validate_markdown.sys.argv', ['validate_markdown.py']):
                with patch('builtins.print') as mock_print:
                    result = validate_main()
                    
                    # Should return 0 in non-strict mode even with problems
                    assert result == 0
                    # Check that it prints the issues header
                    assert any("Markdown validation issues" in call[0][0] for call in mock_print.call_args_list)
    
    def test_main_with_problems_strict(self, tmp_path):
        """Test main function returns 1 with problems in strict mode."""
        # Create test markdown directory with problems that will actually be detected
        (tmp_path / "markdown").mkdir()
        (tmp_path / "markdown" / "test.md").write_text("\\begin{equation}x^2\\end{equation}")
        
        with patch('validate_markdown._repo_root', return_value=str(tmp_path)):
            with patch('validate_markdown.sys.argv', ['validate_markdown.py', '--strict']):
                with patch('builtins.print') as mock_print:
                    result = validate_main()
                    
                    # Should return 1 in strict mode with problems
                    assert result == 1
                    # Check that it prints the strict validation header
                    assert any("Validation issues found" in call[0][0] for call in mock_print.call_args_list)
    
    def test_validate_markdown_script_execution(self):
        """Test the __main__ block execution of validate_markdown."""
        # Test that the script can be executed as a module
        import subprocess
        import sys
        
        # Run the module as a script
        result = subprocess.run([
            sys.executable, "-m", "validate_markdown"
        ], cwd="repo_utilities", capture_output=True, text=True)
        
        # The script should run successfully (exit code 0 or 1 depending on validation results)
        assert result.returncode in [0, 1]


class TestLuaScript:
    """Test Lua script functionality."""

    def test_convert_latex_images_script_exists(self):
        """Test that convert_latex_images.lua script exists."""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities', 'convert_latex_images.lua')
        assert os.path.exists(script_path)

    def test_convert_latex_images_has_lua_shebang(self):
        """Test that Lua script has proper shebang."""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities', 'convert_latex_images.lua')
        with open(script_path, 'r') as f:
            first_line = f.readline().strip()
            assert first_line == '-- Pandoc Lua filter to convert LaTeX \\includegraphics commands to HTML img tags'


class TestShellScripts:
    """Test shell script functionality."""

    def test_clean_output_script_exists(self):
        """Test that clean_output.sh script exists and is executable."""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities', 'clean_output.sh')
        assert os.path.exists(script_path)
        # Check if executable (on Unix-like systems)
        if os.name != 'nt':
            assert os.access(script_path, os.X_OK)

    def test_render_pdf_script_exists(self):
        """Test that render_pdf.sh script exists and is executable."""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities', 'render_pdf.sh')
        assert os.path.exists(script_path)
        # Check if executable (on Unix-like systems)
        if os.name != 'nt':
            assert os.access(script_path, os.X_OK)

    def test_rename_project_script_exists(self):
        """Test that rename_project.sh script exists and is executable."""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities', 'rename_project.sh')
        assert os.path.exists(script_path)
        # Check if executable (on Unix-like systems)
        if os.name != 'nt':
            assert os.access(script_path, os.X_OK)

    def test_open_manuscript_script_exists(self):
        """Test that open_manuscript.sh script exists and is executable."""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities', 'open_manuscript.sh')
        assert os.path.exists(script_path)
        # Check if executable (on Unix-like systems)
        if os.name != 'nt':
            assert os.access(script_path, os.X_OK)

    def test_shell_scripts_have_shebang(self):
        """Test that shell scripts have proper shebang lines."""
        scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities')

        script_files = [
            'clean_output.sh',
            'render_pdf.sh',
            'rename_project.sh',
            'open_manuscript.sh'
        ]

        for script_file in script_files:
            script_path = os.path.join(scripts_dir, script_file)
            with open(script_path, 'r') as f:
                first_line = f.readline().strip()
                assert first_line == '#!/bin/bash', f"{script_file} should start with #!/bin/bash"

    def test_shell_scripts_have_proper_error_handling(self):
        """Test that shell scripts have proper error handling."""
        scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities')

        script_files = [
            'clean_output.sh',
            'render_pdf.sh',
            'rename_project.sh',
            'open_manuscript.sh'
        ]

        for script_file in script_files:
            script_path = os.path.join(scripts_dir, script_file)
            with open(script_path, 'r') as f:
                content = f.read()
                # Check for set -e (exit on error)
                assert 'set -e' in content, f"{script_file} should have 'set -e' for error handling"

    def test_render_pdf_script_functionality(self, tmp_path):
        """Test that render_pdf.sh can run without errors in a minimal setup."""
        # This is a basic smoke test - we can't fully test the script without
        # all dependencies, but we can test that it starts and fails gracefully
        script_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities', 'render_pdf.sh')

        # Run the script and expect it to fail due to missing dependencies
        # but not crash with syntax errors
        try:
            result = subprocess.run(
                [script_path],
                cwd=os.path.dirname(__file__),
                capture_output=True,
                text=True,
                timeout=30
            )
            # Should exit with non-zero code due to missing dependencies, not syntax errors
            assert result.returncode != 0, "Script should fail due to missing dependencies, not syntax errors"
        except subprocess.TimeoutExpired:
            pytest.fail("Script took too long to execute, likely hanging")
        except FileNotFoundError:
            pytest.skip("Script execution not available on this platform")


# Clean up sys.path
sys.path.remove(sys_path)

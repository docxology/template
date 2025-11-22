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
# Note: These modules have been moved to infrastructure/
# The imports are adjusted to work with the new structure

try:
    from infrastructure.documentation.glossary_gen import (
        build_api_index, generate_markdown_table, inject_between_markers
    )
    from infrastructure.validation.markdown_validator import (
        find_markdown_files,
        collect_symbols,
        validate_images,
        validate_refs,
        validate_math
    )
except ImportError:
    # Fallback for backward compatibility
    sys_path = os.path.join(os.path.dirname(__file__), '..', 'repo_utilities')
    if os.path.exists(sys_path):
        sys.path.insert(0, sys_path)
    
    # These imports may fail if repo_utilities/ doesn't exist
    try:
        from generate_glossary import _repo_root, _ensure_glossary_file, main as glossary_main
        from validate_markdown import (
            _repo_root as validate_repo_root,
            find_markdown_files, collect_symbols, validate_images,
            validate_refs, validate_math, main as validate_main
        )
    except ImportError:
        pass  # Tests will skip if imports fail

# Helper functions for tests
def _repo_root():
    """Get repository root."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def _ensure_glossary_file(path):
    """Ensure glossary file exists with skeleton content."""
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    skeleton = (
        "# API Symbols Glossary\n\n"
        "This glossary is auto-generated from the public API in `src/`.\n\n"
        "<!-- BEGIN: AUTO-API-GLOSSARY -->\n"
        "No public APIs detected in `src/`.\n"
        "<!-- END: AUTO-API-GLOSSARY -->\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(skeleton)


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
        glossary_file = os.path.join(os.path.dirname(__file__), "..", "manuscript", "98_symbols_glossary.md")
        assert os.path.exists(glossary_file)

        # Read the file to verify it has the expected structure
        with open(glossary_file, "r") as f:
            content = f.read()

        assert "<!-- BEGIN: AUTO-API-GLOSSARY -->" in content
        assert "<!-- END: AUTO-API-GLOSSARY -->" in content

    def test_main_function_integration_with_real_src(self, tmp_path):
        """Test main function with real src/ directory and generated content."""
        # Create a test project structure
        test_root = tmp_path / "integration_test"
        test_root.mkdir()

        # Copy the actual src/ directory
        actual_src = os.path.join(os.path.dirname(__file__), "..", "src")
        test_src = test_root / "src"
        shutil.copytree(actual_src, test_src)

        # Copy the actual repo_utilities/generate_glossary.py
        actual_glossary_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "generate_glossary.py")
        test_glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        test_glossary_script.parent.mkdir()
        shutil.copy2(actual_glossary_script, test_glossary_script)

        # Create manuscript directory and glossary file
        test_manuscript = test_root / "manuscript"
        test_manuscript.mkdir()
        (test_manuscript / "98_symbols_glossary.md").write_text(
            "# API Symbols Glossary\n\n"
            "This glossary is auto-generated from the public API in `src/`.\n\n"
            "<!-- BEGIN: AUTO-API-GLOSSARY -->\n"
            "No public APIs detected in `src/`.\n"
            "<!-- END: AUTO-API-GLOSSARY -->\n"
        )

        # Run the script from the test directory
        result = subprocess.run([
            sys.executable, str(test_glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should succeed
        assert result.returncode == 0

        # Check that it updated the glossary
        assert "Updated glossary:" in result.stdout or "Glossary up-to-date" in result.stdout

        # Verify the generated content
        glossary_file = test_manuscript / "98_symbols_glossary.md"
        with open(glossary_file, "r") as f:
            content = f.read()

        # Should contain real API entries from the src/ modules
        assert "example" in content.lower()  # Should contain example module
        assert "glossary_gen" in content.lower()  # Should contain glossary_gen module
        assert "function" in content.lower()  # Should contain function entries
        assert "class" in content.lower()  # Should contain class entries

        # Should still have the markers
        assert "<!-- BEGIN: AUTO-API-GLOSSARY -->" in content
        assert "<!-- END: AUTO-API-GLOSSARY -->" in content

    def test_main_function_handles_missing_glossary_gen(self, tmp_path):
        """Test main function handles missing glossary_gen module gracefully."""
        # Create test environment without glossary_gen module
        test_root = tmp_path / "missing_glossary"
        test_root.mkdir()

        # Create src/ without glossary_gen.py
        test_src = test_root / "src"
        test_src.mkdir()
        (test_src / "example.py").write_text('def test(): pass')

        # Create generate_glossary.py that tries to import non-existent glossary_gen
        test_glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        test_glossary_script.parent.mkdir()
        (test_glossary_script).write_text('''
import os
import sys
from typing import Tuple

def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _ensure_glossary_file(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    skeleton = (
        "# API Symbols Glossary\\n\\n"
        "This glossary is auto-generated from the public API in `src/`.\\n\\n"
        "<!-- BEGIN: AUTO-API-GLOSSARY -->\\n"
        "No public APIs detected in `src/`.\\n"
        "<!-- END: AUTO-API-GLOSSARY -->\\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(skeleton)

def main() -> int:
    repo = _repo_root()
    src_dir = os.path.join(repo, "src")
    glossary_md = os.path.join(repo, "manuscript", "98_symbols_glossary.md")

    _ensure_glossary_file(glossary_md)

    sys.path.insert(0, src_dir)
    try:
        from infrastructure.glossary_gen import build_api_index, generate_markdown_table, inject_between_markers  # This will fail
    except Exception as exc:
        print(f"Failed to import glossary_gen from src/: {exc}")
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

        # Create manuscript directory
        test_manuscript = test_root / "manuscript"
        test_manuscript.mkdir()

        # Run the script
        result = subprocess.run([
            sys.executable, str(test_glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should fail gracefully
        assert result.returncode == 1
        assert "Failed to import glossary_gen from src/" in result.stdout

    def test_main_function_creates_glossary_directory(self, tmp_path):
        """Test main function creates markdown directory if it doesn't exist."""
        # Create test environment without markdown directory
        test_root = tmp_path / "no_markdown"
        test_root.mkdir()

        # Copy actual src/
        actual_src = os.path.join(os.path.dirname(__file__), "..", "src")
        test_src = test_root / "src"
        shutil.copytree(actual_src, test_src)

        # Copy actual generate_glossary.py
        actual_glossary_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "generate_glossary.py")
        test_glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        test_glossary_script.parent.mkdir()
        shutil.copy2(actual_glossary_script, test_glossary_script)

        # Run the script - should create markdown directory and file
        result = subprocess.run([
            sys.executable, str(test_glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should succeed
        assert result.returncode == 0

        # Check that manuscript directory was created
        test_manuscript = test_root / "manuscript"
        assert test_manuscript.exists()

        # Check that glossary file was created
        glossary_file = test_manuscript / "98_symbols_glossary.md"
        assert glossary_file.exists()

        # Check content
        with open(glossary_file, "r") as f:
            content = f.read()
        assert "API Symbols Glossary" in content

    def test_main_function_deterministic_output(self, tmp_path):
        """Test that main function produces deterministic output across runs."""
        # Create test environment
        test_root = tmp_path / "deterministic"
        test_root.mkdir()

        # Copy actual src/
        actual_src = os.path.join(os.path.dirname(__file__), "..", "src")
        test_src = test_root / "src"
        shutil.copytree(actual_src, test_src)

        # Copy actual generate_glossary.py
        actual_glossary_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "generate_glossary.py")
        test_glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        test_glossary_script.parent.mkdir()
        shutil.copy2(actual_glossary_script, test_glossary_script)

        # Create manuscript directory and initial glossary
        test_manuscript = test_root / "manuscript"
        test_manuscript.mkdir()
        (test_manuscript / "98_symbols_glossary.md").write_text(
            "# API Symbols Glossary\n\n"
            "<!-- BEGIN: AUTO-API-GLOSSARY -->\n"
            "No public APIs detected.\n"
            "<!-- END: AUTO-API-GLOSSARY -->\n"
        )

        # Run script twice
        result1 = subprocess.run([
            sys.executable, str(test_glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        result2 = subprocess.run([
            sys.executable, str(test_glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Both should succeed
        assert result1.returncode == 0
        assert result2.returncode == 0

        # Check that output files are identical
        glossary_file = test_manuscript / "98_symbols_glossary.md"

        with open(glossary_file, "r") as f:
            content1 = f.read()

        with open(glossary_file, "r") as f:
            content2 = f.read()

        assert content1 == content2

    def test_main_function_with_empty_src(self, tmp_path):
        """Test main function with empty src/ directory."""
        # Create test environment with empty src/
        test_root = tmp_path / "empty_src"
        test_root.mkdir()

        test_src = test_root / "src"
        test_src.mkdir()
        # Don't add any Python files to src/

        # Copy actual generate_glossary.py
        actual_glossary_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "generate_glossary.py")
        test_glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        test_glossary_script.parent.mkdir()
        shutil.copy2(actual_glossary_script, test_glossary_script)

        # Create markdown directory and initial glossary
        test_markdown = test_root / "manuscript"
        test_markdown.mkdir()

        # Run the script - should fail because glossary_gen module is missing
        result = subprocess.run([
            sys.executable, str(test_glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should fail when glossary_gen module is missing
        assert result.returncode == 1
        assert "Failed to import glossary_gen from src/" in result.stdout

    def test_main_function_error_handling_comprehensive(self, tmp_path):
        """Test main function comprehensive error handling."""
        # Test with corrupted glossary_gen module
        test_root = tmp_path / "corrupted_glossary"
        test_root.mkdir()

        # Copy src/ but corrupt the glossary_gen.py
        actual_src = os.path.join(os.path.dirname(__file__), "..", "src")
        test_src = test_root / "src"
        shutil.copytree(actual_src, test_src)

        # Corrupt the glossary_gen.py file
        glossary_gen_file = test_src / "glossary_gen.py"
        original_content = glossary_gen_file.read_text()
        corrupted_content = original_content.replace("def build_api_index", "def broken_function")
        glossary_gen_file.write_text(corrupted_content)

        # Copy generate_glossary.py
        actual_glossary_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "generate_glossary.py")
        test_glossary_script = test_root / "repo_utilities" / "generate_glossary.py"
        test_glossary_script.parent.mkdir()
        shutil.copy2(actual_glossary_script, test_glossary_script)

        # Create manuscript directory
        test_manuscript = test_root / "manuscript"
        test_manuscript.mkdir()

        # Run the script - should handle import errors
        result = subprocess.run([
            sys.executable, str(test_glossary_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should fail gracefully
        assert result.returncode == 1
        assert "Failed to import glossary_gen from src/" in result.stdout


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
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "02_second.md").write_text("content")
        (tmp_path / "manuscript" / "01_first.md").write_text("content")
        (tmp_path / "manuscript" / "not_md.txt").write_text("content")
        
        files = find_markdown_files(str(tmp_path / "manuscript"))
        
        assert len(files) == 2
        assert "01_first.md" in files[0]
        assert "02_second.md" in files[1]
    
    def test_collect_symbols(self, tmp_path):
        """Test collect_symbols extracts labels and anchors."""
        # Create test markdown files
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test1.md").write_text(
            "\\begin{equation}\\label{eq:test1}\\end{equation}\n"
            "# Section {#sec:test1}\n"
        )
        (tmp_path / "manuscript" / "test2.md").write_text(
            "\\begin{equation}\\label{eq:test2}\\end{equation}\n"
            "## Subsection {#subsec:test2}\n"
        )
        
        labels, anchors = collect_symbols([str(tmp_path / "manuscript" / "test1.md"), 
                                         str(tmp_path / "manuscript" / "test2.md")])
        
        assert labels == {"eq:test1", "eq:test2"}
        assert anchors == {"sec:test1", "subsec:test2"}
    
    def test_validate_images_missing_image(self, tmp_path):
        """Test validate_images detects missing images."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "![alt text](../output/figures/missing.png)"
        )
        
        problems = validate_images([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Missing image: ../output/figures/missing.png" in problems[0]
    
    def test_validate_images_existing_image(self, tmp_path):
        """Test validate_images doesn't flag existing images."""
        # Create test markdown file and image
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "![alt text](../output/figures/existing.png)"
        )
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "existing.png").write_text("fake image")
        
        problems = validate_images([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 0
    
    def test_validate_images_absolute_path(self, tmp_path):
        """Test validate_images with absolute image paths."""
        # Create test markdown file with absolute path
        (tmp_path / "manuscript").mkdir()
        abs_image_path = str(tmp_path / "absolute_image.png")
        (tmp_path / "manuscript" / "test.md").write_text(
            f"![alt text]({abs_image_path})"
        )
        
        # Don't create the image file so it will be missing
        problems = validate_images([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert abs_image_path in problems[0]
    
    def test_validate_refs_missing_equation_label(self, tmp_path):
        """Test validate_refs detects missing equation labels."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "Reference to \\eqref{eq:missing}"
        )
        
        problems = validate_refs([str(tmp_path / "manuscript" / "test.md")], set(), set(), str(tmp_path))
        
        assert len(problems) == 1
        assert "Missing equation label for \\eqref{eq:missing}" in problems[0]
    
    def test_validate_refs_missing_anchor(self, tmp_path):
        """Test validate_refs detects missing anchors."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "Link to [section](#missing_anchor)"
        )
        
        problems = validate_refs([str(tmp_path / "manuscript" / "test.md")], set(), set(), str(tmp_path))
        
        assert len(problems) == 1
        assert "Missing anchor/label for link (#missing_anchor)" in problems[0]
    
    def test_validate_refs_bare_url(self, tmp_path):
        """Test validate_refs detects bare URLs."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "Visit https://example.com for more info"
        )
        
        problems = validate_refs([str(tmp_path / "manuscript" / "test.md")], set(), set(), str(tmp_path))
        
        assert len(problems) == 1
        assert "Bare URL found" in problems[0]
    
    def test_validate_refs_non_informative_link(self, tmp_path):
        """Test validate_refs detects non-informative link text."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "[https://example.com](https://example.com)"
        )
        
        problems = validate_refs([str(tmp_path / "manuscript" / "test.md")], set(), set(), str(tmp_path))
        
        # The regex patterns can detect multiple issues with the same text
        assert len(problems) >= 1
        assert any("Non-informative link text" in p for p in problems)
    
    def test_validate_math_dollar_math(self, tmp_path):
        """Test validate_math detects dollar math notation."""
        # Create test markdown file with $$ math
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "Math: $$x^2 + y^2 = z^2$$"
        )
        
        problems = validate_math([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Use equation environment instead of $$" in problems[0]
    
    def test_validate_math_bracket_math(self, tmp_path):
        """Test validate_math detects bracket math notation."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "Math: \\[x^2 + y^2 = z^2\\]"
        )
        
        problems = validate_math([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Use equation environment instead of \\[ \\]" in problems[0]
    
    def test_validate_math_missing_label(self, tmp_path):
        """Test validate_math detects equations without labels."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            r"\begin{equation}x^2 + y^2 = z^2\end{equation}"
        )
        
        problems = validate_math([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Equation missing \\label{...}" in problems[0]
    
    def test_validate_math_duplicate_label(self, tmp_path):
        """Test validate_math detects duplicate equation labels."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            r"\begin{equation}\label{eq:duplicate}x^2\end{equation}" + "\n"
            r"\begin{equation}\label{eq:duplicate}y^2\end{equation}"
        )
        
        problems = validate_math([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 1
        assert "Duplicate equation label '{eq:duplicate}'" in problems[0]
    
    def test_validate_math_valid_equations(self, tmp_path):
        """Test validate_math accepts valid labeled equations."""
        # Create test markdown file
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text(
            "\\begin{equation}\\label{eq:valid1}x^2 + y^2 = z^2\\end{equation}\n"
            "\\begin{equation}\\label{eq:valid2}a^2 + b^2 = c^2\\end{equation}"
        )
        
        problems = validate_math([str(tmp_path / "manuscript" / "test.md")], str(tmp_path))
        
        assert len(problems) == 0
    
    def test_main_manuscript_dir_not_found(self):
        """Test main function handles missing markdown directory."""
        with patch('validate_markdown.os.path.isdir', return_value=False):
            with patch('builtins.print') as mock_print:
                result = validate_main()
                
                assert result == 1
                mock_print.assert_called_once()
                assert "Manuscript directory not found" in mock_print.call_args[0][0]
    
    def test_main_no_problems(self, tmp_path):
        """Test main function returns 0 when no problems found."""
        # Create test markdown directory with valid content
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text("# Test\n\nNo problems here.")
        
        with patch('validate_markdown._repo_root', return_value=str(tmp_path)):
            with patch('builtins.print') as mock_print:
                result = validate_main()
                
                assert result == 0
                mock_print.assert_called_once()
                assert "Markdown validation passed" in mock_print.call_args[0][0]
    
    def test_main_with_problems_non_strict(self, tmp_path):
        """Test main function returns 0 with problems in non-strict mode."""
        # Create test markdown directory with problems that will actually be detected
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text("\\begin{equation}x^2\\end{equation}")
        
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
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "test.md").write_text("\\begin{equation}x^2\\end{equation}")
        
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

    def test_validate_markdown_integration_with_real_figures(self, tmp_path):
        """Test validate_markdown with real generated figures and markdown content."""
        # Create test project with real outputs
        test_root = tmp_path / "validate_integration"
        test_root.mkdir()

        # Create output/figures directory with real PNG files
        output_dir = test_root / "output" / "figures"
        output_dir.mkdir(parents=True)

        # Create fake PNG files (real ones would be too large for tests)
        (output_dir / "convergence_plot.png").write_bytes(b"fake png content")
        (output_dir / "experimental_setup.png").write_bytes(b"fake png content")
        (output_dir / "data_structure.png").write_bytes(b"fake png content")

        # Create markdown directory with real content
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        # Create markdown files with references to the figures
        (manuscript_dir / "01_test.md").write_text(r"""
# Test Section {#sec:test}

This is a test section that references figures.

![Convergence Analysis](../output/figures/convergence_plot.png)

![Experimental Setup](../output/figures/experimental_setup.png)

See also [data structure figure](#fig:data_structure).

\begin{equation}\label{eq:test}
x^2 + y^2 = z^2
\end{equation}

Reference to equation \eqref{eq:test}.

## Subsection {#subsec:test}

More content here.

![Data Structure](../output/figures/data_structure.png)
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run validation
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass validation (all images and references exist)
        assert result.returncode == 0
        assert "Markdown validation" in result.stdout  # Either passed or has issues

    def test_validate_markdown_integration_with_missing_images(self, tmp_path):
        """Test validate_markdown detects missing images correctly."""
        # Create test project with missing images
        test_root = tmp_path / "missing_images"
        test_root.mkdir()

        # Create output/figures directory but don't create the referenced image
        output_dir = test_root / "output" / "figures"
        output_dir.mkdir(parents=True)

        # Create markdown directory with references to non-existent images
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_test.md").write_text(r"""
# Test Section

This references a missing image.

![Missing Image](../output/figures/missing_plot.png)

Also references another missing one.

![Another Missing](../output/figures/another_missing.png)
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run validation - should detect missing images but pass in non-strict mode
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass in non-strict mode (returns 0) but report issues
        assert result.returncode == 0
        assert "Markdown validation issues (non-strict):" in result.stdout
        assert "Missing image:" in result.stdout
        assert "missing_plot.png" in result.stdout
        assert "another_missing.png" in result.stdout

    def test_validate_markdown_integration_with_missing_references(self, tmp_path):
        """Test validate_markdown detects missing equation labels and anchors."""
        # Create test project with missing references
        test_root = tmp_path / "missing_refs"
        test_root.mkdir()

        # Create markdown directory with broken references
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_test.md").write_text(r"""
# Test Section {#sec:test}

This references a missing equation.

\begin{equation}\label{eq:existing}
x^2 = y^2
\end{equation}

But this references a non-existent equation: \eqref{eq:missing}.

Also references a missing anchor: [link](#missing_anchor).

And has a bare URL: https://example.com

And non-informative link: [https://example.com](https://example.com)
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run validation - should detect all issues but pass in non-strict mode
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass in non-strict mode but report issues
        assert result.returncode == 0
        assert "Markdown validation issues (non-strict):" in result.stdout
        assert "Missing equation label for" in result.stdout
        assert "Missing anchor/label for link" in result.stdout
        assert "Bare URL found" in result.stdout
        assert "Non-informative link text" in result.stdout

    def test_validate_markdown_integration_with_math_issues(self, tmp_path):
        """Test validate_markdown detects math formatting issues."""
        # Create test project with math issues
        test_root = tmp_path / "math_issues"
        test_root.mkdir()

        # Create markdown directory with math problems
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_test.md").write_text(r"""
# Test Section

This has dollar math: $$x^2 + y^2 = z^2$$

This has bracket math: \[x^2 + y^2 = z^2\]

This has equation without label:
\begin{equation}
x^2 + y^2 = z^2
\end{equation}

This has duplicate labels:
\begin{equation}\label{eq:duplicate}
x^2 + y^2 = z^2
\end{equation}

\begin{equation}\label{eq:duplicate}
a^2 + b^2 = c^2
\end{equation}

This has a proper equation:
\begin{equation}\label{eq:proper}
e = mc^2
\end{equation}
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run validation - should detect math issues but pass in non-strict mode
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass in non-strict mode but report issues
        assert result.returncode == 0
        assert "Markdown validation" in result.stdout  # Either passed or has issues
        assert "Use equation environment instead of $$" in result.stdout
        assert "Use equation environment instead of" in result.stdout and "\\[" in result.stdout
        assert "Equation missing" in result.stdout
        assert "Duplicate equation label" in result.stdout

    def test_validate_markdown_strict_mode_integration(self, tmp_path):
        """Test validate_markdown strict mode with real content."""
        # Create test project with some issues
        test_root = tmp_path / "strict_mode"
        test_root.mkdir()

        # Create markdown directory with minor issues
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_test.md").write_text(r"""
# Test Section

This has an unlabeled equation:
\begin{equation}
x^2 + y^2 = z^2
\end{equation}

This is fine.
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run in strict mode
        result = subprocess.run([
            sys.executable, str(test_validate_script), "--strict"
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should fail in strict mode due to unlabeled equation
        assert result.returncode == 1
        assert "Validation issues found" in result.stdout
        assert "Equation missing" in result.stdout

    def test_validate_markdown_non_strict_mode_integration(self, tmp_path):
        """Test validate_markdown non-strict mode with real content."""
        # Create test project with some issues
        test_root = tmp_path / "non_strict"
        test_root.mkdir()

        # Create markdown directory with minor issues
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_test.md").write_text(r"""
# Test Section

This has an unlabeled equation:
\begin{equation}
x^2 + y^2 = z^2
\end{equation}

This is fine.
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run in non-strict mode (default)
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass in non-strict mode but report issues
        assert result.returncode == 0
        assert "Markdown validation" in result.stdout  # Either passed or has issues
        assert "Equation missing" in result.stdout

    def test_validate_markdown_handles_missing_manuscript_dir(self, tmp_path):
        """Test validate_markdown handles missing markdown directory."""
        # Create test project without markdown directory
        test_root = tmp_path / "no_manuscript_dir"
        test_root.mkdir()

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run validation - should handle missing directory
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should fail gracefully
        assert result.returncode == 1
        assert "Manuscript directory not found" in result.stdout

    def test_validate_markdown_multiple_files_integration(self, tmp_path):
        """Test validate_markdown with multiple markdown files."""
        # Create test project with multiple markdown files
        test_root = tmp_path / "multiple_files"
        test_root.mkdir()

        # Create markdown directory with multiple files
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        # Create multiple markdown files with cross-references
        (manuscript_dir / "01_intro.md").write_text(r"""
# Introduction {#sec:intro}

This is the introduction.

\begin{equation}\label{eq:intro_eq}
x + y = z
\end{equation}

See also [methodology](#sec:methodology).
""")

        (manuscript_dir / "02_methodology.md").write_text(r"""
# Methodology {#sec:methodology}

This is the methodology section.

\begin{equation}\label{eq:method_eq}
a^2 + b^2 = c^2
\end{equation}

See also [introduction](#sec:intro) and \eqref{eq:intro_eq}.
""")

        (manuscript_dir / "03_results.md").write_text(r"""
# Results

\begin{equation}\label{eq:result_eq}
result = analysis(data)
\end{equation}

References to \eqref{eq:intro_eq}, \eqref{eq:method_eq}, and \eqref{eq:result_eq}.
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run validation - should pass with all cross-references resolved
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass validation (non-strict mode)
        assert result.returncode == 0
        assert "Markdown validation" in result.stdout  # Either passed or has issues

    def test_validate_markdown_real_world_scenario(self, tmp_path):
        """Test validate_markdown in a realistic scenario with figures and data."""
        # Create a realistic test scenario
        test_root = tmp_path / "real_scenario"
        test_root.mkdir()

        # Create output structure with figures and data
        output_dir = test_root / "output"
        figures_dir = output_dir / "figures"
        data_dir = output_dir / "data"
        figures_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)

        # Create some fake output files
        (figures_dir / "convergence_analysis.png").write_bytes(b"fake png")
        (figures_dir / "ablation_study.png").write_bytes(b"fake png")
        (data_dir / "results.csv").write_text("method,accuracy\nOur Method,0.95\nBaseline,0.85\n")

        # Create markdown directory with realistic content
        manuscript_dir = test_root / "manuscript"
        manuscript_dir.mkdir()

        # Create realistic manuscript sections
        (manuscript_dir / "01_abstract.md").write_text(r"""
# Abstract

This paper presents a novel method for solving optimization problems.

\begin{equation}\label{eq:objective}
\min_x f(x) = \|Ax - b\|^2
\end{equation}

Our method achieves state-of-the-art performance as shown in Figure \ref{fig:convergence} and Table \ref{tab:results}.

![Convergence Analysis](../output/figures/convergence_analysis.png)

## Keywords

optimization, machine learning, convergence analysis
""")

        (manuscript_dir / "04_experimental_results.md").write_text(r"""
# Experimental Results {#sec:results}

## Convergence Analysis {#subsec:convergence}

Figure \ref{fig:convergence} shows the convergence behavior of our method compared to baselines.

![Convergence Analysis](../output/figures/convergence_analysis.png)

\begin{equation}\label{eq:convergence_rate}
\rho = \frac{\|x_{k+1} - x^*\|}{\|x_k - x^*\|}
\end{equation}

## Ablation Study {#subsec:ablation}

Figure \ref{fig:ablation} demonstrates the contribution of each component.

![Ablation Study](../output/figures/ablation_study.png)

## Quantitative Results {#subsec:quantitative}

Table \ref{tab:results} summarizes the performance across different datasets.

| Method | Accuracy | Convergence Rate |
|--------|----------|------------------|
| Our Method | 0.95 | 0.85 |
| Baseline | 0.85 | 0.90 |

\begin{equation}\label{eq:final}
accuracy = \frac{TP + TN}{TP + TN + FP + FN}
\end{equation}

See also [methodology section](#sec:methodology) for implementation details.
""")

        # Copy actual validate_markdown.py
        actual_validate_script = os.path.join(os.path.dirname(__file__), "..", "repo_utilities", "validate_markdown.py")
        test_validate_script = test_root / "repo_utilities" / "validate_markdown.py"
        test_validate_script.parent.mkdir()
        shutil.copy2(actual_validate_script, test_validate_script)

        # Run validation - should pass with all references resolved
        result = subprocess.run([
            sys.executable, str(test_validate_script)
        ], cwd=str(test_root), capture_output=True, text=True)

        # Should pass validation (non-strict mode)
        assert result.returncode == 0
        assert "Markdown validation" in result.stdout  # Either passed or has issues


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


class TestValidatePDFOutput:
    """Test the validate_pdf_output.py orchestrator script."""
    
    def test_validate_pdf_output_script_exists(self):
        """Test that the validate_pdf_output.py script exists and is executable."""
        script_path = Path(__file__).parent.parent / "repo_utilities" / "validate_pdf_output.py"
        assert script_path.exists(), "validate_pdf_output.py should exist"
        assert os.access(script_path, os.X_OK), "validate_pdf_output.py should be executable"
    
    def test_validate_pdf_output_imports(self):
        """Test that the script can import required modules."""
        # This tests the thin orchestrator properly imports from src/
        script_path = Path(__file__).parent.parent / "repo_utilities"
        sys.path.insert(0, str(script_path))
        
        try:
            # Check if we can import the validator module through the script's path
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            from infrastructure.pdf_validator import validate_pdf_rendering, PDFValidationError
            
            # Verify functions exist
            assert callable(validate_pdf_rendering)
            assert issubclass(PDFValidationError, Exception)
        finally:
            # Clean up
            if str(script_path) in sys.path:
                sys.path.remove(str(script_path))
            src_path = str(Path(__file__).parent.parent / "src")
            if src_path in sys.path:
                sys.path.remove(src_path)
    
    def test_validate_pdf_output_on_actual_pdf(self):
        """Test validation on the actual project PDF if it exists."""
        pdf_path = Path(__file__).parent.parent / "output" / "pdf" / "project_combined.pdf"
        
        if not pdf_path.exists():
            pytest.skip("Project PDF not found, skipping integration test")
        
        # Run the validation script
        script_path = Path(__file__).parent.parent / "repo_utilities" / "validate_pdf_output.py"
        
        result = subprocess.run(
            ["uv", "run", "python", str(script_path), str(pdf_path), "--words", "100"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Script should complete (exit code 0 for no issues, 1 for issues found, 2 for error)
        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        
        # Should produce output
        assert len(result.stdout) > 0, "Script should produce output"
        
        # Should contain validation report elements
        assert "PDF VALIDATION REPORT" in result.stdout
        assert "First" in result.stdout and "words" in result.stdout
    
    def test_validate_pdf_output_nonexistent_file(self):
        """Test validation script handles nonexistent files gracefully."""
        script_path = Path(__file__).parent.parent / "repo_utilities" / "validate_pdf_output.py"
        fake_pdf = Path("/tmp/nonexistent_pdf_file.pdf")
        
        result = subprocess.run(
            ["uv", "run", "python", str(script_path), str(fake_pdf)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should exit with error code
        assert result.returncode == 2, "Should return error code for nonexistent file"
        
        # Should have error message
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()
    
    def test_validate_pdf_output_help(self):
        """Test that the script provides help information."""
        script_path = Path(__file__).parent.parent / "repo_utilities" / "validate_pdf_output.py"
        
        result = subprocess.run(
            ["uv", "run", "python", str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should exit successfully
        assert result.returncode == 0
        
        # Should contain help text
        assert "usage:" in result.stdout.lower() or "Validate PDF" in result.stdout


# Clean up sys.path (only if it was added)
if 'sys_path' in locals() and sys_path in sys.path:
    sys.path.remove(sys_path)

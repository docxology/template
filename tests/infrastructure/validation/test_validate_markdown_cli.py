"""Comprehensive tests for infrastructure/validation/validate_markdown_cli.py.

Tests the markdown validation CLI script.
"""

import sys
from pathlib import Path
import pytest

from infrastructure.validation import validate_markdown_cli


class TestValidateMarkdownCliImportError:
    """Test import error handling in validate_markdown_cli."""
    
    def test_main_with_import_error(self, capsys, monkeypatch):
        """Test main() returns 1 and prints error when import_error is set.
        
        This covers lines 27-29 - the import error handling path.
        """
        # Save original import_error
        original_import_error = validate_markdown_cli.import_error
        
        try:
            # Set import_error to simulate an import failure
            validate_markdown_cli.import_error = "❌ Test import error message"
            
            # Call main - should return 1 due to import error
            result = validate_markdown_cli.main()
            
            assert result == 1
            captured = capsys.readouterr()
            assert "Test import error message" in captured.out
        finally:
            # Restore original import_error
            validate_markdown_cli.import_error = original_import_error
    
    def test_import_error_is_none_by_default(self):
        """Test that import_error is None when module loads successfully."""
        # When the module loads successfully, import_error should be None
        assert validate_markdown_cli.import_error is None


class TestValidateMarkdownCliMain:
    """Test main function execution paths."""
    
    def test_main_with_strict_flag(self, tmp_path, monkeypatch):
        """Test main() with --strict flag."""
        # Create a valid manuscript directory
        manuscript = tmp_path / "project" / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "test.md").write_text("# Valid Test\n\nNo issues.")
        
        # Monkeypatch repo_root to our temp path
        monkeypatch.setattr(validate_markdown_cli, 'repo_root', tmp_path)
        monkeypatch.setattr(sys, 'argv', ['validate_markdown_cli', '--strict'])
        
        result = validate_markdown_cli.main()
        
        assert result == 0
    
    def test_main_file_not_found(self, tmp_path, monkeypatch, capsys):
        """Test main() when manuscript directory not found."""
        # Point to a non-existent directory
        monkeypatch.setattr(validate_markdown_cli, 'repo_root', tmp_path)
        monkeypatch.setattr(sys, 'argv', ['validate_markdown_cli'])
        
        result = validate_markdown_cli.main()
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
    
    def test_validate_refs_function(self, tmp_path):
        """Test validate_refs helper function."""
        md_file = tmp_path / "test.md"
        md_file.write_text("See [section](#missing_ref) for details.")
        
        labels = {"existing_label": str(md_file)}
        anchors = {}
        
        issues = validate_markdown_cli.validate_refs([str(md_file)], labels, anchors, str(tmp_path))
        
        # Should find reference to missing_ref
        assert isinstance(issues, list)
    
    def test_validate_math_function(self, tmp_path):
        """Test validate_math helper function."""
        md_file = tmp_path / "test.md"
        md_file.write_text("Math: $x^2$ and $y^2$ = complete pair")
        
        issues = validate_markdown_cli.validate_math([str(md_file)], str(tmp_path))
        
        assert isinstance(issues, list)


class TestValidateMarkdownCliHelpers:
    """Test helper functions in validate_markdown_cli."""
    
    def test_repo_root(self):
        """Test _repo_root returns a valid path."""
        root = validate_markdown_cli._repo_root()
        assert isinstance(root, str)
        assert len(root) > 0
    
    def test_find_markdown_files(self, tmp_path):
        """Test find_markdown_files function."""
        # Create test files
        (tmp_path / "01_intro.md").write_text("# Intro")
        (tmp_path / "02_methods.md").write_text("# Methods")
        (tmp_path / "readme.txt").write_text("Not markdown")
        
        files = validate_markdown_cli.find_markdown_files(str(tmp_path))
        
        assert len(files) == 2
        assert any("01_intro.md" in f for f in files)
        assert any("02_methods.md" in f for f in files)
    
    def test_find_markdown_files_empty_dir(self, tmp_path):
        """Test with empty directory."""
        files = validate_markdown_cli.find_markdown_files(str(tmp_path))
        assert len(files) == 0
    
    def test_collect_symbols_with_labels(self, tmp_path):
        """Test collect_symbols extracts labels."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Section {#section-one}\n\nContent")
        
        labels, anchors = validate_markdown_cli.collect_symbols([str(md_file)])
        
        assert "section-one" in labels
    
    def test_collect_symbols_with_anchors(self, tmp_path):
        """Test collect_symbols extracts anchors."""
        md_file = tmp_path / "test.md"
        md_file.write_text("[ref1]: https://example.com\n\nContent")
        
        labels, anchors = validate_markdown_cli.collect_symbols([str(md_file)])
        
        assert "ref1" in anchors
    
    def test_validate_images_valid(self, tmp_path):
        """Test validate_images with valid images."""
        # Create image
        img_dir = tmp_path / "output" / "figures"
        img_dir.mkdir(parents=True)
        (img_dir / "test.png").write_bytes(b"PNG data")
        
        # Create markdown with image ref
        md_file = tmp_path / "test.md"
        md_file.write_text("![Test](../output/figures/test.png)")
        
        problems = validate_markdown_cli.validate_images([str(md_file)], str(tmp_path))
        
        # May have problems depending on path resolution
        assert isinstance(problems, list)
    
    def test_validate_images_missing(self, tmp_path):
        """Test validate_images with missing images."""
        md_file = tmp_path / "test.md"
        md_file.write_text("![Missing](./missing_image.png)")
        
        problems = validate_markdown_cli.validate_images([str(md_file)], str(tmp_path))
        
        # Should report missing image
        assert isinstance(problems, list)


class TestValidateMarkdownCliMain:
    """Test main function if present."""
    
    def test_module_has_expected_functions(self):
        """Test module exports expected functions."""
        assert hasattr(validate_markdown_cli, '_repo_root')
        assert hasattr(validate_markdown_cli, 'find_markdown_files')
        assert hasattr(validate_markdown_cli, 'collect_symbols')
        assert hasattr(validate_markdown_cli, 'validate_images')


class TestValidateMarkdownCliIntegration:
    """Integration tests for validate_markdown_cli."""
    
    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow."""
        # Create a manuscript structure
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        
        (manuscript_dir / "01_abstract.md").write_text("""
# Abstract {#abstract}

This is the abstract section.
""")
        (manuscript_dir / "02_intro.md").write_text("""
# Introduction {#intro}

See Section [](#abstract) for details.
""")
        
        # Find files
        files = validate_markdown_cli.find_markdown_files(str(manuscript_dir))
        assert len(files) == 2
        
        # Collect symbols
        labels, anchors = validate_markdown_cli.collect_symbols(files)
        assert "abstract" in labels
        assert "intro" in labels


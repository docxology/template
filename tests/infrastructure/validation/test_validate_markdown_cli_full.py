"""Full tests for infrastructure/validation/validate_markdown_cli.py.

Tests Markdown validation CLI functionality thoroughly.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestValidateMarkdownCliFunctions:
    """Test module functions."""
    
    def test_repo_root(self):
        """Test _repo_root helper."""
        from infrastructure.validation.validate_markdown_cli import _repo_root
        
        result = _repo_root()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_find_markdown_files(self, tmp_path):
        """Test find_markdown_files function."""
        from infrastructure.validation.validate_markdown_cli import find_markdown_files
        
        (tmp_path / "01_intro.md").write_text("# Intro")
        (tmp_path / "02_body.md").write_text("# Body")
        (tmp_path / "03_conclusion.md").write_text("# Conclusion")
        
        files = find_markdown_files(str(tmp_path))
        
        assert len(files) == 3
        # Files should be sorted numerically
        assert any("01_intro.md" in f for f in files)
    
    def test_find_markdown_files_no_extension(self, tmp_path):
        """Test find_markdown_files with non-markdown files."""
        from infrastructure.validation.validate_markdown_cli import find_markdown_files
        
        (tmp_path / "test.txt").write_text("Not markdown")
        (tmp_path / "doc.md").write_text("# Doc")
        
        files = find_markdown_files(str(tmp_path))
        
        assert len(files) == 1
        assert "doc.md" in files[0]
    
    def test_collect_symbols(self, tmp_path):
        """Test collect_symbols function."""
        from infrastructure.validation.validate_markdown_cli import collect_symbols
        
        md = tmp_path / "test.md"
        md.write_text("# Title {#title}\n\n[ref]: http://example.com")
        
        labels, anchors = collect_symbols([str(md)])
        
        assert "title" in labels
        assert "ref" in anchors
    
    def test_collect_symbols_empty_file(self, tmp_path):
        """Test collect_symbols with empty file."""
        from infrastructure.validation.validate_markdown_cli import collect_symbols
        
        md = tmp_path / "empty.md"
        md.write_text("")
        
        labels, anchors = collect_symbols([str(md)])
        
        assert len(labels) == 0
        assert len(anchors) == 0
    
    def test_validate_images_found(self, tmp_path):
        """Test validate_images with existing image."""
        from infrastructure.validation.validate_markdown_cli import validate_images
        
        (tmp_path / "img.png").write_bytes(b'\x89PNG')
        md = tmp_path / "doc.md"
        md.write_text("![Alt](img.png)")
        
        issues = validate_images([str(md)], str(tmp_path))
        
        assert len(issues) == 0
    
    def test_validate_images_missing(self, tmp_path):
        """Test validate_images with missing image."""
        from infrastructure.validation.validate_markdown_cli import validate_images
        
        md = tmp_path / "doc.md"
        md.write_text("![Alt](missing.png)")
        
        issues = validate_images([str(md)], str(tmp_path))
        
        assert len(issues) == 1
        assert "not found" in issues[0]
    
    def test_validate_images_url(self, tmp_path):
        """Test validate_images with URL image."""
        from infrastructure.validation.validate_markdown_cli import validate_images
        
        md = tmp_path / "doc.md"
        md.write_text("![Alt](http://example.com/img.png)")
        
        issues = validate_images([str(md)], str(tmp_path))
        
        # URLs should not be validated
        assert len(issues) == 0
    
    def test_validate_refs_found(self, tmp_path):
        """Test validate_refs with existing reference."""
        from infrastructure.validation.validate_markdown_cli import validate_refs
        
        md = tmp_path / "doc.md"
        md.write_text("# Section {#section}\n\n[Link](#section)")
        
        labels = {"section": str(md)}
        issues = validate_refs([str(md)], labels, {}, str(tmp_path))
        
        assert len(issues) == 0
    
    def test_validate_refs_missing(self, tmp_path):
        """Test validate_refs with missing reference."""
        from infrastructure.validation.validate_markdown_cli import validate_refs
        
        md = tmp_path / "doc.md"
        md.write_text("[Link](#missing)")
        
        labels = {}
        issues = validate_refs([str(md)], labels, {}, str(tmp_path))
        
        assert len(issues) == 1
        assert "not found" in issues[0]
    
    def test_validate_math_balanced(self, tmp_path):
        """Test validate_math with balanced $ symbols."""
        from infrastructure.validation.validate_markdown_cli import validate_math
        
        md = tmp_path / "doc.md"
        md.write_text("Math: $E = mc^2$ and $F = ma$")
        
        issues = validate_math([str(md)], str(tmp_path))
        
        assert len(issues) == 0
    
    def test_validate_math_unbalanced(self, tmp_path):
        """Test validate_math with unbalanced $ symbols."""
        from infrastructure.validation.validate_markdown_cli import validate_math
        
        md = tmp_path / "doc.md"
        md.write_text("Math: $E = mc^2")
        
        issues = validate_math([str(md)], str(tmp_path))
        
        assert len(issues) == 1
        assert "Unmatched" in issues[0]


class TestValidateMarkdownMain:
    """Test main function."""
    
    def test_main_success(self, tmp_path, capsys):
        """Test main with valid markdown."""
        from infrastructure.validation import validate_markdown_cli
        
        with patch.object(validate_markdown_cli, 'import_error', None):
            with patch('infrastructure.validation.validate_markdown_cli.find_manuscript_directory') as mock_find:
                mock_find.return_value = str(tmp_path)
                
                with patch('infrastructure.validation.validate_markdown_cli.validate_markdown') as mock_validate:
                    mock_validate.return_value = ([], 0)
                    
                    exit_code = validate_markdown_cli.main()
                    
                    assert exit_code == 0
    
    def test_main_with_issues(self, tmp_path, capsys):
        """Test main with validation issues."""
        from infrastructure.validation import validate_markdown_cli
        
        with patch.object(validate_markdown_cli, 'import_error', None):
            with patch('infrastructure.validation.validate_markdown_cli.find_manuscript_directory') as mock_find:
                mock_find.return_value = str(tmp_path)
                
                with patch('infrastructure.validation.validate_markdown_cli.validate_markdown') as mock_validate:
                    mock_validate.return_value = (["Issue 1", "Issue 2"], 1)
                    
                    exit_code = validate_markdown_cli.main()
                    
                    assert exit_code == 1
    
    def test_main_import_error(self, capsys):
        """Test main with import error."""
        from infrastructure.validation import validate_markdown_cli
        
        with patch.object(validate_markdown_cli, 'import_error', "Import failed"):
            exit_code = validate_markdown_cli.main()
            
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Import failed" in captured.out
    
    def test_main_file_not_found(self, capsys):
        """Test main with FileNotFoundError."""
        from infrastructure.validation import validate_markdown_cli
        
        with patch.object(validate_markdown_cli, 'import_error', None):
            with patch('infrastructure.validation.validate_markdown_cli.find_manuscript_directory') as mock_find:
                mock_find.side_effect = FileNotFoundError("Not found")
                
                exit_code = validate_markdown_cli.main()
                
                assert exit_code == 1
    
    def test_main_unexpected_error(self, capsys):
        """Test main with unexpected error."""
        from infrastructure.validation import validate_markdown_cli
        
        with patch.object(validate_markdown_cli, 'import_error', None):
            with patch('infrastructure.validation.validate_markdown_cli.find_manuscript_directory') as mock_find:
                mock_find.side_effect = Exception("Unexpected")
                
                exit_code = validate_markdown_cli.main()
                
                assert exit_code == 1


class TestValidateMarkdownIntegration:
    """Integration tests."""
    
    def test_module_structure(self):
        """Test module has expected structure."""
        from infrastructure.validation import validate_markdown_cli
        
        assert hasattr(validate_markdown_cli, 'main')
        assert hasattr(validate_markdown_cli, 'find_markdown_files')
        assert hasattr(validate_markdown_cli, 'collect_symbols')
        assert hasattr(validate_markdown_cli, 'validate_images')
        assert hasattr(validate_markdown_cli, 'validate_refs')
        assert hasattr(validate_markdown_cli, 'validate_math')


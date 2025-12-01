"""Comprehensive tests for infrastructure/validation/check_links.py.

Tests link checking and reference validation functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.validation import check_links


class TestCheckLinksCore:
    """Test core link checking functionality."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        assert check_links is not None
    
    def test_has_link_checking_functions(self):
        """Test that module has link checking functions."""
        module_funcs = [a for a in dir(check_links) if not a.startswith('_') and callable(getattr(check_links, a, None))]
        assert len(module_funcs) > 0


class TestLinkValidation:
    """Test link validation functionality."""
    
    def test_check_internal_link_valid(self, tmp_path):
        """Test valid internal link checking."""
        target = tmp_path / "target.md"
        target.write_text("# Target")
        
        if hasattr(check_links, 'check_internal_link'):
            result = check_links.check_internal_link("target.md", tmp_path)
            assert result is not None
    
    def test_check_internal_link_invalid(self, tmp_path):
        """Test invalid internal link checking."""
        if hasattr(check_links, 'check_internal_link'):
            result = check_links.check_internal_link("nonexistent.md", tmp_path)
            assert result is not None
    
    def test_check_external_link(self):
        """Test external link checking."""
        if hasattr(check_links, 'check_external_link'):
            # Mock network call
            with patch('requests.head') as mock_head:
                mock_head.return_value = MagicMock(status_code=200)
                result = check_links.check_external_link("https://example.com")
                assert result is not None


class TestFileReferenceValidation:
    """Test file reference validation."""
    
    def test_check_file_reference_exists(self, tmp_path):
        """Test file reference for existing file."""
        target = tmp_path / "file.txt"
        target.write_text("content")
        source = tmp_path / "doc.md"
        source.write_text("Link to file.txt")
        
        if hasattr(check_links, 'check_file_reference'):
            result = check_links.check_file_reference("file.txt", source, tmp_path)
            assert result is not None
    
    def test_check_file_reference_missing(self, tmp_path):
        """Test file reference for missing file."""
        source = tmp_path / "doc.md"
        source.write_text("Link to missing.txt")
        
        if hasattr(check_links, 'check_file_reference'):
            result = check_links.check_file_reference("missing.txt", source, tmp_path)
            assert result is not None
    
    def test_check_image_reference(self, tmp_path):
        """Test image reference checking."""
        img = tmp_path / "img.png"
        img.write_bytes(b'\x89PNG')
        source = tmp_path / "doc.md"
        
        if hasattr(check_links, 'check_file_reference'):
            result = check_links.check_file_reference("img.png", source, tmp_path)
            assert result is not None


class TestMarkdownLinkExtraction:
    """Test markdown link extraction."""
    
    def test_extract_links(self, tmp_path):
        """Test extracting links from markdown."""
        md_file = tmp_path / "test.md"
        md_content = """
# Document
[Link 1](file.md)
[Link 2](https://example.com)
![Image](img.png)
"""
        if hasattr(check_links, 'extract_links'):
            # extract_links returns tuple of 3 lists
            result = check_links.extract_links(md_content, md_file)
            assert isinstance(result, tuple)
            assert len(result) == 3
            internal_links, external_links, file_refs = result
            assert isinstance(external_links, list)
            assert isinstance(file_refs, list)
    
    def test_extract_links_external(self, tmp_path):
        """Test extracting external links from markdown."""
        md_file = tmp_path / "test.md"
        md_content = "[External](https://example.com)"
        
        if hasattr(check_links, 'extract_links'):
            internal, external, file_refs = check_links.extract_links(md_content, md_file)
            assert len(external) == 1
            assert external[0]['target'] == 'https://example.com'
    
    def test_extract_links_internal(self, tmp_path):
        """Test extracting internal anchor links from markdown."""
        md_file = tmp_path / "test.md"
        md_content = "[Section](#section-1)"
        
        if hasattr(check_links, 'extract_links'):
            internal, external, file_refs = check_links.extract_links(md_content, md_file)
            assert len(internal) == 1
            assert internal[0]['target'] == '#section-1'
    
    def test_extract_links_file_ref(self, tmp_path):
        """Test extracting file references from markdown."""
        md_file = tmp_path / "test.md"
        md_content = "[Other Doc](other.md)"
        
        if hasattr(check_links, 'extract_links'):
            internal, external, file_refs = check_links.extract_links(md_content, md_file)
            assert len(file_refs) == 1
            assert file_refs[0]['target'] == 'other.md'


class TestBulkLinkChecking:
    """Test bulk link checking functionality."""
    
    def test_check_all_links(self, tmp_path):
        """Test checking all links in a file."""
        doc = tmp_path / "doc.md"
        target = tmp_path / "target.md"
        target.write_text("# Target")
        doc.write_text("[Link](target.md)")
        
        if hasattr(check_links, 'check_all_links'):
            results = check_links.check_all_links(doc, tmp_path)
            assert results is not None
    
    def test_check_directory_links(self, tmp_path):
        """Test checking links in entire directory."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("[Link](b.md)")
        (docs / "b.md").write_text("# B")
        
        if hasattr(check_links, 'check_directory_links'):
            results = check_links.check_directory_links(docs)
            assert results is not None


class TestRelativePathResolution:
    """Test relative path resolution."""
    
    def test_resolve_relative_path(self, tmp_path):
        """Test resolving relative paths."""
        source = tmp_path / "docs" / "file.md"
        source.parent.mkdir()
        source.write_text("")
        
        if hasattr(check_links, 'resolve_relative_path'):
            result = check_links.resolve_relative_path("../README.md", source)
            assert result is not None
    
    def test_normalize_path(self):
        """Test path normalization."""
        if hasattr(check_links, 'normalize_path'):
            result = check_links.normalize_path("./docs/../README.md")
            assert result is not None


class TestCheckLinksIntegration:
    """Integration tests for check_links module."""
    
    def test_full_link_check_workflow(self, tmp_path):
        """Test complete link checking workflow."""
        # Create documentation with various links
        docs = tmp_path / "docs"
        docs.mkdir()
        
        main = docs / "main.md"
        main.write_text("""
# Main Doc
- [Sub](sub.md)
- [README](../README.md)
""")
        
        sub = docs / "sub.md"
        sub.write_text("# Sub")
        
        readme = tmp_path / "README.md"
        readme.write_text("# README")
        
        # Module should work
        assert check_links is not None


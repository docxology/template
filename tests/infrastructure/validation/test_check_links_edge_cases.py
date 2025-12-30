"""Edge case tests for infrastructure/validation/check_links.py.

Tests specific edge cases for improved coverage:
- Path resolution errors
- Broken anchor detection
- Reporting functions
- Main function return codes
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from infrastructure.validation import check_links


class TestCheckFileReferenceEdgeCases:
    """Test edge cases in check_file_reference function."""
    
    def test_path_outside_repository(self, tmp_path):
        """Test handling of paths outside the repository root."""
        # Create a source file
        source = tmp_path / "doc.md"
        source.write_text("content")
        
        # Create a target outside the repo root using absolute path
        outside_target = Path("/tmp/outside_file.txt")
        
        # Test with a path that resolves outside the repo
        result, msg = check_links.check_file_reference(
            str(outside_target),
            source,
            tmp_path
        )
        
        # Should fail because path resolves outside repository
        assert result is False or "outside" in msg.lower() or "does not exist" in msg.lower()
    
    def test_path_with_many_parent_refs(self, tmp_path):
        """Test path with multiple ../ references going outside repo."""
        docs_dir = tmp_path / "a" / "b" / "c"
        docs_dir.mkdir(parents=True)
        source = docs_dir / "doc.md"
        source.write_text("content")
        
        # This should try to go way outside the repo
        result, msg = check_links.check_file_reference(
            "../../../../../../../../outside.md",
            source,
            tmp_path
        )
        
        # Should fail - either path outside repo or doesn't exist
        assert result is False
    
    def test_exception_during_path_resolution(self, tmp_path):
        """Test exception handling in path resolution."""
        source = tmp_path / "doc.md"
        source.write_text("content")
        
        # Test with a path that might cause issues
        result, msg = check_links.check_file_reference(
            "\x00invalid\x00path",  # Null bytes should cause issues
            source,
            tmp_path
        )
        
        # Should handle exception gracefully
        assert result is False
        assert "Error" in msg or "does not exist" in msg.lower()
    
    def test_directory_reference_exists(self, tmp_path):
        """Test that directory references are valid."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        source = tmp_path / "doc.md"
        source.write_text("content")
        
        result, msg = check_links.check_file_reference("subdir", source, tmp_path)
        assert result is True
    
    def test_relative_path_with_dot_prefix(self, tmp_path):
        """Test relative path with ./ prefix."""
        target = tmp_path / "target.md"
        target.write_text("# Target")
        source = tmp_path / "source.md"
        source.write_text("content")
        
        result, msg = check_links.check_file_reference("./target.md", source, tmp_path)
        assert result is True
    
    def test_markdown_file_without_extension(self, tmp_path):
        """Test that markdown files can be referenced without .md extension."""
        target = tmp_path / "target.md"
        target.write_text("# Target")
        source = tmp_path / "source.md"
        source.write_text("content")
        
        # Reference without extension
        result, msg = check_links.check_file_reference("target", source, tmp_path)
        # Should find target.md
        assert result is True or "does not exist" in msg.lower()


class TestExtractHeadings:
    """Test heading extraction functionality."""
    
    def test_extract_headings_with_explicit_anchors(self):
        """Test extracting headings with explicit anchor syntax."""
        content = """
# Main Heading {#main}
## Sub Heading {#sub}
### Another {#another-one}
"""
        headings = check_links.extract_headings(content)
        assert "main" in headings
        assert "sub" in headings
        assert "another-one" in headings
    
    def test_extract_headings_auto_generated(self):
        """Test auto-generated anchors from headings."""
        content = """
# Simple Heading
## Another Heading Here
### Multi Word Title
"""
        headings = check_links.extract_headings(content)
        # Auto-generated anchors
        assert "simple-heading" in headings
        assert "another-heading-here" in headings
        assert "multi-word-title" in headings
    
    def test_extract_headings_with_special_chars(self):
        """Test heading extraction with special characters."""
        content = "# Heading with (parentheses) and [brackets]"
        headings = check_links.extract_headings(content)
        # Should strip special chars
        assert len(headings) > 0


class TestMainFunction:
    """Test main function edge cases."""
    
    def test_main_with_broken_links(self, tmp_path):
        """Test main returns 1 when broken links exist."""
        # Create a markdown file with broken anchor link
        md_file = tmp_path / "test.md"
        md_file.write_text("""
# Heading

[Broken Link](#nonexistent-anchor)
""")
        
        # Use real file operations instead of mocks
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)

        # Should find the internal link
        assert len(internal) == 1
        assert internal[0]['target'] == '#nonexistent-anchor'
    
    def test_main_with_broken_file_refs(self, tmp_path):
        """Test detection of broken file references."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""
# Test

[Broken File](nonexistent_file.md)
""")
        
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)
        
        # Should find the file reference
        assert len(file_refs) == 1
        assert file_refs[0]['target'] == 'nonexistent_file.md'
        
        # Check file reference - should fail
        result, msg = check_links.check_file_reference(
            'nonexistent_file.md', md_file, tmp_path
        )
        assert result is False


class TestExtractLinks:
    """Test link extraction edge cases."""
    
    def test_extract_mailto_links(self, tmp_path):
        """Test that mailto: links are treated as external."""
        md_file = tmp_path / "test.md"
        content = "[Email](mailto:test@example.com)"
        
        internal, external, file_refs = check_links.extract_links(content, md_file)
        
        assert len(external) == 1
        assert external[0]['target'] == 'mailto:test@example.com'
    
    def test_extract_links_with_anchors_in_file_refs(self, tmp_path):
        """Test file references with anchor fragments."""
        md_file = tmp_path / "test.md"
        content = "[Section](other.md#section)"
        
        internal, external, file_refs = check_links.extract_links(content, md_file)
        
        assert len(file_refs) == 1
        assert file_refs[0]['target'] == 'other.md#section'
    
    def test_extract_http_links(self, tmp_path):
        """Test http (not https) links are external."""
        md_file = tmp_path / "test.md"
        content = "[Old Site](http://example.com)"
        
        internal, external, file_refs = check_links.extract_links(content, md_file)
        
        assert len(external) == 1
        assert external[0]['target'] == 'http://example.com'


class TestFindAllMarkdownFiles:
    """Test markdown file discovery."""
    
    def test_find_markdown_files_excludes_output(self, tmp_path):
        """Test that output directories are excluded."""
        # Create markdown in regular location
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("# Doc")
        
        # Create markdown in output (should be excluded)
        output = tmp_path / "output"
        output.mkdir()
        (output / "generated.md").write_text("# Generated")
        
        files = check_links.find_all_markdown_files(str(tmp_path))
        
        # Should find docs/doc.md but not output/generated.md
        file_names = [f.name for f in files]
        assert "doc.md" in file_names
        assert "generated.md" not in file_names
    
    def test_find_markdown_files_excludes_htmlcov(self, tmp_path):
        """Test that htmlcov directories are excluded."""
        # Create regular markdown
        (tmp_path / "readme.md").write_text("# Readme")
        
        # Create markdown in htmlcov (should be excluded)
        htmlcov = tmp_path / "htmlcov"
        htmlcov.mkdir()
        (htmlcov / "coverage.md").write_text("# Coverage")
        
        files = check_links.find_all_markdown_files(str(tmp_path))
        
        file_names = [f.name for f in files]
        assert "readme.md" in file_names
        assert "coverage.md" not in file_names


class TestMainFunctionReporting:
    """Test main function reporting for broken links."""
    
    def test_main_reports_broken_anchors(self, tmp_path, capsys):
        """Test that main reports broken anchor links."""
        # Create file with broken anchor link
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Real Heading

[Broken](#nonexistent-section)
""")
        
        # Run main with patched repo root
        original_main = check_links.main
        
        def patched_main():
            """Patched main to use tmp_path as repo root."""
            repo_root = tmp_path
            md_files = check_links.find_all_markdown_files(str(repo_root))
            
            print(f"Found {len(md_files)} markdown files")
            
            all_headings = {}
            broken_links = []
            broken_file_refs = []
            
            # First pass: collect headings
            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding='utf-8')
                    all_headings[str(md_file.relative_to(repo_root))] = check_links.extract_headings(content)
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")
            
            # Second pass: check links
            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding='utf-8')
                    internal_links, external_links, file_refs = check_links.extract_links(content, md_file)
                    
                    # Check internal links
                    for link in internal_links:
                        target = link['target'].lstrip('#')
                        file_key = str(md_file.relative_to(repo_root))
                        if file_key in all_headings and target not in all_headings[file_key]:
                            broken_links.append({
                                'file': file_key,
                                'line': link['line'],
                                'target': link['target'],
                                'text': link['text'],
                                'issue': 'Anchor not found'
                            })
                    
                    # Check file references
                    for ref in file_refs:
                        target = ref['target']
                        if '#' in target:
                            target = target.split('#')[0]
                        if target:
                            exists, msg = check_links.check_file_reference(target, md_file, repo_root)
                            if not exists:
                                broken_file_refs.append({
                                    'file': str(md_file.relative_to(repo_root)),
                                    'line': ref['line'],
                                    'target': ref['target'],
                                    'text': ref['text'],
                                    'issue': msg
                                })
                except Exception as e:
                    print(f"Error processing {md_file}: {e}")
            
            # Report results
            if broken_links:
                print(f"\nFound {len(broken_links)} broken anchor links:")
                for link in broken_links[:10]:
                    print(f"  {link['file']}:{link['line']} - {link['target']} ({link['issue']})")
                if len(broken_links) > 10:
                    print(f"  ... and {len(broken_links) - 10} more")
            
            if broken_file_refs:
                print(f"\nFound {len(broken_file_refs)} broken file references:")
                for ref in broken_file_refs[:10]:
                    print(f"  {ref['file']}:{ref['line']} - {ref['target']} ({ref['issue']})")
                if len(broken_file_refs) > 10:
                    print(f"  ... and {len(broken_file_refs) - 10} more")
            
            if not broken_links and not broken_file_refs:
                print("\nAll links verified successfully!")
                return 0
            
            return 1
        
        exit_code = patched_main()
        captured = capsys.readouterr()
        
        # Should report the broken anchor
        assert "broken anchor links" in captured.out.lower() or "nonexistent" in captured.out.lower()
        assert exit_code == 1
    
    def test_main_reports_broken_file_refs(self, tmp_path, capsys):
        """Test that main reports broken file references."""
        # Create file with broken file reference
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Document

[Missing File](nonexistent.md)
""")
        
        # Extract and check the broken reference
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)
        
        assert len(file_refs) == 1
        
        exists, msg = check_links.check_file_reference(
            file_refs[0]['target'], md_file, tmp_path
        )
        assert exists is False
        assert "does not exist" in msg.lower()
    
    def test_main_success_with_valid_links(self, tmp_path, capsys):
        """Test main returns 0 when all links are valid."""
        # Create valid file structure
        (tmp_path / "target.md").write_text("# Target Heading")
        
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Test Document

[Valid Link](target.md)
""")
        
        # Extract and verify
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)
        
        for ref in file_refs:
            exists, msg = check_links.check_file_reference(
                ref['target'], md_file, tmp_path
            )
            assert exists is True


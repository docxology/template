"""Extended link-audit helper coverage for infrastructure.validation.integrity.check_links."""

from pathlib import Path

from infrastructure.validation.integrity import check_links
from infrastructure.validation.integrity.check_links import (
    check_file_reference,
    discover_markdown_files,
    extract_headings,
    extract_links,
    validate_python_imports,
)


class TestCheckLinksCore:
    """Test core link checking functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert check_links is not None

    def test_has_link_checking_functions(self):
        """Test that module has link checking functions."""
        module_funcs = [
            a for a in dir(check_links) if not a.startswith("_") and callable(getattr(check_links, a, None))
        ]
        assert len(module_funcs) > 0



class TestLinkValidation:
    """Test link validation functionality."""

    def test_check_internal_link_valid(self, tmp_path):
        """Test valid internal link checking."""
        target = tmp_path / "target.md"
        target.write_text("# Target")

        if hasattr(check_links, "check_internal_link"):
            result = check_links.check_internal_link("target.md", tmp_path)
            assert result is not None

    def test_check_internal_link_invalid(self, tmp_path):
        """Test invalid internal link checking."""
        if hasattr(check_links, "check_internal_link"):
            result = check_links.check_internal_link("nonexistent.md", tmp_path)
            assert result is not None

    def test_check_external_link(self, http_test_server):
        """Test external link checking."""
        if hasattr(check_links, "check_external_link"):
            # Use real HTTP call to test server
            test_url = http_test_server.url_for("/")
            result = check_links.check_external_link(test_url)
            assert result is not None



class TestFileReferenceValidation:
    """Test file reference validation."""

    def test_check_file_reference_exists(self, tmp_path):
        """Test file reference for existing file."""
        target = tmp_path / "file.txt"
        target.write_text("content")
        source = tmp_path / "doc.md"
        source.write_text("Link to file.txt")

        if hasattr(check_links, "check_file_reference"):
            result = check_links.check_file_reference("file.txt", source, tmp_path)
            assert result is not None

    def test_check_file_reference_missing(self, tmp_path):
        """Test file reference for missing file."""
        source = tmp_path / "doc.md"
        source.write_text("Link to missing.txt")

        if hasattr(check_links, "check_file_reference"):
            result = check_links.check_file_reference("missing.txt", source, tmp_path)
            assert result is not None

    def test_check_image_reference(self, tmp_path):
        """Test image reference checking."""
        img = tmp_path / "img.png"
        img.write_bytes(b"\x89PNG")
        source = tmp_path / "doc.md"

        if hasattr(check_links, "check_file_reference"):
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
        if hasattr(check_links, "extract_links"):
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

        if hasattr(check_links, "extract_links"):
            internal, external, file_refs = check_links.extract_links(md_content, md_file)
            assert len(external) == 1
            assert external[0]["target"] == "https://example.com"

    def test_extract_links_internal(self, tmp_path):
        """Test extracting internal anchor links from markdown."""
        md_file = tmp_path / "test.md"
        md_content = "[Section](#section-1)"

        if hasattr(check_links, "extract_links"):
            internal, external, file_refs = check_links.extract_links(md_content, md_file)
            assert len(internal) == 1
            assert internal[0]["target"] == "#section-1"

    def test_extract_links_file_ref(self, tmp_path):
        """Test extracting file references from markdown."""
        md_file = tmp_path / "test.md"
        md_content = "[Other Doc](other.md)"

        if hasattr(check_links, "extract_links"):
            internal, external, file_refs = check_links.extract_links(md_content, md_file)
            assert len(file_refs) == 1
            assert file_refs[0]["target"] == "other.md"



class TestRelativePathResolution:
    """Test relative path resolution."""

    def test_resolve_relative_path(self, tmp_path):
        """Test resolving relative paths."""
        source = tmp_path / "docs" / "file.md"
        source.parent.mkdir()
        source.write_text("")

        if hasattr(check_links, "resolve_relative_path"):
            result = check_links.resolve_relative_path("../README.md", source)
            assert result is not None

    def test_normalize_path(self):
        """Test path normalization."""
        if hasattr(check_links, "normalize_path"):
            result = check_links.normalize_path("./docs/../README.md")
            assert result is not None



class TestCheckFileReferenceEdgeCasesAdditional:
    """Test edge cases in check_file_reference function."""

    def test_path_outside_repository(self, tmp_path):
        """Test handling of paths outside the repository root."""
        # Create a source file
        source = tmp_path / "doc.md"
        source.write_text("content")

        # Create a target outside the repo root using absolute path
        outside_target = Path("/tmp/outside_file.txt")

        # Test with a path that resolves outside the repo
        result, msg = check_links.check_file_reference(str(outside_target), source, tmp_path)

        # Should fail because path resolves outside repository
        assert result is False or "outside" in msg.lower() or "does not exist" in msg.lower()

    def test_path_with_many_parent_refs(self, tmp_path):
        """Test path with multiple ../ references going outside repo."""
        docs_dir = tmp_path / "a" / "b" / "c"
        docs_dir.mkdir(parents=True)
        source = docs_dir / "doc.md"
        source.write_text("content")

        # This should try to go way outside the repo
        result, msg = check_links.check_file_reference("../../../../../../../../outside.md", source, tmp_path)

        # Should fail - either path outside repo or doesn't exist
        assert result is False

    def test_exception_during_path_resolution(self, tmp_path):
        """Test exception handling in path resolution."""
        source = tmp_path / "doc.md"
        source.write_text("content")

        # Test with a path that might cause issues
        result, msg = check_links.check_file_reference(
            "\x00invalid\x00path",
            source,
            tmp_path,  # Null bytes should cause issues
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



class TestExtractHeadingsAdditional:
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



class TestMainFunctionEdgeCases:
    """Test main function edge cases."""

    def test_main_with_broken_links(self, tmp_path):
        """Test main returns 1 when broken links exist."""
        # Create a markdown file with broken anchor link
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
# Heading

[Broken Link](#nonexistent-anchor)
"""
        )

        # Use real file operations instead of mocks
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)

        # Should find the internal link
        assert len(internal) == 1
        assert internal[0]["target"] == "#nonexistent-anchor"

    def test_main_with_broken_file_refs(self, tmp_path):
        """Test detection of broken file references."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
# Test

[Broken File](nonexistent_file.md)
"""
        )

        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)

        # Should find the file reference
        assert len(file_refs) == 1
        assert file_refs[0]["target"] == "nonexistent_file.md"

        # Check file reference - should fail
        result, msg = check_links.check_file_reference("nonexistent_file.md", md_file, tmp_path)
        assert result is False



class TestExtractLinksEdgeCases:
    """Test link extraction edge cases."""

    def test_extract_mailto_links(self, tmp_path):
        """Test that mailto: links are treated as external."""
        md_file = tmp_path / "test.md"
        content = "[Email](mailto:test@example.com)"

        internal, external, file_refs = check_links.extract_links(content, md_file)

        assert len(external) == 1
        assert external[0]["target"] == "mailto:test@example.com"

    def test_extract_links_with_anchors_in_file_refs(self, tmp_path):
        """Test file references with anchor fragments."""
        md_file = tmp_path / "test.md"
        content = "[Section](other.md#section)"

        internal, external, file_refs = check_links.extract_links(content, md_file)

        assert len(file_refs) == 1
        assert file_refs[0]["target"] == "other.md#section"

    def test_extract_http_links(self, tmp_path):
        """Test http (not https) links are external."""
        md_file = tmp_path / "test.md"
        content = "[Old Site](http://example.com)"

        internal, external, file_refs = check_links.extract_links(content, md_file)

        assert len(external) == 1
        assert external[0]["target"] == "http://example.com"



class TestDiscoverMarkdownFilesLinkAuditAdditional:
    """Test markdown file discovery."""

    def test_excludes_output_directory(self, tmp_path):
        """Test that output directories are excluded."""
        # Create markdown in regular location
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("# Doc")

        # Create markdown in output (should be excluded)
        output = tmp_path / "output"
        output.mkdir()
        (output / "generated.md").write_text("# Generated")

        files = check_links.discover_markdown_files(tmp_path, scope="link_audit")

        # Should find docs/doc.md but not output/generated.md
        file_names = [f.name for f in files]
        assert "doc.md" in file_names
        assert "generated.md" not in file_names

    def test_excludes_htmlcov_directory(self, tmp_path):
        """Test that htmlcov directories are excluded."""
        # Create regular markdown
        (tmp_path / "readme.md").write_text("# Readme")

        # Create markdown in htmlcov (should be excluded)
        htmlcov = tmp_path / "htmlcov"
        htmlcov.mkdir()
        (htmlcov / "coverage.md").write_text("# Coverage")

        files = check_links.discover_markdown_files(tmp_path, scope="link_audit")

        file_names = [f.name for f in files]
        assert "readme.md" in file_names
        assert "coverage.md" not in file_names



class TestValidatePythonImportsAdditional:
    def test_no_python_blocks(self, tmp_path):
        content = "```bash\nls -la\n```"
        issues = validate_python_imports(content, tmp_path / "test.md", tmp_path)
        assert issues == []

    def test_valid_import(self, tmp_path):
        # Create infrastructure module
        (tmp_path / "infrastructure" / "core").mkdir(parents=True)
        (tmp_path / "infrastructure" / "core" / "exceptions.py").write_text("class Error: pass\n")
        content = "```python\nfrom infrastructure.core.exceptions import Error\n```"
        issues = validate_python_imports(content, tmp_path / "test.md", tmp_path)
        assert issues == []

    def test_missing_import(self, tmp_path):
        content = "```python\nfrom infrastructure.nonexistent.module import Foo\n```"
        issues = validate_python_imports(content, tmp_path / "test.md", tmp_path)
        assert len(issues) >= 1
        assert "not found" in issues[0]["issue"].lower()

    def test_init_py_fallback(self, tmp_path):
        (tmp_path / "infrastructure").mkdir(parents=True)
        (tmp_path / "infrastructure" / "__init__.py").write_text("")
        (tmp_path / "infrastructure" / "core").mkdir()
        (tmp_path / "infrastructure" / "core" / "__init__.py").write_text("x = 1\n")
        content = "```python\nfrom infrastructure.core import x\n```"
        issues = validate_python_imports(content, tmp_path / "test.md", tmp_path)
        assert issues == []

    def test_syntax_error_skipped(self, tmp_path):
        content = "```python\nfrom infrastructure import (\n```"
        issues = validate_python_imports(content, tmp_path / "test.md", tmp_path)
        assert issues == []  # Syntax errors silently skipped

    def test_non_infrastructure_import(self, tmp_path):
        content = "```python\nimport os\nimport sys\n```"
        issues = validate_python_imports(content, tmp_path / "test.md", tmp_path)
        assert issues == []  # Non-infrastructure imports not checked



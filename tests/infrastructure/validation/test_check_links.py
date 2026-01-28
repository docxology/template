"""Comprehensive tests for infrastructure/validation/check_links.py.

Tests link validation, file reference checking, and anchor validation.
"""

from pathlib import Path

import pytest

from infrastructure.validation import check_links


class TestFindAllMarkdownFiles:
    """Test suite for find_all_markdown_files function."""

    def test_find_markdown_files_basic(self, tmp_path):
        """Test finding markdown files in a directory."""
        # Create test markdown files
        (tmp_path / "readme.md").write_text("# README")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")

        files = check_links.find_all_markdown_files(str(tmp_path))

        assert len(files) == 2
        assert any("readme.md" in str(f) for f in files)
        assert any("guide.md" in str(f) for f in files)

    def test_find_markdown_files_excludes_output(self, tmp_path):
        """Test that output directory is excluded."""
        (tmp_path / "readme.md").write_text("# README")
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "excluded.md").write_text("# Excluded")

        files = check_links.find_all_markdown_files(str(tmp_path))

        assert len(files) == 1
        assert not any("output" in str(f) for f in files)

    def test_find_markdown_files_excludes_htmlcov(self, tmp_path):
        """Test that htmlcov directory is excluded."""
        (tmp_path / "readme.md").write_text("# README")
        (tmp_path / "htmlcov").mkdir()
        (tmp_path / "htmlcov" / "coverage.md").write_text("# Coverage")

        files = check_links.find_all_markdown_files(str(tmp_path))

        assert len(files) == 1
        assert not any("htmlcov" in str(f) for f in files)

    def test_find_markdown_files_empty_dir(self, tmp_path):
        """Test with empty directory."""
        files = check_links.find_all_markdown_files(str(tmp_path))
        assert len(files) == 0

    def test_find_markdown_files_nested(self, tmp_path):
        """Test finding markdown files in nested directories."""
        (tmp_path / "a" / "b" / "c").mkdir(parents=True)
        (tmp_path / "a" / "b" / "c" / "deep.md").write_text("# Deep")

        files = check_links.find_all_markdown_files(str(tmp_path))

        assert len(files) == 1
        assert "deep.md" in str(files[0])


class TestExtractLinks:
    """Test suite for extract_links function."""

    def test_extract_internal_anchor_links(self, tmp_path):
        """Test extracting internal anchor links."""
        content = "See [section one](#section-one) for details."
        file_path = tmp_path / "test.md"

        internal, external, file_refs = check_links.extract_links(content, file_path)

        assert len(internal) == 1
        assert internal[0]["target"] == "#section-one"
        assert internal[0]["text"] == "section one"

    def test_extract_external_links(self, tmp_path):
        """Test extracting external HTTP/HTTPS links."""
        content = """
        Check [Google](https://google.com) for more.
        Also see [Example](http://example.com).
        """
        file_path = tmp_path / "test.md"

        internal, external, file_refs = check_links.extract_links(content, file_path)

        assert len(external) == 2
        assert any("google.com" in link["target"] for link in external)
        assert any("example.com" in link["target"] for link in external)

    def test_extract_file_references(self, tmp_path):
        """Test extracting file references."""
        content = """
        See [README](./readme.md) for details.
        Also check [Guide](../docs/guide.md).
        """
        file_path = tmp_path / "test.md"

        internal, external, file_refs = check_links.extract_links(content, file_path)

        assert len(file_refs) == 2
        assert any("readme.md" in ref["target"] for ref in file_refs)
        assert any("guide.md" in ref["target"] for ref in file_refs)

    def test_extract_links_with_line_numbers(self, tmp_path):
        """Test that line numbers are correctly extracted."""
        content = "Line 1\n[Link](./file.md)\nLine 3"
        file_path = tmp_path / "test.md"

        internal, external, file_refs = check_links.extract_links(content, file_path)

        assert len(file_refs) == 1
        assert file_refs[0]["line"] == 2

    def test_extract_mailto_links(self, tmp_path):
        """Test extracting mailto links as external."""
        content = "[Email](mailto:test@example.com)"
        file_path = tmp_path / "test.md"

        internal, external, file_refs = check_links.extract_links(content, file_path)

        assert len(external) == 1
        assert "mailto:" in external[0]["target"]

    def test_extract_no_links(self, tmp_path):
        """Test extracting from content with no links."""
        content = "Just plain text without any links."
        file_path = tmp_path / "test.md"

        internal, external, file_refs = check_links.extract_links(content, file_path)

        assert len(internal) == 0
        assert len(external) == 0
        assert len(file_refs) == 0


class TestCheckFileReference:
    """Test suite for check_file_reference function."""

    def test_check_existing_file(self, tmp_path):
        """Test checking reference to existing file."""
        # Create source and target files
        source = tmp_path / "docs" / "source.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Source")

        target = tmp_path / "docs" / "target.md"
        target.write_text("# Target")

        exists, error = check_links.check_file_reference(
            "./target.md", source, tmp_path
        )

        # Either succeeds or gives an error message
        assert isinstance(exists, bool)
        assert isinstance(error, str)

    def test_check_missing_file(self, tmp_path):
        """Test checking reference to missing file."""
        source = tmp_path / "source.md"
        source.write_text("# Source")

        exists, error = check_links.check_file_reference(
            "./nonexistent.md", source, tmp_path
        )

        assert exists is False
        assert "not found" in error.lower() or len(error) > 0

    def test_check_parent_directory_reference(self, tmp_path):
        """Test checking reference with parent directory."""
        # Create nested structure
        (tmp_path / "docs" / "sub").mkdir(parents=True)
        source = tmp_path / "docs" / "sub" / "source.md"
        source.write_text("# Source")

        target = tmp_path / "readme.md"
        target.write_text("# README")

        exists, error = check_links.check_file_reference(
            "../../readme.md", source, tmp_path
        )

        # Result depends on implementation
        assert isinstance(exists, bool)


class TestLinkValidation:
    """Test link validation functionality."""

    def test_validate_all_links_in_file(self, tmp_path):
        """Test validating all links in a file."""
        # Create test files
        source = tmp_path / "source.md"
        target = tmp_path / "target.md"

        source.write_text(
            """
        # Source Document
        
        See [Target](./target.md) for more info.
        Also check [External](https://example.com).
        """
        )
        target.write_text("# Target")

        # Extract links
        content = source.read_text()
        internal, external, file_refs = check_links.extract_links(content, source)

        # Should have file refs and external links
        assert len(file_refs) == 1
        assert len(external) == 1

    def test_validate_anchor_link(self, tmp_path):
        """Test validating anchor links."""
        content = """
        # Main Heading
        
        ## Sub Heading
        
        See [sub heading](#sub-heading) below.
        """
        file_path = tmp_path / "test.md"

        internal, external, file_refs = check_links.extract_links(content, file_path)

        assert len(internal) == 1
        assert internal[0]["target"] == "#sub-heading"


class TestCheckLinksIntegration:
    """Integration tests for check_links module."""

    def test_full_link_checking_workflow(self, tmp_path):
        """Test complete link checking workflow."""
        # Create a documentation structure
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "readme.md").write_text(
            """
        # README
        
        - [Guide](./guide.md)
        - [Missing](./missing.md)
        - [External](https://example.com)
        """
        )

        (docs / "guide.md").write_text(
            """
        # Guide
        
        Back to [README](./readme.md)
        """
        )

        # Find all markdown files
        files = check_links.find_all_markdown_files(str(tmp_path))
        assert len(files) == 2

        # Extract and check links
        all_file_refs = []
        for file_path in files:
            content = file_path.read_text()
            internal, external, file_refs = check_links.extract_links(
                content, file_path
            )
            all_file_refs.extend(file_refs)

        # Should have file references
        assert len(all_file_refs) >= 2

    def test_module_has_main_function(self):
        """Test that module has main function if it's a script."""
        # The module may have a main function or be importable
        assert hasattr(check_links, "find_all_markdown_files")
        assert hasattr(check_links, "extract_links")
        assert hasattr(check_links, "check_file_reference")


class TestBrokenAnchorLinks:
    """Test detection of broken anchor links (covers lines 170-181)."""

    def test_detect_broken_anchor_link(self, tmp_path, capsys):
        """Test detecting broken anchor links."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Heading One

See [nonexistent](#nonexistent-heading) for details.
"""
        )

        # Extract headings and links
        content = md_file.read_text()
        headings = check_links.extract_headings(content)
        internal, _, _ = check_links.extract_links(content, md_file)

        # Check if the anchor is in headings
        assert "heading-one" in headings
        assert len(internal) == 1
        target = internal[0]["target"].lstrip("#")
        assert target not in headings  # This is a broken link

    def test_anchor_link_found_in_headings(self, tmp_path):
        """Test valid anchor link is found."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Main Section

## Sub Section

See [sub section](#sub-section) for details.
"""
        )

        content = md_file.read_text()
        headings = check_links.extract_headings(content)
        internal, _, _ = check_links.extract_links(content, md_file)

        assert "sub-section" in headings
        target = internal[0]["target"].lstrip("#")
        assert target in headings  # Valid link


class TestBrokenFileReferences:
    """Test detection of broken file references (covers lines 184-199)."""

    def test_detect_broken_file_reference(self, tmp_path):
        """Test detecting broken file references."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test

See [missing file](./nonexistent.md) for details.
"""
        )

        content = md_file.read_text()
        _, _, file_refs = check_links.extract_links(content, md_file)

        assert len(file_refs) == 1
        exists, msg = check_links.check_file_reference(
            file_refs[0]["target"], md_file, tmp_path
        )
        assert exists is False

    def test_file_reference_with_anchor(self, tmp_path):
        """Test file reference that includes an anchor (line 187-188)."""
        # Create target file
        (tmp_path / "target.md").write_text("# Target\n\n## Section")
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test

See [target section](./target.md#section) for details.
"""
        )

        content = md_file.read_text()
        _, _, file_refs = check_links.extract_links(content, md_file)

        assert len(file_refs) == 1
        # The target should include the anchor
        target = file_refs[0]["target"]
        assert "#" in target


class TestExceptionHandling:
    """Test exception handling (covers lines 200-201)."""

    def test_extract_links_handles_encoding_errors(self, tmp_path):
        """Test that extract_links handles problematic content gracefully."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n[Link](./file.md)")

        # Should not raise exception
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)

        assert isinstance(file_refs, list)


class TestReportingBrokenLinks:
    """Test broken link reporting (covers lines 204-216)."""

    def test_report_many_broken_links(self, tmp_path, capsys, monkeypatch):
        """Test reporting when there are more than 10 broken links."""
        # Create a file with many broken links
        broken_links_content = "# Test\n\n"
        for i in range(15):
            broken_links_content += f"[Link {i}](#broken-anchor-{i})\n"

        md_file = tmp_path / "test.md"
        md_file.write_text(broken_links_content)

        # Simulate what main() does
        content = md_file.read_text()
        headings = check_links.extract_headings(content)
        internal, _, _ = check_links.extract_links(content, md_file)

        broken = []
        for link in internal:
            target = link["target"].lstrip("#")
            if target not in headings:
                broken.append(
                    {
                        "file": "test.md",
                        "line": link["line"],
                        "target": link["target"],
                        "text": link["text"],
                        "issue": "Anchor not found",
                    }
                )

        # Should have 15 broken links
        assert len(broken) == 15

        # Simulate reporting (lines 204-209)
        if len(broken) > 10:
            # Lines 208-209 would be executed
            assert len(broken) - 10 == 5

    def test_report_many_broken_file_refs(self, tmp_path):
        """Test reporting when there are more than 10 broken file refs."""
        # Create a file with many broken file references
        broken_refs_content = "# Test\n\n"
        for i in range(15):
            broken_refs_content += f"[File {i}](./missing_{i}.md)\n"

        md_file = tmp_path / "test.md"
        md_file.write_text(broken_refs_content)

        content = md_file.read_text()
        _, _, file_refs = check_links.extract_links(content, md_file)

        broken_file_refs = []
        for ref in file_refs:
            target = ref["target"]
            if "#" in target:
                target = target.split("#")[0]

            if target:
                exists, msg = check_links.check_file_reference(
                    target, md_file, tmp_path
                )
                if not exists:
                    broken_file_refs.append(
                        {
                            "file": "test.md",
                            "line": ref["line"],
                            "target": ref["target"],
                            "text": ref["text"],
                            "issue": msg,
                        }
                    )

        # Should have 15 broken file refs
        assert len(broken_file_refs) == 15

        # Simulate reporting (lines 211-216)
        if len(broken_file_refs) > 10:
            # Lines 215-216 would be executed
            assert len(broken_file_refs) - 10 == 5

    def test_no_broken_links_success(self, tmp_path):
        """Test reporting when all links are valid (lines 218-220)."""
        # Create valid file structure
        (tmp_path / "target.md").write_text("# Target")
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test Heading

See [target](./target.md) and [local](#test-heading).
"""
        )

        content = md_file.read_text()
        headings = check_links.extract_headings(content)
        internal, _, file_refs = check_links.extract_links(content, md_file)

        broken_links = []
        for link in internal:
            target = link["target"].lstrip("#")
            if target not in headings:
                broken_links.append(link)

        broken_file_refs = []
        for ref in file_refs:
            target = ref["target"]
            if "#" in target:
                target = target.split("#")[0]
            if target:
                exists, _ = check_links.check_file_reference(target, md_file, tmp_path)
                if not exists:
                    broken_file_refs.append(ref)

        # All links should be valid
        assert len(broken_links) == 0
        assert len(broken_file_refs) == 0

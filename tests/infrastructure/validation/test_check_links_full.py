"""Comprehensive tests for infrastructure/validation/check_links.py.

Tests link checking functionality comprehensively.
"""

from pathlib import Path

import pytest

from infrastructure.validation import check_links
from infrastructure.validation.check_links import (check_file_reference,
                                                   extract_headings,
                                                   extract_links,
                                                   find_all_markdown_files)


class TestFindAllMarkdownFiles:
    """Test find_all_markdown_files function."""

    def test_find_markdown_files(self, tmp_path):
        """Test finding markdown files."""
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")

        files = find_all_markdown_files(str(tmp_path))

        assert len(files) >= 2
        assert any("README.md" in str(f) for f in files)

    def test_skip_output_directory(self, tmp_path):
        """Test that output directory is skipped."""
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "skip.md").write_text("# Skip")

        files = find_all_markdown_files(str(tmp_path))

        # Check that skip.md in output is not included
        file_names = [f.name for f in files]
        assert "README.md" in file_names
        # The output directory should be skipped
        assert not any(f.parent.name == "output" for f in files)

    def test_skip_htmlcov_directory(self, tmp_path):
        """Test that htmlcov directory is skipped."""
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "htmlcov").mkdir()
        (tmp_path / "htmlcov" / "skip.md").write_text("# Skip")

        files = find_all_markdown_files(str(tmp_path))

        # Check that skip.md in htmlcov is not included
        file_names = [f.name for f in files]
        assert "README.md" in file_names
        # The htmlcov directory should be skipped
        assert not any(f.parent.name == "htmlcov" for f in files)

    def test_empty_directory(self, tmp_path):
        """Test empty directory."""
        files = find_all_markdown_files(str(tmp_path))
        assert len(files) == 0


class TestExtractLinks:
    """Test extract_links function."""

    def test_extract_external_link(self, tmp_path):
        """Test extracting external links."""
        md_file = tmp_path / "test.md"
        content = "[Google](https://google.com)"

        internal, external, file_refs = extract_links(content, md_file)

        assert len(external) == 1
        assert external[0]["target"] == "https://google.com"

    def test_extract_internal_anchor(self, tmp_path):
        """Test extracting internal anchor links."""
        md_file = tmp_path / "test.md"
        content = "[Section](#section)"

        internal, external, file_refs = extract_links(content, md_file)

        assert len(internal) == 1
        assert internal[0]["target"] == "#section"

    def test_extract_file_reference(self, tmp_path):
        """Test extracting file references."""
        md_file = tmp_path / "test.md"
        content = "[Other](other.md)"

        internal, external, file_refs = extract_links(content, md_file)

        assert len(file_refs) == 1
        assert file_refs[0]["target"] == "other.md"

    def test_extract_multiple_links(self, tmp_path):
        """Test extracting multiple links."""
        md_file = tmp_path / "test.md"
        content = """
[External](https://example.com)
[Anchor](#top)
[File](other.md)
"""

        internal, external, file_refs = extract_links(content, md_file)

        assert len(external) == 1
        assert len(internal) == 1
        assert len(file_refs) == 1

    def test_extract_http_link(self, tmp_path):
        """Test extracting http link."""
        md_file = tmp_path / "test.md"
        content = "[Site](http://example.com)"

        internal, external, file_refs = extract_links(content, md_file)

        assert len(external) == 1

    def test_extract_mailto_link(self, tmp_path):
        """Test extracting mailto link."""
        md_file = tmp_path / "test.md"
        content = "[Email](mailto:test@example.com)"

        internal, external, file_refs = extract_links(content, md_file)

        assert len(external) == 1

    def test_line_number_tracking(self, tmp_path):
        """Test line number is tracked."""
        md_file = tmp_path / "test.md"
        content = "\n\n[Link](target.md)"

        internal, external, file_refs = extract_links(content, md_file)

        assert file_refs[0]["line"] == 3


class TestCheckFileReference:
    """Test check_file_reference function."""

    def test_file_exists(self, tmp_path):
        """Test valid file reference."""
        target = tmp_path / "target.md"
        target.write_text("# Target")
        source = tmp_path / "source.md"
        source.write_text("")

        exists, msg = check_file_reference("target.md", source, tmp_path)

        assert exists is True

    def test_file_not_exists(self, tmp_path):
        """Test invalid file reference."""
        source = tmp_path / "source.md"
        source.write_text("")

        exists, msg = check_file_reference("missing.md", source, tmp_path)

        assert exists is False
        assert "not exist" in msg.lower()

    def test_relative_path_parent(self, tmp_path):
        """Test relative path with parent directory."""
        (tmp_path / "docs").mkdir()
        source = tmp_path / "docs" / "source.md"
        source.write_text("")
        target = tmp_path / "README.md"
        target.write_text("# README")

        exists, msg = check_file_reference("../README.md", source, tmp_path)

        assert exists is True

    def test_directory_reference(self, tmp_path):
        """Test directory reference."""
        source = tmp_path / "source.md"
        source.write_text("")
        (tmp_path / "docs").mkdir()

        exists, msg = check_file_reference("docs", source, tmp_path)

        assert exists is True

    def test_dotslash_path(self, tmp_path):
        """Test ./relative path."""
        source = tmp_path / "source.md"
        source.write_text("")
        target = tmp_path / "target.md"
        target.write_text("")

        exists, msg = check_file_reference("./target.md", source, tmp_path)

        assert exists is True


class TestExtractHeadings:
    """Test extract_headings function."""

    def test_basic_headings(self):
        """Test extracting basic headings."""
        content = """
# Title
## Section One
### Subsection
"""

        headings = extract_headings(content)

        assert "title" in headings
        assert "section-one" in headings
        assert "subsection" in headings

    def test_explicit_anchors(self):
        """Test explicit anchor syntax."""
        content = "# Title {#custom-anchor}"

        headings = extract_headings(content)

        assert "custom-anchor" in headings

    def test_special_characters(self):
        """Test headings with special characters."""
        content = "## What's New?"

        headings = extract_headings(content)

        assert len(headings) >= 1


class TestExtractHeadingsEdgeCases:
    """Test edge cases for extract_headings function."""

    def test_empty_anchor_after_stripping(self):
        """Test heading that produces empty anchor after stripping."""
        # Heading with only special characters
        content = "# ??? !!!"

        headings = extract_headings(content)

        # Empty anchor should not be added
        assert "" not in headings

    def test_heading_with_numbers_and_special_chars(self):
        """Test heading with numbers and special characters."""
        content = "## Section 3.1: Introduction"

        headings = extract_headings(content)

        # Should have some anchor generated
        assert len(headings) >= 1

    def test_mixed_explicit_and_auto_anchors(self):
        """Test mixed explicit and auto-generated anchors."""
        content = """
# Title {#explicit-title}
## Auto Section
### Another {#another-explicit}
"""

        headings = extract_headings(content)

        assert "explicit-title" in headings
        assert "another-explicit" in headings
        assert "auto-section" in headings


class TestCheckFileReferenceEdgeCases:
    """Test edge cases for check_file_reference."""

    def test_markdown_file_without_extension(self, tmp_path):
        """Test reference to markdown file without .md extension."""
        source = tmp_path / "source.md"
        source.write_text("")
        target = tmp_path / "target.md"
        target.write_text("# Target")

        # Reference without .md extension
        exists, msg = check_file_reference("target", source, tmp_path)

        assert exists is True

    def test_deeply_nested_relative_path(self, tmp_path):
        """Test deeply nested relative paths."""
        # Create structure: docs/sub/deep/source.md -> ../../../README.md
        deep_dir = tmp_path / "docs" / "sub" / "deep"
        deep_dir.mkdir(parents=True)
        source = deep_dir / "source.md"
        source.write_text("")
        target = tmp_path / "README.md"
        target.write_text("# README")

        exists, msg = check_file_reference("../../../README.md", source, tmp_path)

        assert exists is True

    def test_path_resolution_error(self, tmp_path):
        """Test error handling during path resolution."""
        source = tmp_path / "source.md"
        source.write_text("")

        # Use a path that might cause issues (very long or circular)
        exists, msg = check_file_reference("../" * 100 + "file.md", source, tmp_path)

        # Should fail gracefully
        assert exists is False
        assert "outside repository" in msg.lower() or "not exist" in msg.lower()


class TestMainFunction:
    """Test main function with real data."""

    def test_main_exists(self):
        """Test main function exists."""
        assert hasattr(check_links, "main")

    def test_main_returns_exit_code(self):
        """Test main returns integer exit code."""
        # Main uses repo root, so call it directly
        result = check_links.main()
        assert isinstance(result, int)
        assert result in (0, 1)


class TestLinkValidationWorkflows:
    """Test complete link validation workflows with real data."""

    def test_detect_broken_anchor_link(self, tmp_path):
        """Test detection of broken anchor links."""
        md_content = """# Title

This links to [nonexistent section](#does-not-exist).
"""
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        files = find_all_markdown_files(str(tmp_path))
        assert len(files) == 1

        content = md_file.read_text()
        all_headings = {str(md_file): extract_headings(content)}
        internal, external, file_refs = extract_links(content, md_file)

        # Check anchor validation logic
        assert len(internal) == 1
        target = internal[0]["target"].lstrip("#")
        file_key = str(md_file)

        # Verify anchor is not in headings
        assert target not in all_headings[file_key]

    def test_detect_broken_file_reference(self, tmp_path):
        """Test detection of broken file references."""
        md_content = "[Missing doc](nonexistent.md)"
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        content = md_file.read_text()
        internal, external, file_refs = extract_links(content, md_file)

        assert len(file_refs) == 1
        exists, msg = check_file_reference(file_refs[0]["target"], md_file, tmp_path)

        assert exists is False
        assert "not exist" in msg.lower()

    def test_file_reference_with_anchor(self, tmp_path):
        """Test file reference with anchor gets anchor stripped."""
        (tmp_path / "other.md").write_text("# Other Doc")
        md_content = "[Section](other.md#section)"
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        content = md_file.read_text()
        internal, external, file_refs = extract_links(content, md_file)

        assert len(file_refs) == 1
        target = file_refs[0]["target"]

        # Strip anchor for file check
        if "#" in target:
            target = target.split("#")[0]

        exists, msg = check_file_reference(target, md_file, tmp_path)
        assert exists is True

    def test_valid_internal_anchor(self, tmp_path):
        """Test valid internal anchor link."""
        md_content = """# Title

## Section One

Go to [section](#section-one).
"""
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        content = md_file.read_text()
        headings = extract_headings(content)
        internal, external, file_refs = extract_links(content, md_file)

        assert len(internal) == 1
        target = internal[0]["target"].lstrip("#")

        # Verify anchor IS in headings
        assert target in headings

    def test_many_broken_references_workflow(self, tmp_path):
        """Test workflow with many broken references."""
        # Create file with 15 broken file references
        broken_refs = "\n".join([f"[File {i}](missing{i}.md)" for i in range(15)])
        md_content = f"# Title\n\n{broken_refs}"
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        content = md_file.read_text()
        internal, external, file_refs = extract_links(content, md_file)

        # Should find all 15 broken refs
        assert len(file_refs) == 15

        broken = []
        for ref in file_refs:
            exists, msg = check_file_reference(ref["target"], md_file, tmp_path)
            if not exists:
                broken.append(ref)

        assert len(broken) == 15

    def test_many_broken_anchor_links(self, tmp_path):
        """Test workflow with many broken anchor links."""
        # Create file with 15 broken anchor links
        broken_links = "\n".join([f"[Link {i}](#nonexistent-{i})" for i in range(15)])
        md_content = f"# Title\n\n{broken_links}"
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        content = md_file.read_text()
        headings = extract_headings(content)
        internal, external, file_refs = extract_links(content, md_file)

        # Should find all 15 broken anchors
        assert len(internal) == 15

        broken = []
        for link in internal:
            target = link["target"].lstrip("#")
            if target not in headings:
                broken.append(link)

        assert len(broken) == 15


class TestCompleteValidationPaths:
    """Test all code paths through the validation workflow."""

    def test_all_links_valid_workflow(self, tmp_path):
        """Test workflow when all links are valid."""
        # Create interconnected valid docs
        (tmp_path / "README.md").write_text(
            """# README

## Introduction {#intro}

See [Guide](docs/guide.md) for details.
Go to [intro](#intro).
"""
        )
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text(
            """# Guide

See [README](../README.md) for overview.
"""
        )

        files = find_all_markdown_files(str(tmp_path))
        assert len(files) == 2

        # Validate all links
        all_valid = True
        for md_file in files:
            content = md_file.read_text()
            internal, external, file_refs = extract_links(content, md_file)

            # Check file refs
            for ref in file_refs:
                exists, msg = check_file_reference(ref["target"], md_file, tmp_path)
                if not exists:
                    all_valid = False

        assert all_valid

    def test_external_links_extracted_correctly(self, tmp_path):
        """Test that external links are correctly categorized."""
        md_content = """# Links

[Google](https://google.com)
[HTTP Site](http://example.com)
[Email](mailto:test@test.com)
[FTP](ftp://files.example.com)
"""
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        content = md_file.read_text()
        internal, external, file_refs = extract_links(content, md_file)

        # All should be classified as external
        assert len(external) == 4
        assert len(internal) == 0
        assert len(file_refs) == 0


class TestCheckLinksIntegration:
    """Integration tests for check_links module."""

    def test_full_workflow(self, tmp_path):
        """Test complete link checking workflow."""
        # Create interconnected docs
        (tmp_path / "README.md").write_text("[Guide](docs/guide.md)")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("[Back](../README.md)")

        files = find_all_markdown_files(str(tmp_path))
        assert len(files) == 2

        for f in files:
            content = f.read_text()
            internal, external, file_refs = extract_links(content, f)
            for ref in file_refs:
                exists, msg = check_file_reference(ref["target"], f, tmp_path)
                assert exists, f"Link {ref['target']} in {f} should exist"

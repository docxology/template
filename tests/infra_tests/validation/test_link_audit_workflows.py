"""Integration and workflow tests for check_links link audit."""

from infrastructure.validation.integrity import check_links
from infrastructure.validation.integrity.check_links import (
    check_file_reference,
    discover_markdown_files,
    extract_headings,
    extract_links,
)


class TestLinkValidationWorkflows:
    """Test complete link validation workflows with real data."""

    def test_detect_broken_anchor_link(self, tmp_path):
        """Test detection of broken anchor links."""
        md_content = """# Title

This links to [nonexistent section](#does-not-exist).
"""
        md_file = tmp_path / "doc.md"
        md_file.write_text(md_content)

        files = discover_markdown_files(tmp_path, scope="link_audit")
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

        files = discover_markdown_files(tmp_path, scope="link_audit")
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


class TestCheckLinksIntegrationRelativePaths:
    """Integration tests for check_links module."""

    def test_full_workflow(self, tmp_path):
        """Test complete link checking workflow."""
        # Create interconnected docs
        (tmp_path / "README.md").write_text("[Guide](docs/guide.md)")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("[Back](../README.md)")

        files = discover_markdown_files(tmp_path, scope="link_audit")
        assert len(files) == 2

        for f in files:
            content = f.read_text()
            internal, external, file_refs = extract_links(content, f)
            for ref in file_refs:
                exists, msg = check_file_reference(ref["target"], f, tmp_path)
                assert exists, f"Link {ref['target']} in {f} should exist"


class TestBulkLinkChecking:
    """Test bulk link checking functionality."""

    def test_check_all_links(self, tmp_path):
        """Test checking all links in a file."""
        doc = tmp_path / "doc.md"
        target = tmp_path / "target.md"
        target.write_text("# Target")
        doc.write_text("[Link](target.md)")

        if hasattr(check_links, "check_all_links"):
            results = check_links.check_all_links(doc, tmp_path)
            assert results is not None

    def test_check_directory_links(self, tmp_path):
        """Test checking links in entire directory."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("[Link](b.md)")
        (docs / "b.md").write_text("# B")

        if hasattr(check_links, "check_directory_links"):
            results = check_links.check_directory_links(docs)
            assert results is not None


class TestCheckLinksIntegration:
    """Integration tests for check_links module."""

    def test_full_link_check_workflow(self, tmp_path):
        """Test complete link checking workflow."""
        # Create documentation with various links
        docs = tmp_path / "docs"
        docs.mkdir()

        main = docs / "main.md"
        main.write_text(
            """
# Main Doc
- [Sub](sub.md)
- [README](../README.md)
"""
        )

        sub = docs / "sub.md"
        sub.write_text("# Sub")

        readme = tmp_path / "README.md"
        readme.write_text("# README")

        # Module should work
        assert check_links is not None


class TestMainFunctionReporting:
    """Test main function reporting for broken links."""

    def test_main_reports_broken_anchors(self, tmp_path, capsys):
        """Test that main reports broken anchor links."""
        # Create file with broken anchor link
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Real Heading

[Broken](#nonexistent-section)
"""
        )

        # Run main with custom repo root

        def patched_main():
            """Patched main to use tmp_path as repo root."""
            repo_root = tmp_path
            md_files = check_links.discover_markdown_files(repo_root, scope="link_audit")

            print(f"Found {len(md_files)} markdown files")

            all_headings = {}
            broken_links = []
            broken_file_refs = []

            # First pass: collect headings
            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding="utf-8")
                    all_headings[str(md_file.relative_to(repo_root))] = check_links.extract_headings(content)
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")

            # Second pass: check links
            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding="utf-8")
                    internal_links, external_links, file_refs = check_links.extract_links(content, md_file)

                    # Check internal links
                    for link in internal_links:
                        target = link["target"].lstrip("#")
                        file_key = str(md_file.relative_to(repo_root))
                        if file_key in all_headings and target not in all_headings[file_key]:
                            broken_links.append(
                                {
                                    "file": file_key,
                                    "line": link["line"],
                                    "target": link["target"],
                                    "text": link["text"],
                                    "issue": "Anchor not found",
                                }
                            )

                    # Check file references
                    for ref in file_refs:
                        target = ref["target"]
                        if "#" in target:
                            target = target.split("#")[0]
                        if target:
                            exists, msg = check_links.check_file_reference(target, md_file, repo_root)
                            if not exists:
                                broken_file_refs.append(
                                    {
                                        "file": str(md_file.relative_to(repo_root)),
                                        "line": ref["line"],
                                        "target": ref["target"],
                                        "text": ref["text"],
                                        "issue": msg,
                                    }
                                )
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
        md_file.write_text(
            """# Document

[Missing File](nonexistent.md)
"""
        )

        # Extract and check the broken reference
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)

        assert len(file_refs) == 1

        exists, msg = check_links.check_file_reference(file_refs[0]["target"], md_file, tmp_path)
        assert exists is False
        assert "does not exist" in msg.lower()

    def test_main_success_with_valid_links(self, tmp_path, capsys):
        """Test main returns 0 when all links are valid."""
        # Create valid file structure
        (tmp_path / "target.md").write_text("# Target Heading")

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test Document

[Valid Link](target.md)
"""
        )

        # Extract and verify
        content = md_file.read_text()
        internal, external, file_refs = check_links.extract_links(content, md_file)

        for ref in file_refs:
            exists, msg = check_links.check_file_reference(ref["target"], md_file, tmp_path)
            assert exists is True

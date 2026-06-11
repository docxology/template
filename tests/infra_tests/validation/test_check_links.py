"""Tests for infrastructure.validation.integrity.check_links."""

from pathlib import Path

import pytest

from infrastructure.validation.content.discovery import discover_markdown_files as canonical_discover
from infrastructure.validation.integrity import check_links
from infrastructure.validation.integrity import link_extract
from infrastructure.validation.integrity.check_links import (
    check_file_reference,
    discover_markdown_files,
    extract_code_blocks,
    extract_headings,
    extract_links,
    generate_comprehensive_report,
    run_link_audit,
    validate_directory_structures,
    validate_placeholder_consistency,
    validate_python_imports,
)


def test_link_extract_module_import_smoke() -> None:
    """Library surface lives in link_extract; check_links re-exports discovery for CLI callers."""
    assert link_extract.extract_links is check_links.extract_links
    assert check_links.discover_markdown_files is canonical_discover


class TestExtractCodeBlocks:
    def test_finds_code_blocks(self, tmp_path):
        f = tmp_path / "test.md"
        content = "Text\n```python\nprint('hi')\n```\nMore text"
        blocks = extract_code_blocks(content, f)
        assert len(blocks) == 1
        assert blocks[0]["language"] == "python"
        assert "print" in blocks[0]["content"]

    def test_empty_code_block_skipped(self, tmp_path):
        f = tmp_path / "test.md"
        blocks = extract_code_blocks("```python\n\n```", f)
        assert blocks == []

    def test_no_language(self, tmp_path):
        f = tmp_path / "test.md"
        blocks = extract_code_blocks("```\nsome code\n```", f)
        assert len(blocks) == 1
        assert blocks[0]["language"] == ""

    def test_multiple_blocks(self, tmp_path):
        f = tmp_path / "test.md"
        content = "```bash\nls\n```\n\n```python\nprint(1)\n```"
        blocks = extract_code_blocks(content, f)
        assert len(blocks) == 2
        assert blocks[0]["language"] == "bash"
        assert blocks[1]["language"] == "python"



class TestValidateDirectoryStructures:
    def test_valid_tree(self, tmp_path):
        (tmp_path / "src").mkdir()
        content = "```\n" + chr(9500) + chr(9472) * 2 + " src/\n```"
        issues = validate_directory_structures(content, tmp_path / "README.md", tmp_path)
        assert isinstance(issues, list)

    def test_no_tree(self, tmp_path):
        assert validate_directory_structures("No tree diagrams here.", tmp_path / "README.md", tmp_path) == []

    def test_tree_diagram_with_template_var(self, tmp_path):
        content = "```\n├── {project_name}/\n└── {module}/\n```"
        assert validate_directory_structures(content, tmp_path / "test.md", tmp_path) == []

    def test_tree_diagram_with_existing_dir(self, tmp_path):
        (tmp_path / "src").mkdir()
        assert validate_directory_structures("```\n├── src/\n```", tmp_path / "test.md", tmp_path) == []



class TestValidatePythonImports:
    def test_valid_import(self, tmp_path):
        infra = tmp_path / "infrastructure" / "core"
        infra.mkdir(parents=True)
        (infra / "__init__.py").write_text("")
        (infra / "security.py").write_text("x = 1")
        content = "```python\nfrom infrastructure.core.security import x\n```"
        f = tmp_path / "README.md"
        assert validate_python_imports(content, f, tmp_path) == []

    def test_invalid_import(self, tmp_path):
        content = "```python\nfrom infrastructure.nonexistent.module import x\n```"
        f = tmp_path / "README.md"
        issues = validate_python_imports(content, f, tmp_path)
        assert len(issues) == 1
        assert "not found" in issues[0]["issue"]

    def test_syntax_error_skipped(self, tmp_path):
        content = "```python\nthis is not valid python {{{\n```"
        f = tmp_path / "README.md"
        assert validate_python_imports(content, f, tmp_path) == []



class TestValidatePlaceholderConsistency:
    def test_template_usage_ok(self, tmp_path):
        content = "Use projects/{name}/src for your project template."
        f = tmp_path / "README.md"
        assert validate_placeholder_consistency(content, f, tmp_path) == []

    def test_skipped_files(self, tmp_path):
        content = "projects/{name} usage"
        f = tmp_path / "infrastructure" / "AGENTS.md"
        f.parent.mkdir(parents=True)
        assert validate_placeholder_consistency(content, f, tmp_path) == []

    def test_skip_agent_files(self, tmp_path):
        content = "Use {name} for the project."
        fp = tmp_path / "AGENTS.md"
        assert validate_placeholder_consistency(content, fp, tmp_path) == []



class TestGenerateComprehensiveReport:
    def test_no_issues(self):
        issues = {
            "broken_anchor_links": [],
            "broken_file_refs": [],
            "code_block_paths": [],
            "directory_structures": [],
            "python_imports": [],
            "placeholder_consistency": [],
        }
        assert generate_comprehensive_report(issues, 10) == 0

    def test_with_issues(self):
        issues = {
            "broken_anchor_links": [
                {
                    "file": "README.md",
                    "line": 1,
                    "target": "#missing",
                    "text": "Link",
                    "issue": "Anchor not found",
                    "type": "broken_anchor",
                }
            ],
            "broken_file_refs": [],
            "code_block_paths": [],
            "directory_structures": [],
            "python_imports": [],
            "placeholder_consistency": [],
        }
        assert generate_comprehensive_report(issues, 5) == 1

    def test_many_issues_truncated(self):
        many = [
            {
                "file": f"file{i}.md",
                "line": i,
                "target": f"#target{i}",
                "text": f"Link {i}",
                "issue": "Anchor not found",
                "type": "broken_anchor",
            }
            for i in range(10)
        ]
        issues = {
            "broken_anchor_links": many,
            "broken_file_refs": [],
            "code_block_paths": [],
            "directory_structures": [],
            "python_imports": [],
            "placeholder_consistency": [],
        }
        assert generate_comprehensive_report(issues, 20) == 1

    def test_multiple_categories(self):
        issues = {
            "broken_anchor_links": [
                {"file": "a.md", "line": 1, "target": "#x", "text": "x", "issue": "bad", "type": "a"}
            ],
            "broken_file_refs": [
                {"file": "b.md", "line": 2, "target": "f.md", "text": "f", "issue": "missing", "type": "b"}
            ],
            "code_block_paths": [],
            "directory_structures": [],
            "python_imports": [{"file": "c.md", "line": 3, "target": "mod", "issue": "not found", "type": "c"}],
            "placeholder_consistency": [],
        }
        assert generate_comprehensive_report(issues, 15) == 1



class TestRunLinkAudit:
    def test_clean_repo(self, tmp_path):
        (tmp_path / "README.md").write_text("# Hello World\n\nSimple text, no links.")
        assert run_link_audit(tmp_path) == 0

    def test_with_broken_link(self, tmp_path):
        (tmp_path / "README.md").write_text("[Missing](nonexistent.md)")
        assert run_link_audit(tmp_path) == 1



class TestBrokenAnchorLinks:
    def test_detect_broken_anchor_link(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Heading One\n\nSee [nonexistent](#nonexistent-heading) for details.")
        content = md_file.read_text()
        headings = check_links.extract_headings(content)
        internal, _, _ = extract_links(content, md_file)
        assert "heading-one" in headings
        target = internal[0]["target"].lstrip("#")
        assert target not in headings

    def test_anchor_link_found_in_headings(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Main Section\n\n## Sub Section\n\nSee [sub section](#sub-section) for details.")
        content = md_file.read_text()
        headings = check_links.extract_headings(content)
        internal, _, _ = extract_links(content, md_file)
        target = internal[0]["target"].lstrip("#")
        assert target in headings
        assert "sub-section" in headings



class TestCheckLinksIntegrationComprehensive:
    def test_full_link_checking_workflow(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "readme.md").write_text(
            "# README\n\n- [Guide](./guide.md)\n- [Missing](./missing.md)\n- [External](https://example.com)\n"
        )
        (docs / "guide.md").write_text("# Guide\n\nBack to [README](./readme.md)\n")
        files = discover_markdown_files(tmp_path, scope="link_audit")
        assert len(files) == 2
        all_file_refs = []
        for file_path in files:
            internal, external, file_refs = extract_links(file_path.read_text(), file_path)
            assert isinstance(internal, list)
            assert isinstance(external, list)
            all_file_refs.extend(file_refs)
        assert len(all_file_refs) >= 2

    def test_module_exports(self):
        assert hasattr(check_links, "discover_markdown_files")
        assert hasattr(check_links, "extract_links")
        assert hasattr(check_links, "check_file_reference")



class TestDiscoverMarkdownFilesLinkAudit:
    """Test discover_markdown_files function."""

    def test_discovers_markdown_files(self, tmp_path):
        """Test finding markdown files with link_audit scope."""
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")

        files = discover_markdown_files(tmp_path, scope="link_audit")

        assert len(files) >= 2
        assert any("README.md" in str(f) for f in files)

    def test_skip_output_directory(self, tmp_path):
        """Test that output directory is skipped."""
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "skip.md").write_text("# Skip")

        files = discover_markdown_files(tmp_path, scope="link_audit")

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

        files = discover_markdown_files(tmp_path, scope="link_audit")

        # Check that skip.md in htmlcov is not included
        file_names = [f.name for f in files]
        assert "README.md" in file_names
        # The htmlcov directory should be skipped
        assert not any(f.parent.name == "htmlcov" for f in files)

    def test_empty_directory(self, tmp_path):
        """Test empty directory."""
        files = discover_markdown_files(tmp_path, scope="link_audit")
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

    @pytest.mark.timeout(120)
    def test_main_returns_exit_code(self):
        """Test main returns integer exit code."""
        # Main uses repo root, so call it directly
        result = check_links.main()
        assert isinstance(result, int)
        assert result in (0, 1)



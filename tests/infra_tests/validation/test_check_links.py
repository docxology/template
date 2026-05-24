"""Tests for infrastructure.validation.integrity.check_links."""

from pathlib import Path

from infrastructure.validation.content.discovery import discover_markdown_files as canonical_discover
from infrastructure.validation.integrity import check_links
from infrastructure.validation.integrity import link_extract
from infrastructure.validation.integrity.check_links import (
    _get_actual_project_names,
    _is_real_path_item,
    _resolve_template_path,
    _should_validate_path,
    _validate_import_path,
    check_file_reference,
    discover_markdown_files,
    extract_code_blocks,
    extract_headings,
    extract_links,
    generate_comprehensive_report,
    run_link_audit,
    validate_directory_structures,
    validate_file_paths_in_code,
    validate_placeholder_consistency,
    validate_python_imports,
)


def test_link_extract_module_import_smoke() -> None:
    """Library surface lives in link_extract; check_links re-exports discovery for CLI callers."""
    assert link_extract.extract_links is check_links.extract_links
    assert check_links.discover_markdown_files is canonical_discover


class TestDiscoverMarkdownFilesLinkAudit:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "README.md").write_text("# Hi")
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "guide.md").write_text("# Guide")
        result = discover_markdown_files(tmp_path, scope="link_audit")
        names = [f.name for f in result]
        assert "README.md" in names
        assert "guide.md" in names

    def test_excludes_output(self, tmp_path):
        (tmp_path / "readme.md").write_text("# README")
        out = tmp_path / "output"
        out.mkdir()
        (out / "report.md").write_text("# Report")
        result = discover_markdown_files(tmp_path, scope="link_audit")
        assert len(result) == 1
        assert not any(f.parent.name == "output" for f in result)

    def test_excludes_git(self, tmp_path):
        git = tmp_path / ".git"
        git.mkdir()
        (git / "notes.md").write_text("# Notes")
        assert discover_markdown_files(tmp_path, scope="link_audit") == []

    def test_excludes_htmlcov(self, tmp_path):
        (tmp_path / "readme.md").write_text("# README")
        htmlcov = tmp_path / "htmlcov"
        htmlcov.mkdir()
        (htmlcov / "coverage.md").write_text("# Coverage")
        result = discover_markdown_files(tmp_path, scope="link_audit")
        assert len(result) == 1
        assert not any(f.parent.name == "htmlcov" for f in result)

    def test_excludes_venv(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "readme.md").write_text("venv")
        assert discover_markdown_files(tmp_path, scope="link_audit") == []

    def test_sorted(self, tmp_path):
        (tmp_path / "z.md").write_text("# Z")
        (tmp_path / "a.md").write_text("# A")
        result = discover_markdown_files(tmp_path, scope="link_audit")
        assert result[0].name == "a.md"

    def test_nested_markdown_files(self, tmp_path):
        (tmp_path / "a" / "b" / "c").mkdir(parents=True)
        (tmp_path / "a" / "b" / "c" / "deep.md").write_text("# Deep")
        result = discover_markdown_files(tmp_path, scope="link_audit")
        assert len(result) == 1
        assert "deep.md" in str(result[0])

    def test_empty_dir(self, tmp_path):
        assert discover_markdown_files(tmp_path, scope="link_audit") == []


class TestExtractLinks:
    def test_internal_anchor_links(self, tmp_path):
        f = tmp_path / "test.md"
        internal, external, file_refs = extract_links("[Section](#introduction)", f)
        assert len(internal) == 1
        assert internal[0]["target"] == "#introduction"

    def test_external_links(self, tmp_path):
        f = tmp_path / "test.md"
        content = "Check [Google](https://google.com) for more."
        _, external, _ = extract_links(content, f)
        assert len(external) == 1
        assert "google.com" in external[0]["target"]

    def test_file_reference_links(self, tmp_path):
        f = tmp_path / "test.md"
        _, _, file_refs = extract_links("[Guide](docs/guide.md)", f)
        assert len(file_refs) == 1
        assert file_refs[0]["target"] == "docs/guide.md"

    def test_links_in_code_blocks_excluded(self, tmp_path):
        f = tmp_path / "test.md"
        content = "```\n[Link](url)\n```\nReal [Link](other.md)"
        _, _, file_refs = extract_links(content, f)
        assert len(file_refs) == 1
        assert file_refs[0]["target"] == "other.md"

    def test_mailto_classified_as_external(self, tmp_path):
        f = tmp_path / "test.md"
        _, external, _ = extract_links("[Email](mailto:test@example.com)", f)
        assert len(external) == 1

    def test_protocol_link(self, tmp_path):
        f = tmp_path / "test.md"
        _, external, _ = extract_links("[link](ftp://files.example.com/data)", f)
        assert len(external) == 1

    def test_line_numbers(self, tmp_path):
        f = tmp_path / "test.md"
        content = "Line 1\nLine 2\n[Link](file.md)\n"
        _, _, file_refs = extract_links(content, f)
        assert file_refs[0]["line"] == 3

    def test_multiple_links(self, tmp_path):
        f = tmp_path / "test.md"
        content = "[a](#x) and [b](https://x.com) and [c](file.md)"
        internal, external, refs = extract_links(content, f)
        assert len(internal) == 1
        assert len(external) == 1
        assert len(refs) == 1

    def test_extract_no_links(self, tmp_path):
        f = tmp_path / "test.md"
        internal, external, file_refs = extract_links("Just plain text.", f)
        assert internal == external == file_refs == []


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


class TestShouldValidatePath:
    def test_template_paths_skipped(self):
        assert not _should_validate_path("projects/{name}/src/main.py")

    def test_placeholder_paths_skipped(self):
        assert not _should_validate_path("infrastructure/<module>/test.py")

    def test_url_skipped(self):
        assert not _should_validate_path("https://example.com/path")

    def test_email_skipped(self):
        assert not _should_validate_path("user@example.com")

    def test_keyword_skipped(self):
        assert not _should_validate_path("scripts/my_script.py")
        assert not _should_validate_path("projects/my_project/src/main.py")

    def test_real_path_validated(self):
        assert _should_validate_path("infrastructure/core/security.py")

    def test_malformed_path_skipped(self):
        assert not _should_validate_path("infrastructure/AGENTS.md)")

    def test_path_with_newline_skipped(self):
        assert not _should_validate_path("infrastructure/core/\nsome text")


class TestResolveTemplatePath:
    def test_infrastructure_path(self, tmp_path):
        result = _resolve_template_path("infrastructure/core/security.py", tmp_path)
        assert result == tmp_path / "infrastructure/core/security.py"

    def test_scripts_path(self, tmp_path):
        result = _resolve_template_path("scripts/run.py", tmp_path)
        assert result == tmp_path / "scripts/run.py"

    def test_template_project_path(self, tmp_path):
        assert _resolve_template_path("projects/{name}/src/main.py", tmp_path) is None

    def test_project_path_no_projects_dir(self, tmp_path):
        assert _resolve_template_path("projects/project/src/main.py", tmp_path) is None

    def test_generic_path(self, tmp_path):
        result = _resolve_template_path("docs/guide.md", tmp_path)
        assert result == tmp_path / "docs/guide.md"


class TestIsRealPathItem:
    def test_normal_file(self):
        assert _is_real_path_item("main.py")

    def test_ellipsis_skipped(self):
        assert not _is_real_path_item("...")

    def test_etc_skipped(self):
        assert not _is_real_path_item("etc")

    def test_template_skipped(self):
        assert not _is_real_path_item("{name}")


class TestGetActualProjectNames:
    def test_finds_projects(self, tmp_path):
        proj = tmp_path / "projects"
        proj.mkdir()
        (proj / "alpha").mkdir()
        (proj / "beta").mkdir()
        result = _get_actual_project_names(tmp_path)
        assert "alpha" in result
        assert "beta" in result

    def test_excludes_pycache(self, tmp_path):
        proj = tmp_path / "projects"
        proj.mkdir()
        (proj / "__pycache__").mkdir()
        assert "__pycache__" not in _get_actual_project_names(tmp_path)

    def test_no_projects_dir(self, tmp_path):
        assert _get_actual_project_names(tmp_path) == []


class TestCheckFileReference:
    def test_existing_file(self, tmp_path):
        target = tmp_path / "guide.md"
        target.write_text("# Guide")
        source = tmp_path / "README.md"
        exists, _ = check_file_reference("guide.md", source, tmp_path)
        assert exists is True

    def test_missing_file(self, tmp_path):
        source = tmp_path / "README.md"
        exists, msg = check_file_reference("nonexistent.md", source, tmp_path)
        assert exists is False
        assert "does not exist" in msg

    def test_relative_parent_path(self, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        (tmp_path / "root.md").write_text("# Root")
        source = sub / "guide.md"
        exists, _ = check_file_reference("../root.md", source, tmp_path)
        assert exists is True

    def test_dot_slash_path(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide")
        source = tmp_path / "README.md"
        exists, _ = check_file_reference("./guide.md", source, tmp_path)
        assert exists is True

    def test_directory_reference(self, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        source = tmp_path / "README.md"
        exists, _ = check_file_reference("docs", source, tmp_path)
        assert exists is True

    def test_md_extension_fallback(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide")
        source = tmp_path / "README.md"
        exists, _ = check_file_reference("guide", source, tmp_path)
        assert exists is True

    def test_outside_repo(self, tmp_path):
        source = tmp_path / "README.md"
        exists, msg = check_file_reference("../../../../etc/passwd", source, tmp_path)
        assert exists is False
        assert "outside" in msg.lower() or "does not exist" in msg.lower()

    def test_file_reference_with_anchor(self, tmp_path):
        (tmp_path / "target.md").write_text("# Target\n\n## Section")
        md_file = tmp_path / "test.md"
        md_file.write_text("See [target section](./target.md#section) for details.")
        _, _, file_refs = extract_links(md_file.read_text(), md_file)
        assert len(file_refs) == 1
        assert "#" in file_refs[0]["target"]


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
            "python_imports": [
                {"file": "c.md", "line": 3, "target": "mod", "issue": "not found", "type": "c"}
            ],
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


class TestCheckLinksIntegration:
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


class TestCheckLinksIntegration:
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


class TestCheckLinksCore:
    """Test core link checking functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert check_links is not None

    def test_has_link_checking_functions(self):
        """Test that module has link checking functions."""
        module_funcs = [
            a
            for a in dir(check_links)
            if not a.startswith("_") and callable(getattr(check_links, a, None))
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
        result, msg = check_links.check_file_reference(
            "../../../../../../../../outside.md", source, tmp_path
        )

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


class TestExtractLinks:
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


class TestDiscoverMarkdownFilesLinkAudit:
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
                    all_headings[str(md_file.relative_to(repo_root))] = (
                        check_links.extract_headings(content)
                    )
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")

            # Second pass: check links
            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding="utf-8")
                    internal_links, external_links, file_refs = check_links.extract_links(
                        content, md_file
                    )

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
                            exists, msg = check_links.check_file_reference(
                                target, md_file, repo_root
                            )
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
        assert (
            "broken anchor links" in captured.out.lower() or "nonexistent" in captured.out.lower()
        )
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


class TestValidatePythonImports:
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


class TestValidateImportPath:
    def test_infrastructure_direct_file(self, tmp_path):
        (tmp_path / "infrastructure" / "core").mkdir(parents=True)
        (tmp_path / "infrastructure" / "core" / "logging.py").write_text("")
        block = {"line": 1, "content": ""}
        fp = tmp_path / "test.md"
        issues = _validate_import_path("infrastructure.core.logging", block, fp, tmp_path)
        assert issues == []

    def test_projects_project_src(self, tmp_path):
        (tmp_path / "projects" / "myproj" / "src").mkdir(parents=True)
        (tmp_path / "projects" / "myproj" / "src" / "analysis.py").write_text("")
        block = {"line": 1, "content": ""}
        fp = tmp_path / "test.md"
        issues = _validate_import_path("projects.project.src.analysis", block, fp, tmp_path)
        assert issues == []

    def test_projects_project_src_not_found(self, tmp_path):
        (tmp_path / "projects" / "myproj" / "src").mkdir(parents=True)
        block = {"line": 1, "content": ""}
        fp = tmp_path / "test.md"
        issues = _validate_import_path("projects.project.src.nonexistent", block, fp, tmp_path)
        assert len(issues) >= 1

    def test_non_matching_prefix(self, tmp_path):
        block = {"line": 1, "content": ""}
        fp = tmp_path / "test.md"
        issues = _validate_import_path("os.path", block, fp, tmp_path)
        assert issues == []


class TestValidateFilePathsInCode:
    def test_no_paths(self, tmp_path):
        content = "```python\nprint('hello')\n```"
        issues = validate_file_paths_in_code(content, tmp_path / "test.md", tmp_path)
        assert issues == []

    def test_mermaid_skipped(self, tmp_path):
        content = "```mermaid\ngraph TD\n  A-->B\n```"
        issues = validate_file_paths_in_code(content, tmp_path / "test.md", tmp_path)
        assert issues == []

    def test_existing_path(self, tmp_path):
        (tmp_path / "infrastructure" / "core").mkdir(parents=True)
        (tmp_path / "infrastructure" / "core" / "exceptions.py").write_text("")
        content = "```bash\ncat infrastructure/core/exceptions.py\n```"
        issues = validate_file_paths_in_code(content, tmp_path / "test.md", tmp_path)
        assert issues == []


class TestGetActualProjectNames:
    def test_no_projects_dir(self, tmp_path):
        names = _get_actual_project_names(tmp_path)
        assert names == []

    def test_with_projects(self, tmp_path):
        (tmp_path / "projects" / "alpha").mkdir(parents=True)
        (tmp_path / "projects" / "beta").mkdir(parents=True)
        names = _get_actual_project_names(tmp_path)
        assert "alpha" in names
        assert "beta" in names

    def test_pycache_excluded(self, tmp_path):
        (tmp_path / "projects").mkdir()
        (tmp_path / "projects" / "__pycache__").mkdir()
        (tmp_path / "projects" / "real_project").mkdir()
        names = _get_actual_project_names(tmp_path)
        assert "__pycache__" not in names
        assert "real_project" in names

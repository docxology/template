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
    check_file_reference,
    discover_markdown_files,
    extract_code_blocks,
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


class TestFindAllMarkdownFiles:
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

    def test_find_markdown_files_nested(self, tmp_path):
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

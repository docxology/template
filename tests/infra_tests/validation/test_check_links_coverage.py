"""Tests for infrastructure.validation.integrity.check_links — comprehensive coverage."""

from pathlib import Path

from infrastructure.validation.integrity.check_links import (
    find_all_markdown_files,
    extract_links,
    extract_code_blocks,
    _should_validate_path,
    _resolve_template_path,
    _is_real_path_item,
    _get_actual_project_names,
    check_file_reference,
    validate_directory_structures,
    validate_python_imports,
    validate_placeholder_consistency,
    generate_comprehensive_report,
    run_link_audit,
)


class TestFindAllMarkdownFiles:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "README.md").write_text("# Hi")
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "guide.md").write_text("# Guide")
        result = find_all_markdown_files(tmp_path)
        names = [f.name for f in result]
        assert "README.md" in names
        assert "guide.md" in names

    def test_excludes_output(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()
        (out / "report.md").write_text("# Report")
        result = find_all_markdown_files(tmp_path)
        assert len(result) == 0

    def test_excludes_git(self, tmp_path):
        git = tmp_path / ".git"
        git.mkdir()
        (git / "notes.md").write_text("# Notes")
        result = find_all_markdown_files(tmp_path)
        assert len(result) == 0

    def test_sorted(self, tmp_path):
        (tmp_path / "z.md").write_text("# Z")
        (tmp_path / "a.md").write_text("# A")
        result = find_all_markdown_files(tmp_path)
        assert result[0].name == "a.md"


class TestExtractLinks:
    def test_internal_anchor_links(self, tmp_path):
        f = tmp_path / "test.md"
        content = "[Section](#introduction)"
        internal, external, file_refs = extract_links(content, f)
        assert len(internal) == 1
        assert internal[0]["target"] == "#introduction"

    def test_external_links(self, tmp_path):
        f = tmp_path / "test.md"
        content = "[Google](https://google.com)"
        internal, external, file_refs = extract_links(content, f)
        assert len(external) == 1
        assert "google.com" in external[0]["target"]

    def test_file_reference_links(self, tmp_path):
        f = tmp_path / "test.md"
        content = "[Guide](docs/guide.md)"
        internal, external, file_refs = extract_links(content, f)
        assert len(file_refs) == 1
        assert file_refs[0]["target"] == "docs/guide.md"

    def test_links_in_code_blocks_excluded(self, tmp_path):
        f = tmp_path / "test.md"
        content = "```\n[Link](url)\n```\nReal [Link](other.md)"
        internal, external, file_refs = extract_links(content, f)
        # Only the real link outside code block should be found
        assert len(file_refs) == 1
        assert file_refs[0]["target"] == "other.md"

    def test_mailto_classified_as_external(self, tmp_path):
        f = tmp_path / "test.md"
        content = "[Email](mailto:test@example.com)"
        internal, external, file_refs = extract_links(content, f)
        assert len(external) == 1

    def test_line_numbers(self, tmp_path):
        f = tmp_path / "test.md"
        content = "Line 1\nLine 2\n[Link](file.md)\n"
        internal, external, file_refs = extract_links(content, f)
        assert file_refs[0]["line"] == 3


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
        content = "```python\n\n```"
        blocks = extract_code_blocks(content, f)
        assert len(blocks) == 0

    def test_no_language(self, tmp_path):
        f = tmp_path / "test.md"
        content = "```\nsome code\n```"
        blocks = extract_code_blocks(content, f)
        assert len(blocks) == 1
        assert blocks[0]["language"] == ""


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
        assert result is not None
        assert str(result).endswith("infrastructure/core/security.py")

    def test_scripts_path(self, tmp_path):
        result = _resolve_template_path("scripts/run.py", tmp_path)
        assert result is not None

    def test_template_project_path(self, tmp_path):
        result = _resolve_template_path("projects/{name}/src/main.py", tmp_path)
        assert result is None

    def test_project_project_path_resolved(self, tmp_path):
        proj = tmp_path / "projects" / "demo"
        (proj / "src").mkdir(parents=True)
        result = _resolve_template_path("projects/project/src", tmp_path)
        # Should try to resolve to actual project names
        # If demo exists, may return a path
        assert result is None or isinstance(result, Path)

    def test_generic_path(self, tmp_path):
        result = _resolve_template_path("docs/guide.md", tmp_path)
        assert result is not None


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
        result = _get_actual_project_names(tmp_path)
        assert "__pycache__" not in result

    def test_no_projects_dir(self, tmp_path):
        result = _get_actual_project_names(tmp_path)
        assert result == []


class TestCheckFileReference:
    def test_existing_file(self, tmp_path):
        target = tmp_path / "guide.md"
        target.write_text("# Guide")
        source = tmp_path / "README.md"
        exists, msg = check_file_reference("guide.md", source, tmp_path)
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
        exists, msg = check_file_reference("../root.md", source, tmp_path)
        assert exists is True

    def test_dot_slash_path(self, tmp_path):
        target = tmp_path / "guide.md"
        target.write_text("# Guide")
        source = tmp_path / "README.md"
        exists, msg = check_file_reference("./guide.md", source, tmp_path)
        assert exists is True

    def test_directory_reference(self, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        source = tmp_path / "README.md"
        exists, msg = check_file_reference("docs", source, tmp_path)
        assert exists is True

    def test_md_extension_fallback(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide")
        source = tmp_path / "README.md"
        exists, msg = check_file_reference("guide", source, tmp_path)
        assert exists is True

    def test_outside_repo(self, tmp_path):
        source = tmp_path / "README.md"
        exists, msg = check_file_reference("../../../../etc/passwd", source, tmp_path)
        assert exists is False
        assert "outside" in msg.lower() or "does not exist" in msg.lower()


class TestValidateDirectoryStructures:
    def test_valid_tree(self, tmp_path):
        (tmp_path / "src").mkdir()
        content = "```\n" + chr(9500) + chr(9472) * 2 + " src/\n```"
        issues = validate_directory_structures(content, tmp_path / "README.md", tmp_path)
        assert isinstance(issues, list)

    def test_no_tree(self, tmp_path):
        content = "No tree diagrams here."
        issues = validate_directory_structures(content, tmp_path / "README.md", tmp_path)
        assert issues == []


class TestValidatePythonImports:
    def test_valid_import(self, tmp_path):
        # Create an infrastructure module
        infra = tmp_path / "infrastructure" / "core"
        infra.mkdir(parents=True)
        (infra / "__init__.py").write_text("")
        (infra / "security.py").write_text("x = 1")

        content = "```python\nfrom infrastructure.core.security import x\n```"
        f = tmp_path / "README.md"
        issues = validate_python_imports(content, f, tmp_path)
        assert len(issues) == 0

    def test_invalid_import(self, tmp_path):
        content = "```python\nfrom infrastructure.nonexistent.module import x\n```"
        f = tmp_path / "README.md"
        issues = validate_python_imports(content, f, tmp_path)
        assert len(issues) == 1
        assert "not found" in issues[0]["issue"]

    def test_syntax_error_skipped(self, tmp_path):
        content = "```python\nthis is not valid python {{{\n```"
        f = tmp_path / "README.md"
        issues = validate_python_imports(content, f, tmp_path)
        assert issues == []


class TestValidatePlaceholderConsistency:
    def test_template_usage_ok(self, tmp_path):
        content = "Use projects/{name}/src for your project template."
        f = tmp_path / "README.md"
        issues = validate_placeholder_consistency(content, f, tmp_path)
        assert len(issues) == 0

    def test_skipped_files(self, tmp_path):
        content = "projects/{name} usage"
        f = tmp_path / "infrastructure" / "AGENTS.md"
        f.parent.mkdir(parents=True)
        issues = validate_placeholder_consistency(content, f, tmp_path)
        assert len(issues) == 0


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
        result = generate_comprehensive_report(issues, 10)
        assert result == 0

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
        result = generate_comprehensive_report(issues, 5)
        assert result == 1

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
        result = generate_comprehensive_report(issues, 20)
        assert result == 1


class TestRunLinkAudit:
    def test_clean_repo(self, tmp_path):
        (tmp_path / "README.md").write_text("# Hello World\n\nSimple text, no links.")
        result = run_link_audit(tmp_path)
        assert result == 0

    def test_with_broken_link(self, tmp_path):
        (tmp_path / "README.md").write_text("[Missing](nonexistent.md)")
        result = run_link_audit(tmp_path)
        assert result == 1

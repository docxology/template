"""Tests for infrastructure.validation.integrity.check_links — expanded coverage."""


from infrastructure.validation.integrity.check_links import (
    extract_links,
    extract_code_blocks,
    _should_validate_path,
    _is_real_path_item,
    _resolve_template_path,
    check_file_reference,
    find_all_markdown_files,
    validate_directory_structures,
    validate_placeholder_consistency,
    generate_comprehensive_report,
)


class TestExtractLinks:
    def test_internal_anchor(self, tmp_path):
        content = "See [heading](#my-heading) for details."
        fp = tmp_path / "test.md"
        internal, external, refs = extract_links(content, fp)
        assert len(internal) == 1
        assert internal[0]["target"] == "#my-heading"
        assert internal[0]["text"] == "heading"
        assert len(external) == 0
        assert len(refs) == 0

    def test_external_http(self, tmp_path):
        content = "Visit [Google](https://google.com) now."
        fp = tmp_path / "test.md"
        internal, external, refs = extract_links(content, fp)
        assert len(external) == 1
        assert external[0]["target"] == "https://google.com"
        assert len(internal) == 0

    def test_external_mailto(self, tmp_path):
        content = "Email [us](mailto:info@test.com)."
        fp = tmp_path / "test.md"
        _, external, _ = extract_links(content, fp)
        assert len(external) == 1
        assert "mailto:" in external[0]["target"]

    def test_file_reference(self, tmp_path):
        content = "See [docs](../README.md) for info."
        fp = tmp_path / "test.md"
        internal, external, refs = extract_links(content, fp)
        assert len(refs) == 1
        assert refs[0]["target"] == "../README.md"
        assert len(internal) == 0
        assert len(external) == 0

    def test_code_blocks_stripped(self, tmp_path):
        content = "Text `[not a link](foo)` end.\n\n```\n[also not](bar)\n```\n"
        fp = tmp_path / "test.md"
        internal, external, refs = extract_links(content, fp)
        assert len(internal) == 0
        assert len(external) == 0
        assert len(refs) == 0

    def test_multiple_links(self, tmp_path):
        content = "[a](#x) and [b](https://x.com) and [c](file.md)"
        fp = tmp_path / "test.md"
        internal, external, refs = extract_links(content, fp)
        assert len(internal) == 1
        assert len(external) == 1
        assert len(refs) == 1

    def test_line_numbers(self, tmp_path):
        content = "line1\n[link](#heading)\nline3"
        fp = tmp_path / "test.md"
        internal, _, _ = extract_links(content, fp)
        assert internal[0]["line"] == 2

    def test_protocol_link(self, tmp_path):
        content = "[link](ftp://files.example.com/data)"
        fp = tmp_path / "test.md"
        _, external, _ = extract_links(content, fp)
        assert len(external) == 1


class TestExtractCodeBlocks:
    def test_basic_code_block(self, tmp_path):
        content = "text\n```python\nprint('hello')\n```\nmore"
        fp = tmp_path / "test.md"
        blocks = extract_code_blocks(content, fp)
        assert len(blocks) == 1
        assert blocks[0]["language"] == "python"
        assert "print" in blocks[0]["content"]

    def test_no_language(self, tmp_path):
        content = "```\nsome code\n```"
        fp = tmp_path / "test.md"
        blocks = extract_code_blocks(content, fp)
        assert len(blocks) == 1
        assert blocks[0]["language"] == ""

    def test_empty_code_block(self, tmp_path):
        content = "```python\n\n```"
        fp = tmp_path / "test.md"
        blocks = extract_code_blocks(content, fp)
        assert len(blocks) == 0

    def test_multiple_blocks(self, tmp_path):
        content = "```bash\nls\n```\n\n```python\nprint(1)\n```"
        fp = tmp_path / "test.md"
        blocks = extract_code_blocks(content, fp)
        assert len(blocks) == 2
        assert blocks[0]["language"] == "bash"
        assert blocks[1]["language"] == "python"


class TestShouldValidatePath:
    def test_template_path_skipped(self):
        assert _should_validate_path("projects/{name}/src/main.py") is False

    def test_angle_bracket_placeholder(self):
        assert _should_validate_path("infrastructure/<module>/core.py") is False

    def test_url_skipped(self):
        assert _should_validate_path("https://example.com/path") is False

    def test_email_skipped(self):
        assert _should_validate_path("user@example.com") is False

    def test_keyword_skipped(self):
        assert _should_validate_path("projects/my_project/src/analysis.py") is False

    def test_valid_path(self):
        assert _should_validate_path("infrastructure/core/exceptions.py") is True

    def test_malformed_trailing_paren(self):
        assert _should_validate_path("infrastructure/AGENTS.md)") is False

    def test_path_with_newline(self):
        assert _should_validate_path("infrastructure/core\nfoo") is False


class TestIsRealPathItem:
    def test_placeholder_dots(self):
        assert _is_real_path_item("...") is False

    def test_etc(self):
        assert _is_real_path_item("etc") is False

    def test_template_var(self):
        assert _is_real_path_item("{project_name}") is False

    def test_real_file(self):
        assert _is_real_path_item("main.py") is True

    def test_real_dir(self):
        assert _is_real_path_item("src/") is True


class TestResolveTemplatePath:
    def test_infrastructure_path(self, tmp_path):
        result = _resolve_template_path("infrastructure/core/exceptions.py", tmp_path)
        assert result == tmp_path / "infrastructure/core/exceptions.py"

    def test_scripts_path(self, tmp_path):
        result = _resolve_template_path("scripts/run.sh", tmp_path)
        assert result == tmp_path / "scripts/run.sh"

    def test_template_name_returns_none(self, tmp_path):
        result = _resolve_template_path("projects/{name}/src/main.py", tmp_path)
        assert result is None

    def test_generic_path(self, tmp_path):
        result = _resolve_template_path("docs/README.md", tmp_path)
        assert result == tmp_path / "docs/README.md"

    def test_project_path_no_projects_dir(self, tmp_path):
        result = _resolve_template_path("projects/project/src/main.py", tmp_path)
        assert result is None

    def test_output_project_path_no_projects_dir(self, tmp_path):
        result = _resolve_template_path("output/project/pdf/paper.pdf", tmp_path)
        assert result is None


class TestCheckFileReference:
    def test_existing_file(self, tmp_path):
        target_file = tmp_path / "docs" / "README.md"
        target_file.parent.mkdir()
        target_file.write_text("# Docs")
        source = tmp_path / "src" / "main.py"
        source.parent.mkdir()
        source.write_text("")
        exists, msg = check_file_reference("../docs/README.md", source, tmp_path)
        assert exists is True

    def test_missing_file(self, tmp_path):
        source = tmp_path / "src" / "main.py"
        source.parent.mkdir()
        source.write_text("")
        exists, msg = check_file_reference("../nonexistent.md", source, tmp_path)
        assert exists is False
        assert "does not exist" in msg

    def test_relative_dot_slash(self, tmp_path):
        target = tmp_path / "src" / "helper.py"
        target.parent.mkdir()
        target.write_text("")
        source = tmp_path / "src" / "main.py"
        source.write_text("")
        exists, _ = check_file_reference("./helper.py", source, tmp_path)
        assert exists is True

    def test_directory_reference(self, tmp_path):
        target_dir = tmp_path / "docs"
        target_dir.mkdir()
        source = tmp_path / "README.md"
        source.write_text("")
        exists, _ = check_file_reference("docs", source, tmp_path)
        assert exists is True

    def test_md_without_extension(self, tmp_path):
        target = tmp_path / "docs" / "guide.md"
        target.parent.mkdir()
        target.write_text("# Guide")
        source = tmp_path / "README.md"
        source.write_text("")
        exists, _ = check_file_reference("docs/guide", source, tmp_path)
        assert exists is True

    def test_outside_repo(self, tmp_path):
        source = tmp_path / "README.md"
        source.write_text("")
        exists, msg = check_file_reference("../../../../etc/passwd", source, tmp_path)
        assert exists is False
        assert "outside" in msg.lower() or "does not exist" in msg.lower()


class TestFindAllMarkdownFiles:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "README.md").write_text("# Readme")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")
        files = find_all_markdown_files(tmp_path)
        assert len(files) == 2

    def test_excludes_output(self, tmp_path):
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "report.md").write_text("# Report")
        (tmp_path / "README.md").write_text("# Readme")
        files = find_all_markdown_files(tmp_path)
        assert len(files) == 1

    def test_excludes_venv(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "readme.md").write_text("venv")
        files = find_all_markdown_files(tmp_path)
        assert len(files) == 0


class TestValidateDirectoryStructures:
    def test_no_tree_diagrams(self, tmp_path):
        content = "Just regular text, no tree diagrams."
        issues = validate_directory_structures(content, tmp_path / "test.md", tmp_path)
        assert issues == []

    def test_tree_diagram_with_template_var(self, tmp_path):
        content = "```\n├── {project_name}/\n└── {module}/\n```"
        issues = validate_directory_structures(content, tmp_path / "test.md", tmp_path)
        assert issues == []

    def test_tree_diagram_with_existing_dir(self, tmp_path):
        (tmp_path / "src").mkdir()
        content = "```\n├── src/\n```"
        issues = validate_directory_structures(content, tmp_path / "test.md", tmp_path)
        assert issues == []


class TestValidatePlaceholderConsistency:
    def test_skip_agent_files(self, tmp_path):
        content = "Use {name} for the project."
        fp = tmp_path / "AGENTS.md"
        issues = validate_placeholder_consistency(content, fp, tmp_path)
        assert issues == []

    def test_no_placeholders(self, tmp_path):
        content = "No placeholders here."
        fp = tmp_path / "docs" / "test.md"
        issues = validate_placeholder_consistency(content, fp, tmp_path)
        assert issues == []

    def test_template_context_skipped(self, tmp_path):
        content = "Use projects/{name} for the template structure."
        fp = tmp_path / "guide.md"
        issues = validate_placeholder_consistency(content, fp, tmp_path)
        assert issues == []


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
                {"file": "test.md", "line": 1, "target": "#bad", "text": "link", "issue": "Not found", "type": "broken_anchor"}
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
        many_issues = [
            {"file": f"f{i}.md", "line": i, "target": f"#t{i}", "text": f"l{i}", "issue": "bad", "type": "anchor"}
            for i in range(10)
        ]
        issues = {
            "broken_anchor_links": many_issues,
            "broken_file_refs": [],
            "code_block_paths": [],
            "directory_structures": [],
            "python_imports": [],
            "placeholder_consistency": [],
        }
        result = generate_comprehensive_report(issues, 20)
        assert result == 1

    def test_multiple_categories(self):
        issues = {
            "broken_anchor_links": [{"file": "a.md", "line": 1, "target": "#x", "text": "x", "issue": "bad", "type": "a"}],
            "broken_file_refs": [{"file": "b.md", "line": 2, "target": "f.md", "text": "f", "issue": "missing", "type": "b"}],
            "code_block_paths": [],
            "directory_structures": [],
            "python_imports": [{"file": "c.md", "line": 3, "target": "mod", "issue": "not found", "type": "c"}],
            "placeholder_consistency": [],
        }
        result = generate_comprehensive_report(issues, 15)
        assert result == 1

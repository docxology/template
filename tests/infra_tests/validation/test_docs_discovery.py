"""Tests for infrastructure.validation.docs.discovery — pure function coverage."""


from infrastructure.validation.docs.discovery import (
    _get_project_category,
    analyze_documentation_file,
    catalog_agents_readme,
    create_hierarchy,
    discover_markdown_files,
    find_config_files,
    find_markdown_files,
    find_script_files,
    identify_cross_references,
)
from infrastructure.validation.docs.models import DocumentationFile


class TestDiscoverMarkdownFiles:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "doc.md").write_text("# Doc")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "nested.md").write_text("# Nested")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 2

    def test_excludes_output_dir(self, tmp_path):
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "skip.md").write_text("# Skip")
        (tmp_path / "keep.md").write_text("# Keep")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "keep.md"

    def test_excludes_venv(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "skip.md").write_text("# Skip")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 0

    def test_excludes_pycache(self, tmp_path):
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "skip.md").write_text("# Skip")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 0

    def test_empty_dir(self, tmp_path):
        result = discover_markdown_files(tmp_path)
        assert result == []


class TestFindMarkdownFiles:
    def test_is_alias(self, tmp_path):
        (tmp_path / "doc.md").write_text("# Doc")
        result_a = discover_markdown_files(tmp_path)
        result_b = find_markdown_files(tmp_path)
        assert result_a == result_b


class TestCatalogAgentsReadme:
    def test_catalogs_agents_and_readme(self, tmp_path):
        files = [
            tmp_path / "AGENTS.md",
            tmp_path / "README.md",
            tmp_path / "other.md",
        ]
        for f in files:
            f.write_text("# Content")
        result = catalog_agents_readme(files, tmp_path)
        assert "AGENTS.md" in result
        assert "README.md" in result
        assert "other.md" not in result
        assert len(result) == 2

    def test_empty_list(self, tmp_path):
        assert catalog_agents_readme([], tmp_path) == []


class TestFindConfigFiles:
    def test_finds_toml_and_yaml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool]")
        (tmp_path / "config.yaml").write_text("key: val")
        result = find_config_files(tmp_path)
        assert "pyproject.toml" in result
        assert "config.yaml" in result

    def test_excludes_venv_configs(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "setup.toml").write_text("[tool]")
        result = find_config_files(tmp_path)
        assert "setup.toml" not in result

    def test_empty_dir(self, tmp_path):
        result = find_config_files(tmp_path)
        assert result == {}


class TestFindScriptFiles:
    def test_finds_scripts_in_scripts_dir(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run.py").write_text("print('hello')")
        (scripts_dir / "setup.sh").write_text("echo hello")
        result = find_script_files(tmp_path)
        assert len(result) == 2

    def test_ignores_non_script_dirs(self, tmp_path):
        other = tmp_path / "docs"
        other.mkdir()
        (other / "script.py").write_text("print('hello')")
        result = find_script_files(tmp_path)
        assert len(result) == 0

    def test_finds_src_scripts(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")
        result = find_script_files(tmp_path)
        assert len(result) == 1


class TestCreateHierarchy:
    def test_creates_hierarchy(self, tmp_path):
        files = [
            tmp_path / "README.md",
            tmp_path / "docs" / "guide.md",
        ]
        (tmp_path / "docs").mkdir()
        for f in files:
            f.write_text("# Content")
        hierarchy = create_hierarchy(files, tmp_path)
        assert "root" in hierarchy
        assert "docs" in hierarchy

    def test_empty_list(self, tmp_path):
        assert create_hierarchy([], tmp_path) == {}


class TestIdentifyCrossReferences:
    def test_finds_local_links(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("[link](other/file.md)\n[web](https://example.com)\n[anchor](#section)\n")
        result = identify_cross_references([md])
        assert "other/file.md" in result
        # HTTP and anchor links should be excluded
        assert "https://example.com" not in result
        assert "#section" not in result

    def test_no_links(self, tmp_path):
        md = tmp_path / "plain.md"
        md.write_text("No links here.\n")
        result = identify_cross_references([md])
        assert result == set()

    def test_unreadable_file(self, tmp_path):
        # Nonexistent path should not crash
        result = identify_cross_references([tmp_path / "nonexistent.md"])
        assert result == set()


class TestGetProjectCategory:
    def test_manuscript_category(self):
        result = _get_project_category("projects/myproj/manuscript/intro.md", {"myproj"})
        assert result == "project_manuscript_myproj"

    def test_scripts_category(self):
        result = _get_project_category("projects/myproj/scripts/run.py", {"myproj"})
        assert result == "project_scripts_myproj"

    def test_tests_category(self):
        result = _get_project_category("projects/myproj/tests/test_foo.py", {"myproj"})
        assert result == "project_tests_myproj"

    def test_src_category(self):
        result = _get_project_category("projects/myproj/src/main.py", {"myproj"})
        assert result == "project_src_myproj"

    def test_generic_project_category(self):
        result = _get_project_category("projects/myproj/README.md", {"myproj"})
        assert result == "project_myproj"

    def test_non_project_path(self):
        result = _get_project_category("docs/guide.md", {"myproj"})
        assert result is None

    def test_unknown_project_name(self):
        result = _get_project_category("projects/unknown/src/main.py", {"myproj"})
        assert result is None


class TestAnalyzeDocumentationFile:
    def test_basic_analysis(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Title\nSome content with [a link](other.md).\n```python\ncode\n```\n")
        result = analyze_documentation_file(md, tmp_path)
        assert isinstance(result, DocumentationFile)
        assert result.name == "doc.md"
        assert result.word_count > 0
        assert result.line_count > 0
        assert result.has_links is True
        assert result.has_code_blocks is True

    def test_docs_category(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        md = docs_dir / "guide.md"
        md.write_text("# Guide\nContent.\n")
        result = analyze_documentation_file(md, tmp_path)
        assert result.category == "documentation"

    def test_manuscript_category(self, tmp_path):
        ms_dir = tmp_path / "manuscript"
        ms_dir.mkdir()
        md = ms_dir / "intro.md"
        md.write_text("# Introduction\n")
        result = analyze_documentation_file(md, tmp_path)
        assert result.category == "manuscript"

    def test_agents_md_category(self, tmp_path):
        md = tmp_path / "AGENTS.md"
        md.write_text("# Agents\n")
        result = analyze_documentation_file(md, tmp_path)
        assert result.category == "directory_doc"

    def test_readme_md_category(self, tmp_path):
        md = tmp_path / "README.md"
        md.write_text("# Readme\n")
        result = analyze_documentation_file(md, tmp_path)
        assert result.category == "directory_doc"

    def test_other_category(self, tmp_path):
        md = tmp_path / "random.md"
        md.write_text("# Random\n")
        result = analyze_documentation_file(md, tmp_path)
        assert result.category == "other"

    def test_no_links_no_code(self, tmp_path):
        md = tmp_path / "plain.md"
        md.write_text("Just plain text.\n")
        result = analyze_documentation_file(md, tmp_path)
        assert result.has_links is False
        assert result.has_code_blocks is False

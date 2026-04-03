"""Tests for infrastructure.validation.docs.discovery — comprehensive coverage."""


from infrastructure.validation.docs.discovery import (
    discover_markdown_files,
    find_markdown_files,
    catalog_agents_readme,
    find_config_files,
    find_script_files,
    create_hierarchy,
    identify_cross_references,
    categorize_documentation,
    _get_project_category,
    analyze_documentation_file,
    run_discovery_phase,
    _calculate_project_stats,
)


class TestDiscoverMarkdownFiles:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "README.md").write_text("# Hello")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")
        result = discover_markdown_files(tmp_path)
        names = [f.name for f in result]
        assert "README.md" in names
        assert "guide.md" in names

    def test_excludes_output_dir(self, tmp_path):
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "report.md").write_text("# Report")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 0

    def test_excludes_venv(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "readme.md").write_text("# Venv")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 0

    def test_excludes_projects_archive(self, tmp_path):
        (tmp_path / "projects_archive").mkdir()
        (tmp_path / "projects_archive" / "old.md").write_text("# Old")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 0

    def test_empty_dir(self, tmp_path):
        result = discover_markdown_files(tmp_path)
        assert result == []

    def test_sorted_output(self, tmp_path):
        (tmp_path / "z.md").write_text("# Z")
        (tmp_path / "a.md").write_text("# A")
        result = discover_markdown_files(tmp_path)
        assert result[0].name == "a.md"
        assert result[1].name == "z.md"


class TestFindMarkdownFiles:
    def test_alias_works(self, tmp_path):
        (tmp_path / "test.md").write_text("# Test")
        result = find_markdown_files(tmp_path)
        assert len(result) == 1


class TestCatalogAgentsReadme:
    def test_finds_agents_and_readme(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("# Agents")
        (tmp_path / "README.md").write_text("# Readme")
        (tmp_path / "other.md").write_text("# Other")
        md_files = list(tmp_path.glob("*.md"))
        result = catalog_agents_readme(md_files, tmp_path)
        assert "AGENTS.md" in result
        assert "README.md" in result
        assert "other.md" not in result

    def test_nested_agents(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "AGENTS.md").write_text("# Sub Agents")
        md_files = [sub / "AGENTS.md"]
        result = catalog_agents_readme(md_files, tmp_path)
        assert "sub/AGENTS.md" in result


class TestFindConfigFiles:
    def test_finds_config_files(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]")
        (tmp_path / "config.yaml").write_text("key: val")
        result = find_config_files(tmp_path)
        assert "pyproject.toml" in result
        assert "config.yaml" in result

    def test_excludes_venv_configs(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "config.yaml").write_text("key: val")
        result = find_config_files(tmp_path)
        assert "config.yaml" not in result

    def test_empty_dir(self, tmp_path):
        result = find_config_files(tmp_path)
        assert result == {}


class TestFindScriptFiles:
    def test_finds_scripts_in_scripts_dir(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('hi')")
        (scripts / "build.sh").write_text("echo hi")
        result = find_script_files(tmp_path)
        names = [f.name for f in result]
        assert "run.py" in names
        assert "build.sh" in names

    def test_excludes_tests_dir(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("def test(): pass")
        result = find_script_files(tmp_path)
        assert len(result) == 0

    def test_excludes_venv(self, tmp_path):
        venv = tmp_path / ".venv" / "scripts"
        venv.mkdir(parents=True)
        (venv / "activate.py").write_text("pass")
        result = find_script_files(tmp_path)
        assert len(result) == 0


class TestCreateHierarchy:
    def test_groups_by_directory(self, tmp_path):
        (tmp_path / "README.md").write_text("# Root")
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "guide.md").write_text("# Guide")
        md_files = sorted(tmp_path.rglob("*.md"))
        result = create_hierarchy(md_files, tmp_path)
        assert "root" in result
        assert "docs" in result

    def test_root_dir_mapping(self, tmp_path):
        (tmp_path / "test.md").write_text("# T")
        md_files = list(tmp_path.glob("*.md"))
        result = create_hierarchy(md_files, tmp_path)
        assert "root" in result


class TestIdentifyCrossReferences:
    def test_finds_internal_links(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("[Guide](docs/guide.md)\n[External](https://example.com)")
        result = identify_cross_references([f])
        assert "docs/guide.md" in result

    def test_skips_external_links(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("[Link](https://example.com)")
        result = identify_cross_references([f])
        assert len(result) == 0

    def test_skips_anchor_links(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("[Section](#section)")
        result = identify_cross_references([f])
        assert len(result) == 0

    def test_handles_unreadable_file(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_bytes(b"\xff\xfe\x80\x81")
        # Should not crash
        result = identify_cross_references([f])
        assert isinstance(result, set)


class TestGetProjectCategory:
    def test_manuscript_category(self):
        result = _get_project_category("projects/alpha/manuscript/paper.md", {"alpha"})
        assert result == "project_manuscript_alpha"

    def test_scripts_category(self):
        result = _get_project_category("projects/alpha/scripts/run.md", {"alpha"})
        assert result == "project_scripts_alpha"

    def test_tests_category(self):
        result = _get_project_category("projects/alpha/tests/readme.md", {"alpha"})
        assert result == "project_tests_alpha"

    def test_src_category(self):
        result = _get_project_category("projects/alpha/src/readme.md", {"alpha"})
        assert result == "project_src_alpha"

    def test_general_project_category(self):
        result = _get_project_category("projects/alpha/README.md", {"alpha"})
        assert result == "project_alpha"

    def test_not_a_project(self):
        result = _get_project_category("docs/guide.md", {"alpha"})
        assert result is None

    def test_unknown_project_name(self):
        result = _get_project_category("projects/unknown/README.md", {"alpha"})
        assert result is None


class TestCategorizeDocumentation:
    def test_categorizes_docs(self, tmp_path):
        # Set up minimal project structure for discover_projects
        proj = tmp_path / "projects" / "demo"
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "__init__.py").write_text("")
        (proj / "src" / "core.py").write_text("x = 1\n")
        (proj / "tests").mkdir()
        (proj / "tests" / "__init__.py").write_text("")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide")
        (tmp_path / "AGENTS.md").write_text("# Agents")

        md_files = sorted(tmp_path.rglob("*.md"))
        result = categorize_documentation(md_files, tmp_path)
        assert isinstance(result, dict)


class TestAnalyzeDocumentationFile:
    def test_analyzes_file(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Title\n\nSome content with [link](other.md) and ```code```.\n")
        result = analyze_documentation_file(f, tmp_path)
        assert result.name == "test.md"
        assert result.word_count > 0
        assert result.line_count > 0
        assert result.has_links is True
        assert result.has_code_blocks is True

    def test_docs_category(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "guide.md"
        f.write_text("# Guide\n")
        result = analyze_documentation_file(f, tmp_path)
        assert result.category == "documentation"

    def test_manuscript_category(self, tmp_path):
        ms = tmp_path / "manuscript"
        ms.mkdir()
        f = ms / "paper.md"
        f.write_text("# Paper\n")
        result = analyze_documentation_file(f, tmp_path)
        assert result.category == "manuscript"

    def test_directory_doc_category(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("# Readme\n")
        result = analyze_documentation_file(f, tmp_path)
        assert result.category == "directory_doc"

    def test_other_category(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# Notes\n")
        result = analyze_documentation_file(f, tmp_path)
        assert result.category == "other"


class TestCalculateProjectStats:
    def test_basic_stats(self):
        from infrastructure.validation.docs.models import DocumentationFile

        doc = DocumentationFile(
            path="/tmp/test.md",
            relative_path="test.md",
            directory=".",
            name="test.md",
            word_count=100,
            line_count=20,
            has_links=True,
            has_code_blocks=False,
        )
        project_data = {
            "documentation_files": [doc],
            "manuscript_files": [],
            "script_docs": [],
            "test_docs": [],
        }
        result = _calculate_project_stats(project_data)
        assert result["total_files"] == 1
        assert result["total_words"] == 100
        assert result["total_lines"] == 20
        assert result["files_with_links"] == 1
        assert result["files_with_code"] == 0


class TestRunDiscoveryPhase:
    def test_basic_discovery(self, tmp_path):
        (tmp_path / "README.md").write_text("# Root")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")
        (tmp_path / "projects").mkdir()
        result = run_discovery_phase(tmp_path)
        assert "markdown_files" in result
        assert result["markdown_files"] >= 2
        assert "hierarchy" in result
        assert "categories" in result
        assert "documentation_files" in result


class TestDiscoverProjectDocumentation:
    def _make_project(self, tmp_path, name):
        proj = tmp_path / "projects" / name
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "__init__.py").write_text("")
        (proj / "src" / "core.py").write_text("x = 1\n")
        (proj / "tests").mkdir()
        (proj / "tests" / "__init__.py").write_text("")
        ms = proj / "manuscript"
        ms.mkdir()
        (ms / "paper.md").write_text("# Abstract\n\nContent.\n")
        scripts = proj / "scripts"
        scripts.mkdir()
        return proj

    def test_finds_project_docs(self, tmp_path):
        from infrastructure.validation.docs.discovery import discover_project_documentation
        self._make_project(tmp_path, "alpha")
        result = discover_project_documentation(tmp_path)
        assert "alpha" in result
        assert "project_info" in result["alpha"]
        assert "statistics" in result["alpha"]
        assert result["alpha"]["statistics"]["total_files"] >= 0

    def test_empty_projects(self, tmp_path):
        from infrastructure.validation.docs.discovery import discover_project_documentation
        (tmp_path / "projects").mkdir()
        result = discover_project_documentation(tmp_path)
        assert result == {}


class TestValidateProjectDocIntegrity:
    def test_missing_manuscript(self, tmp_path):
        from infrastructure.validation.docs.discovery import validate_project_documentation_integrity
        proj = tmp_path / "projects" / "demo"
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "__init__.py").write_text("")
        (proj / "src" / "core.py").write_text("x = 1\n")
        (proj / "tests").mkdir()
        (proj / "tests" / "__init__.py").write_text("")
        result = validate_project_documentation_integrity(tmp_path)
        assert "demo" in result
        assert any("manuscript" in issue.lower() for issue in result["demo"])

    def test_missing_readme(self, tmp_path):
        from infrastructure.validation.docs.discovery import validate_project_documentation_integrity
        proj = tmp_path / "projects" / "demo"
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "__init__.py").write_text("")
        (proj / "src" / "core.py").write_text("x = 1\n")
        (proj / "tests").mkdir()
        (proj / "tests" / "__init__.py").write_text("")
        result = validate_project_documentation_integrity(tmp_path)
        assert any("README" in issue for issue in result["demo"])


class TestGetAuditContext:
    def test_basic_context(self, tmp_path):
        from infrastructure.validation.docs.discovery import get_audit_context
        (tmp_path / "README.md").write_text("# Root")
        (tmp_path / "projects").mkdir()
        result = get_audit_context(tmp_path)
        assert "projects" in result
        assert "total_markdown_files" in result
        assert "documentation_hierarchy" in result
        assert "documentation_categories" in result

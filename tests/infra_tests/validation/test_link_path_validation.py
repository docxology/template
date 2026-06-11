"""Tests for link path validation in check_links / link_extract."""

from pathlib import Path

from infrastructure.validation.integrity.check_links import (
    _get_actual_project_names,
    _is_real_path_item,
    _resolve_template_path,
    _should_validate_path,
    _validate_import_path,
    validate_file_paths_in_code,
)

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
        for name in ("alpha", "beta"):
            root = proj / name
            root.mkdir()
            (root / "src").mkdir()
            (root / "src" / "__init__.py").write_text("")
            (root / "tests").mkdir()
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



class TestValidateImportPath:
    def test_infrastructure_direct_file(self, tmp_path):
        (tmp_path / "infrastructure" / "core").mkdir(parents=True)
        (tmp_path / "infrastructure" / "core" / "logging.py").write_text("")
        block = {"line": 1, "content": ""}
        fp = tmp_path / "test.md"
        issues = _validate_import_path("infrastructure.core.logging", block, fp, tmp_path)
        assert issues == []

    def test_projects_project_src(self, tmp_path):
        project = tmp_path / "projects" / "myproj"
        (project / "src").mkdir(parents=True)
        (project / "tests").mkdir(parents=True)
        (project / "src" / "__init__.py").write_text("")
        (project / "tests" / "__init__.py").write_text("")
        (project / "src" / "analysis.py").write_text("")
        block = {"line": 1, "content": ""}
        fp = tmp_path / "test.md"
        issues = _validate_import_path("projects.project.src.analysis", block, fp, tmp_path)
        assert issues == []

    def test_projects_project_src_not_found(self, tmp_path):
        project = tmp_path / "projects" / "myproj"
        (project / "src").mkdir(parents=True)
        (project / "tests").mkdir(parents=True)
        (project / "tests" / "__init__.py").write_text("")
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

    def test_project_local_script_path_resolves_from_project_root(self, tmp_path):
        project_root = tmp_path / "projects" / "templates" / "template_demo"
        (project_root / "scripts").mkdir(parents=True)
        (project_root / "scripts" / "compose_manuscript.py").write_text("")
        md_file = project_root / "README.md"
        content = "```bash\nuv run python scripts/compose_manuscript.py\n```"

        issues = validate_file_paths_in_code(content, md_file, tmp_path)

        assert issues == []

    def test_project_local_missing_script_still_fails(self, tmp_path):
        project_root = tmp_path / "projects" / "templates" / "template_demo"
        project_root.mkdir(parents=True)
        md_file = project_root / "README.md"
        content = "```bash\nuv run python scripts/missing_project_script.py\n```"

        issues = validate_file_paths_in_code(content, md_file, tmp_path)

        assert len(issues) == 1
        assert issues[0]["target"] == "scripts/missing_project_script.py"

    def test_project_doc_script_path_falls_back_to_repo_root(self, tmp_path):
        project_root = tmp_path / "projects" / "templates" / "template_demo"
        project_root.mkdir(parents=True)
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "03_render_pdf.py").write_text("")
        md_file = project_root / "README.md"
        content = "```bash\nuv run python scripts/03_render_pdf.py --project template_demo\n```"

        issues = validate_file_paths_in_code(content, md_file, tmp_path)

        assert issues == []

    def test_aggregate_projects_docs_use_repo_root_scripts(self, tmp_path):
        (tmp_path / "projects").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "03_render_pdf.py").write_text("")
        md_file = tmp_path / "projects" / "README.md"
        content = "```bash\nuv run python scripts/03_render_pdf.py --project template_demo\n```"

        issues = validate_file_paths_in_code(content, md_file, tmp_path)

        assert issues == []

    def test_embedded_docs_script_path_does_not_match_root_scripts_substring(self, tmp_path):
        (tmp_path / "docs" / "operational" / "scripts").mkdir(parents=True)
        (tmp_path / "docs" / "operational" / "scripts" / "rotate-logs.sh").write_text("")
        content = "```bash\nbash docs/operational/scripts/rotate-logs.sh\n```"

        issues = validate_file_paths_in_code(content, tmp_path / "docs" / "operational" / "README.md", tmp_path)

        assert issues == []



class TestGetActualProjectNamesAdditional:
    def test_no_projects_dir(self, tmp_path):
        names = _get_actual_project_names(tmp_path)
        assert names == []

    def test_with_projects(self, tmp_path):
        for name in ("alpha", "beta"):
            root = tmp_path / "projects" / name
            root.mkdir(parents=True)
            (root / "src").mkdir()
            (root / "src" / "__init__.py").write_text("")
            (root / "tests").mkdir()
        names = _get_actual_project_names(tmp_path)
        assert "alpha" in names
        assert "beta" in names

    def test_pycache_excluded(self, tmp_path):
        (tmp_path / "projects").mkdir()
        (tmp_path / "projects" / "__pycache__").mkdir()
        real = tmp_path / "projects" / "real_project"
        real.mkdir()
        (real / "src").mkdir()
        (real / "src" / "__init__.py").write_text("")
        (real / "tests").mkdir()
        names = _get_actual_project_names(tmp_path)
        assert "__pycache__" not in names
        assert "real_project" in names

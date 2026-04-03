"""Tests for check_links validate_python_imports and validate_file_paths_in_code — coverage."""


from infrastructure.validation.integrity.check_links import (
    validate_python_imports,
    validate_file_paths_in_code,
    _validate_import_path,
    _get_actual_project_names,
)


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

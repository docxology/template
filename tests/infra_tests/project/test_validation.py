"""Tests for infrastructure/project/validation.py.

Tests project structure validation using real temp directories.
Follows No Mocks Policy — all tests use real files.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.validation import validate_project_structure


class TestValidateProjectStructure:
    """Test validate_project_structure() with real directory structures."""

    def test_returns_false_for_nonexistent_dir(self, tmp_path: Path) -> None:
        valid, msg = validate_project_structure(tmp_path / "nonexistent")
        assert valid is False
        assert "does not exist" in msg

    def test_returns_false_for_file_not_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "not_a_dir.txt"
        f.write_text("content")
        valid, msg = validate_project_structure(f)
        assert valid is False
        assert "Not a directory" in msg

    def test_returns_false_when_src_missing(self, tmp_path: Path) -> None:
        (tmp_path / "tests").mkdir()
        valid, msg = validate_project_structure(tmp_path)
        assert valid is False
        assert "src" in msg

    def test_returns_false_when_tests_missing(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("# code")
        valid, msg = validate_project_structure(tmp_path)
        assert valid is False
        assert "tests" in msg

    def test_returns_false_when_src_has_no_python(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "src" / "README.md").write_text("docs")
        valid, msg = validate_project_structure(tmp_path)
        assert valid is False
        assert "no Python files" in msg

    def test_returns_true_for_valid_structure(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (tmp_path / "tests").mkdir()
        valid, msg = validate_project_structure(tmp_path)
        assert valid is True
        assert "Valid" in msg

    def test_valid_with_optional_dirs(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "code.py").write_text("x = 1")
        (tmp_path / "tests").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "manuscript").mkdir()
        valid, msg = validate_project_structure(tmp_path)
        assert valid is True

    def test_nested_python_files_count(self, tmp_path: Path) -> None:
        src = tmp_path / "src" / "sub"
        src.mkdir(parents=True)
        (src / "deep.py").write_text("y = 2")
        (tmp_path / "tests").mkdir()
        valid, msg = validate_project_structure(tmp_path)
        assert valid is True

"""Tests for the roster-wide public exemplar structural contract."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_template_contract import validate_public_template_contract


def _scaffold(root: Path, project: str, *, with_tests: bool = True) -> None:
    project_root = root / "projects" / project
    (project_root / "src").mkdir(parents=True)
    (project_root / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    if with_tests:
        (project_root / "tests").mkdir()
        (project_root / "tests" / "test_contract.py").write_text(
            "def test_contract():\n    assert True\n", encoding="utf-8"
        )
    for marker in ("AGENTS.md", "README.md", "TODO.md", "pyproject.toml"):
        (project_root / marker).write_text("# marker\n", encoding="utf-8")


def test_public_contract_accepts_a_complete_scaffold(tmp_path: Path) -> None:
    _scaffold(tmp_path, "templates/example")

    report = validate_public_template_contract(tmp_path, public_names=("templates/example",))

    assert report.passed
    assert report.to_dict()["project_count"] == 1


def test_public_contract_rejects_empty_test_scope(tmp_path: Path) -> None:
    _scaffold(tmp_path, "templates/example", with_tests=False)
    (tmp_path / "projects" / "templates" / "example" / "tests").mkdir()

    report = validate_public_template_contract(tmp_path, public_names=("templates/example",))

    assert not report.passed
    assert any(item.code == "EMPTY-TEST-SCOPE" for item in report.findings)


def test_public_contract_rejects_symlinked_root(tmp_path: Path) -> None:
    _scaffold(tmp_path, "private/example")
    target = tmp_path / "projects" / "private" / "example"
    public_root = tmp_path / "projects" / "templates"
    public_root.mkdir(parents=True, exist_ok=True)
    (public_root / "example").symlink_to(target, target_is_directory=True)

    report = validate_public_template_contract(tmp_path, public_names=("templates/example",))

    assert any(item.code == "SYMLINK-ROOT" for item in report.findings)

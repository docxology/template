"""Tests for clean exemplar copy helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.copy_exemplar import _contained_destination, copy_exemplar, plan_copy

REPO_ROOT = Path(__file__).resolve().parents[3]


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _scaffold_git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    source = root / "projects" / "templates" / "template_code_project"
    source.mkdir(parents=True)
    (source / "README.md").write_text("template_code_project\n", encoding="utf-8")
    (source / "STANDALONE.md").write_text("# Standalone\n", encoding="utf-8")
    (source / "pyproject.toml").write_text("[project]\nname = 'template-code-project'\n", encoding="utf-8")
    (source / "docs").mkdir()
    (source / "docs" / "quickstart.md").write_text(
        "Run `uv run pytest projects/templates/template_code_project/tests/`.\n",
        encoding="utf-8",
    )
    (source / "docs" / "logo.bin").write_bytes(b"\xff\x00template_code_project")
    (source / ".venv").mkdir()
    (source / ".venv" / "ignored.py").write_text("ignored\n", encoding="utf-8")
    (source / "output").mkdir()
    (source / "output" / "artifact.txt").write_text("ignored\n", encoding="utf-8")
    (source / ".DS_Store").write_text("ignored\n", encoding="utf-8")
    _git("init", cwd=root)
    _git("add", "projects/templates/template_code_project/README.md", cwd=root)
    _git("add", "projects/templates/template_code_project/STANDALONE.md", cwd=root)
    _git("add", "projects/templates/template_code_project/pyproject.toml", cwd=root)
    _git("add", "projects/templates/template_code_project/docs/quickstart.md", cwd=root)
    _git("add", "projects/templates/template_code_project/docs/logo.bin", cwd=root)
    _git("commit", "-m", "fixture", cwd=root)
    return root


def test_dry_run_reports_copy_plan_without_writing_destination(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    result = plan_copy(repo_root, "templates/template_code_project", dest, new_name="my_project", dry_run=True)

    assert result.dry_run is True
    assert dest.exists() is False
    assert {path.as_posix() for path in result.relative_files} == {
        "README.md",
        "STANDALONE.md",
        "docs/quickstart.md",
        "docs/logo.bin",
        "pyproject.toml",
    }


def test_clean_copy_excludes_local_artifacts_and_preserves_binaries(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    result = copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    assert result.dry_run is False
    assert (dest / "README.md").read_text(encoding="utf-8") == "my_project\n"
    assert (dest / "STANDALONE.md").is_file()
    assert (dest / "docs" / "logo.bin").read_bytes() == b"\xff\x00template_code_project"
    assert not (dest / ".venv").exists()
    assert not (dest / "output").exists()
    assert not (dest / ".DS_Store").exists()


def test_new_name_rewrites_qualified_template_paths_to_destination(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = repo_root / "projects" / "working" / "my_project"

    copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    quickstart = (dest / "docs" / "quickstart.md").read_text(encoding="utf-8")
    assert "projects/working/my_project/tests/" in quickstart
    assert "projects/templates/my_project" not in quickstart
    assert "projects/templates/template_code_project" not in quickstart


def test_new_name_rewrites_python_and_package_slug_spellings(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert "my-project" in pyproject
    assert "template-code-project" not in pyproject
    assert "template_code_project" not in pyproject


def test_copy_rejects_symlinked_source_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    source = repo_root / "projects" / "templates" / "template_code_project"
    source.mkdir(parents=True)
    outside = tmp_path / "private.txt"
    outside.write_text("private\n", encoding="utf-8")
    (source / "README.md").symlink_to(outside)
    dest = tmp_path / "fork"

    with pytest.raises(ValueError, match="refusing to dereference symlink"):
        copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")


def test_fallback_walk_excludes_common_ignored_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    source = repo_root / "projects" / "templates" / "template_textbook"
    (source / "src").mkdir(parents=True)
    (source / "src" / "__init__.py").write_text('"""template_textbook."""\n', encoding="utf-8")
    (source / ".pytest_cache").mkdir()
    (source / ".pytest_cache" / "cache").write_text("ignored\n", encoding="utf-8")
    (source / ".lake").mkdir()
    (source / ".lake" / "build").write_text("ignored\n", encoding="utf-8")
    dest = tmp_path / "fork"

    result = copy_exemplar(repo_root, "templates/template_textbook", dest, new_name="my_textbook")

    assert {path.as_posix() for path in result.relative_files} == {"src/__init__.py"}
    assert (dest / "src" / "__init__.py").read_text(encoding="utf-8") == '"""my_textbook."""\n'
    assert not (dest / ".pytest_cache").exists()
    assert not (dest / ".lake").exists()


def test_live_exemplar_copy_keeps_required_forkability_files(tmp_path: Path) -> None:
    dest = tmp_path / "fork"

    result = copy_exemplar(REPO_ROOT, "templates/template_code_project", dest, new_name="copied_code_project")

    assert len(result.relative_files) > 10
    for rel in ("README.md", "AGENTS.md", "STANDALONE.md", "domain_profile.yaml", "experiment_plan.yaml"):
        assert (dest / rel).is_file(), rel
    for rel in ("pyproject.toml", "uv.lock"):
        path = dest / rel
        if path.is_file():
            source_text = (REPO_ROOT / "projects" / "templates" / "template_code_project" / rel).read_text(
                encoding="utf-8"
            )
            text = path.read_text(encoding="utf-8")
            if "template-code-project" in source_text:
                assert "copied-code-project" in text
            if "template_code_project" in source_text:
                assert "copied_code_project" in text
            assert "template-code-project" not in text
            assert "template_code_project" not in text


def test_documented_script_path_runs_from_repo_root(tmp_path: Path) -> None:
    dest = tmp_path / "fork"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/copy_exemplar.py",
            "--source",
            "templates/template_code_project",
            "--dest",
            str(dest),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Would copy" in proc.stdout
    assert not dest.exists()


def test_live_textbook_copy_excludes_rendered_outputs(tmp_path: Path) -> None:
    dest = tmp_path / "fork"

    result = plan_copy(REPO_ROOT, "templates/template_textbook", dest, new_name="copied_textbook", dry_run=True)

    copied = {path.as_posix() for path in result.relative_files}
    assert copied
    assert not any(path == "rendered" or path.startswith("rendered/") for path in copied)


def test_rejects_non_template_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source must be qualified as templates/"):
        plan_copy(REPO_ROOT, "working/private_project", tmp_path / "fork")


@pytest.mark.parametrize(
    "bad_name", ["../outside", "../../outside", "/tmp/outside", "Uppercase", "has/slash", ".hidden"]
)
def test_rejects_unsafe_new_name_values(tmp_path: Path, bad_name: str) -> None:
    with pytest.raises(ValueError, match="--new-name must be a lowercase project slug"):
        plan_copy(REPO_ROOT, "templates/template_template", tmp_path / "fork", new_name=bad_name, dry_run=True)


def test_containment_guard_rejects_escaping_target(tmp_path: Path) -> None:
    dest = (tmp_path / "fork").resolve()
    with pytest.raises(ValueError, match="copy target would escape destination"):
        _contained_destination(dest, Path("../outside"))

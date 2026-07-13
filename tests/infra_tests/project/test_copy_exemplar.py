"""Tests for clean exemplar copy helpers."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.copy_exemplar import _contained_destination, copy_exemplar, export_exemplar, plan_copy
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("project_name", PUBLIC_PROJECT_NAMES)
def test_every_public_exemplar_exports_as_a_standalone_tree(tmp_path: Path, project_name: str) -> None:
    """Every declared exemplar must survive the same clean export contract."""
    destination = tmp_path / project_name.split("/")[-1]

    export_exemplar(REPO_ROOT, project_name, destination)

    manifest = json.loads((destination / ".template-export.json").read_text(encoding="utf-8"))
    assert manifest["source_project"] == project_name
    assert (destination / "README.md").is_file()
    assert (destination / "pyproject.toml").is_file()
    assert not (destination / ".venv").exists()
    assert not (destination / "output").exists()


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
    # Set a repo-local identity so the fixture commit works on CI runners that
    # have no global git user configured (e.g. ubuntu-latest). macOS dev hosts
    # usually have a global identity, which is why this only bit in CI.
    _git("config", "user.email", "fixture@example.com", cwd=root)
    _git("config", "user.name", "Fixture", cwd=root)
    _git("add", "projects/templates/template_code_project/README.md", cwd=root)
    _git("add", "projects/templates/template_code_project/STANDALONE.md", cwd=root)
    _git("add", "projects/templates/template_code_project/pyproject.toml", cwd=root)
    _git("add", "projects/templates/template_code_project/docs/quickstart.md", cwd=root)
    _git("add", "projects/templates/template_code_project/docs/logo.bin", cwd=root)
    _git("commit", "-m", "fixture", cwd=root)
    return root


def test_rename_text_preserves_unrelated_tokens() -> None:
    from infrastructure.project.copy_exemplar import _rename_text

    source = (
        "doi:10.5281/zenodo.12345678\n"
        "Discuss template_code_project_extra without renaming the suffix token.\n"
        "Run projects/templates/template_code_project/tests/\n"
        "name = 'template-code-project'\n"
    )
    renamed = _rename_text(
        source,
        "template_code_project",
        "my_project",
        old_project_path="projects/templates/template_code_project",
        new_project_path="projects/working/my_project",
    )
    assert "10.5281/zenodo.12345678" in renamed
    assert "template_code_project_extra" in renamed
    assert "name = 'my-project'" in renamed
    assert "projects/working/my_project" in renamed


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


def test_export_writes_content_addressed_provenance_manifest(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    export_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    payload = json.loads((dest / ".template-export.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["source_project"] == "templates/template_code_project"
    assert payload["exported_project"] == "my_project"
    assert payload["source_commit"] != "unknown"
    assert payload["infrastructure_version"] == "unknown"
    assert payload["resource_dependencies"] == []
    readme = dest / "README.md"
    assert payload["files"]["README.md"] == hashlib.sha256(readme.read_bytes()).hexdigest()
    assert ".template-export.json" not in payload["files"]


def test_export_bundles_declared_cross_root_resources(tmp_path: Path) -> None:
    """Declared public pools are copied and included in the manifest hashes."""
    repo_root = _scaffold_git_repo(tmp_path)
    project = repo_root / "projects/templates/template_code_project"
    (project / "export.toml").write_text(
        '[template_export]\ncross_root_dependencies = ["fonds/templates"]\n',
        encoding="utf-8",
    )
    fond = repo_root / "fonds/templates/template_bibliography"
    fond.mkdir(parents=True)
    (fond / "fonds.yaml").write_text("name: bibliography\n", encoding="utf-8")
    dest = tmp_path / "fork"

    export_exemplar(repo_root, "templates/template_code_project", dest)

    resource = dest / "_template_resources/fonds/templates/template_bibliography/fonds.yaml"
    assert resource.read_text(encoding="utf-8") == "name: bibliography\n"
    payload = json.loads((dest / ".template-export.json").read_text(encoding="utf-8"))
    rel = resource.relative_to(dest).as_posix()
    assert payload["resource_dependencies"] == ["fonds/templates"]
    assert payload["files"][rel] == hashlib.sha256(resource.read_bytes()).hexdigest()


def test_project_only_export_omits_declared_resources(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    project = repo_root / "projects/templates/template_code_project"
    (project / "export.toml").write_text(
        '[template_export]\ncross_root_dependencies = ["fonds/templates"]\n',
        encoding="utf-8",
    )
    dest = tmp_path / "fork"

    export_exemplar(repo_root, "templates/template_code_project", dest, project_only=True)

    assert not (dest / "_template_resources").exists()
    payload = json.loads((dest / ".template-export.json").read_text(encoding="utf-8"))
    assert payload["resource_dependencies"] == []


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
            "scripts/audit/copy_exemplar.py",
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

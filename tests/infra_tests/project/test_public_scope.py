"""Tests for public template project scoping."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.discovery import discover_projects
from infrastructure.project.public_scope import (
    LOCAL_ONLY_TEMPLATE_NAMES,
    PUBLIC_PROJECT_NAMES,
    main,
    public_ci_lint_paths,
    public_ci_source_paths,
    public_project_names,
    public_project_source_roots,
)


def _scaffold_project(root: Path, qualified: str) -> Path:
    project = root / "projects" / qualified
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "src" / "__init__.py").write_text("", encoding="utf-8")
    return project


def _scaffold_exemplars(root: Path) -> None:
    for name in PUBLIC_PROJECT_NAMES:
        _scaffold_project(root, name)


def test_public_scope_filters_to_template_projects(tmp_path: Path) -> None:
    """Public CI scope excludes non-template projects that discovery can see."""
    _scaffold_exemplars(tmp_path)
    _scaffold_project(tmp_path, "active/private_research_project")

    discovered = {project.qualified_name for project in discover_projects(tmp_path)}

    assert discovered == {
        "active/private_research_project",
        *PUBLIC_PROJECT_NAMES,
    }
    assert public_project_names(tmp_path) == sorted(PUBLIC_PROJECT_NAMES)
    assert public_ci_source_paths(tmp_path) == [
        Path("infrastructure"),
        Path("scripts"),
        *[Path("projects") / name / "src" for name in PUBLIC_PROJECT_NAMES],
    ]
    assert public_ci_lint_paths(tmp_path) == [
        Path("conftest.py"),
        Path("docs"),
        Path("infrastructure"),
        Path("scripts"),
        Path("tests"),
        *[
            path
            for name in PUBLIC_PROJECT_NAMES
            for path in (
                Path("projects") / name / "src",
                Path("projects") / name / "tests",
            )
        ],
    ]


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_public_scope_excludes_local_private_symlink(tmp_path: Path) -> None:
    """Local symlinked projects remain discoverable but absent from public scope."""
    _scaffold_exemplars(tmp_path)

    external = tmp_path / "private" / "active" / "example_private_project"
    (external / "src").mkdir(parents=True)
    (external / "tests").mkdir()
    (external / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "projects" / "active").mkdir(parents=True, exist_ok=True)
    (tmp_path / "projects" / "active" / "example_private_project").symlink_to(external, target_is_directory=True)

    discovered = {project.qualified_name for project in discover_projects(tmp_path)}

    assert "active/example_private_project" in discovered
    assert public_project_names(tmp_path) == sorted(PUBLIC_PROJECT_NAMES)


def test_project_names_json_cli_emits_matrix_array(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``project-names-json`` prints a one-line JSON array for the CI matrix.

    This is the exact value consumed by ``fromJSON(...)`` in the
    ``test-project`` strategy matrix, so it must be valid JSON listing the
    public exemplars present in the checkout.
    """
    _scaffold_exemplars(tmp_path)
    _scaffold_project(tmp_path, "active/private_research_project")

    exit_code = main(["project-names-json", "--repo-root", str(tmp_path)])

    assert exit_code == 0
    out = capsys.readouterr().out
    # Single line (no embedded newlines) so it slots into $GITHUB_OUTPUT.
    assert out.count("\n") == 1
    parsed = json.loads(out)
    assert parsed == sorted(PUBLIC_PROJECT_NAMES)
    # Private symlinked/active projects never leak into the public matrix.
    assert "active/private_research_project" not in parsed


def test_public_template_roster_has_explicit_local_only_escape_hatch() -> None:
    repo = Path(__file__).resolve().parents[3]
    template_root = repo / "projects" / "templates"
    on_disk = {f"templates/{path.name}" for path in template_root.glob("template_*") if path.is_dir()}
    declared = set(PUBLIC_PROJECT_NAMES)
    local_only = {f"templates/{name}" for name in LOCAL_ONLY_TEMPLATE_NAMES}

    assert declared <= on_disk
    assert on_disk <= declared | local_only


def test_codeowners_explicitly_covers_every_public_template() -> None:
    """The public roster must stay under an explicit template owner rule."""
    repo = Path(__file__).resolve().parents[3]
    codeowners = (repo / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    owner_rules = {
        fields[0]
        for raw_line in codeowners.splitlines()
        if (fields := raw_line.split()) and not fields[0].startswith("#") and "@docxology" in fields[1:]
    }

    template_prefix = "/projects/templates/"
    assert template_prefix in owner_rules
    for project_name in PUBLIC_PROJECT_NAMES:
        assert f"/projects/{project_name}/".startswith(template_prefix)


def test_public_scope_cli_is_quiet_on_stderr() -> None:
    repo = Path(__file__).resolve().parents[3]

    completed = subprocess.run(
        [sys.executable, "-m", "infrastructure.project.public_scope", "source-paths"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stderr == ""
    assert completed.stdout.startswith("infrastructure ")


def test_public_source_roots_are_complete_stable_and_ignore_other_layouts(tmp_path: Path) -> None:
    _scaffold_exemplars(tmp_path)
    expected = tuple(tmp_path / "projects" / name / "src" for name in PUBLIC_PROJECT_NAMES)
    assert public_project_source_roots(tmp_path) == expected
    # A real cyclic link would fail any attempt to resolve this unrelated tree.
    unrelated = tmp_path / "projects" / "working"
    unrelated.symlink_to(unrelated, target_is_directory=True)
    _scaffold_project(tmp_path, "active/owned_private_fixture")
    _scaffold_project(tmp_path, "flat_unlisted_fixture")
    assert public_project_source_roots(tmp_path) == expected


@pytest.mark.parametrize("target", ["missing", "source-file", "source-link", "project-link", "templates-link"])
def test_public_source_roots_refuse_wrong_canonical_origins(tmp_path: Path, target: str) -> None:
    _scaffold_exemplars(tmp_path)
    project = tmp_path / "projects" / PUBLIC_PROJECT_NAMES[0]
    source = project / "src"
    if target == "missing":
        (source / "__init__.py").unlink()
        source.rmdir()
    elif target == "source-file":
        (source / "__init__.py").unlink()
        source.rmdir()
        source.write_text("not a directory")
    else:
        location = {"source-link": source, "project-link": project, "templates-link": project.parent}[target]
        outside = tmp_path / "external-owned-fixture"
        location.rename(outside)
        location.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="canonical public source root"):
        public_project_source_roots(tmp_path)


def test_ci_paths_cli_matches_each_individual_scope(tmp_path: Path) -> None:
    """The combined CLI matches each current single-value scope and its output order."""
    repo = Path(__file__).resolve().parents[3]
    _scaffold_exemplars(tmp_path)
    _scaffold_project(tmp_path, "active/private_research_project")
    individual_scopes = {}
    for command in ("lint-paths", "source-paths"):
        observed = subprocess.run(
            [sys.executable, "-m", "infrastructure.project.public_scope", command, "--repo-root", str(tmp_path)],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        assert observed.stderr == ""
        assert "active/private_research_project" not in observed.stdout
        individual_scopes[command] = observed.stdout.rstrip("\n")
    combined = subprocess.run(
        [sys.executable, "-m", "infrastructure.project.public_scope", "ci-paths", "--repo-root", str(tmp_path)],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert combined.stderr == ""
    assert (
        combined.stdout
        == f"lint_paths={individual_scopes['lint-paths']}\nsource_paths={individual_scopes['source-paths']}\n"
    )


def test_ci_paths_cli_rejects_invalid_arguments_without_outputs() -> None:
    """A real CLI failure remains nonzero and emits no workflow scope outputs."""
    repo = Path(__file__).resolve().parents[3]
    observed = subprocess.run(
        [sys.executable, "-m", "infrastructure.project.public_scope", "ci-paths", "--unexpected-option"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert observed.returncode == 2
    assert observed.stdout == ""
    assert "unrecognized arguments: --unexpected-option" in observed.stderr

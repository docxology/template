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
    public_ci_source_paths,
    public_project_names,
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

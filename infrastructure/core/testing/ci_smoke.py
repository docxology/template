"""Small public-project functional selections; exhaustive acceptance is opt-in."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import shutil
from tempfile import TemporaryDirectory

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

# These selections exercise genuine monorepo DATA/source contracts. Their
# fixtures already create disposable projects; flattening the provider checkout
# would change the behavior under test. Other selections can use a plain copy.
_SOURCE_INTEGRATION_PROJECTS = frozenset(
    {
        "templates/template_autoresearch_project",
        "templates/template_pitch_deck",
        "templates/template_pools_rules_tools",
        "templates/template_template",
    }
)


def _project_smoke_selection(repo_root: Path) -> dict[str, list[str]]:
    """Require a nonempty, confined behavioral selection for every public template."""
    root = repo_root.resolve(strict=True)
    selection: dict[str, list[str]] = json.loads((root / ".github/project-smoke.json").read_text())
    expected = set(PUBLIC_PROJECT_NAMES)
    if not isinstance(selection, dict) or set(selection) != expected:
        raise ValueError("functional smoke roster differs from the public template roster")
    for project, paths in selection.items():
        if (
            not isinstance(paths, list)
            or not paths
            or any(not isinstance(path, str) for path in paths)
            or len(set(paths)) != len(paths)
        ):
            raise ValueError(f"functional smoke selection is empty or duplicated: {project}")
        project_root = root / "projects" / project
        if project_root.resolve() != project_root or not project_root.is_dir():
            raise ValueError(f"functional smoke project root is missing or noncanonical: {project}")
        for relative in paths:
            if not isinstance(relative, str) or not relative.startswith("tests/") or ".." in Path(relative).parts:
                raise ValueError(f"functional smoke test path escapes its project: {project}")
            path = project_root / relative
            if not path.is_file() or not path.resolve().is_relative_to(project_root.resolve()):
                raise ValueError(f"functional smoke test path is missing or escapes its project: {path}")
    return selection


def project_smoke_matrix(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    """Emit the validated complete public functional selection."""
    return {"include": [{"project": project} for project in sorted(_project_smoke_selection(repo_root))]}


def run_project_smoke(repo_root: Path, project: str) -> int:
    """Run real tests in one isolated pytest process without a coverage claim."""
    root = repo_root.resolve(strict=True)
    selection = _project_smoke_selection(root)
    if project not in selection:
        raise ValueError("functional smoke project is not public")
    # Some real project tests regenerate outputs. Keep those writes disposable,
    # including on a developer's checkout, without altering their test behavior.
    with TemporaryDirectory(prefix="template-functional-") as scratch:
        work = Path(scratch) / Path(project).name
        if project in _SOURCE_INTEGRATION_PROJECTS:
            work = root / "projects" / project
        else:
            shutil.copytree(
                root / "projects" / project,
                work,
                ignore=shutil.ignore_patterns(
                    ".venv", ".git", "__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache", "build", "dist"
                ),
            )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *selection[project],
                "--no-cov",
                "-q",
                "--timeout=60",
                "--benchmark-disable",
            ],
            cwd=work,
            timeout=180,
            check=False,
        )
    return result.returncode


__all__ = ["project_smoke_matrix", "run_project_smoke"]

"""Tests for ghost-project path consistency checks."""

from __future__ import annotations

import shutil
from pathlib import Path

from infrastructure.validation.docs.consistency_lint import check_no_ghost_projects

from .conftest import scaffold_repo, write_doc


def test_ghost_project_unconditional_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        "Run `projects/ghost_project/manuscript/build.sh` to start.\n",
    )
    issues = check_no_ghost_projects(repo)
    assert len(issues) == 1
    assert issues[0].category == "ghost-project"
    assert "ghost_project" in issues[0].detail


def test_ghost_project_with_conditional_phrase_is_skipped(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        "When `projects/ghost_project/` is present, see its README. <!-- rotating -->\n",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_canonical_exemplars_are_allowed(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        """See `projects/templates/template_code_project/`.
See `projects/templates/template_prose_project/`.
""",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_active_project_is_allowed(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "guide.md", "See `projects/templates/template_code_project/AGENTS.md`.\n")
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_ongoing_subfolder_names_are_allowed(tmp_path: Path) -> None:
    """`ongoing` is a non-rendered typed subfolder: any name beneath it is allowed."""
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        """See `projects/ongoing/someprivate/file.md` for the private thread.
Bare structural refs like `projects/ongoing/` are fine too.
""",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_unqualified_public_template_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    shutil.rmtree(repo / "projects" / "template_code_project")
    write_doc(repo / "docs" / "guide.md", "See `projects/template_code_project/AGENTS.md`.\n")

    issues = check_no_ghost_projects(repo)

    assert len(issues) == 1
    assert "projects/template_code_project/" in issues[0].detail


def test_ghost_project_placeholders_are_skipped(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        """## Scaffolding

- `projects/<name>/manuscript/`
- `projects/{project}/src/`
- `projects/my_project/tests/`
- `projects/PROJECT_SLUG/scripts/`
""",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_inside_fenced_code_is_ignored(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        """Real reference: see active projects.

```bash
# Example only:
uv run pytest projects/some_archived/tests/
```
""",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_noqa_suppresses_warning(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        "See `projects/some_ghost/AGENTS.md`. <!-- noqa: docs-lint -->\n",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_does_not_match_custom_projects_prefix(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        """See `custom_projects/machine_learning/`.
See `my_projects/foo/`.
""",
    )
    assert check_no_ghost_projects(repo) == []

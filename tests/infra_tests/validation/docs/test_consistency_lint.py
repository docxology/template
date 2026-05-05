"""Tests for infrastructure.validation.docs.consistency_lint.

Zero-mocks: tests build a real on-disk synthetic infra/docs tree.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.consistency_lint import (
    Inconsistency,
    check_module_count_claims,
    check_no_ghost_projects,
)


def _write(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def _scaffold_repo(tmp_path: Path, *, n_packages: int) -> Path:
    """Build a minimal repo: infrastructure/<pkgN>/__init__.py and an active project."""
    for i in range(n_packages):
        _write(tmp_path / "infrastructure" / f"pkg{i}" / "__init__.py", "")
    _write(tmp_path / "infrastructure" / "__init__.py", "")
    # active project so discover_projects() returns at least one
    _write(tmp_path / "projects" / "template_code_project" / "src" / "__init__.py", "")
    _write(tmp_path / "projects" / "template_code_project" / "tests" / "__init__.py", "")
    _write(tmp_path / "docs" / "_generated" / "active_projects.md", "- template_code_project\n")
    return tmp_path


def test_module_count_claim_matches_reality(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "guide.md", "Layer 1 has 15 Python packages.\n")
    issues = check_module_count_claims(repo)
    assert issues == []


def test_module_count_claim_mismatch_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "guide.md", "There are 17 Python subpackages here.\n")
    issues = check_module_count_claims(repo)
    assert len(issues) == 1
    assert isinstance(issues[0], Inconsistency)
    assert issues[0].category == "module-count"
    assert "17" in issues[0].detail
    assert "15" in issues[0].detail


def test_module_count_singular_is_not_flagged(tmp_path: Path) -> None:
    """Phrases like 'each Python package' (singular, no count) must not trigger."""
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "guide.md", "Each Layer-1 Python package ships AGENTS.md.\n")
    assert check_module_count_claims(repo) == []


def test_module_count_inside_fenced_code_is_ignored(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        """Real claim: 15 Python packages.

```text
Old claim: 99 Python packages
```
""",
    )
    issues = check_module_count_claims(repo)
    assert issues == []


def test_ghost_project_unconditional_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        "Run `projects/ghost_project/manuscript/build.sh` to start.\n",
    )
    issues = check_no_ghost_projects(repo)
    assert len(issues) == 1
    assert issues[0].category == "ghost-project"
    assert "ghost_project" in issues[0].detail


def test_ghost_project_with_conditional_phrase_is_skipped(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        "When `projects/ghost_project/` is present, see its README. <!-- rotating -->\n",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_canonical_exemplars_are_allowed(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        """See `projects/template_code_project/`.
See `projects/template_prose_project/`.
See `projects/template_search_project/`.
""",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_active_project_is_allowed(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "guide.md", "See `projects/template_code_project/AGENTS.md`.\n")
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_placeholders_are_skipped(tmp_path: Path) -> None:
    """`projects/<name>/`, `projects/{project}/`, `projects/my_project/` etc. are template scaffolding."""
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
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
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
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
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        "See `projects/some_ghost/AGENTS.md`. <!-- noqa: docs-lint -->\n",
    )
    assert check_no_ghost_projects(repo) == []


def test_ghost_project_does_not_match_custom_projects_prefix(tmp_path: Path) -> None:
    """`custom_projects/foo/` and `my_projects/bar/` must not trigger ghost detection."""
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        """See `custom_projects/machine_learning/`.
See `my_projects/foo/`.
""",
    )
    assert check_no_ghost_projects(repo) == []


def test_module_count_noqa_suppresses_warning(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        "Historical: 99 Python packages. <!-- noqa: docs-lint -->\n",
    )
    assert check_module_count_claims(repo) == []


def test_inconsistency_format_contains_file_and_line(tmp_path: Path) -> None:
    inc = Inconsistency(file=Path("/a/b.md"), line=7, category="module-count", detail="x")
    s = inc.format()
    assert "/a/b.md:7" in s
    assert "[module-count]" in s
    assert "x" in s

"""Tests for infrastructure.validation.docs.consistency_lint.

Zero-mocks: tests build a real on-disk synthetic infra/docs tree.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.consistency_lint import (
    Inconsistency,
    check_canonical_count_singularity,
    check_command_conventions,
    check_doc_imports_resolve,
    check_module_count_claims,
    check_no_ghost_projects,
    check_readme_files_list,
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


def test_command_convention_bare_pytest_in_bash_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "guide.md",
        "Run tests:\n\n```bash\npytest tests/ --cov=infrastructure\n```\n",
    )
    issues = check_command_conventions(repo)
    assert len(issues) == 1
    assert issues[0].category == "command-convention"
    assert "pytest" in issues[0].detail
    assert issues[0].line == 4


def test_command_convention_bare_python3_in_sh_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "g.md", "```sh\npython3 scripts/01_run_tests.py\n```\n")
    issues = check_command_conventions(repo)
    assert len(issues) == 1
    assert "python3" in issues[0].detail


def test_command_convention_uv_run_is_not_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "```bash\nuv run pytest tests/\nuv run python3 scripts/x.py\n```\n",
    )
    assert check_command_conventions(repo) == []


def test_command_convention_python_block_is_ignored(tmp_path: Path) -> None:
    """A ```python fence is code, not a shell command — never flagged."""
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "g.md", "```python\npytest_plugins = []\npython3 = 1\n```\n")
    assert check_command_conventions(repo) == []


def test_command_convention_prose_and_nouns_not_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "We use pytest-httpserver. See pytest.ini.\n\n"
        "```bash\n# pytest is invoked via uv\npytest-httpserver --help\n```\n",
    )
    assert check_command_conventions(repo) == []


def test_command_convention_noqa_suppresses(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "Counter-example:\n\n```bash\npytest tests/  # noqa: docs-lint (deliberate)\n```\n",
    )
    assert check_command_conventions(repo) == []


def test_command_convention_prompt_prefix_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "g.md", "```console\n$ pytest -m security\n```\n")
    issues = check_command_conventions(repo)
    assert len(issues) == 1
    assert issues[0].category == "command-convention"


def test_doc_import_real_symbol_resolves(tmp_path: Path) -> None:
    """A real `infrastructure...` import in a doc fence must NOT be flagged."""
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.core.logging.utils import get_logger\n```\n",
    )
    assert check_doc_imports_resolve(repo) == []


def test_doc_import_bad_symbol_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.core import NoSuchSymbolXYZ\n```\n",
    )
    issues = check_doc_imports_resolve(repo)
    assert len(issues) == 1
    assert issues[0].category == "doc-import"
    assert "NoSuchSymbolXYZ" in issues[0].detail


def test_doc_import_noqa_suppresses(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.new_feature import thing  # noqa: docs-lint\n```\n",
    )
    assert check_doc_imports_resolve(repo) == []


def test_doc_import_dash_m_nonexistent_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "g.md", "```bash\nuv run python -m infrastructure.totally.fake\n```\n")
    issues = check_doc_imports_resolve(repo)
    assert len(issues) == 1
    assert "infrastructure.totally.fake" in issues[0].detail


def test_doc_import_non_code_fence_ignored(tmp_path: Path) -> None:
    """A fence whose language isn't code (e.g. ```yaml) is not scanned."""
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "g.md", "```yaml\nfrom infrastructure.core import Bogus\n```\n")
    assert check_doc_imports_resolve(repo) == []


def test_doc_import_multiline_parenthesised(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.core import (\n    NopeOne,\n    NopeTwo,\n)\n```\n",
    )
    issues = check_doc_imports_resolve(repo)
    assert len(issues) == 1 and issues[0].category == "doc-import"


def test_readme_files_list_missing_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=1)
    pkg = repo / "infrastructure" / "pkg0"
    _write(pkg / "real_mod.py", "x = 1\n")
    _write(pkg / "README.md", "## Files\n\n- `real_mod.py` — present\n- `ghost_mod.py` — vanished\n")
    issues = check_readme_files_list(repo)
    assert len(issues) == 1
    assert issues[0].category == "doc-files-list"
    assert "ghost_mod.py" in issues[0].detail


def test_readme_files_list_all_present_ok(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=1)
    pkg = repo / "infrastructure" / "pkg0"
    _write(pkg / "a.py", "")
    _write(pkg / "README.md", "## Files\n\n- `a.py`\n")
    assert check_readme_files_list(repo) == []


def test_count_singularity_outside_canonical_is_flagged(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "g.md", "The repo has 345 .py files in infrastructure.\n")
    issues = check_canonical_count_singularity(repo)
    assert len(issues) == 1
    assert issues[0].category == "count-singularity"


def test_count_singularity_canonical_facts_is_exempt(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(repo / "docs" / "_generated" / "canonical_facts.md", "Measured: 345 .py files.\n")
    assert check_canonical_count_singularity(repo) == []


def test_count_singularity_noqa_suppresses(tmp_path: Path) -> None:
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "docs" / "g.md",
        "Historical note: 345 Python files (2026-05-15). <!-- noqa: docs-lint -->\n",
    )
    assert check_canonical_count_singularity(repo) == []


def test_tests_dir_is_in_scope_blind_spot_closed(tmp_path: Path) -> None:
    """Regression guard: a bad infra import under tests/**/AGENTS.md MUST be
    caught (the 2026-05-15 triple-check found tests/ was a scope blind spot)."""
    repo = _scaffold_repo(tmp_path, n_packages=15)
    _write(
        repo / "tests" / "infra_tests" / "x" / "AGENTS.md",
        "```python\nfrom infrastructure.core import NoSuchSymbolABC\n```\n",
    )
    issues = check_doc_imports_resolve(repo)
    assert any(
        "tests/infra_tests/x/AGENTS.md" in str(i.file) and i.category == "doc-import"
        for i in issues
    ), "tests/ docs must be in consistency-lint scope"


def test_canonical_exemplar_markdown_is_in_scope(tmp_path: Path) -> None:
    """Regression guard: stale package-count claims in exemplar manuscripts are source docs."""
    repo = _scaffold_repo(tmp_path, n_packages=17)
    _write(
        repo / "projects" / "template_code_project" / "manuscript" / "01_intro.md",
        "The infrastructure layer has 15 Python subpackages.\n",
    )
    issues = check_module_count_claims(repo)
    assert any(
        "projects/template_code_project/manuscript/01_intro.md" in str(i.file)
        and i.category == "module-count"
        for i in issues
    ), "tracked exemplar manuscript markdown must be in consistency-lint scope"


def test_inconsistency_format_contains_file_and_line(tmp_path: Path) -> None:
    inc = Inconsistency(file=Path("/a/b.md"), line=7, category="module-count", detail="x")
    s = inc.format()
    assert "/a/b.md:7" in s
    assert "[module-count]" in s
    assert "x" in s

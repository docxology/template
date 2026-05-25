"""Tests for shell command conventions and stale shell contract checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.consistency_lint import (
    check_command_conventions,
    check_stale_shell_contracts,
)

from .conftest import scaffold_repo, write_doc


def test_command_convention_bare_pytest_in_bash_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        "Run tests:\n\n```bash\npytest tests/ --cov=infrastructure\n```\n",
    )
    issues = check_command_conventions(repo)
    assert len(issues) == 1
    assert issues[0].category == "command-convention"
    assert "pytest" in issues[0].detail
    assert issues[0].line == 4


def test_command_convention_bare_python3_in_sh_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "```sh\npython3 scripts/01_run_tests.py\n```\n")
    issues = check_command_conventions(repo)
    assert len(issues) == 1
    assert "python3" in issues[0].detail


def test_command_convention_uv_run_is_not_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "```bash\nuv run pytest tests/\nuv run python scripts/x.py\n```\n",
    )
    assert check_command_conventions(repo) == []


def test_command_convention_uv_run_python3_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "```bash\nuv run python3 scripts/x.py\n```\n")
    issues = check_command_conventions(repo)
    assert len(issues) == 1
    assert "uv run python3" in issues[0].detail


def test_command_convention_python_block_is_ignored(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "```python\npytest_plugins = []\npython3 = 1\n```\n")
    assert check_command_conventions(repo) == []


def test_command_convention_prose_and_nouns_not_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "We use pytest-httpserver. See pytest.ini.\n\n"
        "```bash\n# pytest is invoked via uv\npytest-httpserver --help\n```\n",
    )
    assert check_command_conventions(repo) == []


def test_command_convention_noqa_suppresses(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "Counter-example:\n\n```bash\npytest tests/  # noqa: docs-lint (deliberate)\n```\n",
    )
    assert check_command_conventions(repo) == []


def test_command_convention_prompt_prefix_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "```console\n$ pytest -m security\n```\n")
    issues = check_command_conventions(repo)
    assert len(issues) == 1
    assert issues[0].category == "command-convention"


def test_stale_shell_export_pipeline_mode_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "Run `export PIPELINE_MODE=1` before ./run.sh\n")
    issues = check_stale_shell_contracts(repo)
    assert len(issues) == 1
    assert issues[0].category == "shell-contract"


def test_stale_shell_pipeline_mode_not_exported_ok(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "Internal PIPELINE_MODE (bash-local, not exported) in run.sh.\n")
    assert check_stale_shell_contracts(repo) == []


def test_stale_shell_deterministic_strip_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "`secure_run.sh` strips `--deterministic` before forwarding to Python.\n",
    )
    issues = check_stale_shell_contracts(repo)
    assert len(issues) == 1
    assert "deterministic" in issues[0].detail.lower()


def test_stale_shell_template_search_unqualified_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "See `projects/template_search_project/manuscript/config.yaml`.\n")
    issues = check_stale_shell_contracts(repo)
    assert len(issues) == 1
    assert "template_search_project" in issues[0].detail


def test_stale_shell_template_search_archive_path_ok(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "Canonical home: `projects_archive/template_search_project/`; copy locally under `projects/` only.\n",
    )
    assert check_stale_shell_contracts(repo) == []

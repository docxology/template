"""Tests for documentation import resolution checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.consistency_lint import check_doc_imports_resolve

from .conftest import scaffold_repo, write_doc


def test_doc_import_real_symbol_resolves(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.core.logging.utils import get_logger\n```\n",
    )
    assert check_doc_imports_resolve(repo) == []


def test_doc_import_bad_symbol_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.core import NoSuchSymbolXYZ\n```\n",
    )
    issues = check_doc_imports_resolve(repo)
    assert len(issues) == 1
    assert issues[0].category == "doc-import"
    assert "NoSuchSymbolXYZ" in issues[0].detail


def test_doc_import_noqa_suppresses(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.new_feature import thing  # noqa: docs-lint\n```\n",
    )
    assert check_doc_imports_resolve(repo) == []


def test_doc_import_dash_m_nonexistent_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "```bash\nuv run python -m infrastructure.totally.fake\n```\n")
    issues = check_doc_imports_resolve(repo)
    assert len(issues) == 1
    assert "infrastructure.totally.fake" in issues[0].detail


def test_doc_import_non_code_fence_ignored(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "```yaml\nfrom infrastructure.core import Bogus\n```\n")
    assert check_doc_imports_resolve(repo) == []


def test_doc_import_multiline_parenthesised(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "```python\nfrom infrastructure.core import (\n    NopeOne,\n    NopeTwo,\n)\n```\n",
    )
    issues = check_doc_imports_resolve(repo)
    assert len(issues) == 1 and issues[0].category == "doc-import"


def test_tests_dir_is_in_scope_blind_spot_closed(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "tests" / "infra_tests" / "x" / "AGENTS.md",
        "```python\nfrom infrastructure.core import NoSuchSymbolABC\n```\n",
    )
    issues = check_doc_imports_resolve(repo)
    assert any("tests/infra_tests/x/AGENTS.md" in str(i.file) and i.category == "doc-import" for i in issues)

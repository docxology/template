"""No-mocks tests for src/infra_facts.py — real repo introspection."""

from __future__ import annotations

import pytest

from infra_facts import InfraIntrospectionError, build_infra_tokens, infra_subpackage_python_counts
from paths import locate_repo_root, project_root


@pytest.fixture(scope="module")
def repo_root():
    return locate_repo_root(project_root())


def test_infra_subpackage_python_counts_returns_real_rows(repo_root):
    rows = infra_subpackage_python_counts(repo_root)
    assert len(rows) > 5
    names = {name for name, _ in rows}
    assert "core" in names
    assert "rendering" in names


def test_infra_subpackage_python_counts_all_positive_and_sorted(repo_root):
    rows = infra_subpackage_python_counts(repo_root)
    counts = [count for _, count in rows]
    assert all(count > 0 for count in counts)
    assert counts == sorted(counts, reverse=True)


def test_infra_subpackage_python_counts_sum_is_plausible_vs_total(repo_root):
    from infrastructure.documentation.counts_doc import tracked_infra_python_count

    rows = infra_subpackage_python_counts(repo_root)
    total = tracked_infra_python_count(repo_root)
    # Per-subpackage sum can be <= the repo-wide total (top-level infra/*.py
    # files outside any subpackage aren't attributed to a subpackage here),
    # but must never exceed it.
    assert sum(count for _, count in rows) <= total


def test_build_infra_tokens_returns_real_values(repo_root):
    tokens = build_infra_tokens(repo_root)
    assert int(tokens["INFRA_SUBPACKAGE_COUNT"]) > 5
    assert int(tokens["INFRA_PYTHON_FILE_COUNT"]) > 100
    assert tokens["INFRA_LARGEST_SUBPACKAGE"]
    assert int(tokens["INFRA_LARGEST_SUBPACKAGE_COUNT"]) > 0


def test_build_infra_tokens_unattributed_count_reconciles_the_two_totals(repo_root):
    """Proof that the deck's own explanation of "668 vs 666" is arithmetically
    exact, not an approximation — the visual-QA red-team pass flagged this
    exact discrepancy as confusing without an explanation (2026-07-09)."""
    tokens = build_infra_tokens(repo_root)
    rows = infra_subpackage_python_counts(repo_root)
    subpackage_sum = sum(count for _, count in rows)
    unattributed = int(tokens["INFRA_UNATTRIBUTED_FILE_COUNT"])
    assert unattributed >= 0
    assert subpackage_sum + unattributed == int(tokens["INFRA_PYTHON_FILE_COUNT"])


def test_build_infra_tokens_largest_subpackage_matches_top_row(repo_root):
    tokens = build_infra_tokens(repo_root)
    rows = infra_subpackage_python_counts(repo_root)
    assert tokens["INFRA_LARGEST_SUBPACKAGE"] == rows[0][0]
    assert int(tokens["INFRA_LARGEST_SUBPACKAGE_COUNT"]) == rows[0][1]


def test_infra_subpackage_python_counts_raises_domain_error_when_not_a_git_repo(tmp_path):
    """Real reproduction of the red-team-flagged bare-crash bug: pointing at
    a real directory tree that is NOT a git repository must raise the
    domain-specific `InfraIntrospectionError`, not a raw
    `subprocess.CalledProcessError`."""
    package_dir = tmp_path / "infrastructure" / "somepkg"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "module.py").write_text("", encoding="utf-8")

    with pytest.raises(InfraIntrospectionError):
        infra_subpackage_python_counts(tmp_path)

"""Tests for project-discovery documentation contract checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.consistency_lint import check_project_discovery_claims

from .conftest import scaffold_repo, write_doc


def test_config_only_discovery_claim_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=3)
    write_doc(
        repo / "docs" / "guide.md",
        "A project is auto-discovered if `projects/<name>/manuscript/config.yaml` exists.\n",
    )

    issues = check_project_discovery_claims(repo)

    assert len(issues) == 1
    assert issues[0].category == "project-discovery"
    assert "src/" in issues[0].detail
    assert "tests/" in issues[0].detail


def test_discovery_claim_with_src_and_tests_context_is_allowed(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=3)
    write_doc(
        repo / "docs" / "guide.md",
        (
            "A project is auto-discovered when it has `src/` and `tests/`.\n"
            "`manuscript/config.yaml` supplies metadata for rendering.\n"
        ),
    )

    assert check_project_discovery_claims(repo) == []

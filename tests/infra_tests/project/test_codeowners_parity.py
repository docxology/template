"""CODEOWNERS generator parity tests."""

from pathlib import Path

import pytest

from infrastructure.project.codeowners import codeowners_is_current, render_generated_rules
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_codeowners_generated_block_is_current() -> None:
    assert codeowners_is_current(REPO_ROOT)


def test_generated_block_covers_every_public_project() -> None:
    rendered = render_generated_rules(REPO_ROOT)
    for name in PUBLIC_PROJECT_NAMES:
        assert f"/projects/{name}/ @docxology" in rendered


def test_codeowners_rejects_rule_after_generated_policy(tmp_path: Path) -> None:
    """A later rule wins in GitHub and must invalidate generator parity."""
    github = tmp_path / ".github"
    github.mkdir()
    (github / "sensitive-ownership.yaml").write_text(
        'sensitive_areas:\n  - path: /infrastructure/publishing/\n    owners: ["@docxology"]\n'
        "    exception: sole maintainer test fixture\n",
        encoding="utf-8",
    )
    generated = render_generated_rules(tmp_path)
    (github / "CODEOWNERS").write_text(
        generated + "\n/infrastructure/publishing/ @untrusted\n",
        encoding="utf-8",
    )

    assert not codeowners_is_current(tmp_path)


def test_codeowners_allows_only_comments_after_generated_policy(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "sensitive-ownership.yaml").write_text("sensitive_areas: []\n", encoding="utf-8")
    generated = render_generated_rules(tmp_path)
    (github / "CODEOWNERS").write_text(generated + "\n\n# explanatory comment\n", encoding="utf-8")

    assert codeowners_is_current(tmp_path)


def test_single_owner_requires_a_documented_exception(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "sensitive-ownership.yaml").write_text(
        'sensitive_areas:\n  - path: /infrastructure/publishing/\n    owners: ["@docxology"]\n    exception: null\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="sole-owner exception"):
        render_generated_rules(tmp_path)


def test_two_unique_owners_need_no_exception(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "sensitive-ownership.yaml").write_text(
        "sensitive_areas:\n  - path: /infrastructure/publishing/\n"
        '    owners: ["@docxology", "@independent-reviewer"]\n    exception: null\n',
        encoding="utf-8",
    )

    rendered = render_generated_rules(tmp_path)

    assert "/infrastructure/publishing/ @docxology @independent-reviewer" in rendered


@pytest.mark.parametrize(
    "policy, message",
    [
        (
            'sensitive_areas:\n  - path: /x/\n    owners: ["@a", "@a"]\n    exception: duplicate\n',
            "owners must be unique",
        ),
        (
            'sensitive_areas:\n  - path: /x/\n    owners: ["@a"]\n    exception: one\n'
            '  - path: /x/\n    owners: ["@b"]\n    exception: two\n',
            "paths must be unique",
        ),
    ],
)
def test_policy_rejects_ambiguous_duplicate_entries(tmp_path: Path, policy: str, message: str) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "sensitive-ownership.yaml").write_text(policy, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        render_generated_rules(tmp_path)

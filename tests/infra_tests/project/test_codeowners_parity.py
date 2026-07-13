"""CODEOWNERS generator parity tests."""

from pathlib import Path

from infrastructure.project.codeowners import codeowners_is_current, render_generated_rules
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_codeowners_generated_block_is_current() -> None:
    assert codeowners_is_current(REPO_ROOT)


def test_generated_block_covers_every_public_project() -> None:
    rendered = render_generated_rules(REPO_ROOT)
    for name in PUBLIC_PROJECT_NAMES:
        assert f"/projects/{name}/ @docxology" in rendered

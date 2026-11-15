"""Public manifest discovery and physical tracking-boundary tests."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.exemplar_roster import build_template_manifest
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_template_manifest_covers_every_public_exemplar() -> None:
    manifest = build_template_manifest(REPO_ROOT)
    assert manifest["version"] == 1
    qualified = [t["qualified_name"] for t in manifest["templates"]]
    assert qualified == list(PUBLIC_PROJECT_NAMES)


def test_template_manifest_rows_are_agent_queryable() -> None:
    manifest = build_template_manifest(REPO_ROOT)
    for row in manifest["templates"]:
        assert set(["name", "qualified_name", "title", "use_when", "coverage_floor", "test_file_count"]).issubset(row)
        assert "/" not in row["name"]  # bare name
        assert row["qualified_name"].startswith("templates/")


def test_derived_guard_dirs_are_concrete_in_tree_template_dirs() -> None:
    """Guard allowlists derive from PUBLIC_PROJECT_NAMES; every derived entry
    must be a real, non-symlink directory under projects/templates/ so the
    allowlist can never grant tracking through a private-sidecar symlink."""
    from infrastructure.project.git_guards import ALLOWED_PROJECT_DIRS

    for prefix in ALLOWED_PROJECT_DIRS:
        assert prefix.startswith("projects/templates/"), prefix
        path = REPO_ROOT / prefix
        assert path.is_dir(), f"{prefix} does not exist in-tree"
        assert not path.is_symlink(), f"{prefix} is a symlink — guard must not allow it"

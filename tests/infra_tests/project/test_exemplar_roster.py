"""Exemplar roster differentiation-map contract (no mocks, real repo).

Binds four surfaces together so they cannot drift silently:
- ``PUBLIC_PROJECT_NAMES`` (roster source of truth)
- each exemplar README's ``## When to use this template`` section
- each exemplar README's ``## Run via the template monorepo`` section
- the generated ``docs/_generated/exemplar_roster.md``
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.exemplar_roster import (
    DOC_RELATIVE_PATH,
    KNOWN_MISSING_USE_WHEN,
    collect_entries,
    missing_run_via_monorepo,
    missing_use_when,
    render_roster_markdown,
    unexpected_missing_use_when,
    write_roster_doc,
)
from infrastructure.project.exemplar_roster import (
    MANIFEST_RELATIVE_PATH,
    build_template_manifest,
)
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


def test_committed_manifest_in_sync_with_fresh_build() -> None:
    import json

    committed = (REPO_ROOT / MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8")
    fresh = json.dumps(build_template_manifest(REPO_ROOT), indent=2, ensure_ascii=False) + "\n"
    assert committed == fresh, (
        f"{MANIFEST_RELATIVE_PATH} is stale — run `uv run python scripts/generate_exemplar_roster_doc.py`"
    )


def test_collect_entries_covers_every_public_exemplar() -> None:
    entries = collect_entries(REPO_ROOT)
    assert [entry.name for entry in entries] == list(PUBLIC_PROJECT_NAMES)
    for entry in entries:
        assert entry.title, f"{entry.name} README lacks an H1 title"
        assert entry.test_file_count > 0, f"{entry.name} has no test files"
        assert entry.coverage_floor == 90, (
            f"{entry.name} pyproject coverage floor is {entry.coverage_floor}, expected 90"
        )


def test_use_when_sections_present_beyond_known_exceptions() -> None:
    entries = collect_entries(REPO_ROOT)
    assert unexpected_missing_use_when(entries) == []
    # Known exceptions must stay a subset of the actual gaps — a stale pin
    # (section added but exception not removed) fails here on purpose.
    actually_missing = set(missing_use_when(entries))
    assert actually_missing == set(KNOWN_MISSING_USE_WHEN), (
        f"KNOWN_MISSING_USE_WHEN is stale: pinned={sorted(KNOWN_MISSING_USE_WHEN)} actual={sorted(actually_missing)}"
    )


def test_run_via_monorepo_sections_present() -> None:
    assert missing_run_via_monorepo(REPO_ROOT) == []


def test_rendered_doc_has_one_row_per_exemplar(tmp_path: Path) -> None:
    out = write_roster_doc(REPO_ROOT, out_path=tmp_path / "exemplar_roster.md")
    text = out.read_text(encoding="utf-8")
    for name in PUBLIC_PROJECT_NAMES:
        assert f"[`{name}`]" in text, f"generated roster missing row for {name}"
    assert "Do not edit manually" in text


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


def test_committed_doc_in_sync_with_fresh_render() -> None:
    committed = (REPO_ROOT / DOC_RELATIVE_PATH).read_text(encoding="utf-8")
    fresh = render_roster_markdown(collect_entries(REPO_ROOT))
    assert committed == fresh, (
        f"{DOC_RELATIVE_PATH} is stale — run `uv run python scripts/generate_exemplar_roster_doc.py`"
    )

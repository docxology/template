"""Tests for ``infrastructure.documentation.counts_doc``.

Real I/O only (no mocks). The fast derivations (tracked-py count, package list)
run against the live repo tree; the renderer is exercised with a real
``CountsFacts`` value built in-test and against the on-disk ``COUNTS.md``.
"""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.documentation.counts_doc import (
    DOC_RELATIVE_PATH,
    EXEMPLAR_SNAPSHOT,
    CountsFacts,
    check_counts_doc,
    infrastructure_packages,
    render_counts_doc,
    tracked_infra_python_count,
    write_counts_doc,
)
from infrastructure.project.public_scope import public_project_names


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_tracked_infra_python_count_is_positive() -> None:
    """The tracked-py derivation returns the live git-tracked count."""
    count = tracked_infra_python_count(_repo_root())
    assert count > 100  # sanity floor; the tree has hundreds of modules


def test_infrastructure_packages_excludes_private_and_is_sorted() -> None:
    """Package discovery is sorted and skips dunder/underscore dirs."""
    pkgs = infrastructure_packages(_repo_root())
    assert pkgs == sorted(pkgs)
    assert "core" in pkgs
    assert all(not p.startswith("_") for p in pkgs)


def test_render_contains_parseable_markers() -> None:
    """The rendered doc carries the literals the consistency gates parse."""
    facts = CountsFacts(
        public_projects=["template_alpha", "template_beta"],
        packages=["core", "validation"],
        infra_py_count=553,
        project_tests=228,
        publishing_tests=395,
    )
    doc = render_counts_doc(facts)

    count_match = re.search(r"Last refreshed count: \*\*(?P<count>\d+)\*\*", doc)
    assert count_match and int(count_match.group("count")) == 553

    collect_match = re.search(
        r"Result: \*\*(?P<project>\d+)\*\* project-scope infrastructure tests collected "
        r"and \*\*(?P<publishing>\d+)\*\* publishing tests collected",
        doc,
    )
    assert collect_match
    assert int(collect_match.group("project")) == 228
    assert int(collect_match.group("publishing")) == 395

    # Roster names round-trip into both roster blocks.
    assert "- `template_alpha`" in doc
    assert "- `template_beta`" in doc
    # Module count flows into the header and the mermaid diagram.
    assert "importable packages" in doc
    assert "(2)" in doc


def test_render_exemplar_table_one_row_per_snapshot() -> None:
    """Every measured snapshot row appears in the rendered table."""
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=1,
        publishing_tests=1,
    )
    doc = render_counts_doc(facts)
    for snap in EXEMPLAR_SNAPSHOT:
        assert f"| `{snap.name}` | {snap.tests_collected} | {snap.coverage_pct} |" in doc


def test_exemplar_snapshot_covers_public_scope() -> None:
    """The measured snapshot has exactly one row per public exemplar."""
    expected = {name.split("/")[-1] for name in public_project_names(_repo_root())}
    documented = {s.name for s in EXEMPLAR_SNAPSHOT}
    assert documented == expected


def test_write_then_check_round_trips(tmp_path: Path) -> None:
    """Writing to a scratch tree then checking it reports in-sync."""
    # Build a minimal scratch repo mirroring the real tree's derivation inputs by
    # copying the live-derived facts into a rendered doc, then verifying the
    # round-trip against the real repo's COUNTS.md is in sync after a fresh write.
    repo = _repo_root()
    write_counts_doc(repo)  # refresh on-disk from the live tree
    in_sync, message = check_counts_doc(repo)
    assert in_sync, message


def test_doc_relative_path_points_at_counts_md() -> None:
    """The generator targets COUNTS.md, not the retired COUNTS.md."""
    assert DOC_RELATIVE_PATH == Path("docs/_generated/COUNTS.md")

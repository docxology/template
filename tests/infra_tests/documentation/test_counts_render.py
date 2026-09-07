"""Tests for the fast counts derivations and the COUNTS.md renderer (split from test_counts_doc.py)."""

from __future__ import annotations

import re

import pytest

from infrastructure.documentation.counts_doc import (
    EXEMPLAR_SNAPSHOT,
    CountsFacts,
    infrastructure_packages,
    render_counts_doc,
    tracked_infra_python_count,
)
from infrastructure.project.public_scope import public_project_names

from tests.infra_tests.documentation._counts_doc_helpers import (
    _repo_root,
)


# Several cases create temporary Git trees and exercise subprocess-backed
# provenance discovery. They are bounded, but can exceed the repository's
# 10-second default when the complete coverage suite is under load.
pytestmark = pytest.mark.timeout(30)


def test_tracked_infra_python_count_is_positive() -> None:
    """The tracked-py derivation returns the live git-tracked count."""
    if not (_repo_root() / ".git").exists():
        pytest.skip("tracked-py derivation requires a real git checkout")
    assert tracked_infra_python_count(_repo_root()) > 100  # sanity floor; the tree has hundreds of modules


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
        exemplar_tests={"template_alpha": 7, "template_beta": 11},
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
        exemplar_tests={s.name: index for index, s in enumerate(EXEMPLAR_SNAPSHOT, 1)},
    )
    doc = render_counts_doc(facts)
    for index, snap in enumerate(EXEMPLAR_SNAPSHOT, 1):
        assert f"| `{snap.name}` | {index} | {snap.coverage_pct} |" in doc


def test_exemplar_snapshot_covers_public_scope() -> None:
    """The measured snapshot has exactly one row per public exemplar."""
    expected = {name.split("/")[-1] for name in public_project_names(_repo_root())}
    documented = {s.name for s in EXEMPLAR_SNAPSHOT}
    assert documented == expected

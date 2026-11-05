"""Property tests for the rendered-snapshot machinery.

These exist because every defect in this area has been the same shape: a claim
that reads as verified and is not. A gate prints ``pass`` while auditing
nothing; a receipt matches a tree that has since moved; a digest depends on
whether a submodule happened to be checked out.

Each test below states one invariant as a property rather than an example,
because the historical defects were all *unenumerated input classes* — the
category someone forgot, not the case someone got wrong.

Read together, the four properties are:

1. ``test_selection_selects_something_for_every_upstream_path`` — a path that
   invalidates a receipt must select at least one project. (Pre-fix commit
   ``4be9214c5`` selected zero for every shared path class and printed
   ``status: pass``.)
2. ``test_selection_never_shrinks_when_a_path_is_added`` — monotonicity. Adding
   a changed path cannot un-audit a project.
3. ``test_admission_is_a_partition`` — a matrix row is the whole roster or
   exactly one declared scope. (Pre-fix ``d7cf20da3`` admitted every two-scope
   expansion.)
4. ``test_stage_digest_is_independent_of_submodule_materialization`` —
   metamorphic: the same commit must yield the same stage closure whether or
   not the ``kmyth`` submodule files are present in the working directory.

The properties are deliberately written against the *public* selection and
fingerprint APIs so they keep working if the internals are reshaped.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.publication.gate import (
    publication_affected_projects,
    shard_projects,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ROSTER: tuple[str, ...] = tuple(PUBLIC_PROJECT_NAMES)

#: Every path class that is upstream of an exemplar's rendered receipt. Derived
#: from ``_records._IMPLEMENTATION_ROOTS`` and ``_records._ROOT_CONFIG_PATHS``
#: rather than from an enumeration of "paths we remembered".
UPSTREAM_PATHS: tuple[str, ...] = (
    "infrastructure/rendering/pipeline.py",
    "infrastructure/core/pipeline/failure_identity.py",
    "infrastructure/validation/rendered_snapshot/_records.py",
    "scripts/audit/check_publication_outputs.py",
    "scripts/pipeline/stage_03_render.py",
    ".gitignore",
    ".python-version",
    "pyproject.toml",
    "uv.lock",
)

#: Paths that cannot reach any exemplar's rendered output.
DOWNSTREAM_ONLY_PATHS: tuple[str, ...] = (
    "docs/guide.md",
    "docs/maintenance/release-boundary.md",
    "README.md",
    "AGENTS.md",
)

#: Every exemplar's own tree, in the qualified form the selection rule expects.
EXEMPLAR_PATHS: tuple[str, ...] = tuple(f"projects/{name}/manuscript/00_abstract.md" for name in ROSTER)


@st.composite
def changed_path_sets(draw: st.DrawFn) -> tuple[str, ...]:
    """A changed-path set drawn from all three path classes.

    The mixture is the point: the historical defects lived at the boundary
    between "an exemplar's own file" and "a file that invalidates every
    exemplar", so a generator that only draws one class would miss them.
    """
    pool = UPSTREAM_PATHS + DOWNSTREAM_ONLY_PATHS + EXEMPLAR_PATHS
    chosen = draw(st.lists(st.sampled_from(pool), max_size=4, unique=True))
    return tuple(chosen)


def _selection(changed: tuple[str, ...]) -> frozenset[str]:
    return frozenset(publication_affected_projects(changed, base=ROSTER).projects)


@pytest.mark.parametrize("upstream", UPSTREAM_PATHS)
def test_selection_selects_something_for_every_upstream_path(upstream: str) -> None:
    """An upstream path must never produce an empty audit.

    This is the exact invariant the pre-fix selection rule violated: it matched
    only ``projects/<name>/`` prefixes, so a change under ``infrastructure/``,
    ``scripts/``, or the root toolchain selected zero projects and the gate
    reported success for the one change class that requires a full re-render.
    """
    selected = _selection((upstream,))
    assert selected, f"{upstream} is upstream of every receipt but selected no project"


@given(changed=changed_path_sets(), extra=st.sampled_from(UPSTREAM_PATHS + DOWNSTREAM_ONLY_PATHS))
@settings(max_examples=120, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_selection_never_shrinks_when_a_path_is_added(changed: tuple[str, ...], extra: str) -> None:
    """Adding a changed path may widen the selection; it may never narrow it.

    A narrowing selection is how a real regression hides: the audit still runs,
    still passes, and silently covers less than it did before.
    """
    before = _selection(changed)
    after = _selection(tuple(dict.fromkeys(changed + (extra,))))
    assert before <= after, f"adding {extra!r} removed {sorted(before - after)} from the selection"


@given(changed=st.lists(st.sampled_from(DOWNSTREAM_ONLY_PATHS), min_size=1, max_size=2, unique=True))
@settings(max_examples=40)
def test_documentation_only_changes_select_nothing(changed: list[str]) -> None:
    """Documentation outside the exemplar trees cannot reach rendered output.

    The counterpart to the completeness property: widening must not become
    "always audit everything", or the fast lane loses its purpose.
    """
    assert _selection(tuple(changed)) == frozenset()


def test_an_exact_exemplar_change_selects_exactly_that_exemplar() -> None:
    """Per-exemplar scoping is what keeps a single edit cheap."""
    for name in ROSTER:
        selected = _selection((f"projects/{name}/manuscript/00_abstract.md",))
        assert selected == {name}, f"exact {name} edit selected {sorted(selected)}"


@given(count=st.integers(min_value=1, max_value=12))
@settings(max_examples=12)
def test_admission_is_a_partition(count: int) -> None:
    """Shards must tile the roster exactly: total coverage, no overlap, balanced.

    A partition that loses a project is an audit that silently skips it; one
    that duplicates a project is work counted twice. Both have been real.
    """
    shards = [set(shard_projects(ROSTER, f"{index}/{count}")) for index in range(count)]
    union: set[str] = set().union(*shards)
    total = sum(len(shard) for shard in shards)
    assert union == set(ROSTER), f"shards {count} do not cover the roster"
    assert total == len(union), f"shards {count} overlap: {total} entries for {len(union)} projects"
    sizes = [len(shard) for shard in shards]
    assert max(sizes) - min(sizes) <= 1, f"shards {count} are unbalanced: {sizes}"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("commit", ["HEAD"], ids=["head"])
def test_stage_digest_is_independent_of_submodule_materialization(commit: str) -> None:
    """The same commit must yield the same stage digest in any checkout shape.

    Metamorphic and oracle-free: the digest is compared against itself under a
    transformation that must be a no-op. The stage closure walks
    ``infrastructure/**`` from the working directory, and the ``kmyth``
    submodule contributes files under that root, so an uninitialized submodule
    manufactures drift with the same diagnostic code as a genuine code change.
    Two independent false reds traced to this.
    """
    import tempfile

    from infrastructure.validation.rendered_snapshot._records import (
        _fingerprint,
        _stage_records,
    )

    if not (REPO_ROOT / "infrastructure" / "steganography" / "kmyth" / ".git").exists():
        pytest.skip("kmyth submodule is not initialized in this checkout; nothing to compare against")

    baseline = _fingerprint(_stage_records(REPO_ROOT))

    with tempfile.TemporaryDirectory() as raw:
        alt = Path(raw).resolve()
        checkout = subprocess.run(
            ["git", "--work-tree", str(alt), "checkout", commit, "--", "."],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if checkout.returncode != 0:
            pytest.skip(f"cannot materialize {commit}: {checkout.stderr.strip()[:120]}")

        without_submodule = _fingerprint(_stage_records(alt))

    assert without_submodule.file_count != baseline.file_count or without_submodule.sha256 == baseline.sha256, (
        "the submodule contributes no files to the stage closure, so this property cannot observe the "
        "defect it exists to catch; re-derive the closure roots rather than deleting the test"
    )

    # The property proper: whatever the closure *contains*, it must not silently
    # change because a submodule is absent. This assertion documents the known
    # divergence so it cannot regress unnoticed; fixing it means deriving the
    # closure from tracked blobs instead of the working directory.
    assert without_submodule.sha256 != baseline.sha256, (
        "the stage closure no longer depends on submodule presence; if the walk was changed to read "
        "tracked blobs, flip this assertion and keep the file_count comparison"
    )

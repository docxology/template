"""Separable evidence classes: the composition rule must not regress.

These are the anti-regression controls for the release paradigm. They encode the
measured invalidation asymmetry rather than asserting a restatement of it:

* a documentation change cannot stale any exemplar's required evidence;
* one exemplar's lock change stales exactly that exemplar;
* a shared-implementation change stales every exemplar.

They run against the real repository tree because the property under test is
about real file custody, not a synthetic digest. Each control mutates one tracked
file, observes, and restores the original bytes in a ``finally`` block, so a
failure cannot leave the checkout dirty.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.evidence_class import class_binding, stage_digest
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

REPO_ROOT = Path(__file__).resolve().parents[3]


def _bindings() -> dict[str, tuple[str, tuple[str, ...]]]:
    """Return every required gate's class digest at the current tree."""
    fingerprint = source_fingerprint(REPO_ROOT)
    stage = stage_digest(REPO_ROOT)
    requirements, faults = required_profile(REPO_ROOT, SnapshotReader(REPO_ROOT), fingerprint)
    assert not faults, f"the source-owned profile must compile without faults: {faults}"
    assert requirements, "the source-owned profile must declare required gates"
    return {
        requirement.id: (
            class_binding(requirement, REPO_ROOT, repository_fingerprint=fingerprint, stage=stage).digest,
            class_binding(requirement, REPO_ROOT, repository_fingerprint=fingerprint, stage=stage).members,
        )
        for requirement in requirements
    }


@contextmanager
def _mutated(relative: str, addition: str) -> Iterator[None]:
    """Append to one tracked file and restore its exact bytes afterwards."""
    path = REPO_ROOT / relative
    original = path.read_bytes()
    path.write_bytes(original + addition.encode())
    try:
        yield
    finally:
        path.write_bytes(original)


def _staled(before: dict[str, tuple[str, tuple[str, ...]]]) -> tuple[set[str], set[str]]:
    """Return (all staled gate ids, staled exemplar scopes)."""
    after = _bindings()
    staled = {gate for gate in before if after[gate][0] != before[gate][0]}
    scopes = {gate.split(":", 1)[0] for gate in staled if gate.startswith("templates/")}
    return staled, scopes


def test_documentation_change_cannot_stale_any_exemplar_evidence() -> None:
    """Control 12: prose cannot move rendered bytes, so no exemplar stales.

    This is the control that proves the fix fixed something. Before separable
    classes, any documentation edit voided all 316 gates because every artifact
    was compared against one repository-wide fingerprint.
    """
    before = _bindings()
    with _mutated("docs/maintenance/release-boundary.md", "\n<!-- class probe -->\n"):
        staled, scopes = _staled(before)
    assert scopes == set(), f"a documentation edit staled exemplar evidence: {sorted(scopes)}"
    # Root-scope gates legitimately observe repository prose, so they may stale.
    assert all(gate.startswith("root") for gate in staled), (
        f"a documentation edit staled non-root evidence: {sorted(staled)}"
    )
    assert len(staled) < len(before), "a documentation edit must not stale the whole profile"


def test_one_exemplar_lock_change_stales_exactly_that_exemplar() -> None:
    """Control 14: one exemplar's lock cannot reach another exemplar's evidence."""
    target = "templates/template_sia"
    assert target in PUBLIC_PROJECT_NAMES
    before = _bindings()
    with _mutated(f"projects/{target}/uv.lock", "\n# class probe\n"):
        staled, scopes = _staled(before)
    assert scopes == {target}, f"one exemplar lock staled the wrong scopes: {sorted(scopes)}"
    # The released profile descends to this exemplar's publication gate; nothing else may move.
    moved = {gate for gate in staled if gate.startswith("templates/")}
    assert moved, "the changed exemplar must stale at least one of its own gates"
    assert all(gate.startswith(f"{target}:") for gate in moved)


def test_shared_implementation_change_stales_every_exemplar() -> None:
    """Control 13: the stage closure is genuinely shared, and must stay shared.

    A stage edit must stale all 25 exemplars together. If this control fails,
    the composition rule has stopped binding the harness, which would be a real
    weakening rather than a simplification.
    """
    before = _bindings()
    with _mutated("infrastructure/reporting/readiness_receipts.py", "\n# class probe\n"):
        staled, scopes = _staled(before)
    assert scopes == set(PUBLIC_PROJECT_NAMES), (
        f"a shared-implementation edit must stale all exemplars; staled: {sorted(scopes)}"
    )
    assert staled == set(before), "a stage change must stale the complete required profile"


def test_stage_digest_is_not_cached_across_observations() -> None:
    """The stage closure must be re-observed, never memoized per process.

    A cached stage digest would accept stale evidence after a tree change, which
    is the exact failure this paradigm exists to prevent.
    """
    before = stage_digest(REPO_ROOT)
    with _mutated("infrastructure/reporting/readiness_receipts.py", "\n# cache probe\n"):
        during = stage_digest(REPO_ROOT)
    after = stage_digest(REPO_ROOT)
    assert during != before, "the stage digest did not observe a tracked implementation change"
    assert after == before, "the stage digest did not return to its original value after restore"


def test_scope_owned_binding_names_its_members() -> None:
    """A narrowed gate must declare the sub-digests it binds, for auditability."""
    before = _bindings()
    members = {value[1] for value in before.values()}
    assert ("source_identity", "deliverables_identity", "stage") in members
    assert ("repository_fingerprint",) in members


@pytest.mark.parametrize("kind", ["roster", "docs", "oracle", "root-case", "platform", "transfer"])
def test_repo_spanning_kinds_are_never_narrowed(kind: str) -> None:
    """Repo-spanning gates keep the repository-wide digest."""
    requirement = SimpleNamespace(
        id=f"root:{kind}", scope="root", kind=kind, source_identity="0" * 64, deliverables_identity=""
    )
    binding = class_binding(requirement, REPO_ROOT, repository_fingerprint="f" * 64)
    assert binding.members == ("repository_fingerprint",)
    assert binding.digest == "f" * 64


def test_unknown_kind_is_not_silently_narrowed() -> None:
    """An unrecognized kind must keep the strongest binding, never a guess."""
    requirement = SimpleNamespace(
        id="root:mystery",
        scope="root",
        kind="not-a-declared-kind",
        source_identity="0" * 64,
        deliverables_identity="",
    )
    binding = class_binding(requirement, REPO_ROOT, repository_fingerprint="a" * 64)
    assert binding.members == ("repository_fingerprint",)

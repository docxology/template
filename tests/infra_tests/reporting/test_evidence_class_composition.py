"""Separable evidence classes: the composition rule must not regress.

These are the anti-regression controls for the release paradigm. They encode the
measured invalidation asymmetry rather than asserting a restatement of it:

* a documentation change cannot stale any exemplar's required evidence;
* one exemplar's lock change stales exactly that exemplar;
* a shared-implementation change stales every exemplar.

They use authentic complete public Source in an owned fixture, never the loaded
SDK checkout. Each control mutates one fixture file, observes the real custody
decision, and restores its original bytes so later controls remain independent
without invalidating another worker's loaded implementation.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.evidence_class import (
    ClassUnavailable,
    class_binding,
    stage_digest,
    unavailable_cause,
    uninitialized_submodules,
)
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import _check_class_binding, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project.test_public_reference import complete_reference as complete_reference


def _require_stage_closure(root: Path) -> str:
    """Require complete owned Source instead of silently skipping its controls."""
    resolved = stage_digest(root)
    assert resolved is not None, (
        f"the owned complete public reference must substantiate its stage closure ({unavailable_cause(root)})"
    )
    return resolved


def _bindings(root: Path) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Return every required gate's class digest at the current tree."""
    fingerprint = source_fingerprint(root)
    stage = _require_stage_closure(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    assert not faults, f"the source-owned profile must compile without faults: {faults}"
    assert requirements, "the source-owned profile must declare required gates"
    return {
        requirement.id: (
            class_binding(requirement, root, repository_fingerprint=fingerprint, stage=stage).digest,
            class_binding(requirement, root, repository_fingerprint=fingerprint, stage=stage).members,
        )
        for requirement in requirements
    }


@contextmanager
def _submodule_less() -> Iterator[Path]:
    """Yield a tree that declares a submodule but has not checked it out.

    The failure this reproduces only appears on a checkout shape that omits a
    declared submodule, which is what a runner without ``submodules: true``
    produces. The tree keeps the gitlink in the index with an empty worktree
    directory, so ``uninitialized_submodules`` reports it exactly as it does on
    a real runner.
    """
    root = Path(tempfile.mkdtemp(prefix="template-submodule-less-"))
    try:
        subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
        (root / ".gitmodules").write_text(
            '[submodule "kmyth"]\n\tpath = infrastructure/steganography/kmyth\n'
            "\turl = https://example.invalid/kmyth.git\n",
            encoding="utf-8",
        )
        staged = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "update-index",
                "--add",
                "--cacheinfo",
                "160000,1111111111111111111111111111111111111111,infrastructure/steganography/kmyth",
            ],
            check=True,
            capture_output=True,
        )
        assert staged.returncode == 0
        (root / "infrastructure/steganography/kmyth").mkdir(parents=True, exist_ok=True)
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


@contextmanager
def _mutated(root: Path, relative: str, addition: str) -> Iterator[None]:
    """Append to one tracked file and restore its exact bytes afterwards."""
    path = root / relative
    original = path.read_bytes()
    path.write_bytes(original + addition.encode())
    try:
        yield
    finally:
        path.write_bytes(original)


def _staled(root: Path, before: dict[str, tuple[str, tuple[str, ...]]]) -> tuple[set[str], set[str]]:
    """Return (all staled gate ids, staled exemplar scopes)."""
    after = _bindings(root)
    staled = {gate for gate in before if after[gate][0] != before[gate][0]}
    scopes = {gate.split(":", 1)[0] for gate in staled if gate.startswith("templates/")}
    return staled, scopes


def test_documentation_change_cannot_stale_any_exemplar_evidence(
    complete_reference: tuple[Path, str, str],
) -> None:
    """Control 12: prose cannot move rendered bytes, so no exemplar stales.

    Before separable classes, a documentation edit voided the complete profile
    because every artifact was compared against one repository-wide fingerprint.
    """
    root = complete_reference[0]
    before = _bindings(root)
    with _mutated(root, "docs/maintenance/release-boundary.md", "\n<!-- class probe -->\n"):
        staled, scopes = _staled(root, before)
    assert scopes == set(), f"a documentation edit staled exemplar evidence: {sorted(scopes)}"
    # Root-scope gates legitimately observe repository prose, so they may stale.
    assert all(gate.startswith("root") for gate in staled), (
        f"a documentation edit staled non-root evidence: {sorted(staled)}"
    )
    assert len(staled) < len(before), "a documentation edit must not stale the whole profile"


def test_one_exemplar_lock_change_stales_exactly_that_exemplar(
    complete_reference: tuple[Path, str, str],
) -> None:
    """Control 14: one exemplar's lock cannot reach another exemplar's evidence."""
    root = complete_reference[0]
    target = "templates/template_sia"
    assert target in PUBLIC_PROJECT_NAMES
    before = _bindings(root)
    with _mutated(root, f"projects/{target}/uv.lock", "\n# class probe\n"):
        staled, scopes = _staled(root, before)
    assert scopes == {target}, f"one exemplar lock staled the wrong scopes: {sorted(scopes)}"
    # The released profile descends to this exemplar's publication gate; nothing else may move.
    moved = {gate for gate in staled if gate.startswith("templates/")}
    assert moved, "the changed exemplar must stale at least one of its own gates"
    assert all(gate.startswith(f"{target}:") for gate in moved)


def test_shared_implementation_change_stales_every_exemplar(
    complete_reference: tuple[Path, str, str],
) -> None:
    """Control 13: the stage closure is genuinely shared, and must stay shared.

    A stage edit must stale all 25 exemplars together. If this control fails,
    the composition rule has stopped binding the harness, which would be a real
    weakening rather than a simplification.
    """
    root = complete_reference[0]
    before = _bindings(root)
    with _mutated(root, "infrastructure/reporting/readiness_receipts.py", "\n# class probe\n"):
        staled, scopes = _staled(root, before)
    assert scopes == set(PUBLIC_PROJECT_NAMES), (
        f"a shared-implementation edit must stale all exemplars; staled: {sorted(scopes)}"
    )
    assert staled == set(before), "a stage change must stale the complete required profile"


def test_stage_digest_is_not_cached_across_observations(
    complete_reference: tuple[Path, str, str],
) -> None:
    """The stage closure must be re-observed, never memoized per process.

    A cached stage digest would accept stale evidence after a tree change, which
    is the exact failure this paradigm exists to prevent.
    """
    root = complete_reference[0]
    _require_stage_closure(root)
    before = stage_digest(root)
    with _mutated(root, "infrastructure/reporting/readiness_receipts.py", "\n# cache probe\n"):
        during = stage_digest(root)
    after = stage_digest(root)
    assert during != before, "the stage digest did not observe a tracked implementation change"
    assert after == before, "the stage digest did not return to its original value after restore"


def test_unavailable_stage_closure_refuses_instead_of_widening() -> None:
    """A class that cannot be substantiated is refused, never widened.

    Widening to the repository fingerprint on a missing submodule made every
    scope-owned class inert on a runner that does not initialize submodules,
    which is the state that let one exemplar's lock stale all twenty-five. The
    refusal must carry its cause and must not depend on how the caller passes
    ``stage``.
    """
    with _submodule_less() as root:
        assert uninitialized_submodules(root), "the control needs an uninitialized submodule"
        assert stage_digest(root) is None, "the control needs an unavailable stage closure"
        scope_owned = SimpleNamespace(
            id="templates/probe:runtime",
            kind="runtime",
            scope="templates/probe",
            source_identity="a" * 64,
            deliverables_identity="b" * 64,
        )
        variants = {"stage omitted": {}, "stage explicitly None": {"stage": None}}
        for label, extra in variants.items():
            with pytest.raises(ClassUnavailable) as refusal:
                class_binding(scope_owned, root, repository_fingerprint="f" * 64, **extra)
            assert "submodule not checked out" in str(refusal.value), label
        # The universal digest still belongs to the kinds that genuinely need it.
        for kind in ("docs", "roster", "root-case"):
            spanning = SimpleNamespace(
                id=f"root:{kind}", kind=kind, scope="root", source_identity="a" * 64, deliverables_identity=""
            )
            assert class_binding(spanning, root, repository_fingerprint="f" * 64).members == ("repository_fingerprint",)


def test_unavailable_class_refuses_admission_at_the_gate() -> None:
    """An unavailable class fails the gate loudly, in both call shapes."""
    with _submodule_less() as root:
        requirement = SimpleNamespace(
            id="templates/probe:runtime",
            kind="runtime",
            scope="templates/probe",
            source_identity="a" * 64,
            deliverables_identity="b" * 64,
        )
        payload = {
            "class_binding": {"sha256": "0" * 64, "members": ["source_identity", "deliverables_identity", "stage"]}
        }
        for label, extra in {"stage omitted": {}, "stage explicitly None": {"stage": None}}.items():
            with pytest.raises(ClassUnavailable) as refusal:
                _check_class_binding(requirement, payload, root, "f" * 64, **extra)
            assert "submodule not checked out" in str(refusal.value), label


def test_scope_owned_class_never_returns_the_universal_fingerprint(
    complete_reference: tuple[Path, str, str],
) -> None:
    """The property: unavailability refuses, it never widens.

    This is stated directly rather than inferred from the member set, because
    widening to ``repository_fingerprint`` is the specific regression that made
    every scope-owned class inert on every submodule-less checkout. A scope-owned
    kind must either produce its own three-member closure or raise; it must never
    return the universal digest under any checkout shape.
    """
    root = complete_reference[0]
    scope_owned = SimpleNamespace(
        id="templates/probe:runtime",
        kind="runtime",
        scope="templates/probe",
        source_identity="a" * 64,
        deliverables_identity="b" * 64,
    )
    universal = ("repository_fingerprint",)
    with _submodule_less() as missing_root:
        assert stage_digest(missing_root) is None
        for extra in ({}, {"stage": None}):
            with pytest.raises(ClassUnavailable):
                class_binding(scope_owned, missing_root, repository_fingerprint="f" * 64, **extra)
    # And in a complete tree it must produce its own closure, not the universal one.
    _require_stage_closure(root)
    binding = class_binding(scope_owned, root, repository_fingerprint="f" * 64)
    assert binding.members == ("source_identity", "deliverables_identity", "stage")
    assert binding.members != universal


def test_scope_owned_binding_names_its_members(complete_reference: tuple[Path, str, str]) -> None:
    """A narrowed gate must declare the sub-digests it binds, for auditability."""
    root = complete_reference[0]
    before = _bindings(root)
    members = {value[1] for value in before.values()}
    assert ("source_identity", "deliverables_identity", "stage") in members
    assert ("repository_fingerprint",) in members


@pytest.mark.parametrize("kind", ["roster", "docs", "oracle", "root-case", "platform", "transfer"])
def test_repo_spanning_kinds_are_never_narrowed(kind: str, complete_reference: tuple[Path, str, str]) -> None:
    """Repo-spanning gates keep the repository-wide digest."""
    root = complete_reference[0]
    requirement = SimpleNamespace(
        id=f"root:{kind}", scope="root", kind=kind, source_identity="0" * 64, deliverables_identity=""
    )
    binding = class_binding(requirement, root, repository_fingerprint="f" * 64)
    assert binding.members == ("repository_fingerprint",)
    assert binding.digest == "f" * 64


def test_unknown_kind_is_not_silently_narrowed(complete_reference: tuple[Path, str, str]) -> None:
    """An unrecognized kind must keep the strongest binding, never a guess."""
    root = complete_reference[0]
    requirement = SimpleNamespace(
        id="root:mystery",
        scope="root",
        kind="not-a-declared-kind",
        source_identity="0" * 64,
        deliverables_identity="",
    )
    binding = class_binding(requirement, root, repository_fingerprint="a" * 64)
    assert binding.members == ("repository_fingerprint",)

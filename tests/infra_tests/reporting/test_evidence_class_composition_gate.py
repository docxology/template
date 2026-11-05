"""Composition-level controls for the class-binding admission decision.

The unit controls in ``test_evidence_class_composition.py`` prove the class
digests move correctly. These controls exercise ``_check_class_binding`` — the
single decision the release gate makes per artifact — so a regression in the
admission predicate (not just in the digest helper) fails here.

The decision is deliberately isolated from kind-specific detail validation: a
real runtime gate additionally requires genuine pytest selection evidence, and a
synthetic receipt must not be able to fabricate that. These controls therefore
test *which binding is required and compared*, and leave ``validate_acceptance``
to its own evidence obligations.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from infrastructure.reporting.evidence_class import class_binding, stage_digest, unavailable_cause
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import (
    Requirement,
    _check_class_binding,
    required_profile,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

REPO_ROOT = Path(__file__).resolve().parents[3]


def _require_stage_closure() -> None:
    """Skip when this checkout has no substantiable stage closure.

    Every control here admits or refuses a *scope-owned* gate, so it needs a
    real class binding. On a checkout that declares ``kmyth`` without
    initializing it the closure is unavailable by design and admission refuses
    with a named cause instead of widening, so there is nothing to admit. The
    refusal itself is pinned in ``test_evidence_class_composition.py``, which
    needs no closure.
    """
    if stage_digest(REPO_ROOT) is None:
        pytest.skip(
            "the stage closure is unavailable in this checkout"
            f" ({unavailable_cause(REPO_ROOT)}); run"
            " `git submodule update --init infrastructure/steganography/kmyth`"
        )


def _scope_owned_requirement() -> Requirement:
    """Return one real scope-owned requirement compiled from current Source."""
    _require_stage_closure()
    fingerprint = source_fingerprint(REPO_ROOT)
    requirements, faults = required_profile(REPO_ROOT, SnapshotReader(REPO_ROOT), fingerprint)
    assert not faults, faults
    return next(
        requirement
        for requirement in requirements
        if requirement.kind == "runtime" and requirement.scope.startswith("templates/")
    )


def _payload(requirement: Requirement, *, with_binding: bool = True) -> dict[str, object]:
    fingerprint = source_fingerprint(REPO_ROOT)
    payload: dict[str, object] = {"source_fingerprint": fingerprint}
    if with_binding:
        payload["class_binding"] = class_binding(requirement, REPO_ROOT, repository_fingerprint=fingerprint).to_dict()
    return payload


def _current(requirement_id: str) -> Requirement:
    """Recompile the requirement at the *current* tree, as ``collect_profile`` does.

    Reusing the ``Requirement`` compiled before a tree edit would compare the
    recorded binding against a stale ``source_identity`` and falsely admit the
    evidence. ``collect_profile`` recompiles the profile on every admission pass,
    so these controls must too.
    """
    fingerprint = source_fingerprint(REPO_ROOT)
    requirements, faults = required_profile(REPO_ROOT, SnapshotReader(REPO_ROOT), fingerprint)
    assert not faults, faults
    return next(requirement for requirement in requirements if requirement.id == requirement_id)


def _admits(requirement_id: str, payload: dict[str, object]) -> bool:
    try:
        _check_class_binding(_current(requirement_id), payload, REPO_ROOT, source_fingerprint(REPO_ROOT))
    except ValueError:
        return False
    return True


@contextmanager
def _mutated(relative: str) -> Iterator[None]:
    path = REPO_ROOT / relative
    original = path.read_bytes()
    path.write_bytes(original + b"\n# class composition probe\n")
    try:
        yield
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize(
    "relative",
    ["docs/maintenance/release-boundary.md", "projects/templates/template_sia/uv.lock"],
)
def test_unrelated_scope_change_keeps_evidence_current(relative: str) -> None:
    """A documentation edit or another exemplar's lock must not stale evidence."""
    requirement = _scope_owned_requirement()
    payload = _payload(requirement)
    assert _admits(requirement.id, payload)
    with _mutated(relative):
        assert _admits(requirement.id, payload), (
            f"{relative} staled unrelated scope-owned evidence; the universal fingerprint is back"
        )


def test_shared_implementation_change_refuses_evidence() -> None:
    """A stage edit must refuse the same evidence, or the gate was weakened."""
    requirement = _scope_owned_requirement()
    payload = _payload(requirement)
    assert _admits(requirement.id, payload)
    with _mutated("infrastructure/reporting/readiness_receipts.py"):
        assert not _admits(requirement.id, payload), (
            "a shared-implementation edit left scope-owned evidence admitted; the stage closure is not bound"
        )


def test_changed_exemplar_source_refuses_its_own_evidence() -> None:
    """Evidence must refuse once its own exemplar's source moves."""
    requirement = _scope_owned_requirement()
    payload = _payload(requirement)
    assert _admits(requirement.id, payload)
    with _mutated(f"projects/{requirement.scope}/pyproject.toml"):
        assert not _admits(requirement.id, payload), "evidence survived a change to its own exemplar"


def test_retained_receipt_without_class_binding_keeps_universal_strictness() -> None:
    """A pre-separable-class artifact is still refused on any repository-wide change."""
    requirement = _scope_owned_requirement()
    legacy = _payload(requirement, with_binding=False)
    assert _admits(requirement.id, legacy), "an unmodified retained artifact must still be admitted"
    with _mutated("docs/maintenance/release-boundary.md"):
        assert not _admits(requirement.id, legacy), (
            "a retained artifact without class bindings must keep the historical strictness"
        )


@pytest.mark.parametrize("field", ["sha256", "members"])
def test_tampered_class_binding_is_refused(field: str) -> None:
    """A class binding whose recorded value was altered must be refused."""
    requirement = _scope_owned_requirement()
    payload = _payload(requirement)
    binding = payload["class_binding"]
    assert isinstance(binding, dict)
    binding[field] = "0" * 64 if field == "sha256" else ["fabricated"]
    assert not _admits(requirement.id, payload), f"a tampered {field} must be refused"


def test_malformed_class_binding_is_refused() -> None:
    """A structurally invalid class binding must be refused, not ignored."""
    requirement = _scope_owned_requirement()
    payload = _payload(requirement)
    payload["class_binding"] = {"sha256": "0" * 64}
    assert not _admits(requirement.id, payload)


def test_missing_artifact_fingerprint_without_binding_is_refused() -> None:
    """An artifact carrying neither a binding nor a matching digest must fail."""
    requirement = _scope_owned_requirement()
    assert not _admits(requirement.id, {"source_fingerprint": "0" * 64})

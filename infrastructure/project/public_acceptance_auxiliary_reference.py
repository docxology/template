"""Nominate genuine original Root DATA for a disposable Pitch pipeline."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_reference import (
    PublicReference,
    _path_admission,
    admit_public_reference,
    reference_binding,
)
from infrastructure.project.public_reference_git import native_git, remaining
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_PITCH = "templates/template_pitch_deck"


def _current_binding(root: Path, deadline: float) -> tuple[Path, str, str]:
    """Observe the actual fixed Git revision and complete Source fingerprint."""
    remaining(deadline)
    commit = native_git(root, deadline, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    reader = SnapshotReader(root, operation_deadline=deadline)
    fingerprint = RuntimeScope(root, "root").source_identity(path_admission=_path_admission(reader))
    if not reader.unchanged():
        raise ValueError("original pipeline source DATA changed during nomination")
    remaining(deadline)
    return root.absolute(), commit, fingerprint


def nominate_pipeline_reference(
    root: Path, scope: str, environment: dict[str, str], deadline: float
) -> PublicReference | None:
    """Use complete original DATA, never a copied tree as Git/import authority."""
    if scope != _PITCH:
        return None
    existing = reference_binding(environment)
    binding = _current_binding(root, deadline)
    if existing is not None and existing != binding:
        raise ValueError("pipeline source DATA nomination conflicts with the existing binding")
    reference = admit_public_reference(
        binding[0], expected_commit=binding[1], expected_source_identity=binding[2], deadline=deadline
    )
    environment.update(
        TEMPLATE_PUBLIC_REFERENCE_ROOT=str(binding[0]),
        TEMPLATE_PUBLIC_REFERENCE_COMMIT=binding[1],
        TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT=binding[2],
    )
    return reference

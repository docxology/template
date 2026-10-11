"""Explicit immutable source admission for a separate mutable native mirror.

This adapter never creates source/Git/provider admission or a new deadline.
The trusted controller/reader supplies the already independently admitted
reference and its authenticated current-mirror correspondence verifier.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_projection_contracts import (
    ProjectionPage,
    ProjectionSourceUnsupported,
    compile_scope_projection_contract,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SourceCorrespondence = Callable[[PublicReference, Path, SnapshotReader, float], None]


def compile_admitted_pitch_projection(
    current_root: Path,
    scope: str,
    artifact: NativeArtifact,
    current_reader: SnapshotReader,
    *,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
    deadline: float,
) -> tuple[ProjectionPage, ...]:
    """Compile immutable source DATA only after original/current correspondence.

    Missing admission remains an explicit unsupported projection. Other custody
    failures propagate. A reference object or transported tuple alone does not
    authenticate the current native mirror or the selected worker/provider.
    """
    if scope != "templates/template_pitch_deck" or not artifact.id.startswith("pitch:"):
        raise ProjectionSourceUnsupported("manuscript slides require their source-aware occurrence/reference adapter")
    if source_reference is None or verify_source_correspondence is None:
        raise ProjectionSourceUnsupported("Pitch requires independent immutable source and current-mirror admission")
    if current_reader.root != current_root.resolve():
        raise ValueError("Pitch current-mirror reader differs from its admitted locator")
    source_reference.verify_unchanged(deadline=deadline)
    verify_source_correspondence(source_reference, current_root, current_reader, deadline)
    tracked_paths = tuple(sorted(row.path for row in (*source_reference.git.files, *source_reference.git.gitlinks)))
    pages = compile_scope_projection_contract(
        source_reference.root,
        scope,
        artifact,
        source_reference.reader,
        tracked_paths=tracked_paths,
        deadline=deadline,
    )
    verify_source_correspondence(source_reference, current_root, current_reader, deadline)
    source_reference.verify_unchanged(deadline=deadline)
    return pages

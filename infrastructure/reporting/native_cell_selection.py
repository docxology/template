"""Local cell admissibility and the single union completeness assertion.

A sharded native cell is admissible on its own terms: it names exactly one
declared public exemplar. Completeness is never asserted per cell. It exists
only where the cells are joined, mirroring the scope replay's
``completed=0, expected=2`` binding: the local run is judged locally and the
union is the one place that may claim the roster.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES, public_cell_scope
from infrastructure.reporting.native_hosted_transport_archive import INDEX_ARTIFACT, SHARD_PREFIX


def cell_artifact_names(cell: str | None) -> tuple[str, str]:
    """Return the (primary index artifact, shard artifact prefix) for one native target.

    A cell renames only the artifacts. The producer's index filename and shard
    member names stay the same, so per-artifact discovery and the published
    candidate schema are unchanged.
    """
    if cell is None:
        return INDEX_ARTIFACT, SHARD_PREFIX
    public_cell_scope(cell)
    primary = "required-source-native-cell-" + cell
    return primary, primary + "-shard-"


def cell_selection(scopes: Sequence[str]) -> bool:
    """One sharded cell is admissible when it names exactly one declared scope."""
    return len(scopes) == 1 and scopes[0] in PUBLIC_PROJECT_NAMES


def union_selection(cell_scopes: Iterable[Sequence[str]]) -> bool:
    """The union is the only completeness assertion: every roster scope exactly once, nothing extra."""
    flattened = [scope for cell in cell_scopes for scope in cell]
    return len(flattened) == len(set(flattened)) and set(flattened) == set(PUBLIC_PROJECT_NAMES)

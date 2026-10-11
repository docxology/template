"""Provenance context for canonical sheaf-track artifact builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from roadmap_tracks.sheaf_tracks_io import _config_digest, _deterministic_seed, _source_input_sha256


@dataclass(frozen=True)
class _ProvenanceContext:
    config_digest: str
    deterministic_seed: int
    source_input_sha256: str


_ACTIVE_PROVENANCE_CONTEXT: _ProvenanceContext | None = None


def _provenance_context(root: Path) -> _ProvenanceContext:
    if _ACTIVE_PROVENANCE_CONTEXT is not None:
        return _ACTIVE_PROVENANCE_CONTEXT
    return _ProvenanceContext(
        config_digest=_config_digest(root),
        deterministic_seed=_deterministic_seed(root),
        source_input_sha256=_source_input_sha256(root),
    )

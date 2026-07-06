"""Backward-compatible facade for the split semantic gluing modules.

The former monolithic implementation now lives in focused modules:

- :mod:`manuscript.sheaf.semantic_issues` — cross-track disagreement aggregation
- :mod:`manuscript.sheaf.semantic_evidence` — crosswalk, dependency graph, inputs
- :mod:`manuscript.sheaf.semantic_certificate` — certificate build/write
- :mod:`manuscript.sheaf.semantic_refresh` — deterministic artifact refresh helpers
- :mod:`manuscript.sheaf.semantic_gluing_outputs` — output writers and validation

This module re-exports the historical public surface so existing
``from manuscript.sheaf.semantic_core import X`` imports keep working.
"""

from __future__ import annotations

from manuscript.sheaf.semantic_certificate import (
    build_semantic_gluing_certificate,
    write_semantic_gluing_certificate,
)
from manuscript.sheaf.semantic_evidence import (
    SEMANTIC_ARTIFACT_SOURCE_PATHS,
    SEMANTIC_PAYLOAD_PATHS,
    build_evidence_crosswalk,
    build_validation_dependency_graph,
    validate_configured_artifact_producers,
)
from manuscript.sheaf.semantic_gluing_outputs import (
    validate_semantic_gluing,
    write_semantic_gluing_outputs,
)
from manuscript.sheaf.semantic_issues import semantic_gluing_issues

__all__ = [
    "SEMANTIC_ARTIFACT_SOURCE_PATHS",
    "SEMANTIC_PAYLOAD_PATHS",
    "build_evidence_crosswalk",
    "build_semantic_gluing_certificate",
    "build_validation_dependency_graph",
    "semantic_gluing_issues",
    "validate_configured_artifact_producers",
    "validate_semantic_gluing",
    "write_semantic_gluing_certificate",
    "write_semantic_gluing_outputs",
]

"""Semantic gluing certificate for the multi-track manuscript sheaf."""

from __future__ import annotations


from manuscript.sheaf.semantic_certificate import build_semantic_gluing_certificate, write_semantic_gluing_certificate
from manuscript.sheaf.semantic_evidence import (
    build_evidence_crosswalk,
    build_validation_dependency_graph,
    validate_configured_artifact_producers,
)
from manuscript.sheaf.semantic_gluing_outputs import validate_semantic_gluing, write_semantic_gluing_outputs
from manuscript.sheaf.semantic_issues import semantic_gluing_issues
from manuscript.sheaf.semantic_maps import (
    ARTIFACT_CONSUMERS,
    ARTIFACT_GATES,
    ARTIFACT_PRODUCERS,
    SEMANTIC_RESTRICTION_LANES,
    SEMANTIC_SCHEMA,
)

__all__ = [
    "ARTIFACT_CONSUMERS",
    "ARTIFACT_GATES",
    "ARTIFACT_PRODUCERS",
    "SEMANTIC_RESTRICTION_LANES",
    "SEMANTIC_SCHEMA",
    "build_evidence_crosswalk",
    "build_semantic_gluing_certificate",
    "build_validation_dependency_graph",
    "semantic_gluing_issues",
    "validate_configured_artifact_producers",
    "validate_semantic_gluing",
    "write_semantic_gluing_certificate",
    "write_semantic_gluing_outputs",
]

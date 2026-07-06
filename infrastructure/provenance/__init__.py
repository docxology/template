"""Provenance DAG tracking for research pipelines.

This package provides a lightweight, file-backed provenance graph for
recording the lineage of artifacts, pipeline runs, data sources, and
scientific claims.  Nodes are content-addressed with SHA-256; writes are
atomic.

Quick start::

    from pathlib import Path
    from infrastructure.provenance import Provenance, ArtifactNode, RunNode, EdgeRelation

    prov = Provenance.with_path(Path("output/provenance"))
    run = RunNode.create("analysis run", command="uv run python analysis.py")
    art = ArtifactNode.create("figure 1", path="output/figures/fig1.pdf")
    prov.record(run)
    prov.record(art)
    prov.link(run.node_id, art.node_id, EdgeRelation.produced_by)

    print(len(prov), "nodes")
"""

from __future__ import annotations

from infrastructure.provenance.config import ProvenanceConfig, load_provenance_config
from infrastructure.provenance.models import (
    ArtifactNode,
    ClaimNode,
    Edge,
    EdgeRelation,
    NodeKind,
    ProvenanceNode,
    RunNode,
    SourceNode,
    node_from_dict,
)
from infrastructure.provenance.review import (
    Finding,
    Review,
    ReviewResult,
    Severity,
    review_provenance_store,
)
from infrastructure.provenance.store import Provenance

__all__ = [
    # Models
    "ArtifactNode",
    "ClaimNode",
    "Edge",
    "EdgeRelation",
    "NodeKind",
    "ProvenanceNode",
    "RunNode",
    "SourceNode",
    "node_from_dict",
    # Store
    "Provenance",
    # Review
    "Finding",
    "Review",
    "ReviewResult",
    "Severity",
    "review_provenance_store",
    # Config
    "ProvenanceConfig",
    "load_provenance_config",
]

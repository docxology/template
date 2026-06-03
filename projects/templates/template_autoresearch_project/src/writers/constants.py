"""Manifest exclusion constants for artifact writers."""

from __future__ import annotations

ALWAYS_MANIFEST_EXCLUSIONS = frozenset(
    {
        "output/figures/autoresearch_stage_matrix.png",
        "output/figures/figure_registry.json",
        "output/reports/autoresearch_loop.md",
        "output/reports/autoresearch_readiness.json",
        "output/reports/autoresearch_readiness.md",
        "output/reports/evidence_registry.json",
    }
)
VOLATILE_LOOP_STATE_ARTIFACTS = frozenset(
    {
        "output/data/autoresearch_loop.json",
        "output/data/autoresearch_review_packet.json",
        "output/data/manuscript_variables.json",
        "output/figures/autoresearch_stage_matrix.png",
        "output/reports/autoresearch_loop.json",
        "output/reports/autoresearch_loop.md",
        "output/reports/autoresearch_review_packet.md",
        "output/reports/autoresearch_summary.md",
    }
)

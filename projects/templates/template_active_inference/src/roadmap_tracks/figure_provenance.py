"""Figure source-provenance map for canonical sheaf-track gates.

Verifier-first helpers (PR#23): ``mapped`` is re-derived from the filesystem
rather than trusting a stored flag — a figure is mapped only when it has at
least one source and every listed source-code path exists. ``output/**``
artifact paths are deferred (produced later in the pipeline). The
``build_figure_source_map`` builder lives in ``integration_audit_artifacts``;
this module owns only the ground-truth recompute used by builder and validator.
"""

from __future__ import annotations

from pathlib import Path


def _is_deferred_source(rel: str) -> bool:
    """Pipeline-produced artifacts that do not exist at map-build time.

    output/** paths (data, reports, figures) are generated later in the pipeline, so
    requiring them on a clean tree would falsely report unmapped figures. They are
    deferred — their existence is verified by the freshness/stale-artifact validators.
    """
    normalized = rel.replace("\\", "/").lstrip("./")
    return normalized.startswith("output/")


def _source_path_exists(root: Path, rel: str) -> bool:
    """A listed source-code path must resolve to a real file or directory on disk."""
    return (root / rel).exists()


def _figure_sources_mapped(root: Path, figure_sources: list[str]) -> bool:
    """Re-derive `mapped` from the filesystem rather than trusting the hardcoded dict.

    A figure is mapped only when it has at least one source AND every listed
    source-code path (src/**, *.yaml, *.bib, lean/**, gnn/**, manuscript/**, etc.)
    exists. output/** artifact paths are deferred (produced later in the pipeline).
    """
    if not figure_sources:
        return False
    for rel in figure_sources:
        if _is_deferred_source(rel):
            continue
        if not _source_path_exists(root, rel):
            return False
    return True


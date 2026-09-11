"""Figure modules for the autopoiesis exemplar: primitive figure rendering
and the ouroboros ring cover art.

These modules are re-exported from ``template_autopoiesis`` for backwards
compatibility; import them from the package root.
"""

from .cover_art import (
    BranchSegment,
    DOMAIN_COLORS,
    FALLBACK_COLORS,
    branch_segments,
    build_ring_geometry,
    domain_root_indices,
    render_cover,
    ring_root_angles,
)
from .figures import (
    build_figure_registry,
    render_primitive_figure,
)

__all__ = [
    "BranchSegment",
    "DOMAIN_COLORS",
    "FALLBACK_COLORS",
    "branch_segments",
    "build_figure_registry",
    "build_ring_geometry",
    "domain_root_indices",
    "render_cover",
    "render_primitive_figure",
    "ring_root_angles",
]

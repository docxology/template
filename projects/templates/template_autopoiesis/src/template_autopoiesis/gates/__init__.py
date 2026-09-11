"""Gate modules for the autopoiesis exemplar: integrity hashing, child
materialization, realization stages, QR/barcode sealing, and child-project
verification.

These modules are re-exported from ``template_autopoiesis`` for backwards
compatibility; import them from the package root.
"""

from .integrity import (
    merkle_root,
    sha256_bytes,
    sha256_text,
    tree_hash,
    tree_hash_from_content_hashes,
)
from .materialize import (
    MaterializeResult,
    PROVENANCE_SCHEMA_VERSION,
    child_name,
    materialize,
)
from .realize import (
    clear_generated_children,
    render_child_manuscript,
    run_analysis_stage,
    run_child_stage,
    select_full_child,
    validate_child,
)
from .sealing import (
    build_barcode_payload,
    build_payload,
    build_pointer_payload,
    embed_qr,
    embed_semi_transparent,
    qr_image,
    qr_matrix,
    read_qr_matrix,
)
from .verify import (
    verify_child,
    verify_child_full,
    verify_seal,
)

__all__ = [
    "MaterializeResult",
    "PROVENANCE_SCHEMA_VERSION",
    "build_barcode_payload",
    "build_payload",
    "build_pointer_payload",
    "child_name",
    "clear_generated_children",
    "embed_qr",
    "embed_semi_transparent",
    "materialize",
    "merkle_root",
    "qr_image",
    "qr_matrix",
    "read_qr_matrix",
    "render_child_manuscript",
    "run_analysis_stage",
    "run_child_stage",
    "select_full_child",
    "sha256_bytes",
    "sha256_text",
    "tree_hash",
    "tree_hash_from_content_hashes",
    "validate_child",
    "verify_child",
    "verify_child_full",
    "verify_seal",
]

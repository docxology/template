"""Visual redaction profiles, PDF proof generation, and output verification.

Split into submodules by concern: ``profiles`` (visual styles + variant
matrix), ``proof_renderer``/``proof_pdf`` (development proof PDFs),
``stego_kmyth`` (the sole infrastructure-importing steganography/Kmyth
adapter), and ``verification`` (generated-output checks).
"""

from redacted_report.visuals.profiles import (
    KMYTH_SEAL_ARTIFACTS,
    PDF_BACKGROUND_MODES,
    REDACTION_VISUAL_STYLES,
    SECURITY_METHODS,
    ColorRGB,
    PDFBackgroundProfile,
    RedactionVisualProfile,
    build_visual_variant_matrix,
    expected_dev_variant_filenames,
    expected_visual_variant_ids,
    normalize_pdf_background,
    normalize_redaction_style,
    render_visual_redaction_text,
    style_redaction_decisions,
    visual_redacted_segments,
)
from redacted_report.visuals.proof_pdf import write_dev_variant_pdfs
from redacted_report.visuals.verification import verify_dev_variant_outputs

__all__ = [
    "KMYTH_SEAL_ARTIFACTS",
    "PDF_BACKGROUND_MODES",
    "REDACTION_VISUAL_STYLES",
    "SECURITY_METHODS",
    "ColorRGB",
    "PDFBackgroundProfile",
    "RedactionVisualProfile",
    "build_visual_variant_matrix",
    "expected_dev_variant_filenames",
    "expected_visual_variant_ids",
    "normalize_pdf_background",
    "normalize_redaction_style",
    "render_visual_redaction_text",
    "style_redaction_decisions",
    "verify_dev_variant_outputs",
    "visual_redacted_segments",
    "write_dev_variant_pdfs",
]

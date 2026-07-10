"""Visual redaction style and PDF background profiles (the 4x4 matrix axes).

Single source of truth for the combinatoric dimensions of the proof matrix:
four redaction styles x four page backgrounds. ``visuals`` re-exports every
name here, so external import paths are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from redacted_report.publication_meta import publication_author_and_date  # noqa: F401 - byline API re-export

ColorRGB = tuple[int, int, int]

SECURITY_METHODS = (
    "sha256_sha512_hash_manifest",
    "diagonal_watermark_overlay",
    "footer_provenance_overlay",
    "first_page_invisible_text_overlay",
    "qr_payload_barcode",
    "code128_page_barcode",
    "pdf_info_metadata",
    "xmp_metadata",
    "embedded_stego_manifest_attachment",
)

KMYTH_SEAL_ARTIFACTS = ("hash_manifest", "pdf")


@dataclass(frozen=True)
class RedactionVisualProfile:
    """Visual treatment for redacted spans in proof PDFs."""

    name: str
    label: str
    token: str
    fill_rgb: ColorRGB
    text_rgb: ColorRGB
    border_rgb: ColorRGB


@dataclass(frozen=True)
class PDFBackgroundProfile:
    """Page background treatment for redaction proof PDFs."""

    name: str
    label: str
    fill_rgb: ColorRGB
    text_rgb: ColorRGB
    subdued_text_rgb: ColorRGB
    blur_context: bool = False


REDACTION_VISUAL_STYLES = (
    RedactionVisualProfile("blackout", "Blackout", "[BLACKOUT]", (0, 0, 0), (255, 255, 255), (0, 0, 0)),
    RedactionVisualProfile("whiteout", "Whiteout", "[WHITEOUT]", (255, 255, 255), (110, 110, 110), (170, 170, 170)),
    RedactionVisualProfile("grayout", "Grayout", "[GRAYOUT]", (132, 132, 132), (255, 255, 255), (92, 92, 92)),
    RedactionVisualProfile("blur", "Blur", "[BLUR]", (214, 214, 214), (80, 80, 80), (150, 150, 150)),
)

PDF_BACKGROUND_MODES = (
    PDFBackgroundProfile("white", "White", (255, 255, 255), (18, 18, 18), (120, 120, 120)),
    PDFBackgroundProfile("gray", "Gray", (216, 216, 216), (20, 20, 20), (105, 105, 105)),
    PDFBackgroundProfile("black", "Black", (0, 0, 0), (245, 245, 245), (165, 165, 165)),
    PDFBackgroundProfile("blur", "Blur", (238, 238, 238), (34, 34, 34), (138, 138, 138), blur_context=True),
)

_STYLE_BY_NAME = {profile.name: profile for profile in REDACTION_VISUAL_STYLES}
_BACKGROUND_BY_NAME = {profile.name: profile for profile in PDF_BACKGROUND_MODES}


def normalize_redaction_style(value: str) -> RedactionVisualProfile:
    """Return the configured visual redaction style."""
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _STYLE_BY_NAME:
        expected = ", ".join(_STYLE_BY_NAME)
        raise ValueError(f"unsupported redaction style: {value}; expected one of: {expected}")
    return _STYLE_BY_NAME[key]


def normalize_pdf_background(value: str) -> PDFBackgroundProfile:
    """Return the configured proof-PDF background profile."""
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _BACKGROUND_BY_NAME:
        expected = ", ".join(_BACKGROUND_BY_NAME)
        raise ValueError(f"unsupported PDF background: {value}; expected one of: {expected}")
    return _BACKGROUND_BY_NAME[key]

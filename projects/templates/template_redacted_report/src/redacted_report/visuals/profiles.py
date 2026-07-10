"""Visual redaction profiles and the source-safe variant matrix."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from redacted_report.redaction import (
    RedactionDecision,
    RedactionSegment,
    build_redaction_ledger,
    redact_text,
    segment_hash_manifest,
)


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


def style_redaction_decisions(
    decisions: Sequence[RedactionDecision],
    style: str | RedactionVisualProfile,
) -> list[RedactionDecision]:
    """Return decisions with replacements set for a visual proof style."""
    profile = normalize_redaction_style(style) if isinstance(style, str) else style
    return [
        RedactionDecision(
            segment_id=decision.segment_id,
            start=decision.start,
            end=decision.end,
            reason=decision.reason,
            replacement=profile.token,
        )
        for decision in decisions
    ]


def render_visual_redaction_text(
    text: str,
    decisions: Sequence[RedactionDecision],
    *,
    style: str = "blackout",
) -> str:
    """Render sanitized text using the named visual-redaction token."""
    return str(redact_text(text, style_redaction_decisions(decisions, style)))


def visual_redacted_segments(
    segments: Sequence[RedactionSegment],
    decisions: Sequence[RedactionDecision],
    *,
    style: str = "blackout",
) -> tuple[dict[str, object], ...]:
    """Return source-safe segment records with visual redaction tokens."""
    decision_map = _decisions_by_segment(decisions)
    return tuple(
        {
            "id": segment.id,
            "classification": segment.classification,
            "text": render_visual_redaction_text(segment.text, decision_map.get(segment.id, ()), style=style),
            "source_controls": segment.source_controls,
            "redaction_style": normalize_redaction_style(style).name,
        }
        for segment in segments
    )


def build_visual_variant_matrix(
    segments: Sequence[RedactionSegment],
    decisions: Sequence[RedactionDecision],
    *,
    include_steganography: bool = True,
    include_kmyth: bool = False,
    kmyth_available: bool = False,
    kmyth_summary: str = "not evaluated",
    kmyth_binary_dir: str | Path | None = None,
    pdf_password_configured: bool = False,
) -> dict[str, object]:
    """Build a source-safe manifest for all redaction/background combinations."""
    security_methods = list(SECURITY_METHODS)
    if pdf_password_configured:
        security_methods.append("pdf_password_encryption")
    if include_kmyth:
        security_methods.append("kmyth_tpm_sidecar_sealing_requested")
        if kmyth_available:
            security_methods.append("kmyth_tpm_sidecar_sealing_available")

    variants: list[dict[str, object]] = []
    for background in PDF_BACKGROUND_MODES:
        for style in REDACTION_VISUAL_STYLES:
            variant_id = f"{style.name}_on_{background.name}"
            variants.append(
                {
                    "variant_id": variant_id,
                    "redaction_style": style.name,
                    "pdf_background": background.name,
                    "base_pdf": f"{variant_id}.pdf",
                    "steganography_pdf": f"{variant_id}_steganography.pdf" if include_steganography else "",
                    "hash_manifest": f"{variant_id}.hashes.json" if include_steganography else "",
                    "security_methods": tuple(security_methods) if include_steganography else (),
                    "kmyth_requested": include_kmyth and include_steganography,
                    "kmyth_available": kmyth_available and include_steganography,
                    "kmyth_sidecar_count": 0,
                    "kmyth_pdf_sidecar": "",
                    "kmyth_hash_manifest_sidecar": "",
                }
            )

    return {
        "schema": "template-redacted-report-visual-variant-matrix-v1",
        "variant_count": len(variants),
        "redaction_styles": tuple(profile.name for profile in REDACTION_VISUAL_STYLES),
        "pdf_backgrounds": tuple(profile.name for profile in PDF_BACKGROUND_MODES),
        "include_steganography": include_steganography,
        "include_kmyth": include_kmyth,
        "pdf_password_configured": pdf_password_configured,
        "security_methods": tuple(security_methods) if include_steganography else (),
        "kmyth": {
            "requested": include_kmyth and include_steganography,
            "available": kmyth_available and include_steganography,
            "binary_dir": str(kmyth_binary_dir or ""),
            "summary": kmyth_summary,
            "seal_artifacts": KMYTH_SEAL_ARTIFACTS if include_kmyth and include_steganography else (),
            "sidecars_created": 0,
            "status": "not_requested"
            if not include_kmyth or not include_steganography
            else "available"
            if kmyth_available
            else "unavailable",
        },
        "redaction_ledger": build_redaction_ledger(list(segments), list(decisions)),
        "segment_hash_manifest": segment_hash_manifest(list(segments), list(decisions)),
        "variants": tuple(variants),
    }


def expected_visual_variant_ids() -> tuple[str, ...]:
    """Return the stable redaction/background variant identifiers."""
    return tuple(
        f"{style.name}_on_{background.name}" for background in PDF_BACKGROUND_MODES for style in REDACTION_VISUAL_STYLES
    )


def expected_dev_variant_filenames(
    *,
    include_steganography: bool = True,
    include_hash_manifests: bool = True,
    include_kmyth_sidecars: bool = False,
) -> tuple[str, ...]:
    """Return the stable filenames emitted by the development proof matrix."""
    names: list[str] = []
    for variant_id in expected_visual_variant_ids():
        names.append(f"{variant_id}.pdf")
        if include_steganography:
            names.append(f"{variant_id}_steganography.pdf")
        if include_hash_manifests:
            names.append(f"{variant_id}.hashes.json")
        if include_kmyth_sidecars:
            names.extend((f"{variant_id}.hashes.json.ski", f"{variant_id}_steganography.pdf.ski"))
    names.append("variant_matrix.json")
    return tuple(names)


def _decisions_by_segment(decisions: Sequence[RedactionDecision]) -> dict[str, list[RedactionDecision]]:
    grouped: dict[str, list[RedactionDecision]] = {}
    for decision in decisions:
        grouped.setdefault(decision.segment_id, []).append(decision)
    return grouped

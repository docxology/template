"""Development proof-matrix writer: one PDF per redaction/background variant."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from redacted_report.redaction import RedactionDecision, RedactionSegment
from redacted_report.visuals._hashing import file_sha256 as _file_sha256
from redacted_report.visuals.profiles import (
    PDFBackgroundProfile,
    RedactionVisualProfile,
    build_visual_variant_matrix,
    normalize_pdf_background,
    normalize_redaction_style,
)
from redacted_report.visuals.proof_renderer import _ProofPDFRenderer
from redacted_report.visuals.stego_kmyth import (
    _kmyth_sidecars_for,
    _resolve_kmyth_status,
    _write_steganography_pdf,
)


def write_dev_variant_pdfs(
    segments: Sequence[RedactionSegment],
    decisions: Sequence[RedactionDecision],
    output_dir: Path,
    *,
    title: str = "Redacted Report Visual Proof Matrix",
    include_steganography: bool = True,
    include_kmyth: bool = False,
    deterministic_steganography: bool = True,
    pdf_password: str | None = None,
    kmyth_binary_dir: str | Path | None = None,
    kmyth_required: bool = False,
    kmyth_timeout_seconds: int = 120,
) -> dict[str, object]:  # pragma: no cover - integration-tested by the dev generator
    """Write one proof PDF per visual combination plus optional secure variants."""
    output_dir.mkdir(parents=True, exist_ok=True)
    kmyth_status = _resolve_kmyth_status(
        include_kmyth=include_kmyth and include_steganography,
        binary_dir=kmyth_binary_dir,
        seal_probe_timeout_seconds=min(kmyth_timeout_seconds, 15),
    )
    kmyth_available = bool(kmyth_status["available"])
    matrix = build_visual_variant_matrix(
        segments,
        decisions,
        include_steganography=include_steganography,
        include_kmyth=include_kmyth,
        kmyth_available=kmyth_available,
        kmyth_summary=str(kmyth_status["summary"]),
        kmyth_binary_dir=kmyth_binary_dir,
        pdf_password_configured=bool(pdf_password),
    )
    raw_variants = cast(Sequence[dict[str, object]], matrix["variants"])
    variants = [dict(item) for item in raw_variants]

    previous_deterministic = os.environ.get("STEGANOGRAPHY_DETERMINISTIC")
    if deterministic_steganography:
        os.environ["STEGANOGRAPHY_DETERMINISTIC"] = "1"
    try:
        for variant in variants:
            style = normalize_redaction_style(str(variant["redaction_style"]))
            background = normalize_pdf_background(str(variant["pdf_background"]))
            base_pdf = output_dir / str(variant["base_pdf"])
            _write_visual_pdf(base_pdf, segments, decisions, style, background, title=title)
            variant["base_pdf_bytes"] = base_pdf.stat().st_size
            variant["base_pdf_sha256"] = _file_sha256(base_pdf)

            if include_steganography:
                secure_pdf = output_dir / str(variant["steganography_pdf"])
                _write_steganography_pdf(
                    base_pdf,
                    secure_pdf,
                    style=style,
                    background=background,
                    title=title,
                    include_kmyth=include_kmyth and kmyth_available,
                    pdf_password=pdf_password,
                    kmyth_binary_dir=kmyth_binary_dir,
                    kmyth_required=kmyth_required,
                    kmyth_timeout_seconds=kmyth_timeout_seconds,
                )
                hash_manifest = output_dir / str(variant["hash_manifest"])
                variant["steganography_pdf_bytes"] = secure_pdf.stat().st_size
                variant["steganography_pdf_sha256"] = _file_sha256(secure_pdf)
                variant["hash_manifest_exists"] = hash_manifest.exists()
                if hash_manifest.exists():
                    variant["hash_manifest_sha256"] = _file_sha256(hash_manifest)
                sidecars = _kmyth_sidecars_for(base_pdf, secure_pdf)
                existing_sidecars = {key: path for key, path in sidecars.items() if path.exists()}
                variant["kmyth_requested"] = include_kmyth
                variant["kmyth_available"] = kmyth_available
                variant["kmyth_sidecar_count"] = len(existing_sidecars)
                variant["kmyth_pdf_sidecar"] = existing_sidecars.get("pdf", Path()).name
                variant["kmyth_hash_manifest_sidecar"] = existing_sidecars.get("hash_manifest", Path()).name
    finally:
        if previous_deterministic is None:
            os.environ.pop("STEGANOGRAPHY_DETERMINISTIC", None)
        else:
            os.environ["STEGANOGRAPHY_DETERMINISTIC"] = previous_deterministic

    sidecar_total = 0
    for variant in variants:
        count = variant.get("kmyth_sidecar_count", 0)
        if isinstance(count, int):
            sidecar_total += count
    kmyth_summary = {
        **cast(dict[str, object], matrix["kmyth"]),
        "available": kmyth_available,
        "summary": kmyth_status["summary"],
        "seal_path": kmyth_status["seal_path"],
        "unseal_path": kmyth_status["unseal_path"],
        "tools_runnable": kmyth_status["tools_runnable"],
        "sidecars_created": sidecar_total,
        "required": kmyth_required,
        "status": "not_requested"
        if not include_kmyth or not include_steganography
        else "unavailable"
        if not kmyth_available
        else "sidecars_created"
        if sidecar_total
        else "available_no_sidecars",
    }
    matrix = {**matrix, "kmyth": kmyth_summary, "variants": tuple(variants)}
    matrix_path = output_dir / "variant_matrix.json"
    matrix_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**matrix, "variant_matrix_path": matrix_path.as_posix()}


def _write_visual_pdf(
    output_pdf: Path,
    segments: Sequence[RedactionSegment],
    decisions: Sequence[RedactionDecision],
    style: RedactionVisualProfile,
    background: PDFBackgroundProfile,
    *,
    title: str,
) -> None:  # pragma: no cover - integration-tested by the dev generator
    try:
        from reportlab.lib.colors import Color
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from reportlab.pdfgen import canvas
    except ImportError as exc:  # pragma: no cover - exercised only in minimal environments
        raise RuntimeError("reportlab is required to generate visual redaction proof PDFs") from exc

    renderer = _ProofPDFRenderer(
        output_pdf=output_pdf,
        style=style,
        background=background,
        title=title,
        color_cls=Color,
        pagesize=letter,
        string_width_fn=stringWidth,
        canvas_cls=canvas.Canvas,
    )
    renderer.render(segments, decisions)

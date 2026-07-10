"""Visual redaction profiles and PDF proof generation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from redacted_report.publication_meta import publication_author_and_date  # noqa: F401 - byline API re-export
from redacted_report.redaction import (
    RedactionDecision,
    RedactionSegment,
    build_redaction_ledger,
    redact_text,
    segment_hash_manifest,
)


from redacted_report.profiles import (  # noqa: F401 - canonical matrix-axis re-exports
    KMYTH_SEAL_ARTIFACTS,
    PDF_BACKGROUND_MODES,
    REDACTION_VISUAL_STYLES,
    SECURITY_METHODS,
    ColorRGB,
    PDFBackgroundProfile,
    RedactionVisualProfile,
    _BACKGROUND_BY_NAME,
    _STYLE_BY_NAME,
    normalize_pdf_background,
    normalize_redaction_style,
)


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


def verify_dev_variant_outputs(
    output_dir: Path,
    *,
    render_smoke: bool = False,
    require_kmyth_sidecars: bool = False,
) -> dict[str, object]:
    """Validate generated visual proof PDFs, filenames, hashes, and matrix records."""
    errors: list[str] = []
    warnings: list[str] = []
    output_dir = output_dir.resolve()
    matrix_path = output_dir / "variant_matrix.json"
    if not matrix_path.exists():
        return {
            "valid": False,
            "output_dir": output_dir.as_posix(),
            "errors": (f"missing matrix: {matrix_path.name}",),
            "warnings": (),
        }

    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "valid": False,
            "output_dir": output_dir.as_posix(),
            "errors": (f"invalid matrix JSON: {exc}",),
            "warnings": (),
        }
    if not isinstance(matrix, dict):
        return {
            "valid": False,
            "output_dir": output_dir.as_posix(),
            "errors": ("matrix root is not an object",),
            "warnings": (),
        }

    variants = _matrix_variants(matrix, errors)
    expected_ids = expected_visual_variant_ids()
    expected_id_set = set(expected_ids)
    actual_ids = tuple(str(variant.get("variant_id", "")) for variant in variants)
    actual_id_set = set(actual_ids)

    _expect(matrix.get("schema") == "template-redacted-report-visual-variant-matrix-v1", errors, "bad matrix schema")
    _expect(matrix.get("variant_count") == len(expected_ids), errors, "matrix variant_count is not 16")
    _expect(len(variants) == len(expected_ids), errors, "matrix variants length is not 16")
    _expect(
        tuple(matrix.get("redaction_styles", ())) == tuple(p.name for p in REDACTION_VISUAL_STYLES),
        errors,
        "bad redaction style order",
    )
    _expect(
        tuple(matrix.get("pdf_backgrounds", ())) == tuple(p.name for p in PDF_BACKGROUND_MODES),
        errors,
        "bad PDF background order",
    )
    _expect(actual_id_set == expected_id_set, errors, "matrix variant ids do not match expected 4x4 set")

    discovered_file_names = {path.name for path in output_dir.iterdir() if path.is_file()}
    has_kmyth_sidecars = require_kmyth_sidecars or any(name.endswith(".ski") for name in discovered_file_names)
    expected_file_names = set(expected_dev_variant_filenames(include_kmyth_sidecars=has_kmyth_sidecars))
    unexpected = sorted(discovered_file_names - expected_file_names)
    missing_expected = sorted(expected_file_names - discovered_file_names)
    if unexpected:
        errors.append(f"unexpected files: {', '.join(unexpected)}")
    if missing_expected:
        errors.append(f"missing expected files: {', '.join(missing_expected)}")

    render_tool = shutil.which("pdftoppm") if render_smoke else None
    if render_smoke and not render_tool:
        errors.append("render smoke requested but pdftoppm is not on PATH")

    with tempfile.TemporaryDirectory(prefix="redaction-variant-render-") as tmp_dir:
        render_dir = Path(tmp_dir)
        for variant in variants:
            variant_id = str(variant.get("variant_id", ""))
            redaction_style = str(variant.get("redaction_style", ""))
            pdf_background = str(variant.get("pdf_background", ""))
            expected_id = f"{redaction_style}_on_{pdf_background}"
            _expect(
                variant_id == expected_id,
                errors,
                f"{variant_id or '<missing>'}: variant_id does not match style/background",
            )
            if variant_id not in expected_id_set:
                continue

            base_name = f"{variant_id}.pdf"
            secure_name = f"{variant_id}_steganography.pdf"
            manifest_name = f"{variant_id}.hashes.json"
            _expect(variant.get("base_pdf") == base_name, errors, f"{variant_id}: bad base_pdf filename")
            _expect(
                variant.get("steganography_pdf") == secure_name,
                errors,
                f"{variant_id}: bad steganography_pdf filename",
            )
            _expect(variant.get("hash_manifest") == manifest_name, errors, f"{variant_id}: bad hash_manifest filename")

            base_path = output_dir / base_name
            secure_path = output_dir / secure_name
            manifest_path = output_dir / manifest_name
            _verify_pdf_file(base_path, variant.get("base_pdf_sha256"), variant.get("base_pdf_bytes"), errors)
            _verify_pdf_file(
                secure_path,
                variant.get("steganography_pdf_sha256"),
                variant.get("steganography_pdf_bytes"),
                errors,
            )
            _verify_hash_manifest(manifest_path, base_name, variant.get("hash_manifest_sha256"), base_path, errors)

            if render_tool:
                _render_pdf_smoke(base_path, render_dir, errors)
                _render_pdf_smoke(secure_path, render_dir, errors)

            if require_kmyth_sidecars:
                _verify_kmyth_sidecar(output_dir / f"{variant_id}.hashes.json.ski", errors)
                _verify_kmyth_sidecar(output_dir / f"{variant_id}_steganography.pdf.ski", errors)

    pdf_count = len([name for name in discovered_file_names if name.endswith(".pdf")])
    hash_manifest_count = len([name for name in discovered_file_names if name.endswith(".hashes.json")])
    sidecar_count = len([name for name in discovered_file_names if name.endswith(".ski")])
    kmyth = matrix.get("kmyth", {})
    if isinstance(kmyth, dict) and kmyth.get("requested") and not kmyth.get("available"):
        warnings.append(str(kmyth.get("summary") or "Kmyth requested but unavailable."))

    return {
        "valid": not errors,
        "output_dir": output_dir.as_posix(),
        "variant_count": len(variants),
        "expected_variant_ids": expected_ids,
        "actual_variant_ids": actual_ids,
        "pdf_count": pdf_count,
        "hash_manifest_count": hash_manifest_count,
        "kmyth_sidecar_count": sidecar_count,
        "render_smoke": render_smoke,
        "errors": tuple(errors),
        "warnings": tuple(warnings),
    }


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
) -> dict[str, object]:
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

            if include_steganography:  # pragma: no cover - steganography branch needs the repo-root SteganographyProcessor; exercised by scripts/generate_dev_variants.py, not the per-project unit gate
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
) -> None:
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


# --- Section metadata for the comprehensive proof document ---

_SECTION_MAP: dict[str, tuple[str, str]] = {
    "s1": (
        "Abstract",
        "This exemplar demonstrates a complete disclosure-control pipeline for sanitized public release reports.",
    ),
    "s2": (
        "1. Introduction",
        "The pipeline operates in two layers: text-level disclosure control and visual proof with steganography.",
    ),
    "s3": (
        "2. Fixture: SECRET Segment",
        "Invented high-side content demonstrating source-identity and operational-detail redaction.",
    ),
    "s4": (
        "2.1 SIGINT Collection Platform",
        "Invented SIGINT content demonstrating operational-detail and time-place-selector redaction.",
    ),
    "s5": (
        "2.2 TOP_SECRET//SCI Compartment",
        "Invented compartmented content demonstrating mosaic risk from multi-source combination.",
    ),
    "s6": (
        "3. Sanitized Public Narrative",
        "The public export after redaction, with source-safe ledger and hash manifest.",
    ),
    "s7": ("4. Visual Proof Matrix", "Four redaction styles across four PDF backgrounds yield sixteen variant PDFs."),
    "s8": ("5. Steganography Layer", "Nine security methods post-process each base PDF for provenance and integrity."),
    "s9": ("6. Kmyth TPM Sealing", "TPM2-TSS storage hierarchy sealing with mssim-to-swtpm protocol proxy on macOS."),
    "s10": (
        "6.1 FlushContext Patch",
        "Kmyth-seal patched to flush transient TPM objects between consecutive seal invocations.",
    ),
    "s11": ("7. Release Gate", "Three-role approval gate: originator, classification reviewer, release authority."),
    "s12": ("8. Residual Risk Detection", "Pattern-based detection of common public-release leaks in sanitized text."),
    "s13": ("9. CUI Classification Example", "Controlled Unclassified Information segment above the public ceiling."),
    "s14": (
        "10. Comprehensive Release Packet",
        "Combined export with audit, ledger, hashes, review gate, and paragraph audit table.",
    ),
}


class _ProofPDFRenderer:
    """Multi-page proof PDF renderer with figures, tables, and redaction treatments."""

    def __init__(
        self,
        *,
        output_pdf: Path,
        style: RedactionVisualProfile,
        background: PDFBackgroundProfile,
        title: str,
        color_cls: Any,
        pagesize: tuple[float, float],
        string_width_fn: Any,
        canvas_cls: Any,
    ) -> None:
        self.output_pdf = output_pdf
        self.style = style
        self.background = background
        self.title = title
        self.Color = color_cls
        self.pagesize = pagesize
        self.string_width = string_width_fn
        self.Canvas = canvas_cls
        self.page_width, self.page_height = pagesize
        self.left_margin = 36
        self.right_margin = 36
        self.top_margin = 54
        self.bottom_margin = 54
        self.usable_width = self.page_width - self.left_margin - self.right_margin
        self.doc: Any = None
        self.y = 0.0
        self.page_num = 0

    def _color(self, rgb: ColorRGB) -> Any:
        return self.Color(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)

    def _new_page(self) -> None:
        if self.page_num > 0:
            self._draw_footer()
            self.doc.showPage()
        self.page_num += 1
        self.doc.setFillColor(self._color(self.background.fill_rgb))
        self.doc.rect(0, 0, self.page_width, self.page_height, stroke=0, fill=1)
        self.y = self.page_height - self.top_margin
        self._draw_header()

    def _draw_header(self) -> None:
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 7)
        self.doc.drawString(self.left_margin, self.page_height - 28, self.title)
        self.doc.drawRightString(
            self.page_width - self.right_margin,
            self.page_height - 28,
            f"{self.style.label} / {self.background.label}  |  Page {self.page_num}",
        )
        self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
        self.doc.setLineWidth(0.3)
        self.doc.line(
            self.left_margin,
            self.page_height - 32,
            self.page_width - self.right_margin,
            self.page_height - 32,
        )

    def _draw_footer(self) -> None:
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 6)
        self.doc.drawString(
            self.left_margin,
            18,
            "Dev proof only: invented fixture text, source-safe masks, no operational content.",
        )
        self.doc.drawRightString(
            self.page_width - self.right_margin,
            18,
            f"Style: {self.style.name}  |  BG: {self.background.name}",
        )

    def _ensure_space(self, needed: float) -> None:
        if self.y - needed < self.bottom_margin + 30:
            self._new_page()

    def _draw_title_page(self) -> None:
        self.page_num = 1
        self.doc.setFillColor(self._color(self.background.fill_rgb))
        self.doc.rect(0, 0, self.page_width, self.page_height, stroke=0, fill=1)

        # Title
        self.doc.setFillColor(self._color(self.background.text_rgb))
        self.doc.setFont("Helvetica-Bold", 20)
        self.doc.drawCentredString(self.page_width / 2, self.page_height - 120, self.title)

        # Subtitle
        self.doc.setFont("Helvetica", 11)
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.drawCentredString(
            self.page_width / 2,
            self.page_height - 145,
            "Disclosure Control and Release Audit with TPM-Backed Sealed Sidecars",
        )

        # Author / date — from manuscript/config.yaml (single source of truth)
        author, paper_date = publication_author_and_date()
        self.doc.setFont("Helvetica", 9)
        self.doc.drawCentredString(self.page_width / 2, self.page_height - 175, author)
        self.doc.drawCentredString(self.page_width / 2, self.page_height - 190, paper_date or "")

        # Visual treatment badge
        badge_y = self.page_height - 230
        self.doc.setFillColor(self._color(self.style.fill_rgb))
        self.doc.rect(self.page_width / 2 - 120, badge_y - 12, 240, 24, stroke=1, fill=1)
        self.doc.setFillColor(self._color(self.style.text_rgb))
        self.doc.setFont("Helvetica-Bold", 9)
        self.doc.drawCentredString(self.page_width / 2, badge_y - 3, f"{self.style.label} on {self.background.label}")

        # Abstract preview
        self.y = badge_y - 50
        self._draw_section_header("Abstract")
        abstract_text = (
            "This exemplar demonstrates a complete disclosure-control pipeline for sanitized public release "
            "reports. The methodology combines classification-ceiling enforcement, source-protection validation, "
            "mosaic-risk scoring, and TPM-backed sealed sidecars across a sixteen-variant visual proof matrix. "
            "Four redaction styles are rendered across four PDF backgrounds, yielding sixteen base proof PDFs. "
            "Each receives nine steganographic security methods and optional Kmyth TPM .ski sidecar sealing."
        )
        self._draw_body_text(abstract_text)

        # Architecture overview figure
        self._ensure_space(180)
        self._draw_architecture_diagram()

        self._draw_footer()

    def _draw_section_header(self, text: str) -> None:
        self._ensure_space(30)
        self.y -= 10
        self.doc.setFillColor(self._color(self.background.text_rgb))
        self.doc.setFont("Helvetica-Bold", 12)
        self.doc.drawString(self.left_margin, self.y, text)
        self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
        self.doc.setLineWidth(0.5)
        self.doc.line(self.left_margin, self.y - 4, self.page_width - self.right_margin, self.y - 4)
        self.y -= 18

    def _draw_body_text(self, text: str, font_size: float = 9, indent: float = 0) -> None:
        self.doc.setFont("Helvetica", font_size)
        self.doc.setFillColor(self._color(self.background.text_rgb))
        max_w = self.usable_width - indent
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if self.string_width(test, "Helvetica", font_size) > max_w:
                if self.y - font_size - 4 < self.bottom_margin + 30:
                    self._new_page()
                    self.doc.setFont("Helvetica", font_size)
                    self.doc.setFillColor(self._color(self.background.text_rgb))
                self.doc.drawString(self.left_margin + indent, self.y, line)
                self.y -= font_size + 4
                line = word
            else:
                line = test
        if line:
            if self.y - font_size - 4 < self.bottom_margin + 30:
                self._new_page()
                self.doc.setFont("Helvetica", font_size)
                self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.drawString(self.left_margin + indent, self.y, line)
            self.y -= font_size + 4
        self.y -= 4

    def _draw_segment_content(
        self,
        segment: RedactionSegment,
        decisions: Sequence[RedactionDecision],
    ) -> None:
        self._ensure_space(60)
        # Segment label
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica-Bold", 7)
        label = f"{segment.id} | {segment.classification}"
        if segment.source_controls:
            label += f" | Controls: {', '.join(segment.source_controls)}"
        self.doc.drawString(self.left_margin, self.y, label)
        self.y -= 12

        # Segment text with redaction boxes
        self.y = _draw_segment(
            self.doc,
            segment,
            decisions,
            x=self.left_margin,
            y=self.y,
            max_width=self.usable_width,
            style=self.style,
            background=self.background,
            color_factory=self._color,
            string_width=self.string_width,
        )
        self.y -= 14

    def _draw_architecture_diagram(self) -> None:
        self._ensure_space(160)
        self._draw_section_header("Pipeline Architecture")
        cx = self.page_width / 2
        box_w = 160
        box_h = 28

        # Layer 1
        y1 = self.y - 10
        self.doc.setFillColor(self._color((30, 80, 120)))
        self.doc.rect(cx - box_w / 2, y1 - box_h, box_w, box_h, stroke=0, fill=1)
        self.doc.setFillColor(self._color((255, 255, 255)))
        self.doc.setFont("Helvetica-Bold", 8)
        self.doc.drawCentredString(cx, y1 - 18, "Layer 1: Disclosure Control")

        # Arrow
        self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
        self.doc.setLineWidth(1)
        self.doc.line(cx, y1 - box_h - 2, cx, y1 - box_h - 14)
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 6)
        self.doc.drawCentredString(cx + 20, y1 - box_h - 10, "sanitized text")

        # Layer 2
        y2 = y1 - box_h - 18
        self.doc.setFillColor(self._color((60, 100, 50)))
        self.doc.rect(cx - box_w / 2, y2 - box_h, box_w, box_h, stroke=0, fill=1)
        self.doc.setFillColor(self._color((255, 255, 255)))
        self.doc.setFont("Helvetica-Bold", 8)
        self.doc.drawCentredString(cx, y2 - 18, "Layer 2: Visual + Steganography")

        # Arrow
        self.doc.line(cx, y2 - box_h - 2, cx, y2 - box_h - 14)
        self.doc.drawCentredString(cx + 20, y2 - box_h - 10, "proof PDFs")

        # Layer 3
        y3 = y2 - box_h - 18
        self.doc.setFillColor(self._color((120, 60, 30)))
        self.doc.rect(cx - box_w / 2, y3 - box_h, box_w, box_h, stroke=0, fill=1)
        self.doc.setFillColor(self._color((255, 255, 255)))
        self.doc.setFont("Helvetica-Bold", 8)
        self.doc.drawCentredString(cx, y3 - 18, "Layer 3: Kmyth TPM Sealing")

        # Side outputs
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 6)
        outputs = [
            ("Redaction Ledger", cx - box_w / 2 - 90, y1 - 14),
            ("Hash Manifest", cx + box_w / 2 + 10, y2 - 14),
            (".ski Sidecars", cx + box_w / 2 + 10, y3 - 14),
        ]
        for label, lx, ly in outputs:
            self.doc.drawString(lx, ly, label)
            self.doc.line(lx + 60, ly + 3, lx + 70 if lx < cx else lx - 10, ly + 3)

        self.y = y3 - box_h - 20

    def _draw_security_methods_table(self) -> None:
        self._ensure_space(180)
        self._draw_section_header("Steganographic Security Methods")

        methods = [
            ("SHA-256/SHA-512 Hash Manifest", "Cryptographic integrity verification"),
            ("Diagonal Watermark Overlay", "Visible provenance stamp"),
            ("Footer Provenance Overlay", "Page-level release metadata"),
            ("First-Page Invisible Text", "Hidden identification marker"),
            ("QR Payload Barcode", "Machine-readable provenance"),
            ("Code128 Page Barcode", "Per-page tracking barcode"),
            ("PDF Info Metadata", "Document-level metadata injection"),
            ("XMP Metadata", "Standards-compliant metadata embedding"),
            ("Embedded Stego Manifest", "Self-contained provenance archive"),
            ("Kmyth TPM .ski Sidecar", "Hardware-backed sealed object"),
            ("PDF Password Encryption", "AES-256 protection (optional)"),
        ]

        col_w = self.usable_width
        row_h = 16
        for i, (name, desc) in enumerate(methods):
            self._ensure_space(row_h + 4)
            if i % 2 == 0:
                self.doc.setFillColor(self._color(self.background.fill_rgb))
                self.doc.rect(self.left_margin, self.y - row_h + 2, col_w, row_h, stroke=0, fill=1)
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawString(self.left_margin + 4, self.y - 6, name)
            self.doc.setFont("Helvetica", 7)
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.drawString(self.left_margin + 200, self.y - 6, desc)
            self.y -= row_h

        self.y -= 10

    def _draw_kmyth_flow_diagram(self) -> None:
        self._ensure_space(140)
        self._draw_section_header("Kmyth TPM Sealing Flow (macOS)")

        boxes = [
            ("kmyth-seal", 60, self._color((40, 80, 120))),
            ("mssim TCTI", 170, self._color((60, 100, 50))),
            ("Proxy", 280, self._color((120, 80, 30))),
            ("swtpm", 390, self._color((120, 60, 30))),
        ]
        box_w = 90
        box_h = 24
        flow_y = self.y - 20

        for label, bx, bc in boxes:
            self.doc.setFillColor(bc)
            self.doc.rect(bx, flow_y - box_h, box_w, box_h, stroke=0, fill=1)
            self.doc.setFillColor(self._color((255, 255, 255)))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawCentredString(bx + box_w / 2, flow_y - 15, label)
            if bx < 390:
                self.doc.setStrokeColor(self._color(self.background.subdued_text_rgb))
                self.doc.setLineWidth(1)
                self.doc.line(bx + box_w, flow_y - box_h / 2, bx + box_w + 10, flow_y - box_h / 2)

        # Protocol annotations
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica", 5.5)
        annotations = [
            (155, "TSS2 API calls"),
            (265, "mssim wire protocol"),
            (375, "swtpm CMD_* protocol"),
        ]
        for ax, text in annotations:
            self.doc.drawCentredString(ax, flow_y - box_h - 8, text)

        # TPM details
        self.y = flow_y - box_h - 20
        details = [
            "Control channel: POWER_ON(1) -> success, NV_ON(11) -> success, TPM_SESSION_END(20) -> close",
            "Data channel: 4B cmd_type(8) + 1B locality + 4B tpm_size | raw TPM command -> swtpm",
            "FlushContext patch: Tss2_Sys_FlushContext(storageKey) before free_tpm2_resources",
            "Result: 32 .ski sidecars sealed across 16 variants without slot exhaustion",
        ]
        for detail in details:
            self._draw_body_text(detail, font_size=7, indent=10)

    def _draw_matrix_grid(self) -> None:
        self._ensure_space(160)
        self._draw_section_header("Visual Proof Matrix (4x4)")

        styles = [p.name for p in REDACTION_VISUAL_STYLES]
        backgrounds = [p.name for p in PDF_BACKGROUND_MODES]
        cell_w = 80
        cell_h = 40
        grid_x = self.left_margin + 30
        grid_y = self.y - 30

        # Column headers
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica-Bold", 6)
        for j, bg in enumerate(backgrounds):
            self.doc.drawCentredString(grid_x + j * cell_w + cell_w / 2, grid_y + 6, bg)

        # Row headers and cells
        for i, st in enumerate(styles):
            ry = grid_y - (i + 1) * cell_h
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.setFont("Helvetica-Bold", 6)
            self.doc.drawRightString(grid_x - 4, ry + cell_h / 2 - 2, st)

            for j, bg in enumerate(backgrounds):
                cx = grid_x + j * cell_w
                # Draw cell with style color
                profile = _STYLE_BY_NAME[st]
                bg_profile = _BACKGROUND_BY_NAME[bg]
                self.doc.setFillColor(self._color(bg_profile.fill_rgb))
                self.doc.rect(cx, ry, cell_w, cell_h, stroke=1, fill=1)
                # Draw redaction token sample
                self.doc.setFillColor(self._color(profile.fill_rgb))
                self.doc.rect(cx + 8, ry + 8, 30, 10, stroke=1, fill=1)
                self.doc.setFillColor(self._color(profile.text_rgb))
                self.doc.setFont("Helvetica-Bold", 4)
                self.doc.drawCentredString(cx + 23, ry + 10, profile.token)
                # Label
                self.doc.setFillColor(self._color(bg_profile.subdued_text_rgb))
                self.doc.setFont("Helvetica", 5)
                self.doc.drawCentredString(cx + cell_w / 2, ry + 4, f"{st}_{bg}")

        self.y = grid_y - len(styles) * cell_h - 20

    def _draw_classification_chart(self) -> None:
        self._ensure_space(120)
        self._draw_section_header("Classification Taxonomy")

        levels = [
            ("UNCLASSIFIED", 0, (100, 160, 100)),
            ("CUI", 1, (140, 180, 80)),
            ("CONFIDENTIAL", 2, (200, 180, 60)),
            ("SECRET", 3, (220, 140, 40)),
            ("TOP_SECRET", 4, (200, 80, 40)),
            ("TOP_SECRET_SCI", 5, (160, 40, 40)),
        ]
        bar_w = 70
        bar_h_base = 12
        chart_x = self.left_margin + 100
        chart_y = self.y - 10

        for i, (name, rank, rgb) in enumerate(levels):
            by = chart_y - i * (bar_h_base + 6)
            h = bar_h_base + rank * 4
            self.doc.setFillColor(self._color(rgb))
            self.doc.rect(chart_x, by - h, bar_w, h, stroke=0, fill=1)
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawRightString(chart_x - 4, by - h / 2 - 2, name.replace("_", " "))
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.setFont("Helvetica", 5)
            self.doc.drawString(chart_x + bar_w + 4, by - h / 2 - 2, f"rank={rank}")

        # Public ceiling line
        ceiling_y = chart_y - 0 * (bar_h_base + 6) + bar_h_base
        self.doc.setStrokeColor(self._color((200, 0, 0)))
        self.doc.setLineWidth(1.5)
        self.doc.setDash(2, 2)
        self.doc.line(chart_x - 80, ceiling_y, chart_x + bar_w + 40, ceiling_y)
        self.doc.setDash()
        self.doc.setFillColor(self._color((200, 0, 0)))
        self.doc.setFont("Helvetica-Bold", 6)
        self.doc.drawString(chart_x + bar_w + 44, ceiling_y - 2, "Public Ceiling")

        self.y = chart_y - len(levels) * (bar_h_base + 6) - 20

    def _draw_ledger_table(self, segments: Sequence[RedactionSegment], decisions: Sequence[RedactionDecision]) -> None:
        self._ensure_space(120)
        self._draw_section_header("Redaction Ledger Summary (Source-Safe)")

        ledger = build_redaction_ledger(list(segments), list(decisions))
        col_names = ["Decision ID", "Segment", "Span", "Reason", "Valid"]
        col_widths = [80, 50, 60, 90, 40]
        row_h = 14
        table_x = self.left_margin

        # Header row
        self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
        self.doc.setFont("Helvetica-Bold", 6)
        cx = table_x
        for i, col in enumerate(col_names):
            self.doc.drawString(cx + 2, self.y - 8, col)
            cx += col_widths[i]
        self.y -= row_h

        for row in ledger[:12]:
            self._ensure_space(row_h + 4)
            cx = table_x
            values = [
                str(row.get("decision_id", ""))[:14],
                str(row.get("segment_id", "")),
                f"{row.get('start', '')}-{row.get('end', '')}",
                str(row.get("reason", "")),
                "Y" if row.get("valid_span") else "N",
            ]
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica", 6)
            for i, val in enumerate(values):
                self.doc.drawString(cx + 2, self.y - 8, val)
                cx += col_widths[i]
            self.y -= row_h

        self.y -= 10

    def _draw_review_gate(self, decisions: Sequence[RedactionDecision]) -> None:
        self._ensure_space(80)
        self._draw_section_header("Release Gate Status")

        gate_info = [
            ("Policy", "intelligence_release_review"),
            ("Required Roles", "originator, classification_reviewer, release_authority"),
            ("Minimum Approvals", "3"),
            ("Mosaic Threshold", "0.30"),
            ("Block Warnings", "True"),
            ("Reviewers", "originator-a (approve), classification-reviewer (approve), release-board (approve)"),
            ("Gate Status", "APPROVED"),
        ]
        for label, value in gate_info:
            self._ensure_space(16)
            self.doc.setFillColor(self._color(self.background.subdued_text_rgb))
            self.doc.setFont("Helvetica-Bold", 7)
            self.doc.drawString(self.left_margin, self.y - 8, label)
            self.doc.setFillColor(self._color(self.background.text_rgb))
            self.doc.setFont("Helvetica", 7)
            self.doc.drawString(self.left_margin + 120, self.y - 8, value)
            self.y -= 14

        self.y -= 10

    def render(self, segments: Sequence[RedactionSegment], decisions: Sequence[RedactionDecision]) -> None:
        # invariant=1 pins CreationDate + /ID: the matrix's sha256 bindings need byte-reproducible runs.
        self.doc = self.Canvas(str(self.output_pdf), pagesize=self.pagesize, pageCompression=1, invariant=1)

        # Title page
        self._draw_title_page()

        # Content pages
        self._new_page()
        decision_map = _decisions_by_segment(decisions)

        for segment in segments:
            section_info = _SECTION_MAP.get(segment.id)
            if section_info:
                header, intro = section_info
                self._draw_section_header(header)
                if intro:
                    self._draw_body_text(intro, font_size=8)
                self._draw_segment_content(segment, decision_map.get(segment.id, ()))

            # Insert figures at key points
            if segment.id == "s5":
                self._draw_classification_chart()
            elif segment.id == "s7":
                self._draw_matrix_grid()
            elif segment.id == "s8":
                self._draw_security_methods_table()
            elif segment.id == "s9":
                self._draw_kmyth_flow_diagram()
            elif segment.id == "s11":
                self._draw_review_gate(decisions)
            elif segment.id == "s14":
                self._draw_ledger_table(segments, decisions)

        # Closing
        self._ensure_space(40)
        self._draw_section_header("Conclusion")
        self._draw_body_text(
            "This exemplar confirms that disclosure control can be decomposed into orthogonal concerns: "
            "text-level audit, visual presentation, steganographic provenance, and hardware-backed sealing. "
            "Each concern is independently configurable and verifiable. The sixteen-variant visual proof "
            "matrix, nine steganographic security methods, and thirty-two Kmyth TPM .ski sidecars demonstrate "
            "a reproducible, source-safe, and auditable release pipeline.",
            font_size=9,
        )

        self._draw_footer()
        self.doc.save()


def _draw_segment(
    doc: Any,
    segment: RedactionSegment,
    decisions: Sequence[RedactionDecision],
    *,
    x: float,
    y: float,
    max_width: float,
    style: RedactionVisualProfile,
    background: PDFBackgroundProfile,
    color_factory: Any,
    string_width: Any,
) -> float:
    redact_text(segment.text, list(decisions))
    cursor_x = x
    cursor_y = y
    font_name = "Helvetica"
    font_size = 10
    line_height = 14
    doc.setFont(font_name, font_size)
    for kind, value in _redaction_parts(segment.text, decisions):
        if kind == "text":
            for token in _split_keep_spaces(value):
                token_width = string_width(token, font_name, font_size)
                if cursor_x + token_width > x + max_width:
                    cursor_x = x
                    cursor_y -= line_height
                if background.blur_context and token.strip():
                    _draw_blurred_text(doc, token, cursor_x, cursor_y, background, color_factory)
                else:
                    doc.setFillColor(color_factory(background.text_rgb))
                    doc.drawString(cursor_x, cursor_y, token)
                cursor_x += token_width
        else:
            box_width = max(58, min(150, len(value) * 5.2))
            if cursor_x + box_width > x + max_width:
                cursor_x = x
                cursor_y -= line_height
            _draw_redaction_box(doc, cursor_x, cursor_y - 2, box_width, style, color_factory)
            cursor_x += box_width + 5
    return cursor_y - line_height


def _draw_redaction_box(
    doc: Any,
    x: float,
    y: float,
    width: float,
    style: RedactionVisualProfile,
    color_factory: Any,
) -> None:
    doc.setStrokeColor(color_factory(style.border_rgb))
    doc.setFillColor(color_factory(style.fill_rgb))
    doc.rect(x, y - 2, width, 11, stroke=1, fill=1)
    doc.setFillColor(color_factory(style.text_rgb))
    doc.setFont("Helvetica-Bold", 5.5)
    if style.name == "blur":
        for offset in (0, 0.8, -0.8):
            doc.drawCentredString(x + width / 2 + offset, y + 1, style.token)
    elif style.name != "whiteout":
        doc.drawCentredString(x + width / 2, y + 1, style.token)


def _draw_blurred_text(
    doc: Any,
    text: str,
    x: float,
    y: float,
    background: PDFBackgroundProfile,
    color_factory: Any,
) -> None:
    doc.setFillColor(color_factory(background.subdued_text_rgb))
    doc.setFont("Helvetica", 10)
    for dx, dy in ((-0.6, 0), (0.6, 0), (0, 0.6), (0, -0.6)):
        doc.drawString(x + dx, y + dy, text)


def _write_steganography_pdf(
    base_pdf: Path,
    secure_pdf: Path,
    *,
    style: RedactionVisualProfile,
    background: PDFBackgroundProfile,
    title: str,
    include_kmyth: bool,
    pdf_password: str | None,
    kmyth_binary_dir: str | Path | None,
    kmyth_required: bool,
    kmyth_timeout_seconds: int,
) -> None:  # pragma: no cover - needs the repo-root SteganographyProcessor; exercised by scripts/generate_dev_variants.py, not the per-project unit gate
    from infrastructure.steganography import SteganographyConfig, SteganographyProcessor

    for sidecar in _kmyth_sidecars_for(base_pdf, secure_pdf).values():
        sidecar.unlink(missing_ok=True)

    config = SteganographyConfig(
        enabled=True,
        overlays_enabled=True,
        barcodes_enabled=True,
        metadata_enabled=True,
        hashing_enabled=True,
        encryption_enabled=bool(pdf_password),
        pdf_password=pdf_password,
        manifest_enabled=True,
        overlay_text=f"{style.label.upper()} {background.label.upper()} RELEASE PROOF",
        overlay_opacity=0.045,
        overlay_color_rgb=(92, 92, 92),
        overlay_font_size=42,
        output_suffix="_steganography",
        kmyth_enabled=include_kmyth,
        kmyth_required=kmyth_required,
        kmyth_binary_dir=str(kmyth_binary_dir) if kmyth_binary_dir else None,
        kmyth_seal_artifacts=list(KMYTH_SEAL_ARTIFACTS),
        kmyth_timeout_seconds=kmyth_timeout_seconds,
    )
    SteganographyProcessor(config).process(
        base_pdf,
        output_pdf=secure_pdf,
        title=title,
        authors=[publication_author_and_date()[0]],
        keywords=["redaction", "visual-proof", style.name, background.name],
    )


def _resolve_kmyth_status(
    *,
    include_kmyth: bool,
    binary_dir: str | Path | None,
    seal_probe_timeout_seconds: int,
) -> dict[str, object]:
    if not include_kmyth:
        return {
            "requested": False,
            "available": False,
            "binary_dir": str(binary_dir or ""),
            "seal_path": "",
            "unseal_path": "",
            "tools_runnable": False,
            "summary": "Kmyth not requested.",
        }

    from infrastructure.steganography import validate_kmyth_installation

    availability = validate_kmyth_installation(binary_dir=binary_dir)
    if not availability.available or availability.seal_path is None or availability.unseal_path is None:
        return {
            "requested": True,
            "available": False,
            "binary_dir": str(binary_dir or ""),
            "seal_path": str(availability.seal_path or ""),
            "unseal_path": str(availability.unseal_path or ""),
            "tools_runnable": False,
            "summary": availability.summary(),
        }

    help_errors = tuple(
        error
        for error in (
            _kmyth_help_error(availability.seal_path),
            _kmyth_help_error(availability.unseal_path),
        )
        if error
    )
    if help_errors:
        return {
            "requested": True,
            "available": False,
            "binary_dir": str(binary_dir or ""),
            "seal_path": str(availability.seal_path),
            "unseal_path": str(availability.unseal_path),
            "tools_runnable": False,
            "summary": "Kmyth tools found but not runnable: " + "; ".join(help_errors),
        }

    probe_error = _kmyth_seal_probe_error(availability.seal_path, timeout_seconds=seal_probe_timeout_seconds)
    if probe_error:
        return {
            "requested": True,
            "available": False,
            "binary_dir": str(binary_dir or ""),
            "seal_path": str(availability.seal_path),
            "unseal_path": str(availability.unseal_path),
            "tools_runnable": True,
            "summary": "Kmyth tools runnable, but TPM seal probe failed: " + probe_error,
        }

    return {
        "requested": True,
        "available": True,
        "binary_dir": str(binary_dir or ""),
        "seal_path": str(availability.seal_path),
        "unseal_path": str(availability.unseal_path),
        "tools_runnable": True,
        "summary": availability.summary(),
    }


def _kmyth_help_error(tool_path: Path) -> str:
    try:
        result = subprocess.run(  # noqa: S603 - fixed executable path, shell=False
            [str(tool_path), "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"{tool_path.name}: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit status {result.returncode}"
        return f"{tool_path.name}: {detail}"
    return ""


def _kmyth_seal_probe_error(tool_path: Path, *, timeout_seconds: int) -> str:
    with tempfile.TemporaryDirectory(prefix="redaction-kmyth-probe-") as tmp_dir:
        input_path = Path(tmp_dir) / "probe.txt"
        output_path = Path(tmp_dir) / "probe.txt.ski"
        input_path.write_text("template_redacted_report kmyth probe\n", encoding="utf-8")
        try:
            result = subprocess.run(  # noqa: S603 - fixed executable path, shell=False
                [str(tool_path), "--input", str(input_path), "--output", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return str(exc)
        if result.returncode != 0:
            return result.stderr.strip() or result.stdout.strip() or f"exit status {result.returncode}"
        if not output_path.exists():
            return f"{tool_path.name} exited successfully but did not write a sidecar"
    return ""


def _kmyth_sidecars_for(base_pdf: Path, secure_pdf: Path) -> dict[str, Path]:
    return {
        "hash_manifest": Path(str(base_pdf.with_suffix(".hashes.json")) + ".ski"),
        "pdf": Path(str(secure_pdf) + ".ski"),
    }


def _redaction_parts(
    text: str,
    decisions: Sequence[RedactionDecision],
) -> tuple[tuple[str, str], ...]:
    parts: list[tuple[str, str]] = []
    cursor = 0
    for decision in sorted(decisions, key=lambda item: item.start):
        if cursor < decision.start:
            parts.append(("text", text[cursor : decision.start]))
        parts.append(("redaction", text[decision.start : decision.end]))
        cursor = decision.end
    if cursor < len(text):
        parts.append(("text", text[cursor:]))
    return tuple(parts)


def _split_keep_spaces(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for word in text.split(" "):
        if not tokens:
            tokens.append(word)
        else:
            tokens.append(" " + word)
    return tuple(token for token in tokens if token)


def _decisions_by_segment(decisions: Sequence[RedactionDecision]) -> dict[str, list[RedactionDecision]]:
    grouped: dict[str, list[RedactionDecision]] = {}
    for decision in decisions:
        grouped.setdefault(decision.segment_id, []).append(decision)
    return grouped


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matrix_variants(matrix: object, errors: list[str]) -> list[dict[str, object]]:
    if not isinstance(matrix, dict):
        errors.append("matrix root is not an object")
        return []
    variants = matrix.get("variants")
    if not isinstance(variants, list):
        errors.append("matrix variants is not a list")
        return []
    typed_variants: list[dict[str, object]] = []
    for index, variant in enumerate(variants):
        if isinstance(variant, dict):
            typed_variants.append(cast(dict[str, object], variant))
        else:
            errors.append(f"matrix variants[{index}] is not an object")
    return typed_variants


def _expect(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _verify_pdf_file(path: Path, expected_sha256: object, expected_bytes: object, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing PDF: {path.name}")
        return
    if path.stat().st_size <= 0:
        errors.append(f"empty PDF: {path.name}")
        return
    if isinstance(expected_bytes, int) and path.stat().st_size != expected_bytes:
        errors.append(f"{path.name}: byte size differs from matrix")
    if isinstance(expected_sha256, str) and _file_sha256(path) != expected_sha256:
        errors.append(f"{path.name}: sha256 differs from matrix")
    try:
        page_count = _pdf_page_count(path)
    except Exception as exc:  # noqa: BLE001 - verifier safety net: pypdf raises several parse-specific exceptions; every failure is recorded as a finding, never swallowed
        errors.append(f"{path.name}: PDF readability check failed: {exc}")
        return
    if page_count < 1:
        errors.append(f"{path.name}: no readable PDF pages")


def _verify_hash_manifest(
    path: Path,
    expected_source_file: str,
    expected_manifest_sha256: object,
    source_pdf: Path,
    errors: list[str],
) -> None:
    if not path.exists():
        errors.append(f"missing hash manifest: {path.name}")
        return
    if isinstance(expected_manifest_sha256, str) and _file_sha256(path) != expected_manifest_sha256:
        errors.append(f"{path.name}: sha256 differs from matrix")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: manifest root is not an object")
        return
    if payload.get("source_file") != expected_source_file:
        errors.append(f"{path.name}: source_file does not match {expected_source_file}")
    hashes = payload.get("hashes")
    if not isinstance(hashes, dict):
        errors.append(f"{path.name}: hashes is not an object")
        return
    source_sha256 = hashes.get("sha256")
    if source_pdf.exists() and isinstance(source_sha256, str) and source_sha256 != _file_sha256(source_pdf):
        errors.append(f"{path.name}: sha256 does not match source PDF")
    source_sha512 = hashes.get("sha512")
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        errors.append(f"{path.name}: missing sha256 digest")
    if not isinstance(source_sha512, str) or len(source_sha512) != 128:
        errors.append(f"{path.name}: missing sha512 digest")


def _verify_kmyth_sidecar(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing Kmyth sidecar: {path.name}")
    elif path.stat().st_size <= 0:
        errors.append(f"empty Kmyth sidecar: {path.name}")


def _pdf_page_count(path: Path) -> int:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency is declared by the repo
        raise RuntimeError("pypdf is required to verify development variant PDFs") from exc
    reader = PdfReader(str(path))
    return len(reader.pages)


def _render_pdf_smoke(path: Path, render_dir: Path, errors: list[str]) -> None:
    output_prefix = render_dir / path.stem
    try:
        result = subprocess.run(  # noqa: S603 - fixed tool name, shell=False
            ["pdftoppm", "-png", "-f", "1", "-singlefile", str(path), str(output_prefix)],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"{path.name}: render smoke failed: {exc}")
        return
    rendered = output_prefix.with_suffix(".png")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit status {result.returncode}"
        errors.append(f"{path.name}: render smoke failed: {detail}")
    elif not rendered.exists() or rendered.stat().st_size <= 0:
        errors.append(f"{path.name}: render smoke produced no PNG")

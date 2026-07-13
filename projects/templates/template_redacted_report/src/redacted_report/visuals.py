"""Visual redaction profiles and PDF proof generation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from infrastructure.steganography import KmythAvailability

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
from redacted_report._proof_renderer import (  # noqa: F401 - compatibility re-exports
    _SECTION_MAP,
    _ProofPDFRenderer,
    _decisions_by_segment,
    _draw_blurred_text,
    _draw_redaction_box,
    _draw_segment,
    _redaction_parts,
    _split_keep_spaces,
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
    page_counter: Callable[[Path], int] | None = None,
    executable_resolver: Callable[[str], str | None] = shutil.which,
) -> dict[str, object]:
    """Validate generated visual proof PDFs, filenames, hashes, and matrix records."""
    errors: list[str] = []
    warnings: list[str] = []
    count_pages = page_counter or _pdf_page_count
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

    render_tool = executable_resolver("pdftoppm") if render_smoke else None
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
            _verify_pdf_file(
                base_path,
                variant.get("base_pdf_sha256"),
                variant.get("base_pdf_bytes"),
                errors,
                page_counter=count_pages,
            )
            _verify_pdf_file(
                secure_path,
                variant.get("steganography_pdf_sha256"),
                variant.get("steganography_pdf_bytes"),
                errors,
                page_counter=count_pages,
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
    installation_validator: Callable[..., KmythAvailability] | None = None,
    help_checker: Callable[[Path], str] | None = None,
    seal_probe: Callable[..., str] | None = None,
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

    if installation_validator is None:
        from infrastructure.steganography import validate_kmyth_installation

        installation_validator = validate_kmyth_installation
    check_help = help_checker or _kmyth_help_error
    probe_seal = seal_probe or _kmyth_seal_probe_error
    availability = installation_validator(binary_dir=binary_dir)
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
            check_help(availability.seal_path),
            check_help(availability.unseal_path),
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

    probe_error = probe_seal(availability.seal_path, timeout_seconds=seal_probe_timeout_seconds)
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


def _kmyth_help_error(
    tool_path: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    try:
        result = runner(  # noqa: S603 - fixed executable path, shell=False
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


def _kmyth_seal_probe_error(
    tool_path: Path,
    *,
    timeout_seconds: int,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    with tempfile.TemporaryDirectory(prefix="redaction-kmyth-probe-") as tmp_dir:
        input_path = Path(tmp_dir) / "probe.txt"
        output_path = Path(tmp_dir) / "probe.txt.ski"
        input_path.write_text("template_redacted_report kmyth probe\n", encoding="utf-8")
        try:
            result = runner(  # noqa: S603 - fixed executable path, shell=False
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


def _verify_pdf_file(
    path: Path,
    expected_sha256: object,
    expected_bytes: object,
    errors: list[str],
    *,
    page_counter: Callable[[Path], int] | None = None,
) -> None:
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
        page_count = (page_counter or _pdf_page_count)(path)
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

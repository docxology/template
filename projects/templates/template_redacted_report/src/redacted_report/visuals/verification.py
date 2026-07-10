"""Validation of generated proof-matrix outputs: files, hashes, matrix records."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import cast

from redacted_report.visuals._hashing import file_sha256 as _file_sha256
from redacted_report.visuals.profiles import (
    PDF_BACKGROUND_MODES,
    REDACTION_VISUAL_STYLES,
    expected_dev_variant_filenames,
    expected_visual_variant_ids,
)


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

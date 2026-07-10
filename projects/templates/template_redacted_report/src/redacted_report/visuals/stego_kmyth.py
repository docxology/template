"""Steganography and Kmyth TPM adapter.

Per ``manuscript/layer_contract.yaml`` this is the only ``src/`` module allowed
to import ``infrastructure`` (the monorepo steganography verifier).
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from redacted_report.visuals.profiles import (
    KMYTH_SEAL_ARTIFACTS,
    PDFBackgroundProfile,
    RedactionVisualProfile,
)


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
) -> None:  # pragma: no cover - integration-tested by the dev generator
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
        authors=["Research Template Author"],
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

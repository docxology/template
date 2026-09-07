"""Optional Kmyth probing used by the redacted-report visual writer."""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.steganography import KmythAvailability


def resolve_kmyth_status(
    *,
    include_kmyth: bool,
    binary_dir: str | Path | None,
    seal_probe_timeout_seconds: int,
    installation_validator: Callable[..., KmythAvailability] | None = None,
    help_checker: Callable[[Path], str] | None = None,
    seal_probe: Callable[..., str] | None = None,
) -> dict[str, object]:
    """Return an explicit available/unavailable status for optional Kmyth."""
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
    check_help = help_checker or kmyth_help_error
    probe_seal = seal_probe or kmyth_seal_probe_error
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


def kmyth_help_error(
    tool_path: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """Return a diagnostic when an optional Kmyth binary cannot show help."""
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


def kmyth_seal_probe_error(
    tool_path: Path,
    *,
    timeout_seconds: int,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """Return a diagnostic when a Kmyth seal probe cannot create a sidecar."""
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


# Keep the private helper names importable from ``redacted_report.visuals`` for
# existing project-local tests and scripts while the implementation lives in a
# focused optional-tool module.
_resolve_kmyth_status = resolve_kmyth_status
_kmyth_help_error = kmyth_help_error
_kmyth_seal_probe_error = kmyth_seal_probe_error

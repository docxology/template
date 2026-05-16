"""Steganography configuration.

Defines SteganographyConfig — a dataclass controlling which steganographic
techniques are applied when producing the secure PDF variant.

Also exposes :func:`resolve_build_timestamp`, the single source of truth for
the build-timestamp embedded in overlays, barcodes, metadata, XMP packets,
and hash manifests. When ``STEGANOGRAPHY_DETERMINISTIC=1`` is set (or the
``deterministic=True`` keyword is passed), the timestamp is pinned to the
``%cI`` (strict ISO-8601) of the latest ``HEAD`` commit so two consecutive
secure-pipeline runs produce byte-identical PDFs.
"""

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


__all__ = [
    "DocumentMetadata",
    "SteganographyConfig",
    "resolve_build_timestamp",
]


# ── Deterministic build-timestamp resolution ──────────────────────────────


def _wallclock_iso8601_z() -> str:
    """Return the current UTC time as a strict-ISO8601 ``Z`` string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_build_timestamp(
    *,
    deterministic: bool | None = None,
    repo_root: Path | None = None,
) -> str:
    """Return an ISO-8601 build timestamp.

    When ``deterministic`` is ``True`` (or the environment variable
    ``STEGANOGRAPHY_DETERMINISTIC`` is set to ``1`` / ``true`` / ``yes`` and
    ``deterministic`` is left ``None``), the timestamp is read from
    ``git log -1 --format=%cI`` in *repo_root* — yielding a value that is
    stable across runs as long as ``HEAD`` does not move. Otherwise the
    current wall-clock time in UTC ISO-8601 (``Z`` suffix) is returned.

    If deterministic mode is requested but ``git`` is not on PATH, returns
    a non-zero exit, or *repo_root* is not a git checkout, the function
    falls back to the wall-clock value and emits a single
    :func:`logger.warning` so the audit trail records the degradation.

    Args:
        deterministic: Tri-state flag.

            * ``True``  — force deterministic mode.
            * ``False`` — force wall-clock mode (env var ignored).
            * ``None``  — default; consult ``STEGANOGRAPHY_DETERMINISTIC``.
        repo_root: Repository root to query. Defaults to
            :func:`pathlib.Path.cwd` when omitted.

    Returns:
        ISO-8601 timestamp string. In deterministic mode the value carries
        the commit's recorded timezone offset (``%cI``); in wall-clock mode
        the value uses the ``Z`` (UTC) suffix.
    """
    if deterministic is None:
        env = os.environ.get("STEGANOGRAPHY_DETERMINISTIC", "").strip().lower()
        deterministic = env in {"1", "true", "yes", "on"}

    if not deterministic:
        return _wallclock_iso8601_z()

    cwd = Path(repo_root) if repo_root is not None else Path.cwd()

    try:
        result = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "log", "-1", "--format=%cI"],
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError:
        logger.warning(
            "STEGANOGRAPHY_DETERMINISTIC requested but 'git' is not on PATH; falling back to wall-clock timestamp."
        )
        return _wallclock_iso8601_z()
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning(
            "STEGANOGRAPHY_DETERMINISTIC requested but git invocation failed (%s); "
            "falling back to wall-clock timestamp.",
            exc,
        )
        return _wallclock_iso8601_z()

    if result.returncode != 0:
        logger.warning(
            "STEGANOGRAPHY_DETERMINISTIC requested but 'git log -1 --format=%%cI' "
            "returned exit %d in %s; falling back to wall-clock timestamp.",
            result.returncode,
            cwd,
        )
        return _wallclock_iso8601_z()

    ts = result.stdout.strip()
    if not ts:
        logger.warning(
            "STEGANOGRAPHY_DETERMINISTIC requested but git returned an empty "
            "timestamp in %s; falling back to wall-clock timestamp.",
            cwd,
        )
        return _wallclock_iso8601_z()

    return ts


@dataclass
class DocumentMetadata:
    """Document identity fields passed to metadata injection functions.

    Groups the repeated (title, authors, hashes, document_id, keywords) tuple
    that build_document_metadata and build_xmp_packet both require.
    """

    title: str = ""
    authors: list[str] | None = None
    hashes: dict[str, str] | None = None
    document_id: str = ""
    keywords: list[str] | None = None
    extra: dict[str, str] | None = None


@dataclass
class SteganographyConfig:
    """Configuration for steganographic PDF post-processing.

    Attributes:
        enabled: Master switch — when False no processing occurs.
        overlays_enabled: Diagonal watermark text overlays.
        barcodes_enabled: QR / Code128 / DataMatrix barcode strips.
        metadata_enabled: XMP and PDF Info dictionary injection.
        hashing_enabled: Hash computation and embedding.
        encryption_enabled: AES-256 payload encryption and PDF password.

        overlay_mode: Overlay content mode:
            'text'  — repeating diagonal text (default)
            'qr'    — tiled QR codes encoding document metadata
            'none'  — disable the full-page overlay while keeping footer
        overlay_text: Watermark text rendered diagonally across pages.
        overlay_opacity: Alpha (0.0 = invisible, 1.0 = solid).
        overlay_color_rgb: RGB tuple (0–255 per channel).
        overlay_font_size: Font size for text overlay.
        overlay_repeat_count: Number of text repetitions across the page.
        overlay_qr_data: Custom data for QR overlay mode (auto if None).

        barcode_content: Data to encode in barcodes (None → auto).
        hash_algorithms: Hash algorithms to compute.
        pdf_password: Optional password for PDF-level encryption.
        output_suffix: Suffix appended to the output filename.
        manifest_enabled: Whether to write a JSON hash manifest sidecar.
    """

    enabled: bool = False
    overlays_enabled: bool = True
    barcodes_enabled: bool = True
    metadata_enabled: bool = True
    hashing_enabled: bool = True
    encryption_enabled: bool = False

    # ── Full-page overlay settings ────────────────────────────────────
    overlay_mode: str = "text"  # 'text' | 'qr' | 'none'
    overlay_text: str = "CONFIDENTIAL"
    overlay_opacity: float = 0.08
    overlay_color_rgb: tuple = (128, 128, 128)
    overlay_font_size: int = 60
    overlay_repeat_count: int = 5
    overlay_qr_data: str | None = None  # custom data for QR mode

    # ── Barcode strip settings ────────────────────────────────────────
    barcode_content: str | None = None

    # ── Hashing ───────────────────────────────────────────────────────
    hash_algorithms: list[str] = field(default_factory=lambda: ["sha256", "sha512"])

    # ── Encryption ────────────────────────────────────────────────────
    pdf_password: str | None = None

    # ── Output ────────────────────────────────────────────────────────
    output_suffix: str = "_steganography"
    manifest_enabled: bool = True

    # ── Factory ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SteganographyConfig":
        """Build config from a raw dictionary (e.g. parsed YAML section).

        Unknown keys are silently ignored so forward-compatible config files
        work without errors.
        """
        if not data:
            return cls()

        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Normalise shorthand booleans from YAML
        bool_aliases = {
            "overlays": "overlays_enabled",
            "barcodes": "barcodes_enabled",
            "metadata": "metadata_enabled",
            "hashing": "hashing_enabled",
            "encryption": "encryption_enabled",
        }
        for alias, canon in bool_aliases.items():
            if alias in data and canon not in filtered:
                filtered[canon] = bool(data[alias])

        # Handle overlay_color as list → tuple
        if "overlay_color_rgb" in filtered and isinstance(filtered["overlay_color_rgb"], list):
            filtered["overlay_color_rgb"] = tuple(filtered["overlay_color_rgb"])

        return cls(**filtered)

    @classmethod
    def all_enabled(cls) -> "SteganographyConfig":
        """Return a config with every technique switched on."""
        return cls(
            enabled=True,
            overlays_enabled=True,
            barcodes_enabled=True,
            metadata_enabled=True,
            hashing_enabled=True,
            encryption_enabled=True,
        )

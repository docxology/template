"""Barcode data/payload builders for steganographic overlays.

Builds compact text payloads for QR codes and Code128 barcodes.
Each QR builder targets <=100 characters for reliable phone scanning.

Part of the infrastructure steganography layer (Layer 1).
"""

from __future__ import annotations

from datetime import datetime, timezone

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


# ── Barcode data builder ─────────────────────────────────────────────────


def build_barcode_payload(
    title: str = "",
    hashes: dict[str, str] | None = None,
    document_id: str = "",
    extra: dict[str, str] | None = None,
) -> str:
    """Build a compact barcode payload string.

    The payload is a pipe-delimited string suitable for QR and Code128
    encoding.

    Args:
        title: Document title.
        hashes: Algorithm -> digest mapping (only first 16 chars used).
        document_id: Unique document identifier.
        extra: Additional key=value pairs.

    Returns:
        Payload string.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parts = [f"T:{title[:60]}", f"TS:{timestamp}"]

    if document_id:
        parts.append(f"ID:{document_id}")

    if hashes:
        for algo, digest in hashes.items():
            parts.append(f"{algo.upper()[:6]}:{digest[:16]}")

    if extra:
        for k, v in extra.items():
            parts.append(f"{k}:{v}")

    payload = "|".join(parts)
    logger.debug(f"Barcode payload built: {payload[:80]}")
    return payload


# ── QR code content builders (COMPACT -- <=100 chars for phone scanning) ──
#
# Phone cameras need low-density QR codes to scan reliably at small sizes.
# Each builder targets <=100 characters to stay at QR version 5 or below,
# which produces a ~37x37 module grid -- easily scannable at 40-50pt.


def build_metadata_qr_text(
    title: str = "",
    authors: list[str] | None = None,
    document_id: str = "",
    **_kwargs,
) -> str:
    """Build compact metadata for the metadata QR code (<=100 chars)."""
    parts = []
    if title:
        parts.append(title[:40])
    if document_id:
        # Use hyphen instead of colon to avoid URI scheme triggering in camera apps
        parts.append(f"Doc-ID {document_id[:16]}")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts.append(ts)
    return " | ".join(parts)


def build_citation_qr_text(
    title: str = "",
    authors: list[str] | None = None,
    **_kwargs,
) -> str:
    """Build a compact citation string (<=100 chars)."""
    author = authors[0] if authors else "Unknown"
    year = datetime.now(timezone.utc).strftime("%Y")
    cite = f"{author} ({year}). {title[:50]}."
    return cite[:100]


def build_mailto_qr_text(
    title: str = "",
    authors: list[str] | None = None,
    author_emails: list[str | None] = None,
    **_kwargs,
) -> str:
    """Build a proper mailto: URI that opens an email draft.

    Keeps the URI short and simple to avoid freezing phone apps.
    Uses urllib to correctly URL-encode parameters.
    """
    if author_emails:
        import urllib.parse

        email = author_emails[0]
        subject_raw = title[:40] if title else "Inquiry"
        subject = urllib.parse.quote(subject_raw)
        body = urllib.parse.quote("Please find my inquiry attached.")
        return f"mailto:{email}?subject={subject}&body={body}"
    # Fallback: just show name
    name = authors[0] if authors else "Author"
    return f"Contact {name}"


def build_integrity_qr_text(
    document_id: str = "",
    hashes: dict[str, str] | None = None,
    **_kwargs,
) -> str:
    """Build a compact integrity hash for the integrity QR (<=100 chars).

    Shows the SHA256 of the compiled PDF binary file, avoiding colon prefixes.
    """
    parts = []
    if hashes and "sha256" in hashes:
        parts.append(f"SHA-256 {hashes['sha256'][:24]}...")
    if document_id:
        parts.append(f"ID {document_id[:12]}")
    return " | ".join(parts)

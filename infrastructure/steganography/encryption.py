"""Encryption and digital fingerprinting utilities.

Provides AES-256-GCM encryption for metadata payloads, HMAC-based digital
fingerprints, and optional PDF-level password protection via pypdf.

Dependencies are imported lazily so the module loads without error even when
``cryptography`` is not installed — encryption features will simply be
unavailable at runtime.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from pathlib import Path

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# ── Lazy dependency flags ────────────────────────────────────────────────

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore[import-untyped]

    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    _CRYPTOGRAPHY_AVAILABLE = False


def _require_cryptography() -> None:
    """Raise ImportError with guidance if ``cryptography`` is missing."""
    if not _CRYPTOGRAPHY_AVAILABLE:
        raise ImportError(
            "The 'cryptography' package is required for AES-256 encryption. "
            "Install it with: pip install cryptography"
        )


# ── AES-256-GCM payload encryption ──────────────────────────────────────


def encrypt_payload(
    plaintext: str,
    key: bytes | None = None,
) -> dict[str, str]:
    """Encrypt a plaintext string with AES-256-GCM.

    Args:
        plaintext: UTF-8 string to encrypt.
        key: 32-byte key.  **Generated randomly** if not provided (the
             caller is responsible for persisting the key).

    Returns:
        Dict with ``ciphertext`` (base64), ``nonce`` (base64), and
        ``key`` (base64) — all strings for easy JSON serialisation.
    """
    _require_cryptography()

    if key is None:
        key = AESGCM.generate_key(bit_length=256)

    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    result = {
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "key": base64.b64encode(key).decode(),
    }
    logger.debug(f"Payload encrypted (AES-256-GCM), ciphertext length={len(ciphertext)}")
    return result


def decrypt_payload(
    ciphertext_b64: str,
    nonce_b64: str,
    key_b64: str,
) -> str:
    """Decrypt an AES-256-GCM encrypted payload.

    Args:
        ciphertext_b64: Base64-encoded ciphertext.
        nonce_b64: Base64-encoded nonce.
        key_b64: Base64-encoded key.

    Returns:
        Decrypted plaintext string.
    """
    _require_cryptography()

    key = base64.b64decode(key_b64)
    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return str(plaintext.decode("utf-8"))


# ── HMAC digital fingerprint ────────────────────────────────────────────


def generate_fingerprint(
    content: bytes,
    secret: str | None = None,
) -> dict[str, str]:
    """Generate an HMAC-SHA256 digital fingerprint.

    This does **not** require the ``cryptography`` package — it uses the
    stdlib ``hmac`` module.

    Args:
        content: Byte content to fingerprint.
        secret: HMAC secret key string.  A random 32-byte hex token is
                generated if not provided.

    Returns:
        Dict with ``fingerprint`` (hex) and ``secret`` (hex).
    """
    if secret is None:
        secret = secrets.token_hex(32)

    fp = hmac.new(secret.encode("utf-8"), content, hashlib.sha256).hexdigest()
    logger.debug(f"HMAC-SHA256 fingerprint: {fp[:16]}…")

    return {"fingerprint": fp, "secret": secret}


# ── PDF password protection ─────────────────────────────────────────────


def apply_pdf_password(
    input_pdf: Path,
    output_pdf: Path,
    user_password: str,
    owner_password: str | None = None,
) -> Path:
    """Apply password-based encryption to a PDF file.

    Uses ``pypdf`` for PDF manipulation.  Applies 128-bit RC4 encryption
    (broad reader compatibility).

    Args:
        input_pdf: Source PDF.
        output_pdf: Destination PDF.
        user_password: Password required to open the document.
        owner_password: Owner password for full permissions (defaults to
                        *user_password*).

    Returns:
        Path to the encrypted PDF.
    """
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "The 'pypdf' package is required for PDF password protection. "
            "Install it with: pip install pypdf"
        ) from None

    if owner_password is None:
        owner_password = user_password

    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Copy existing metadata
    if reader.metadata:
        writer.add_metadata({k: v for k, v in reader.metadata.items() if isinstance(v, str)})

    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password,
    )

    with open(output_pdf, "wb") as fh:
        writer.write(fh)

    logger.info(f"PDF password protection applied → {output_pdf.name}")
    return output_pdf


def generate_document_id() -> str:
    """Generate a unique document identifier (UUID4-style hex token)."""
    return secrets.token_hex(16)

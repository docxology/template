"""Hash computation and embedding utilities.

Computes cryptographic hashes of PDF content and writes a JSON manifest
sidecar.  Hash values are also embedded in barcodes and PDF metadata by
other submodules.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def compute_file_hashes(
    file_path: Path,
    algorithms: list[str] | None = None,
) -> dict[str, str]:
    """Compute cryptographic hashes for *file_path*.

    Args:
        file_path: Path to the file to hash.
        algorithms: Hash algorithm names accepted by :func:`hashlib.new`.
                    Defaults to ``["sha256", "sha512"]``.

    Returns:
        Mapping of algorithm name → hex-digest string.
    """
    if algorithms is None:
        algorithms = ["sha256", "sha512"]

    content = file_path.read_bytes()
    results: dict[str, str] = {}

    for algo in algorithms:
        try:
            h = hashlib.new(algo)
            h.update(content)
            results[algo] = h.hexdigest()
            logger.debug(f"Computed {algo} hash for {file_path.name}: {results[algo][:16]}…")
        except ValueError:
            logger.warning(f"Unsupported hash algorithm '{algo}' — skipping")

    return results

def write_hash_manifest(
    pdf_path: Path,
    hashes: dict[str, str],
    output_path: Path | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write a JSON sidecar manifest containing hash values.

    Args:
        pdf_path: Path to the source PDF (used for the ``source_file`` field).
        hashes: Algorithm → hex-digest mapping.
        output_path: Where to write the manifest.  Defaults to
                     ``<pdf_path>.hashes.json``.
        extra: Additional key-value pairs to include in the manifest.

    Returns:
        Path to the written manifest file.
    """
    if output_path is None:
        output_path = pdf_path.with_suffix(".hashes.json")

    manifest: dict[str, Any] = {
        "source_file": pdf_path.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hashes": hashes,
    }
    if extra:
        manifest.update(extra)

    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"Hash manifest written → {output_path}")
    return output_path

def compute_content_hash(content: bytes, algorithm: str = "sha256") -> str:
    """Compute a hash of arbitrary byte content.

    Args:
        content: Raw bytes to hash.
        algorithm: Hash algorithm name.

    Returns:
        Hex-digest string.
    """
    h = hashlib.new(algorithm)
    h.update(content)
    return h.hexdigest()

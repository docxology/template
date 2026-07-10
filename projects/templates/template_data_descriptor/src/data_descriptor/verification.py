"""Byte-level verification of a descriptor against on-disk data files.

The descriptor is the source of truth for a dataset release: it *declares* a
sha256 checksum and a row count for every file. These helpers recompute those
values from the actual bytes on disk and report agreement. This is what turns a
descriptor from a hopeful manifest into a checkable contract: a declared
checksum that no longer matches the file it names is a release-blocking defect,
not a cosmetic one.

Files that a descriptor legitimately references but does not bundle (the
metadata-only release boundary) are reported as ``absent`` rather than as
failures — verification is only asserted for bytes that are actually present.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STATUS_VERIFIED = "verified"
STATUS_ABSENT = "absent"
STATUS_CHECKSUM_MISMATCH = "checksum_mismatch"
STATUS_ROW_MISMATCH = "row_mismatch"


@dataclass(frozen=True)
class FileVerification:
    """Result of checking one declared file against its bytes on disk.

    Attributes:
        path: The descriptor-relative file path.
        status: One of ``verified``, ``absent``, ``checksum_mismatch``, or
            ``row_mismatch``.
        declared_checksum: The ``sha256:...`` string declared in the descriptor.
        actual_checksum: The recomputed ``sha256:...`` string, or ``""`` when the
            file is absent.
        declared_rows: The row count declared in the descriptor.
        actual_rows: The recomputed data-row count, or ``-1`` when the file is
            absent.
        checksum_ok: Whether declared and actual checksums agree.
        rows_ok: Whether declared and actual row counts agree.
    """

    path: str
    status: str
    declared_checksum: str
    actual_checksum: str
    declared_rows: int
    actual_rows: int
    checksum_ok: bool
    rows_ok: bool


def compute_file_digest(path: Path) -> str:
    """Return the ``sha256:<hex>`` digest of a file's raw bytes.

    Args:
        path: File to hash.

    Returns:
        The digest as a ``sha256:``-prefixed lowercase hex string.
    """
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def count_csv_rows(path: Path) -> int:
    """Count data rows in a CSV file, excluding the header and blank lines.

    Args:
        path: CSV file to count.

    Returns:
        The number of non-empty rows after the header. An empty (or
        header-only) file yields ``0``.
    """
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return 0
    return len(lines) - 1


def verify_descriptor_files(descriptor: dict[str, Any], base_dir: Path) -> tuple[FileVerification, ...]:
    """Verify every declared file against the bytes present under ``base_dir``.

    Args:
        descriptor: A parsed descriptor mapping.
        base_dir: Directory that descriptor-relative file paths resolve against.

    Returns:
        One :class:`FileVerification` per declared file entry, in declaration
        order. Files absent from disk are reported with status ``absent`` and
        never fail the checksum/row comparison.
    """
    files = descriptor.get("files", [])
    results: list[FileVerification] = []
    if not isinstance(files, list):
        return ()
    for item in files:
        if not isinstance(item, dict):
            continue
        results.append(_verify_one(item, base_dir))
    return tuple(results)


def verification_summary(verifications: tuple[FileVerification, ...]) -> dict[str, int]:
    """Aggregate verification statuses into counts.

    Args:
        verifications: Results from :func:`verify_descriptor_files`.

    Returns:
        A mapping with ``verified``, ``absent``, and ``mismatch`` counts plus a
        ``total`` key.
    """
    verified = sum(1 for v in verifications if v.status == STATUS_VERIFIED)
    absent = sum(1 for v in verifications if v.status == STATUS_ABSENT)
    mismatch = sum(1 for v in verifications if v.status in (STATUS_CHECKSUM_MISMATCH, STATUS_ROW_MISMATCH))
    return {
        "total": len(verifications),
        "verified": verified,
        "absent": absent,
        "mismatch": mismatch,
    }


def _verify_one(item: dict[str, Any], base_dir: Path) -> FileVerification:
    path = str(item.get("path", ""))
    declared_checksum = str(item.get("checksum", ""))
    declared_rows = int(item.get("rows", 0) or 0)
    resolved = base_dir / path
    if not path or not resolved.is_file():
        return FileVerification(
            path=path,
            status=STATUS_ABSENT,
            declared_checksum=declared_checksum,
            actual_checksum="",
            declared_rows=declared_rows,
            actual_rows=-1,
            checksum_ok=False,
            rows_ok=False,
        )
    actual_checksum = compute_file_digest(resolved)
    actual_rows = count_csv_rows(resolved)
    checksum_ok = actual_checksum == declared_checksum
    rows_ok = actual_rows == declared_rows
    if checksum_ok and rows_ok:
        status = STATUS_VERIFIED
    elif not checksum_ok:
        status = STATUS_CHECKSUM_MISMATCH
    else:
        status = STATUS_ROW_MISMATCH
    return FileVerification(
        path=path,
        status=status,
        declared_checksum=declared_checksum,
        actual_checksum=actual_checksum,
        declared_rows=declared_rows,
        actual_rows=actual_rows,
        checksum_ok=checksum_ok,
        rows_ok=rows_ok,
    )

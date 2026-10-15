"""Source-lock-authenticate nominated wheel bytes without importing its code.

The caller separately supplies actual local selection or authenticated retained
original bytes. This DATA parser mints no provider/process/runtime capability.
"""

from __future__ import annotations

import hashlib
import stat
import tomllib
import zipfile
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)


def inspect_pdfium_source_wheel(
    source: NativeSourceContext, filename: str, raw: bytes, *, deadline: float
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Admit only an exact filename/hash/size wheel in the genuine current lock."""
    from infrastructure.reporting.native_office_pdfium_provider import (
        MAX_BYTES,
    )

    remaining(deadline)
    if not isinstance(source, NativeSourceContext) or not isinstance(raw, bytes):
        raise ValueError("PDFium Source wheel requires genuine Source and actual byte input")
    if (
        not isinstance(filename, str)
        or Path(filename).name != filename
        or not filename.endswith(".whl")
        or len(raw) > MAX_BYTES
    ):
        raise ValueError("PDFium Source wheel filename/body exceeds its exact finite declaration")
    source.verify_correspondence(
        source.reference,
        source.bindings.current_root,
        source.current_source_reader,
        deadline,
    )
    lock = source.current_source_reader.read("uv.lock")
    result = inspect_pdfium_locked_wheel(filename, raw, lock.content, deadline=deadline)
    source.verify_correspondence(source.reference, source.bindings.current_root, source.current_source_reader, deadline)
    remaining(deadline)
    return result


def inspect_pdfium_locked_wheel(
    filename: str, raw: bytes, lock_bytes: bytes, *, deadline: float
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Parse exact held lock/wheel DATA; this grants no Source/provider authority."""
    from infrastructure.reporting.native_office_pdfium_provider import MAX_BYTES, MAX_FILES, PROVIDERS, _label

    remaining(deadline)
    if (
        not isinstance(raw, bytes)
        or not isinstance(lock_bytes, bytes)
        or not isinstance(filename, str)
        or Path(filename).name != filename
        or not filename.endswith(".whl")
        or len(raw) > MAX_BYTES
    ):
        raise ValueError("PDFium held lock/wheel DATA has invalid or unbounded bytes/filename")
    packages = [row for row in tomllib.loads(lock_bytes.decode())["package"] if row["name"] == "pypdfium2"]
    if len(packages) != 1:
        raise ValueError("PDFium Source lock package is absent or ambiguous")
    digest = hashlib.sha256(raw).hexdigest()
    declarations = [
        row
        for row in packages[0]["wheels"]
        if row["url"].rsplit("/", 1)[-1] == filename and row["hash"] == "sha256:" + digest and row["size"] == len(raw)
    ]
    if len(declarations) != 1:
        raise ValueError("PDFium nominated wheel is not the exact Source-listed original/current platform wheel")
    members: dict[str, bytes] = {}
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        total = 0
        for row in archive.infolist():
            remaining(deadline)
            label = _label(row.filename.rstrip("/"))
            if row.is_dir():
                continue
            mode = row.external_attr >> 16
            total += row.file_size
            if (
                label.as_posix() in members
                or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                or len(members) >= MAX_FILES
                or total > MAX_BYTES
            ):
                raise ValueError("PDFium Source wheel member/type/byte closure differs")
            if label.parts[0] not in PROVIDERS and not label.parts[0].endswith(".dist-info"):
                raise ValueError("PDFium Source wheel has an unrelated package root")
            content = archive.read(row)
            if len(content) != row.file_size:
                raise ValueError("PDFium Source wheel decoded member size differs")
            members[label.as_posix()] = content
    metadata = [name for name in members if name.endswith(".dist-info/METADATA")]
    if len(metadata) != 1:
        raise ValueError("PDFium Source wheel metadata is absent or ambiguous")
    headers = BytesParser().parsebytes(members[metadata[0]])
    if headers.get_all("Name") != ["pypdfium2"] or headers.get_all("Version") != [packages[0]["version"]]:
        raise ValueError("PDFium Source wheel metadata differs from its exact declared package/version")
    remaining(deadline)
    return members, {
        "sha256": digest,
        "bytes": len(raw),
        "source_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "version": packages[0]["version"],
    }


def _validate_pdfium_batch_inputs(source: NativeSourceContext, selections: tuple[Any, ...], deadline: float) -> None:
    """Validate a finite fixed input list; never construct an admission."""
    remaining(deadline)
    if not isinstance(source, NativeSourceContext):
        raise ValueError("PDFium batch requires genuine Source")
    _validate_pdfium_batch_selections(selections)


def _validate_pdfium_batch_selections(selections: tuple[Any, ...]) -> None:
    """Refuse malformed fixed selection DATA without constructing authority."""
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumSelection

    if type(selections) is not tuple or not 0 < len(selections) <= len(PUBLIC_PROJECT_NAMES):
        raise ValueError("PDFium batch requires a finite nonempty tuple of selections")
    scopes: set[str] = set()
    for item in selections:
        if (
            type(item) is not tuple
            or len(item) != 2
            or not isinstance(item[0], str)
            or item[0] not in PUBLIC_PROJECT_NAMES
            or item[0] in scopes
            or not isinstance(item[1], NativePDFiumSelection)
        ):
            raise ValueError("PDFium batch requires unique declared scopes and typed selections")
        scopes.add(item[0])

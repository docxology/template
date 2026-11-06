"""Closed Source-native archive bounds and confined member decoding."""

from __future__ import annotations

import io
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

from infrastructure.project.public_hosted_origin import MAX_ARCHIVE

SCHEMA = "template-source-native-hosted-transport-v2"
INDEX_ARTIFACT = "required-source-native-index"
SHARD_PREFIX = "required-source-native-shard-"
MAX_SHARDS = 256
MAX_MEMBERS = 200_000
MAX_TOTAL = 8 * 1024 * 1024 * 1024
MAX_CHUNK = 8 * 1024 * 1024
MAX_SHARD = 32 * 1024 * 1024


def _file_identity(path: Path) -> tuple[int, ...]:
    value = path.lstat()
    if not stat.S_ISREG(value.st_mode):
        raise ValueError("native hosted retained member is no longer a regular file")
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_nlink,
    )


def _path(label: object) -> str:
    if not isinstance(label, str):
        raise ValueError("native transport path must be a string")
    path = PurePosixPath(label)
    if not label or path.is_absolute() or str(path) != label or ".." in path.parts or "\\" in label or "\0" in label:
        raise ValueError("native transport requires canonical confined relative members")
    return label


def _hash(label: object) -> str:
    if not isinstance(label, str) or re.fullmatch(r"[0-9a-f]{64}", label) is None:
        raise ValueError("native transport SHA256 is invalid")
    return label


def _archive(raw: bytes, *, maximum: int, count: int) -> dict[str, bytes]:
    if len(raw) > MAX_ARCHIVE:
        raise ValueError("native transport retains the existing64MiB per-archive bound")
    members: dict[str, bytes] = {}
    total = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.infolist()) > count:
            raise ValueError("native transport archive census exceeds its Source bound")
        for row in archive.infolist():
            label = _path(row.filename)
            mode = row.external_attr >> 16
            total += row.file_size
            if row.is_dir() or label in members or stat.S_IFMT(mode) not in (0, stat.S_IFREG) or total > maximum:
                raise ValueError("native transport archive membership/type/bytes differ")
            body = archive.read(row)
            if len(body) != row.file_size:
                raise ValueError("native transport archive decoded size differs")
            members[label] = body
    return members


def _auxiliary_capacity(root: Path, decoded_bytes: int) -> None:
    """Observe the existing physical transport reserve before independent copies."""
    import shutil

    from infrastructure.core.testing._ci_execution_files import RESERVE

    if shutil.disk_usage(root).free < RESERVE + decoded_bytes:
        raise ValueError("auxiliary archive disk reserve refused before import")


def import_auxiliary_archive(
    root: Path,
    destination: Path,
    raw: bytes,
    *,
    deadline: float,
    mode: int,
    fresh: bool,
    prior_decoded_bytes: int = 0,
    prior_members: int = 0,
) -> tuple[dict[str, str], int]:
    """Import one authenticated auxiliary ZIP without retaining all decoded bodies.

    The existing compressed/per-file64MiB and10,000-member auxiliary limits
    remain distinct from the Source-native whole-transport8GiB ceiling. This
    function grants byte custody only; callers retain origin and full readers.
    """
    import hashlib
    import os

    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
    from infrastructure.project.public_acceptance_evidence import evidence_directory
    from infrastructure.project.public_reference_git import remaining
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    remaining(deadline)
    if len(raw) > MAX_ARCHIVE or mode not in (0o400, 0o600):
        raise ValueError("auxiliary archive exceeds its compressed byte bound or file role")
    if type(prior_decoded_bytes) is not int or not 0 <= prior_decoded_bytes <= MAX_TOTAL:
        raise ValueError("auxiliary prior decoded-byte census is invalid")
    if type(prior_members) is not int or not 0 <= prior_members <= MAX_MEMBERS:
        raise ValueError("auxiliary prior member census is invalid")
    destination = evidence_directory(root, destination, fresh=fresh)
    reader = SnapshotReader(root, operation_deadline=deadline)
    imported: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > 10000 or prior_members + len(entries) > MAX_MEMBERS:
            raise ValueError("auxiliary archive exceeds its existing member census")
        names: set[str] = set()
        total = 0
        for entry in entries:
            remaining(deadline)
            label = _path(entry.filename)
            file_mode = entry.external_attr >> 16
            if (
                entry.is_dir()
                or label in names
                or stat.S_IFMT(file_mode) not in (0, stat.S_IFREG)
                or not 0 <= entry.file_size <= MAX_ARCHIVE
            ):
                raise ValueError("auxiliary archive membership/type/per-file bytes differ")
            reader.public_path((destination / label).relative_to(root).as_posix())
            names.add(label)
            total += entry.file_size
            if prior_decoded_bytes + total > MAX_TOTAL:
                raise ValueError("auxiliary archive exceeds the Source-native whole-transport byte ceiling")
        if "receipt.json" not in names:
            raise ValueError("auxiliary original archive omitted its literal receipt")
        remaining(deadline)
        _auxiliary_capacity(root, total)
        destination.mkdir(parents=True, mode=0o700, exist_ok=not fresh)
        observed_total = 0
        for entry in entries:
            remaining(deadline)
            # Decode one already-admitted bounded member, including CRC/EOF
            # verification, before publishing its confined independent copy.
            with archive.open(entry) as stream:
                body = stream.read(MAX_ARCHIVE + 1)
                if len(body) != entry.file_size or stream.read(1):
                    raise ValueError("auxiliary archive decoded member size differs")
            remaining(deadline)
            observed_total += len(body)
            if prior_decoded_bytes + observed_total > MAX_TOTAL:
                raise ValueError("auxiliary archive actual bytes exceed the whole-transport ceiling")
            _auxiliary_capacity(root, len(body))
            target = destination / entry.filename
            label = target.relative_to(root).as_posix()
            if os.path.lexists(target):
                if read_bytes_confined(root, target, max_bytes=MAX_ARCHIVE) != body:
                    raise ValueError("auxiliary authenticated original conflicts with existing DATA")
            else:
                atomic_write_bytes_confined(root, target, body, mode=mode)
            if read_bytes_confined(root, target, max_bytes=MAX_ARCHIVE) != body:
                raise ValueError("auxiliary imported original differs from authenticated bytes")
            imported[label] = hashlib.sha256(body).hexdigest()
            remaining(deadline)
        if observed_total != total or len(imported) != len(entries):
            raise ValueError("auxiliary archive actual decoded census/bytes differ")
    remaining(deadline)
    return imported, total

"""Closed Source-native archive bounds and confined member decoding."""

from __future__ import annotations

import io
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

from infrastructure.project.public_hosted_origin import MAX_ARCHIVE

SCHEMA = "template-source-native-hosted-transport-v1"
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

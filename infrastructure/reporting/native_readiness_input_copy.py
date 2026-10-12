"""Copy declared Source/common DATA into the owner-controlled full-Git mirror."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.pipeline.fingerprints import tree_records
from infrastructure.project.public_reference import MAX_REFERENCE_BYTES, _directory
from infrastructure.project.public_reference_git import MAX_FILES, remaining
from infrastructure.reporting.readiness_receipts import (
    _READINESS_SOURCE_METADATA_NAMES,
    _public_roots,
    source_fingerprint,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

COMMON_DIRECTORIES = (
    "projects",
    "installed",
    "auxiliary",
    "auxiliary-darwin",
    "sandbox-transfer",
    "native-dependencies",
)


def copy_source_mirror_data(source: Path, destination: Path, *, expected_identity: str, deadline: float) -> None:
    """Retain ignored but Source-declared fixtures, including empty directories.

    Only the canonical public Source census is copied. SDK import/provider
    selection remains the separately installed wheel's responsibility.
    """
    remaining(deadline)
    if source == destination or source_fingerprint(source) != expected_identity:
        raise ValueError("source mirror copy needs the externally selected original Source identity")
    roots, excluded = _public_roots(source)
    observed = total = 0
    for base in roots:
        for label, kind, digest in tree_records(
            base, source=True, excluded_roots=excluded, excluded_names=_READINESS_SOURCE_METADATA_NAMES
        ):
            remaining(deadline)
            path = base if label == "." else base / label
            relative = path.relative_to(source).as_posix()
            target = (
                _directory(SnapshotReader(destination), relative)
                if kind == "directory"
                else SnapshotReader(destination).public_path(relative)
            )
            observed += 1
            if observed > MAX_FILES:
                raise ValueError("source mirror DATA exceeds the existing Source census")
            if kind == "directory":
                if target.exists() and not stat.S_ISDIR(target.lstat().st_mode):
                    raise ValueError("source mirror directory is substituted")
                target.mkdir(parents=True, exist_ok=True)
            elif kind == "file":
                reader = SnapshotReader(source)
                held = reader.read(relative)
                total += len(held.content)
                if total > MAX_REFERENCE_BYTES or held.sha256 != digest or not reader.unchanged():
                    raise ValueError("source mirror DATA changed or exceeds the original reference byte cap")
                if target.exists() or target.is_symlink():
                    if SnapshotReader(destination).read(relative).content != held.content:
                        raise ValueError("source mirror DATA cannot replace a different committed observation")
                else:
                    atomic_write_bytes_confined(destination, target, held.content, mode=0o600)
            else:
                raise ValueError("source mirror DATA census contains a missing/unsupported entry")
    if source_fingerprint(source) != expected_identity or source_fingerprint(destination) != expected_identity:
        raise ValueError("source mirror DATA differs from the same externally selected Source fingerprint")
    remaining(deadline)


def copy_original_common_readiness(source: Path, destination: Path, *, deadline: float) -> None:
    """Preserve same-run common input bytes without treating them as authority."""
    count = total = 0
    for lane in COMMON_DIRECTORIES:
        directory = source / "output/readiness" / lane
        if not directory.exists():
            continue
        for parent, directories, files in os.walk(directory, followlinks=False):
            remaining(deadline)
            if any(not stat.S_ISDIR((Path(parent) / name).lstat().st_mode) for name in directories):
                raise ValueError("common readiness input contains a substituted directory")
            for name in sorted(files):
                relative = (Path(parent) / name).relative_to(source).as_posix()
                reader = SnapshotReader(source)
                held = reader.read(relative)
                count += 1
                total += len(held.content)
                if count > 200000 or len(held.content) > 64 * 1024**2 or total > 8 * 1024**3:
                    raise ValueError("common readiness inputs exceed their bounded public DATA transport census")
                if not stat.S_ISREG(held.path.lstat().st_mode):
                    raise ValueError("common readiness input is not a regular retained file")
                target = SnapshotReader(destination).public_path(relative)
                if target.exists() or target.is_symlink():
                    raise ValueError("common readiness copy cannot overwrite an earlier observation")
                atomic_write_bytes_confined(destination, target, held.content, mode=0o600)
                copied = SnapshotReader(destination).read(relative)
                if copied.sha256 != hashlib.sha256(held.content).hexdigest() or not reader.unchanged():
                    raise ValueError("common readiness DATA changed during its confined copy")
    remaining(deadline)

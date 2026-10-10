"""Bounded preservation of failed cold-launch evidence, without acceptance.

The failed target is separately named. No native collector admits its index,
regardless of any positive status labels retained inside diagnostic DATA.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_acceptance_evidence import evidence_directory
from infrastructure.project.public_hosted_origin import MAX_ARCHIVE, _context
from infrastructure.reporting.native_hosted_original_producer import _zip
from infrastructure.reporting.native_hosted_transport_archive import (
    MAX_CHUNK,
    MAX_MEMBERS,
    MAX_SHARD,
    MAX_SHARDS,
    MAX_TOTAL,
    _file_identity,
)
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-failed-native-diagnostics-v1"
INDEX_PATH = "failed-native-index.json"
INDEX_ARTIFACT = "required-source-native-failure-index"
SHARD_PREFIX = "required-source-native-failure-shard-"


def pack_failed_native_evidence(
    root: Path, mirror: Path, scratch: Path, *, repository: str, run_id: int, revision: str, kind: str = "failed-native"
) -> None:
    """Retain actual existing owned evidence; no synthetic exit/process facts."""
    _context(repository, run_id, revision)
    root = root.resolve(strict=True)
    if kind not in {"failed-native", "failed-reader", "failed-handoff"}:
        raise ValueError("failed transport needs its exact Source-owned diagnostic role")
    for path in (mirror, scratch):
        if not path.is_absolute() or path.is_symlink() or path == root or path.is_relative_to(root):
            raise ValueError("failed diagnostics require the externally nominated separate owned launch destinations")
    directory = root / "output/readiness" / (kind + "-transport")
    directory = evidence_directory(root, directory, fresh=True)
    directory.mkdir(parents=True, mode=0o700)
    # Runtime, dependency caches and Source trees are intentionally excluded.
    # These concrete producer directories contain actual raw process/Code data.
    inputs = [
        ("readiness", mirror / "output/readiness"),
        ("outer", scratch / "outer-processes"),
        ("capture", scratch / "installed/capture-code"),
    ]
    singles = (scratch / "installed/implementation-input.json", scratch / "failed-installed-launch.json")
    pending: list[tuple[str, Path, Path]] = []
    for lane, base in inputs:
        if not base.exists():
            continue
        if base.is_symlink() or not base.is_dir():
            raise ValueError("failed diagnostic producer directory was substituted")
        for parent, directories, filenames in os.walk(base, followlinks=False):
            if any(not stat.S_ISDIR((Path(parent) / name).lstat().st_mode) for name in directories):
                raise ValueError("failed diagnostic directory contains an unowned alias")
            for name in sorted(filenames):
                path = Path(parent) / name
                pending.append((lane + "/" + path.relative_to(base).as_posix(), path, base))
                if len(pending) > MAX_MEMBERS:
                    raise ValueError("failed diagnostics exceed the Source-owned finite file census")
    for single in singles:
        if single.exists() or single.is_symlink():
            pending.append((single.name, single, single.parent))
    if not pending:
        raise ValueError("failed launch produced no retained execution evidence")
    files: list[dict[str, Any]] = []
    shards: list[dict[str, Any]] = []
    chunks: dict[str, bytes] = {}
    seen: set[str] = set()
    identities: dict[Path, tuple[int, ...]] = {}
    chunk_bytes = total = 0

    def flush() -> None:
        nonlocal chunk_bytes
        if not chunks:
            return
        if len(shards) >= MAX_SHARDS:
            raise ValueError("failed diagnostic shard census exceeds its256 bound")
        filename = f"{kind}-shard-{len(shards):04d}.zip"
        body = _zip(chunks)
        if len(body) > MAX_ARCHIVE:
            raise ValueError("failed diagnostic shard exceeds unchanged64MiB archive bound")
        atomic_write_bytes_confined(root, directory / f"shard-{len(shards):04d}" / filename, body, mode=0o600)
        shards.append(
            {
                "filename": filename,
                "sha256": hashlib.sha256(body).hexdigest(),
                "members": [
                    {"path": name, "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
                    for name, value in sorted(chunks.items())
                ],
            }
        )
        chunks.clear()
        chunk_bytes = 0

    for label, path, base in sorted(pending):
        identity = _file_identity(path)
        body = read_bytes_confined(base, path, max_bytes=MAX_ARCHIVE)
        if _file_identity(path) != identity:
            raise ValueError("failed original diagnostic changed while retained")
        identities[path] = identity
        total += len(body)
        if total > MAX_TOTAL:
            raise ValueError("failed diagnostic target exceeds its separately bounded8GiB census")
        destination = root / "output/readiness" / (kind + "-launch") / label
        SnapshotReader(root).public_path(destination.relative_to(root).as_posix())
        atomic_write_bytes_confined(root, destination, body, mode=0o600)
        blocks = []
        for offset in range(0, len(body), MAX_CHUNK):
            block = body[offset : offset + MAX_CHUNK]
            digest = hashlib.sha256(block).hexdigest()
            blocks.append(digest)
            if digest in seen:
                continue
            if chunk_bytes + len(block) > MAX_SHARD:
                flush()
            chunks["chunks/" + digest] = block
            seen.add(digest)
            chunk_bytes += len(block)
        files.append(
            {
                "path": destination.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "chunks": blocks,
            }
        )
    flush()
    if any(_file_identity(path) != identity for path, identity in identities.items()):
        raise ValueError("failed original raw evidence changed before diagnostic sealing")
    index = {
        "schema_version": SCHEMA,
        "repository": repository,
        "hosted_run_id": run_id,
        "source_commit": revision,
        "source_identity": source_fingerprint(root),
        "files": files,
        "shards": shards,
    }
    encoded = (json.dumps(index, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if len(encoded) > MAX_ARCHIVE:
        raise ValueError("failed diagnostic index exceeds unchanged64MiB archive bound")
    atomic_write_bytes_confined(root, directory / "index" / (kind + "-index.json"), encoded, mode=0o600)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--mirror", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--kind", choices=("failed-native", "failed-reader", "failed-handoff"), default="failed-native")
    args = parser.parse_args(argv)
    try:
        pack_failed_native_evidence(
            args.repo_root,
            args.mirror,
            args.scratch,
            repository=args.repository,
            run_id=args.run_id,
            revision=args.revision,
            kind=args.kind,
        )
    except (OSError, ValueError) as error:
        sys.stdout.write("failed native diagnostic retention refused: " + str(error) + "\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

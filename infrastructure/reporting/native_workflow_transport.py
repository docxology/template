"""Validate bounded transport DATA for the Source-declared upload steps.

This utility checks exact frozen bytes and membership. It does not construct
native process, Source, runtime, hosted-origin or publication capabilities.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

from infrastructure.project.public_hosted_origin import MAX_ARCHIVE, _context
from infrastructure.reporting.native_hosted_transport_archive import (
    INDEX_ARTIFACT,
    MAX_CHUNK,
    MAX_MEMBERS,
    MAX_SHARD,
    MAX_SHARDS,
    MAX_TOTAL,
    SCHEMA as NATIVE_SCHEMA,
    SHARD_PREFIX as NATIVE_PREFIX,
    _archive,
    _file_identity,
    _hash,
    _path,
)
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.required_candidate_transport import (
    INDEX_PATH as CANDIDATE_INDEX,
    SCHEMA as CANDIDATE_SCHEMA,
    SHARD_PREFIX as CANDIDATE_PREFIX,
)
from infrastructure.reporting.native_failed_transport import SCHEMA as FAILED_SCHEMA


def prepare_transport_upload(
    root: Path, directory: Path, *, kind: str, repository: str, run_id: int, revision: str
) -> dict[str, Any]:
    """Return a checked upload plan; no gate acceptance is inferred from DATA."""
    _context(repository, run_id, revision)
    root = root.resolve(strict=True)
    directory = directory.absolute()
    failed = kind in {"failed-native", "failed-reader", "failed-handoff"}
    if kind not in {
        "native",
        "candidate",
        "failed-native",
        "failed-reader",
        "failed-handoff",
    } or not directory.is_relative_to(root):
        raise ValueError("transport upload requires one Source-owned confined target")
    reader = SnapshotReader(root)
    relative = directory.relative_to(root).as_posix()
    reader.public_path(relative)
    filename = "native-index.json" if kind == "native" else CANDIDATE_INDEX
    primary = INDEX_ARTIFACT if kind == "native" else "platform-required-acceptance"
    prefix = NATIVE_PREFIX if kind == "native" else CANDIDATE_PREFIX
    schema = NATIVE_SCHEMA if kind == "native" else CANDIDATE_SCHEMA
    if failed:
        filename = kind + "-index.json"
        label = kind.removeprefix("failed-")
        primary = "required-source-" + label + "-failure-index"
        prefix = "required-source-" + label + "-failure-shard-"
        schema = FAILED_SCHEMA
    index = reader.read(f"{relative}/index/{filename}", max_bytes=MAX_ARCHIVE)
    data = index.json_object()
    if (
        data.get("schema_version") != schema
        or data.get("repository") != repository
        or data.get("hosted_run_id") != run_id
        or data.get("source_commit") != revision
        or data.get("source_identity") != source_fingerprint(root)
    ):
        raise ValueError("transport index differs from the selected Source/run/repository target")
    shards, files = data.get("shards"), data.get("files")
    if (
        not isinstance(shards, list)
        or not 0 < len(shards) <= MAX_SHARDS
        or not isinstance(files, list)
        or not 0 < len(files) <= MAX_MEMBERS
    ):
        raise ValueError("transport index exceeds the declared shard/logical-file census")
    chunks: dict[str, int] = {}
    retained: dict[Path, tuple[int, ...]] = {index.path: _file_identity(index.path)}
    chunk_total = logical_total = 0
    for ordinal, row in enumerate(shards):
        expected = f"{kind}-shard-{ordinal:04d}.zip"
        if not isinstance(row, dict) or set(row) != {"filename", "sha256", "members"} or row["filename"] != expected:
            raise ValueError("transport shard identity/ordinal fields differ")
        shard_reader = SnapshotReader(root)
        held = shard_reader.read(f"{relative}/shard-{ordinal:04d}/{expected}", max_bytes=MAX_ARCHIVE)
        retained[held.path] = _file_identity(held.path)
        if held.sha256 != _hash(row["sha256"]):
            raise ValueError("transport retained shard body differs from the frozen producer index")
        members = _archive(held.content, maximum=MAX_SHARD, count=MAX_MEMBERS)
        if row["members"] != [
            {"path": key, "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
            for key, value in sorted(members.items())
        ]:
            raise ValueError("transport shard member bytes/hash/count differ")
        for label, content in members.items():
            digest = _hash(label.removeprefix("chunks/"))
            if (
                label != "chunks/" + digest
                or digest in chunks
                or len(content) > MAX_CHUNK
                or hashlib.sha256(content).hexdigest() != digest
            ):
                raise ValueError("transport chunks are repeated, foreign or changed")
            chunks[digest] = len(content)
            chunk_total += len(content)
            if chunk_total > MAX_TOTAL:
                raise ValueError("transport whole chunk target exceeds its declared8GiB bound")
        if not shard_reader.unchanged():
            raise ValueError("transport shard changed during upload planning")
    paths: set[str] = set()
    used: set[str] = set()
    for row in files:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "bytes", "chunks"}:
            raise ValueError("transport logical member fields differ")
        label, digest = _path(row["path"]), _hash(row["sha256"])
        if (
            label in paths
            or type(row["bytes"]) is not int
            or not 0 <= row["bytes"] <= MAX_ARCHIVE
            or not isinstance(row["chunks"], list)
            or len(row["chunks"]) > 8
        ):
            raise ValueError("transport logical file census exceeds unchanged64MiB member bounds")
        reader.public_path(label)
        sizes = []
        for block in row["chunks"]:
            key = _hash(block)
            if key not in chunks:
                raise ValueError("transport logical member references an unowned chunk")
            used.add(key)
            sizes.append(chunks[key])
        if sum(sizes) != row["bytes"]:
            raise ValueError("transport logical member decoded size differs")
        # Source producer already froze its logical bytes; uploader checks them
        # again without interpreting any native/publication acceptance status.
        file_reader = SnapshotReader(root)
        held = file_reader.read(label, max_bytes=MAX_ARCHIVE)
        if held.sha256 != digest or len(held.content) != row["bytes"]:
            raise ValueError("transport logical body changed before upload")
        if row["chunks"] != [
            hashlib.sha256(held.content[offset : offset + MAX_CHUNK]).hexdigest()
            for offset in range(0, len(held.content), MAX_CHUNK)
        ]:
            raise ValueError("transport ordered chunks differ from the exact logical bytes")
        if not file_reader.unchanged():
            raise ValueError("transport logical body changed during upload planning")
        retained[held.path] = _file_identity(held.path)
        paths.add(label)
        logical_total += row["bytes"]
        if logical_total > MAX_TOTAL:
            raise ValueError("transport whole logical target exceeds its declared8GiB bound")
    if (
        used != set(chunks)
        or not reader.unchanged()
        or any(_file_identity(path) != identity for path, identity in retained.items())
    ):
        raise ValueError("transport frozen membership/identity changed before upload")
    return {
        "primary_name": primary,
        "index_filename": filename,
        "shard_prefix": prefix,
        "member_prefix": kind,
        "shard_count": len(shards),
        "index_sha256": index.sha256,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument(
        "--kind", required=True, choices=("native", "candidate", "failed-native", "failed-reader", "failed-handoff")
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args(argv)
    try:
        plan = prepare_transport_upload(
            args.repo_root,
            args.directory,
            kind=args.kind,
            repository=args.repository,
            run_id=args.run_id,
            revision=args.revision,
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.stdout.write("transport upload refused: " + str(error) + "\n")
        return 2
    for key, value in plan.items():
        sys.stdout.write(f"{key}={value}" + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

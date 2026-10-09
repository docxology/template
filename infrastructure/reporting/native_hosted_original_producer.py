"""Deterministic bounded transport of genuinely supervised native originals.

Only a live Source producer with completed held original launches can pack this
target. Shards contain exact retained bytes; transport DATA grants no runtime,
native, Code, original-process or publication acceptance on its own.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.implementation_custody import source_file_bytes
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_hosted_origin import MAX_ARCHIVE, _context
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_format_joint_source import (
    NativeOriginalLaunch,
    NativeReaderOperation,
    validate_original_joint_launch,
    validate_retained_sdk_closure,
)
from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
from infrastructure.reporting.native_hosted_original_custody import (
    MAX_CHUNK,
    MAX_MEMBERS,
    MAX_SHARD,
    MAX_SHARDS,
    MAX_TOTAL,
    SCHEMA,
    _file_identity,
    _hash,
    _path,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes


@dataclass(frozen=True)
class NativeHostedTransportRequest:
    """Explicit hosted producer destination/run nomination, never authority."""

    directory: Path
    repository: str
    run_id: int


def _zip(members: Mapping[str, bytes]) -> bytes:
    destination = io.BytesIO()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
        for label, body in sorted(members.items()):
            entry = zipfile.ZipInfo(label, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(entry, body)
    return destination.getvalue()


def _mutable_output(label: str) -> bool:
    path = Path(label)
    return path.is_relative_to("output") or any(
        path.is_relative_to(Path("projects") / scope / "output") for scope in PUBLIC_PROJECT_NAMES
    )


def pack_native_hosted_originals(
    source: NativeSourceContext,
    originals: Mapping[str, NativeOriginalLaunch],
    directory: Path,
    *,
    repository: str,
    run_id: int,
    deadline: float,
) -> dict[str, Any]:
    """Freeze the actual all25 originals before the same Source owner closes.

    The supplied originals must have completed genuine supervision and exact
    Source/Code closure. No receipt-decoding or arbitrary path census can mint
    this producer boundary. Logical files retain the existing64MiB ceiling;
    separate Source-owned whole-target bounds govern exact sharding/census.
    """
    remaining(deadline)
    producer = current_native_producer_operation()
    if producer is None or producer.source is not source or producer.deadline != deadline:
        raise ValueError("native transport requires the genuine live Source producer and its original clock")
    _context(repository, run_id, source.reference.commit)
    if tuple(originals) != PUBLIC_PROJECT_NAMES:
        raise ValueError("native transport requires the complete ordered Source public roster")
    root = source.bindings.current_root
    directory = evidence_directory(root, directory, fresh=True)
    directory.mkdir(parents=True, mode=0o700)
    root_reader = SnapshotReader(root)
    producer.verify(root_reader, run_id=source.bindings.run_id, deadline=deadline)
    bindings: dict[str, str | None] = {}
    wheel_rows: dict[str, dict[str, Any]] = {}
    original_rows: dict[str, dict[str, Any]] = {}
    physical: dict[str, tuple[int, ...]] = {}
    packed_digests: dict[str, str] = {}
    files: list[dict[str, Any]] = []
    shards: list[dict[str, Any]] = []
    chunks: dict[str, bytes] = {}
    all_chunk_digests: set[str] = set()
    chunk_bytes = total = 0

    def admit(label: str, digest: str | None = None) -> None:
        label = _path(label)
        root_reader.public_path(label)
        if digest is not None:
            _hash(digest)
        if not _mutable_output(label):
            # Immutable source references are supplied by independently admitted
            # exact-commit Source; they must never overwrite the reader's Source.
            if digest is not None and SnapshotReader(root).read(label).sha256 != digest:
                raise ValueError("native transport source binding differs from the independently held Source")
            return
        if Path(label).is_relative_to(directory.relative_to(root)):
            raise ValueError("native transport refuses recursively packing its own output")
        previous = bindings.get(label)
        if previous is not None and digest is not None and previous != digest:
            raise ValueError("native retained graph references conflicting bytes for one path")
        bindings[label] = digest if digest is not None else previous
        if len(bindings) > MAX_MEMBERS:
            raise ValueError("native target exceeds its Source-owned file census")

    def graph(value: object, parent: Path) -> None:
        remaining(deadline)
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                label = value["path"]
                digest = value["sha256"]
                if len(digest) == 64:
                    path = Path(label)
                    if path.is_absolute():
                        if path.is_relative_to(root):
                            admit(path.relative_to(root).as_posix(), digest)
                    elif len(path.parts) == 1 and path.name.startswith("payload-"):
                        admit((parent / path).relative_to(root).as_posix(), digest)
                    else:
                        admit(label, digest)
            for item in value.values():
                graph(item, parent)
        elif isinstance(value, list):
            for item in value:
                graph(item, parent)

    for scope, original in originals.items():
        remaining(deadline)
        if (
            not isinstance(original, NativeOriginalLaunch)
            or original.scope != scope
            or original.original_deadline != deadline
            or not isinstance(original.pdfium_provider, NativePDFiumProvider)
            or original.pdfium_provider.source is not source
        ):
            raise ValueError("native target cannot be packed from decoded or unrelated original launch data")
        reader = SnapshotReader(root)
        specification = reader.read(original.specification_relative)
        process = reader.read(original.process_relative)
        closure = reader.read(original.closure_relative)
        native = reader.read(original.native_execution_relative)
        if native.sha256 != original.native_execution_sha256:
            raise ValueError("native producer original observation differs from genuine held completion")
        operation = NativeReaderOperation(source, deadline, {scope: original}, {scope: original.pdfium_provider})
        reader.native_operation = operation
        _, descriptor = validate_original_joint_launch(
            specification.json_object(), specification, process, closure, reader, operation
        )
        validate_retained_sdk_closure(closure, specification.json_object(), descriptor, reader, operation)
        cell = specification.path.parent
        for owner, directories, names in os.walk(cell, followlinks=False):
            remaining(deadline)
            for name in directories:
                if not stat.S_ISDIR((Path(owner) / name).lstat().st_mode):
                    raise ValueError("native original cell contains a substituted/symlink directory")
            for name in names:
                path = Path(owner) / name
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise ValueError("native original cell contains a nonregular retained member")
                admit(path.relative_to(root).as_posix())
        for row in fields(original):
            if row.name == "pdfium_provider":
                continue
            value = getattr(original, row.name)
            original_rows.setdefault(scope, {})[row.name] = list(value) if isinstance(value, tuple) else value
        wheel = original.pdfium_provider
        wheel.verify_current(deadline=deadline)
        body = source_file_bytes(wheel.selection.wheel)
        digest = hashlib.sha256(body).hexdigest()
        inputs = wheel.held_inputs()
        if digest != inputs["wheel"]["sha256"] or len(body) != inputs["wheel"]["bytes"] or len(body) > MAX_ARCHIVE:
            raise ValueError("native retained original PDFium wheel changed or exceeds unchanged per-file bound")
        target = directory / "original-wheels" / (digest + ".whl")
        if not target.exists():
            atomic_write_bytes_confined(root, target, body, mode=0o600)
        label = target.relative_to(root).as_posix()
        # Wheel is a direct Source-owned addition; it is outside the recursive
        # original cell and can only be nominated by the held actual provider.
        bindings[label] = digest
        wheel_rows[scope] = {"filename": wheel.selection.wheel.name, "artifact": {"path": label, "sha256": digest}}
        if not reader.unchanged():
            raise ValueError("native genuine original closing Source/Code bytes changed before packing")

    scanned: set[str] = set()
    while set(bindings) - scanned:
        for label in sorted(set(bindings) - scanned):
            remaining(deadline)
            scanned.add(label)
            path = root_reader.public_path(label)
            if path.suffix == ".json":
                snapshot = SnapshotReader(root).read(label)
                if bindings[label] is not None and snapshot.sha256 != bindings[label]:
                    raise ValueError("native original graph JSON differs from exact retained binding")
                graph(
                    json_object_from_bytes(b'{"original_json":' + snapshot.content + b"}")["original_json"], path.parent
                )

    def flush() -> None:
        nonlocal chunk_bytes
        remaining(deadline)
        if not chunks:
            return
        if len(shards) >= MAX_SHARDS:
            raise ValueError("native target exceeds its Source-declared bounded shard census")
        body = _zip(chunks)
        if len(body) > MAX_ARCHIVE:
            raise ValueError("native shard archive exceeds the existing64MiB boundary")
        filename = f"native-shard-{len(shards):04d}.zip"
        target = directory / f"shard-{len(shards):04d}" / filename
        atomic_write_bytes_confined(root, target, body, mode=0o600)
        shards.append(
            {
                "filename": filename,
                "sha256": hashlib.sha256(body).hexdigest(),
                "members": [
                    {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                    for name, data in sorted(chunks.items())
                ],
            }
        )
        chunks.clear()
        chunk_bytes = 0

    for label, expected in sorted(bindings.items()):
        remaining(deadline)
        reader = SnapshotReader(root)
        snapshot = reader.read(label)
        if expected is not None and snapshot.sha256 != expected:
            raise ValueError("native original graph member changed before deterministic shard construction")
        total += len(snapshot.content)
        if len(snapshot.content) > MAX_ARCHIVE or total > MAX_TOTAL:
            raise ValueError("native target exceeds Source logical-file or whole-target byte bounds")
        physical[label] = _file_identity(snapshot.path)
        packed_digests[label] = snapshot.sha256
        file_chunks: list[str] = []
        for offset in range(0, len(snapshot.content), MAX_CHUNK):
            block = snapshot.content[offset : offset + MAX_CHUNK]
            digest = hashlib.sha256(block).hexdigest()
            file_chunks.append(digest)
            if digest in all_chunk_digests:
                continue
            if chunk_bytes + len(block) > MAX_SHARD:
                flush()
            chunks["chunks/" + digest] = block
            all_chunk_digests.add(digest)
            chunk_bytes += len(block)
        files.append({"path": label, "sha256": snapshot.sha256, "bytes": len(snapshot.content), "chunks": file_chunks})
        if not reader.unchanged():
            raise ValueError("native original graph member changed during shard construction")
    flush()
    index = {
        "schema_version": SCHEMA,
        "repository": repository,
        "hosted_run_id": run_id,
        "source_commit": source.reference.commit,
        "source_identity": source.reference.source_identity,
        "scopes": list(PUBLIC_PROJECT_NAMES),
        "originals": original_rows,
        "pdfium_wheels": wheel_rows,
        "shards": shards,
        "files": files,
    }
    encoded = (json.dumps(index, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if len(encoded) > MAX_ARCHIVE:
        raise ValueError("native exact index exceeds the existing64MiB artifact boundary")
    for label, identity in physical.items():
        reader = SnapshotReader(root)
        snapshot = reader.read(label)
        if (
            _file_identity(snapshot.path) != identity
            or snapshot.sha256 != packed_digests[label]
            or not reader.unchanged()
        ):
            raise ValueError("native original graph changed before final Source-owned transport closure")
    producer.verify(SnapshotReader(root), run_id=source.bindings.run_id, deadline=deadline)
    binding = write_json(root, directory / "index" / "native-index.json", index)
    remaining(deadline)
    return {
        "index": binding,
        "shard_count": len(shards),
        "file_count": len(files),
        "bytes": total,
        "directory": directory.relative_to(root).as_posix(),
    }

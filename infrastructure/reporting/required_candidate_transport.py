"""Source-owned bounded shards for the complete independently passed candidate.

The primary artifact remains platform-required-acceptance and below64MiB. Its
index binds every separately named shard. A future reader must authenticate
the original hosted artifact bytes and independently admit native originals;
this JSON index supplies no original-process or runtime capability.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import evidence_directory
from infrastructure.project.public_hosted_origin import HostedReadbackContext, MAX_ARCHIVE, _context
from infrastructure.project.public_reference_git import remaining
from infrastructure.publishing.release_acceptance import RECEIPT_PATH
from infrastructure.reporting.native_format_joint_source import NativeReaderOperation
from infrastructure.reporting.native_hosted_transport_archive import (
    MAX_CHUNK,
    MAX_MEMBERS,
    MAX_SHARD,
    MAX_SHARDS,
    MAX_TOTAL,
    _file_identity,
)
from infrastructure.reporting.native_hosted_original_producer import _zip
from infrastructure.reporting.native_hosted_original_custody import NativeHostedArtifactCustodian
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_profile import collect_profile
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCHEMA = "template-required-candidate-sharded-transport-v1"
INDEX_PATH = "candidate-index.json"
SHARD_PREFIX = "platform-required-acceptance-shard-"


@dataclass(frozen=True)
class RequiredCandidatePackingInputs:
    """Explicit packing nominations; this object grants no acceptance authority."""

    native_custodian: NativeHostedArtifactCustodian
    directory: Path
    repository: str
    run_id: int
    deadline: float


def _graph_paths(root: Path, receipt: str, reader: SnapshotReader, *, deadline: float) -> dict[str, str]:
    """Walk exact bindings; source bytes stay in the admitted Source checkout."""
    pending: list[tuple[str, str | None]] = [(receipt, None)]
    paths: dict[str, str] = {}

    def walk(value: object, parent: Path) -> None:
        if isinstance(value, dict):
            path, digest = value.get("path"), value.get("sha256")
            if isinstance(path, str) and isinstance(digest, str) and len(digest) == 64:
                label = Path(path)
                if label.is_absolute():
                    if label.is_relative_to(root):
                        pending.append((label.relative_to(root).as_posix(), digest))
                elif label.name == path and path.startswith("payload-"):
                    pending.append(((parent / path).relative_to(root).as_posix(), digest))
                else:
                    pending.append((path, digest))
            if isinstance(value.get("artifact"), str) and isinstance(value.get("artifact_sha256"), str):
                pending.append((value["artifact"], value["artifact_sha256"]))
            for item in value.values():
                walk(item, parent)
        elif isinstance(value, list):
            for item in value:
                walk(item, parent)

    while pending:
        remaining(deadline)
        label, expected = pending.pop()
        reader.public_path(label)
        prior = paths.get(label)
        if prior is not None:
            if expected is not None and prior != expected:
                raise ValueError("candidate graph has conflicting exact artifact bindings")
            continue
        held = reader.read(label)
        if expected is not None and held.sha256 != expected:
            raise ValueError("candidate graph bytes differ from the verified binding")
        if not Path(label).is_relative_to("output/readiness"):
            continue
        paths[label] = held.sha256
        if len(paths) > MAX_MEMBERS:
            raise ValueError("candidate evidence exceeds its Source-declared bounded member census")
        if label.endswith(".json"):
            from infrastructure.project.public_root_census_encoding import SCHEMA as CENSUS_ENCODING_SCHEMA, decode

            payload = held.json_object()
            if payload.get("schema_version") == CENSUS_ENCODING_SCHEMA:
                payload = decode(payload)
            walk(payload, held.path.parent)
        if not reader.unchanged():
            raise ValueError("candidate graph member changed during packing census")
    return paths


def pack_required_candidate(
    source: NativeSourceContext,
    operation: NativeReaderOperation,
    *,
    native_custodian: NativeHostedArtifactCustodian,
    hosted_origin: HostedReadbackContext,
    directory: Path,
    repository: str,
    run_id: int,
    deadline: float,
) -> dict[str, Any]:
    """Pack only an actually admitted current reader's complete passing closure."""
    remaining(deadline)
    if (
        not isinstance(operation, NativeReaderOperation)
        or operation.source is not source
        or deadline != operation.deadline
    ):
        raise ValueError("candidate packing requires the genuinely held reader and its unchanged outer clock")
    _context(repository, run_id, source.reference.commit)
    root = source.bindings.current_root
    reader = SnapshotReader(root, native_operation=operation, hosted_origin=hosted_origin)
    operation.verify(reader)
    receipt = reader.read(RECEIPT_PATH)
    evidence = collect_profile(root, receipt.path, reader)
    if evidence.candidate_state != "pass" or not reader.unchanged():
        raise ValueError("candidate cannot publish shards unless every required Source gate independently passes")
    return _pack_required_candidate_from_reader(
        operation,
        reader,
        receipt,
        packing_inputs=RequiredCandidatePackingInputs(native_custodian, directory, repository, run_id, deadline),
        hosted_origin=hosted_origin,
    )


def _pack_required_candidate_from_reader(
    operation: NativeReaderOperation,
    reader: SnapshotReader,
    receipt: ArtifactSnapshot,
    *,
    packing_inputs: RequiredCandidatePackingInputs,
    hosted_origin: HostedReadbackContext,
) -> dict[str, Any]:
    """Pack bytes immediately within a caller's complete passing profile observation."""
    if not isinstance(operation, NativeReaderOperation) or not isinstance(
        packing_inputs, RequiredCandidatePackingInputs
    ):
        raise ValueError("candidate packing requires independently held reader and explicit packing nominations")
    source = operation.source
    native_custodian = packing_inputs.native_custodian
    directory, repository = packing_inputs.directory, packing_inputs.repository
    run_id, deadline = packing_inputs.run_id, packing_inputs.deadline
    remaining(deadline)
    root = source.bindings.current_root
    if (
        reader.root != root
        or reader.native_operation is not operation
        or reader.hosted_origin != hosted_origin
        or not isinstance(hosted_origin, HostedReadbackContext)
        or deadline != operation.deadline
        or receipt.relative != RECEIPT_PATH
        or reader.read(RECEIPT_PATH) is not receipt
        or not reader.unchanged()
    ):
        raise ValueError("candidate packing lost its actual Source/reader/receipt observation or original clock")
    operation.verify(reader)
    _context(repository, run_id, source.reference.commit)
    if (hosted_origin.repository, hosted_origin.run_id, hosted_origin.head_sha) != (
        repository,
        run_id,
        source.reference.commit,
    ):
        raise ValueError("candidate packing hosted nomination differs from the independently held reader")
    if (
        not isinstance(native_custodian, NativeHostedArtifactCustodian)
        or native_custodian.deadline != deadline
        or native_custodian.repository != repository
        or native_custodian.run_id != run_id
        or native_custodian.head_sha != source.reference.commit
        or not operation.originals
    ):
        raise ValueError("candidate requires the genuinely collected exact-run native byte census")
    native_custodian.verify_source(source, scope=next(iter(operation.originals)))
    paths = _graph_paths(root, RECEIPT_PATH, reader, deadline=deadline)
    # The native closure includes relocated SDK/cache/Python-child payloads.
    # Absolute producer labels inside DATA are never opened on this host.
    # Carry every independently authenticated retained member explicitly.
    for binding in native_custodian.retained_file_bindings():
        label, digest = binding["path"], binding["sha256"]
        if label in paths and paths[label] != digest:
            raise ValueError("candidate/native closures disagree on one exact retained body")
        paths[label] = digest
    # Profile validators can consume source-declared auxiliary graphs that do
    # not use the generic JSON binding shape. Include their actual snapshots.
    for held in reader.snapshots.values():
        if Path(held.relative).is_relative_to("output/readiness"):
            if held.relative in paths and paths[held.relative] != held.sha256:
                raise ValueError("candidate consumed snapshot differs from its bound graph")
            paths[held.relative] = held.sha256
    if len(paths) > MAX_MEMBERS:
        raise ValueError("complete candidate exceeds its Source-owned member census")
    directory = evidence_directory(root, directory, fresh=True)
    directory.mkdir(parents=True, mode=0o700)
    identities: dict[str, tuple[int, ...]] = {}
    files: list[dict[str, Any]] = []
    shards: list[dict[str, Any]] = []
    chunks: dict[str, bytes] = {}
    seen: set[str] = set()
    chunk_bytes = total = 0

    def flush() -> None:
        nonlocal chunk_bytes
        remaining(deadline)
        if not chunks:
            return
        if len(shards) >= MAX_SHARDS:
            raise ValueError("candidate exceeds its256 separately bounded shard census")
        body = _zip(chunks)
        if len(body) > MAX_ARCHIVE:
            raise ValueError("candidate shard exceeds the unchanged64MiB artifact cap")
        filename = f"candidate-shard-{len(shards):04d}.zip"
        atomic_write_bytes_confined(root, directory / f"shard-{len(shards):04d}" / filename, body, mode=0o600)
        shards.append(
            {
                "filename": filename,
                "sha256": hashlib.sha256(body).hexdigest(),
                "members": [
                    {"path": key, "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
                    for key, value in sorted(chunks.items())
                ],
            }
        )
        chunks.clear()
        chunk_bytes = 0

    for label, digest in sorted(paths.items()):
        remaining(deadline)
        held_reader = SnapshotReader(root)
        held = held_reader.read(label)
        total += len(held.content)
        if held.sha256 != digest or len(held.content) > MAX_ARCHIVE or total > MAX_TOTAL:
            raise ValueError("candidate evidence changed or exceeds its logical64MiB/whole8GiB bounds")
        identities[label] = _file_identity(held.path)
        blocks = []
        for offset in range(0, len(held.content), MAX_CHUNK):
            body = held.content[offset : offset + MAX_CHUNK]
            block = hashlib.sha256(body).hexdigest()
            blocks.append(block)
            if block in seen:
                continue
            if chunk_bytes + len(body) > MAX_SHARD:
                flush()
            chunks["chunks/" + block] = body
            seen.add(block)
            chunk_bytes += len(body)
        files.append({"path": label, "sha256": digest, "bytes": len(held.content), "chunks": blocks})
        if not held_reader.unchanged():
            raise ValueError("candidate evidence changed while retained bytes were frozen")
    flush()
    for label, identity in identities.items():
        held_reader = SnapshotReader(root)
        held = held_reader.read(label)
        if _file_identity(held.path) != identity or held.sha256 != paths[label] or not held_reader.unchanged():
            raise ValueError("candidate evidence lost its final retained physical/body identity")
    operation.verify(reader)
    native_custodian.verify_source(source, scope=next(iter(operation.originals)))
    if not reader.unchanged():
        raise ValueError("candidate packing consumed evidence changed after its passing observation")
    index = {
        "schema_version": SCHEMA,
        "repository": repository,
        "hosted_run_id": run_id,
        "source_commit": source.reference.commit,
        "source_identity": source.reference.source_identity,
        "receipt": {"path": RECEIPT_PATH, "sha256": receipt.sha256},
        "shards": shards,
        "files": files,
    }
    encoded = (json.dumps(index, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if len(encoded) > MAX_ARCHIVE:
        raise ValueError("candidate primary index exceeds the unchanged64MiB artifact cap")
    destination = directory / "index" / INDEX_PATH
    atomic_write_bytes_confined(root, destination, encoded, mode=0o600)
    binding = {"path": destination.relative_to(root).as_posix(), "sha256": hashlib.sha256(encoded).hexdigest()}
    operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("candidate packing lost its retained Source/evidence observation during index publication")
    remaining(deadline)
    return {
        "index": binding,
        "shard_count": len(shards),
        "receipt_sha256": receipt.sha256,
        "file_count": len(files),
        "bytes": total,
    }

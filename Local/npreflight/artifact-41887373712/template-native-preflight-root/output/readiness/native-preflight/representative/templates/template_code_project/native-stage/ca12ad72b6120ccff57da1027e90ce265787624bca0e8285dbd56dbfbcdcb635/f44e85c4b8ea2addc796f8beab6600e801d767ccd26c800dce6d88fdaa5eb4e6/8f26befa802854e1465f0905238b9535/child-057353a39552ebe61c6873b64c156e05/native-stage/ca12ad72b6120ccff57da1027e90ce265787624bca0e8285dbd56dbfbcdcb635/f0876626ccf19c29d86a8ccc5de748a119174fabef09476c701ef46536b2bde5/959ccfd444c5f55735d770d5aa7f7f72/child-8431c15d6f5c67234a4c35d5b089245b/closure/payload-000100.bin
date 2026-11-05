"""Observe actual completed Source API writes inside the genuine script scope.

These are write/body observations. They do not create per-leaf originals or
claim that all prior registered reads are scientific dependencies. Direct,
native/C, threaded and external writes remain explicitly unqualified.
"""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, cast

from infrastructure.core.analysis_data_custody import MAX_FILE_BYTES
from infrastructure.core.analysis_read_custody import _ReadCapture, _consumer, _identity
from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    atomic_write_bytes_confined_observed,
    read_bytes_confined,
)
from infrastructure.core.pipeline.fingerprints import canonical_digest

SCHEMA = "template-analysis-completed-write-bytes-v2"
MAX_WRITE_METADATA_BYTES = 1024 * 1024
_ACTIVE: ContextVar[_WriteCapture | None] = ContextVar("template_actual_analysis_writes", default=None)


@dataclass
class _WriteCapture:
    reads: _ReadCapture
    rows: list[dict[str, Any]] = field(default_factory=list)
    total_bytes: int = 0

    def verify(self) -> None:
        self.reads.verify()
        if _ACTIVE.get() is not self or self.reads.owner_pid != os.getpid():
            raise ValueError("analysis write observations lost their actual worker/read owner")

    def completed_body(self, name: str, digest: str, identity: list[int]) -> int | None:
        self.verify()
        for row in reversed(self.rows):
            if (row["path"], row["sha256"], row["native_identity"]) == (name, digest, identity):
                return cast(int, row["ordinal"])
        return None

    def data(self) -> dict[str, Any]:
        self.verify()
        body = {
            "schema": SCHEMA,
            "run_id": self.reads.run_id,
            "stage_key": self.reads.stage_key,
            "analysis_nonce": self.reads.nonce,
            "request_digest": self.reads.request_digest,
            "owner_pid": self.reads.owner_pid,
            "records": self.rows,
            "total_written_bytes": self.total_bytes,
            "coverage_boundary": "registered-Source-API-writes-only; native-direct-external-writes-not-qualified",
        }
        if len(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()) > MAX_WRITE_METADATA_BYTES:
            raise ValueError("analysis completed-write metadata exceeds its held completion receipt ceiling")
        return {**body, "content_digest": canonical_digest(body)}


@contextmanager
def observe_stage_analysis_writes(reads: _ReadCapture) -> Iterator[_WriteCapture]:
    """Begin only within the worker's actual already verified read scope."""
    if not isinstance(reads, _ReadCapture) or _ACTIVE.get() is not None:
        raise ValueError("analysis write scope needs its real active worker read capture")
    reads.verify()
    owner = _WriteCapture(reads)
    if reads.write_observation is not None:
        raise ValueError("analysis completed writes cannot replace another actual read/write scope")
    reads.write_observation = owner
    token = _ACTIVE.set(owner)
    try:
        owner.verify()
        yield owner
        owner.verify()
    finally:
        reads.write_observation = None
        _ACTIVE.reset(token)


def _retain(owner: _WriteCapture, content: bytes) -> str:
    digest = hashlib.sha256(content).hexdigest()
    relative = (
        Path("output/.pipeline/analysis-data")
        / hashlib.sha256(owner.reads.run_id.encode()).hexdigest()
        / "blobs"
        / digest
    )
    target = owner.reads.project / relative
    try:
        existing = read_bytes_confined(owner.reads.project, target, max_bytes=MAX_FILE_BYTES)
    except FileNotFoundError:
        atomic_write_bytes_confined(owner.reads.project, target, content, mode=0o600)
    else:
        if existing != content:
            raise ValueError("analysis write body differs from its actual run-owned retained slot")
    return relative.as_posix()


def current_analysis_write_project() -> Path | None:
    """Read the genuine live worker scope; caller DATA cannot create it."""
    owner = _ACTIVE.get()
    if owner is None:
        return None
    owner.verify()
    return owner.reads.project


def write_analysis_bytes(project: Path, path: Path, content: bytes) -> Path:
    """Write those exact bytes and record the actual completed output body.

    No callback, declared input list, witness, status or original is accepted.
    A recorded read-prefix length/digest is temporal observation, not a claim
    that the producer scientifically depends on every preceding read.
    """
    project, path = project.absolute(), path.absolute()
    if not isinstance(content, bytes) or len(content) > MAX_FILE_BYTES:
        raise ValueError("analysis write requires bounded complete byte content")
    if project.is_symlink() or not path.is_relative_to(project) or ".." in path.parts:
        raise ValueError("analysis write escaped its actual project")
    owner = _ACTIVE.get()
    if owner is None:
        atomic_write_bytes_confined(project, path, content)
        return path
    owner.verify()
    if project != owner.reads.project:
        raise ValueError("analysis write supplied a different actual project owner")
    name = path.relative_to(project).as_posix()
    if (
        not Path(name).is_relative_to(Path("output"))
        or len(Path(name).parts) < 2
        or any(part.startswith(".") for part in Path(name).parts)
        or len(owner.rows) >= 10000
        or owner.total_bytes + len(content) > 256 * 1024 * 1024
    ):
        raise ValueError("analysis write is outside its held output/event/body policy")
    prior_observed = None
    try:
        before = _identity(path)
        old = read_bytes_confined(project, path, max_bytes=MAX_FILE_BYTES)
        if _identity(path) != before:
            raise ValueError("analysis prior observed body changed during its actual bounded read")
        prior_observed = {
            "sha256": hashlib.sha256(old).hexdigest(),
            "bytes": len(old),
            "native_identity": list(before),
            "retained_path": _retain(owner, old),
        }
    except FileNotFoundError:
        pass
    producer = _consumer(owner.reads.repo)
    read_count = len(owner.reads.rows)
    read_digest = canonical_digest(owner.reads.rows[:read_count])
    after = atomic_write_bytes_confined_observed(project, path, content)
    if _identity(path) != after:
        raise ValueError("analysis target changed after publication of its actual held written inode")
    held = read_bytes_confined(project, path, max_bytes=MAX_FILE_BYTES)
    if _identity(path) != after or held != content:
        raise ValueError("analysis completed write differs from its exact returned output body")
    retained = _retain(owner, held)
    owner.rows.append(
        {
            "ordinal": len(owner.rows) + 1,
            "path": name,
            "sha256": hashlib.sha256(held).hexdigest(),
            "bytes": len(held),
            "native_identity": list(after),
            "retained_path": retained,
            "prior_observed": prior_observed,
            "prior_observation_authority": "prior-path-observation-only; not-compare-and-swap-history",
            "producer": producer,
            "prior_registered_read_count": read_count,
            "prior_registered_read_prefix_digest": read_digest,
        }
    )
    owner.total_bytes += len(held)
    owner.verify()
    return path

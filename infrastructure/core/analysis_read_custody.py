"""Observe exact bytes returned by the real Source-owned project read API.

This implementation records actual completed reads, not alleged dependencies
or original-process authority. The genuine stage worker owns the observation
scope. Native/C/direct/external reads remain unqualified until migrated and
audited independently; an empty recorded list never proves their absence.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import stat
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from infrastructure.core.analysis_data_custody import DATA_FILES, DATA_ROOTS, MAX_FILE_BYTES, remaining
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest

SCHEMA = "template-analysis-returned-read-bytes-v2"
MAX_READ_METADATA_BYTES = 4 * 1024 * 1024
_ACTIVE: ContextVar[_ReadCapture | None] = ContextVar("template_actual_analysis_reads", default=None)


def _identity(path: Path) -> tuple[int, int, int, int, int]:
    item = path.lstat()
    if not stat.S_ISREG(item.st_mode) or path.is_symlink():
        raise ValueError("analysis read requires one actual regular confined body")
    return item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns


def _consumer(root: Path) -> dict[str, Any]:
    """Observe actual consuming Source frame, never a caller-supplied label."""
    frame = inspect.currentframe()
    try:
        frame = frame.f_back if frame is not None else None
        while frame is not None:
            name = frame.f_code.co_filename
            path = Path(name).absolute()
            if path.is_relative_to(root / "projects") and path.is_file() and path.name != "_runtime.py":
                content = read_bytes_confined(root, path, max_bytes=8 * 1024 * 1024)
                return {
                    "source": path.relative_to(root).as_posix(),
                    "source_sha256": hashlib.sha256(content).hexdigest(),
                    "function": frame.f_code.co_name,
                    "line": frame.f_lineno,
                }
            frame = frame.f_back
    finally:
        del frame
    raise ValueError("analysis read omitted its actual consuming project Source frame")


@dataclass
class _ReadCapture:
    project: Path
    repo: Path
    run_id: str
    stage_key: str
    nonce: str
    request_digest: str
    incoming: dict[str, dict[str, Any]]
    deadline: float
    owner_pid: int = field(default_factory=os.getpid)
    rows: list[dict[str, Any]] = field(default_factory=list)
    total_bytes: int = 0
    write_observation: Any = None

    def verify(self) -> None:
        remaining(self.deadline)
        if self.owner_pid != os.getpid() or _ACTIVE.get() is not self:
            raise ValueError("analysis read observation lost its actual stage owner/process/clock")

    def data(self) -> dict[str, Any]:
        self.verify()
        body = {
            "schema": SCHEMA,
            "run_id": self.run_id,
            "stage_key": self.stage_key,
            "analysis_nonce": self.nonce,
            "request_digest": self.request_digest,
            "owner_pid": self.owner_pid,
            "records": self.rows,
            "total_returned_bytes": self.total_bytes,
            "completed_writes": self.write_observation.data() if self.write_observation is not None else None,
            "coverage_boundary": "registered-Source-API-reads-only; native-direct-external-reads-not-qualified",
        }
        if len(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()) > MAX_READ_METADATA_BYTES:
            raise ValueError("analysis returned-read metadata exceeds its held completion receipt ceiling")
        return {**body, "content_digest": canonical_digest(body)}


@contextmanager
def observe_stage_analysis_reads(
    repo: Path,
    project: Path,
    *,
    run_id: str,
    stage_key: str,
    nonce: str,
    request_digest: str,
    incoming: dict[str, Any],
    deadline: float,
) -> Iterator[_ReadCapture]:
    """Scope observation around the worker's actual frozen script execution.

    This does not construct an OriginalLaunch or admit a run. Its fields are
    retained observations only. The worker must already have verified the real
    complete request, Source/runtime/code/nonce and incoming bytes before entry.
    """
    if _ACTIVE.get() is not None:
        raise ValueError("analysis returned-byte observation cannot replace an active stage owner")
    if (
        not isinstance(incoming, dict)
        or incoming.get("run_id") != run_id
        or incoming.get("stage_key") != stage_key
        or not isinstance(incoming.get("records"), list)
        or not isinstance(nonce, str)
        or len(nonce) != 32
        or any(char not in "0123456789abcdef" for char in nonce)
        or not isinstance(request_digest, str)
        or len(request_digest) != 64
        or any(char not in "0123456789abcdef" for char in request_digest)
    ):
        raise ValueError("analysis read observation omitted its actual verified worker request identity")
    remaining(deadline)
    repo, project = repo.absolute(), project.absolute()
    if not project.is_relative_to(repo / "projects") or project.is_symlink() or repo.is_symlink():
        raise ValueError("analysis read requires actual confined repository/project ownership")
    rows = {row["path"]: row for row in incoming["records"]}
    if len(rows) != len(incoming["records"]):
        raise ValueError("analysis read incoming original body roster is duplicated")
    owner = _ReadCapture(project, repo, run_id, stage_key, nonce, request_digest, rows, deadline)
    token = _ACTIVE.set(owner)
    try:
        owner.verify()
        yield owner
        owner.verify()
    finally:
        _ACTIVE.reset(token)


def read_analysis_bytes(project: Path, path: Path) -> bytes:
    """Return the actual held body and record those exact bytes when supervised.

    This API accepts no callback, status, expected body, original or alleged
    read list. It independently opens a complete regular confined file, checks
    its OS identity, retains the body, then returns precisely that same body.
    """
    project, path = project.absolute(), path.absolute()
    if not path.is_relative_to(project) or ".." in path.parts or project.is_symlink():
        raise ValueError("analysis read escaped its actual project")
    owner = _ACTIVE.get()
    if owner is None:
        return read_bytes_confined(project, path, max_bytes=MAX_FILE_BYTES)
    owner.verify()
    if project != owner.project:
        raise ValueError("analysis read supplied a different actual project owner")
    name = path.relative_to(project).as_posix()
    if (
        not (
            name in DATA_FILES
            or any(Path(name).is_relative_to(Path(root)) for root in DATA_ROOTS)
            or Path(name).is_relative_to(Path("output"))
        )
        or Path(name).is_relative_to(Path("output/.pipeline"))
        or any(part == ".env" or part.startswith(".env.") for part in Path(name).parts)
    ):
        raise ValueError("analysis read body is outside its declared noncredential data policy")
    before = _identity(path)
    content = read_bytes_confined(project, path, max_bytes=MAX_FILE_BYTES)
    if before != _identity(path):
        raise ValueError("analysis actual read body changed while returning its held bytes")
    owner.total_bytes += len(content)
    if len(owner.rows) >= 10000 or owner.total_bytes > 256 * 1024 * 1024:
        raise ValueError("analysis completed read observations exceed the held event/body ceilings")
    digest = hashlib.sha256(content).hexdigest()
    relative = (
        Path("output/.pipeline/analysis-data") / hashlib.sha256(owner.run_id.encode()).hexdigest() / "blobs" / digest
    )
    retained = project / relative
    try:
        previous = read_bytes_confined(project, retained, max_bytes=MAX_FILE_BYTES)
    except FileNotFoundError:
        atomic_write_bytes_confined(project, retained, content, mode=0o600)
    else:
        if previous != content:
            raise ValueError("analysis actual read body differs from its original run-owned retained hash slot")
    original = owner.incoming.get(name)
    origin = (
        "original-incoming-body"
        if original is not None and (original["sha256"], original["native_identity"]) == (digest, list(before))
        else "not-unchanged-selected-incoming-body; original-write-causality-unqualified"
    )
    if owner.write_observation is not None:
        written = owner.write_observation.completed_body(name, digest, list(before))
        if written is not None:
            origin = f"actual-completed-Source-write:{written}"
    owner.rows.append(
        {
            "ordinal": len(owner.rows) + 1,
            "path": name,
            "sha256": digest,
            "bytes": len(content),
            "native_identity": list(before),
            "retained_path": relative.as_posix(),
            "origin": origin,
            "consumer": _consumer(owner.repo),
        }
    )
    owner.verify()
    return content

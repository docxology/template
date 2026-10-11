"""Retain actual boundary data bytes around supervised analysis execution.

These snapshots are observations, never success, semantic truth or a file-read
trace. The Source controller supplies the run/stage and original finite clock.
Only the existing actual stage supervisor may couple them to its worker's
observed PID/OS result. Portable admission separately authenticates that owner.
"""

from __future__ import annotations

import hashlib
import json
import math
import stat
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory
from infrastructure.core.pipeline.artifacts._inventory import iter_bounded_tree_paths
from infrastructure.core.pipeline.fingerprints import canonical_digest

SCHEMA = "template-analysis-boundary-data-v1"
DATA_ROOTS = ("content", "data", "manuscript", "docs/manuscript")
DATA_FILES = ("figures.yaml", "tracks.yaml", "pyproject.toml")
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 256 * 1024 * 1024
MAX_FILES = 10000
MAX_DISCOVERY_PATHS = 100000


def remaining(deadline: float) -> float:
    """Check the existing supervisor clock; never create a replacement budget."""
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("analysis data custody needs the existing finite supervisor deadline")
    available = deadline - time.monotonic()
    if available <= 0:
        raise TimeoutError("analysis data custody exhausted the original supervisor deadline")
    return available


@dataclass(frozen=True)
class AnalysisDataFile:
    """One complete boundary inventory member and retained exact original body."""

    path: str
    sha256: str
    bytes: int
    retained_path: str
    native_identity: tuple[int, int, int, int, int]


def _selected_files(project: Path, deadline: float) -> tuple[tuple[str, ...], tuple[Path, ...]]:
    """Select complete declared data roots plus the existing stable-output policy."""
    roots = []
    files: set[Path] = set()
    discovered = 0

    def add(path: Path) -> None:
        if path not in files and len(files) >= MAX_FILES:
            raise ValueError("complete analysis boundary exceeds the held file ceiling during discovery")
        files.add(path)

    for name in DATA_ROOTS:
        remaining(deadline)
        root = project / name
        if not root.exists() and not root.is_symlink():
            continue
        if not stat.S_ISDIR(root.lstat().st_mode) or root.is_symlink():
            raise ValueError("analysis data root is a symlink or is not a directory: " + name)
        roots.append(name)
        for path in iter_bounded_tree_paths(root, max_paths=MAX_DISCOVERY_PATHS, original_deadline=deadline):
            remaining(deadline)
            discovered += 1
            if discovered > MAX_DISCOVERY_PATHS:
                raise ValueError("analysis source data discovery exceeds its held path ceiling")
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError("analysis data boundary contains a link or nonregular member")
            if stat.S_ISREG(mode):
                add(path)
    for name in DATA_FILES:
        path = project / name
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError("analysis data declaration is not a regular confined file")
            add(path)
    output = collect_stable_output_inventory(
        project / "output", max_snapshot_paths=MAX_DISCOVERY_PATHS, original_deadline=deadline
    )
    if output.issues:
        raise ValueError("analysis boundary stable-output inventory refused: " + "; ".join(output.issues))
    for path in output.files:
        remaining(deadline)
        add(path)
    selected = tuple(sorted(files))
    if len(selected) > MAX_FILES:
        raise ValueError("complete analysis boundary exceeds the held file ceiling")
    if any(
        any(part == ".env" or part.startswith(".env.") for part in path.relative_to(project).parts) for path in selected
    ):
        raise ValueError("analysis boundary cannot retain credential-named data")
    return tuple(roots), selected


def capture_analysis_data(
    project: Path,
    *,
    run_id: str,
    stage_key: str,
    deadline: float,
) -> dict[str, Any]:
    """Capture every selected byte once, preserving exact original bodies by hash.

    Identical retained bytes share storage within this run. This never reuses a
    prior outcome or skips execution, and retained body bytes are checked on
    every reuse. Source/SDK/run/process authenticity remains a separate boundary.
    """
    if not isinstance(run_id, str) or not run_id or not isinstance(stage_key, str) or not stage_key:
        raise ValueError("analysis data needs the actual nonempty run and stage identity")
    project = project.absolute()
    if project.is_symlink() or not stat.S_ISDIR(project.lstat().st_mode):
        raise ValueError("analysis data project must be a real directory")
    roots, files = _selected_files(project, deadline)
    blob_root = Path("output/.pipeline/analysis-data") / hashlib.sha256(run_id.encode()).hexdigest() / "blobs"
    rows = []
    identities = []
    total = 0
    for path in files:
        remaining(deadline)
        before = path.stat()
        identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        content = read_bytes_confined(project, path, max_bytes=MAX_FILE_BYTES)
        after = path.stat()
        if identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("analysis boundary body changed while capturing original bytes")
        total += len(content)
        if total > MAX_SNAPSHOT_BYTES:
            raise ValueError("complete analysis boundary exceeds its total held byte ceiling")
        digest = hashlib.sha256(content).hexdigest()
        retained = blob_root / digest
        target = project / retained
        try:
            existing = read_bytes_confined(project, target, max_bytes=MAX_FILE_BYTES)
        except FileNotFoundError:
            atomic_write_bytes_confined(project, target, content, mode=0o600)
        else:
            if existing != content:
                raise ValueError("retained analysis original body changed in its owned hash slot")
        rows.append(
            AnalysisDataFile(
                path.relative_to(project).as_posix(),
                digest,
                len(content),
                retained.as_posix(),
                identity,
            )
        )
        identities.append((path, identity))
    if _selected_files(project, deadline) != (roots, files):
        raise ValueError("complete analysis boundary membership changed while capturing original bytes")
    for path, expected in identities:
        actual = path.stat()
        if expected != (actual.st_dev, actual.st_ino, actual.st_size, actual.st_mtime_ns, actual.st_ctime_ns):
            raise ValueError("analysis data changed before boundary capture closed")
    body = {
        "schema": SCHEMA,
        "run_id": run_id,
        "stage_key": stage_key,
        "root_policy": list(DATA_ROOTS),
        "file_policy": list(DATA_FILES),
        "present_roots": list(roots),
        "output_policy": "stable-shippable-output-v1",
        "records": [{**asdict(row), "native_identity": list(row.native_identity)} for row in rows],
        "total_bytes": total,
        "claim_boundary": "boundary-inventory-only; not-per-read-lineage-or-scientific-truth",
    }
    if len(json.dumps(body, sort_keys=True).encode()) > 8 * 1024 * 1024:
        raise ValueError("complete analysis boundary declaration exceeds its retained JSON ceiling")
    remaining(deadline)
    return {**body, "content_digest": canonical_digest(body)}


def require_analysis_data(
    raw: object,
    project: Path,
    *,
    run_id: str,
    stage_key: str,
    deadline: float,
) -> None:
    """Reconstruct actual current membership and bytes; DATA supplies no subset."""
    if raw != capture_analysis_data(project, run_id=run_id, stage_key=stage_key, deadline=deadline):
        raise ValueError("analysis current data differs from the complete admitted boundary snapshot")

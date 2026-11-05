"""Git-bound public Source bodies, including exactly declared derived fixture DATA.

The declaration is committed Source, never a preparation receipt or a prefix
exemption. Readers authenticate it before interpreting any derived bodies.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.pipeline.artifacts._inventory import _is_ignored_output_relative
from infrastructure.core.pipeline.fingerprint_files import anchored_parent, observation, open_directory
from infrastructure.core.pipeline.fingerprints import _ROOT_SOURCE_CONTROLS
from infrastructure.project.acceptance_fixture_preparation import MANIFEST_PATH, parse_fixture_manifest
from infrastructure.project.public_reference_git import (
    GitFile,
    GitReference,
    MAX_FILES,
    blob_identity,
    committed_blobs,
    remaining,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import _READINESS_SOURCE_METADATA_NAMES, _public_roots
from infrastructure.reporting.release_readiness_snapshot import PUBLIC_ROOT_FILES, PUBLIC_AGENT_FILES, SnapshotReader

MAX_SOURCE_BYTES = 512 * 1024 * 1024
_FIXTURE_ROOTS = (
    "tests/fixtures/real_codebases/requests",
    "tests/fixtures/real_codebases/fastapi",
    "tests/fixtures/timeseries",
)
FixtureBody = tuple[int, str, bool]
BlobBinding = tuple[GitFile, str]


@dataclass(frozen=True)
class FixtureAdmission:
    """Held fixture DATA and original full physical directory observations."""

    root: Path
    reader: SnapshotReader
    reference: GitReference
    files: tuple[tuple[str, FixtureBody], ...]
    directories: tuple[tuple[str, tuple[int, ...]], ...]
    absent_groups: tuple[str, ...]

    def verify(self, deadline: float) -> None:
        """Refuse later hidden entries, directory ABA and held-body replacement."""
        remaining(deadline)
        if not self.reader.unchanged():
            raise ValueError("Source fixture held bodies changed after admission")
        for relative, expected in self.directories:
            with anchored_parent(self.root / relative) as parent:
                if parent is None:
                    raise ValueError("Source fixture directory disappeared after admission")
                with open_directory(parent, Path(relative).name) as descriptor:
                    if observation(os.fstat(descriptor)) != expected:
                        raise ValueError("Source fixture directory changed after admission")
        current = admit_source_fixtures(self.root, self.reader, self.reference, deadline)
        if (
            current.files != self.files
            or current.directories != self.directories
            or current.absent_groups != self.absent_groups
        ):
            raise ValueError("Source fixture physical census changed after admission")


def _committed_public_bodies(source_root: Path, reference: GitReference, deadline: float) -> set[str]:
    """Select committed paths independently of current filesystem membership."""
    roots, excluded = _public_roots(source_root)
    prefixes = tuple(root.relative_to(source_root).as_posix() + "/" for root in roots)
    exclusions = {root.relative_to(source_root).as_posix() for root in excluded}
    excluded_prefixes = tuple(root + "/" for root in exclusions)
    outputs = tuple("projects/" + scope + "/output/" for scope in PUBLIC_PROJECT_NAMES)
    selected = set()
    for relative in committed_blobs(reference):
        remaining(deadline)
        if relative in PUBLIC_ROOT_FILES | PUBLIC_AGENT_FILES:
            selected.add(relative)
            continue
        output = next((prefix for prefix in outputs if relative.startswith(prefix)), None)
        if output is not None:
            if not _is_ignored_output_relative(Path(relative[len(output) :])):
                selected.add(relative)
            continue
        base = next((prefix for prefix in prefixes if relative.startswith(prefix)), None)
        if base is None or relative in exclusions or relative.startswith(excluded_prefixes):
            continue
        parts = relative[len(base) :].split("/")
        if (
            any(part in _READINESS_SOURCE_METADATA_NAMES | {"__pycache__"} for part in parts)
            or any(Path(part).suffix in {".pyc", ".pyo"} for part in parts)
            or parts[0] in _ROOT_SOURCE_CONTROLS
            or len(parts) >= 2
            and parts[0] == "src"
            and parts[1].endswith(".egg-info")
        ):
            continue
        selected.add(relative)
    return selected


def _held_body(
    reader: SnapshotReader, relative: str, *, max_bytes: int = 64 * 1024 * 1024
) -> tuple[bytes, str, os.stat_result]:
    path = reader.public_path(relative)
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"Source body is not a regular file: {relative!r}")
    held = reader.read(relative, max_bytes=max_bytes)
    if held.identity != (metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns) or observation(
        path.lstat()
    ) != observation(metadata):
        raise ValueError(f"Source body changed during held admission: {relative!r}")
    return held.content, held.sha256, metadata


def _raw_binding(relative: str, body: bytes, metadata: os.stat_result, binding: BlobBinding) -> None:
    record, object_format = binding
    if blob_identity(body, object_format) != record.oid:
        raise ValueError(f"Source body differs from its original committed blob: {relative!r}")
    if bool(metadata.st_mode & 0o111) != (record.mode == "100755"):
        raise ValueError(f"Source body mode differs from its committed blob: {relative!r}")


def _present_group(root: Path, relative: str) -> bool:
    with anchored_parent(root / relative) as parent:
        if parent is None:
            return False
        try:
            metadata = os.stat(Path(relative).name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"Source fixture group is linked or not a directory: {relative!r}")
        return True


def _absence_ancestor(root: Path, relative: str, deadline: float) -> tuple[str, tuple[int, ...]]:
    """Hold the closest existing public ancestor of an absent fixed group."""
    path = root / relative
    while path.parent != root:
        remaining(deadline)
        with anchored_parent(path) as parent:
            if parent is not None:
                return path.parent.relative_to(root).as_posix(), observation(os.fstat(parent))
        path = path.parent
    raise ValueError("absent Source fixture group lacks its required public ancestor")


def admit_source_fixtures(
    root: Path, reader: SnapshotReader, reference: GitReference, deadline: float
) -> FixtureAdmission:
    """Authenticate declarations/seeds and census every physical prepared group.

    Entire absent groups are permitted for local authoring. Present groups must
    have exactly their declared regular files and ancestor directories, including
    all entries hidden by the ordinary canonical Source exclusions.
    """
    remaining(deadline)
    if root != reader.root:
        raise ValueError("Source fixture root differs from its held public reader")
    committed = committed_blobs(reference)
    manifest_binding = committed.get(MANIFEST_PATH)
    if manifest_binding is None:
        if (
            (root / MANIFEST_PATH).exists()
            or (root / MANIFEST_PATH).is_symlink()
            or any(_present_group(root, name) for name in _FIXTURE_ROOTS)
        ):
            raise ValueError("Source fixtures require a committed raw Git manifest")
        ancestors = {_absence_ancestor(root, name, deadline) for name in _FIXTURE_ROOTS}
        return FixtureAdmission(root, reader, reference, (), tuple(sorted(ancestors)), _FIXTURE_ROOTS)
    body, _, metadata = _held_body(reader, MANIFEST_PATH)
    _raw_binding(MANIFEST_PATH, body, metadata, manifest_binding)
    manifest = parse_fixture_manifest(body)
    authorized: dict[str, FixtureBody] = {}
    held_directories: list[tuple[str, tuple[int, ...]]] = []
    absent_groups: list[str] = []
    count = total = 0
    for group in manifest["groups"]:
        remaining(deadline)
        base = group["root"]
        expected: dict[str, FixtureBody] = {}
        for declaration in group["files"]:
            remaining(deadline)
            name = declaration["path"]
            if "source" in declaration:
                source = declaration["source"]
                binding = committed.get(source)
                if binding is None:
                    raise ValueError(f"Source fixture seed lacks a committed blob: {source!r}")
                seed, digest, seed_metadata = _held_body(reader, source)
                _raw_binding(source, seed, seed_metadata, binding)
                total += len(seed)
                if total > MAX_SOURCE_BYTES:
                    raise ValueError("Source fixture seeds exceed the existing held-byte bound")
                expected[name] = (len(seed), digest, bool(seed_metadata.st_mode & 0o111))
            else:
                expected[name] = (declaration["bytes"], declaration["sha256"], declaration["executable"])
        directories = set(group["directories"])
        if not _present_group(root, base):
            absent_groups.append(base)
            held_directories.append(_absence_ancestor(root, base, deadline))
            continue
        observed_files: set[str] = set()
        observed_directories: set[str] = set()

        def census(descriptor: int, prefix: str) -> None:
            nonlocal count, total
            before = observation(os.fstat(descriptor))
            held_directories.append((base + ("/" + prefix.rstrip("/") if prefix else ""), before))
            with os.scandir(descriptor) as entries:
                for entry in entries:
                    remaining(deadline)
                    count += 1
                    if count > MAX_FILES:
                        raise ValueError("Source fixture tree exceeds the existing entry bound")
                    name = prefix + entry.name
                    relative = base + "/" + name
                    metadata = os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)
                    if name in directories and stat.S_ISDIR(metadata.st_mode):
                        observed_directories.add(name)
                        with open_directory(descriptor, entry.name) as child:
                            census(child, name + "/")
                    elif name in expected and stat.S_ISREG(metadata.st_mode):
                        expected_size, expected_hash, expected_executable = expected[name]
                        if metadata.st_size > 64 * 1024 * 1024:
                            raise ValueError("Source fixture body exceeds the existing byte bound")
                        body, digest, held_metadata = _held_body(reader, relative)
                        if observation(held_metadata) != observation(metadata):
                            raise ValueError(f"Source fixture path changed during admission: {relative!r}")
                        binding = committed.get(relative)
                        if binding is not None:
                            _raw_binding(relative, body, held_metadata, binding)
                        if (len(body), digest, bool(held_metadata.st_mode & 0o111)) != (
                            expected_size,
                            expected_hash,
                            expected_executable,
                        ):
                            raise ValueError(f"Source fixture body differs from its exact declaration: {relative!r}")
                        if observation(os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)) != observation(
                            metadata
                        ):
                            raise ValueError(f"Source fixture path changed during admission: {relative!r}")
                        total += len(body)
                        if total > MAX_SOURCE_BYTES:
                            raise ValueError("Source fixture DATA exceeds the existing held-byte bound")
                        observed_files.add(name)
                        authorized[relative] = expected[name]
                    else:
                        # No body read, path following or private filename echo.
                        raise ValueError(f"Source fixture group has an undeclared or nonregular entry: {group['id']!r}")
            if observation(os.fstat(descriptor)) != before:
                raise ValueError("Source fixture directory changed during census")

        with anchored_parent(root / base) as parent:
            if parent is None:
                raise ValueError("Source fixture group disappeared during admission")
            with open_directory(parent, Path(base).name) as descriptor:
                census(descriptor, "")
        if observed_files != set(expected) or observed_directories != directories:
            raise ValueError(f"Source fixture group has an incomplete file/directory census: {group['id']!r}")
    if not reader.unchanged():
        raise ValueError("Source fixture declarations or bodies changed during admission")
    remaining(deadline)
    return FixtureAdmission(
        root,
        reader,
        reference,
        tuple(sorted(authorized.items())),
        tuple(sorted(set(held_directories))),
        tuple(sorted(absent_groups)),
    )


def admit_source_bodies(
    root: Path,
    reader: SnapshotReader,
    reference: GitReference,
    records: tuple[tuple[str, str, str], ...],
    deadline: float,
) -> tuple[dict[str, str], FixtureAdmission]:
    """Bind complete canonical bodies to raw Git or exact Git-bound fixture DATA."""
    fixtures = admit_source_fixtures(root, reader, reference, deadline)
    if len(records) > MAX_FILES or len({relative for relative, _, _ in records}) != len(records):
        raise ValueError("Source canonical inventory exceeds its bound or repeats a path")
    fixture_files = dict(fixtures.files)
    committed = committed_blobs(reference)
    observed = {relative for relative, kind, _ in records if kind in {"file", "deliverable"}}
    missing = _committed_public_bodies(root, reference, deadline) - observed
    if missing:
        raise ValueError(f"Source is missing a committed canonical body: {min(missing)!r}")
    if set(fixture_files) - observed:
        raise ValueError("Source fixture body is outside the complete canonical inventory")
    files: dict[str, str] = {}
    total = 0
    for relative, kind, digest in records:
        remaining(deadline)
        if kind == "missing":
            raise ValueError("Source has a missing canonical source root")
        if kind not in {"file", "deliverable"}:
            continue
        body, actual_hash, metadata = _held_body(reader, relative)
        total += len(body)
        if total > MAX_SOURCE_BYTES:
            raise ValueError("complete public Source DATA exceeds its held-byte bound")
        if kind == "file" and actual_hash != digest:
            raise ValueError(f"Source body changed between inventory and admission: {relative!r}")
        binding = committed.get(relative)
        if binding is not None:
            _raw_binding(relative, body, metadata, binding)
        elif relative not in fixture_files:
            raise ValueError(f"Source body is untracked or differs from the committed blob: {relative!r} ({kind})")
        elif (len(body), actual_hash, bool(metadata.st_mode & 0o111)) != fixture_files[relative]:
            raise ValueError(f"Source fixture body changed after its full physical census: {relative!r}")
        files[relative] = actual_hash
    if not files:
        raise ValueError("Source requires a nonempty canonical public source inventory")
    if not reader.unchanged():
        raise ValueError("Source body changed during complete admission")
    remaining(deadline)
    return files, fixtures

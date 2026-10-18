"""External native source bindings and a real full-Git mirror correspondence.

Only the trusted original controller/current reader constructs the bindings.
Transport descriptors are observations, never source or provider authority.
The enclosing supervisor supplies one already-live operation deadline.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.implementation_custody import verify_implementation_custody
from infrastructure.core.pipeline.fingerprints import canonical_digest, tree_records
from infrastructure.core.pipeline.fingerprint_files import (
    anchored_parent,
)
from infrastructure.project.public_reference import (
    MAX_REFERENCE_BYTES,
    PublicReference,
    admit_public_reference,
    reference_binding,
)
from infrastructure.project.public_reference_git import (
    GitReference,
    MAX_FILES,
    committed_blobs,
    inventory,
    remaining,
)
from infrastructure.project.public_source_body_admission import FixtureAdmission, admit_source_fixtures
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_projection_contracts import (
    ProjectionSourceUnsupported,
)
from infrastructure.reporting.readiness_receipts import (
    _READINESS_SOURCE_METADATA_NAMES,
    _public_roots,
)
from infrastructure.reporting.release_readiness_snapshot import (
    SnapshotReader,
    json_object_from_bytes,
)

DESCRIPTOR_SCHEMA = "template-native-external-source-observation-v2"
SourceRecords = tuple[tuple[str, str, str], ...]
DirectoryIdentities = tuple[tuple[Path, tuple[int, int]], ...]


@dataclass(frozen=True)
class NativeExternalSourceBindings:
    """Externally nominated inputs, not fields decoded from producer output.

    Source root/commit/fingerprint come from the original explicit
    reference_binding. The supervisor nominates the separate full-Git mirror,
    observes its physical identity, and admits the selected actual SDK before
    launch. Later readers independently supply their own current bindings.
    """

    original_source_root: Path
    expected_commit: str
    expected_source_identity: str
    current_root: Path
    current_root_identity: tuple[int, int]
    selected_sdk_package_root: Path
    expected_implementation_bytes: bytes
    run_id: str


def _physical_directory(path: Path) -> tuple[int, int]:
    if not path.is_absolute() or path.absolute() != path.resolve(strict=True):
        raise ValueError("native source bindings require exact non-symlink absolute roots")
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("native source binding root is not an actual directory")
    return metadata.st_dev, metadata.st_ino


def _verify_selected_sdk(bindings: NativeExternalSourceBindings, fresh_pycache_prefix: Path | None) -> None:
    import infrastructure

    _physical_directory(bindings.selected_sdk_package_root)
    if infrastructure.__file__ is None:
        raise ValueError("native selected SDK location is unavailable")
    if Path(infrastructure.__file__).absolute().parent != bindings.selected_sdk_package_root:
        raise ValueError("native bootstrap loaded a different SDK/provider root")
    expected = json_object_from_bytes(bindings.expected_implementation_bytes)
    verify_implementation_custody(expected, fresh_pycache_prefix=fresh_pycache_prefix)


def _anchored_directory_identity(path: Path, deadline: float) -> tuple[int, int]:
    """Observe a real directory through the existing held ancestor policy."""
    remaining(deadline)
    if not path.is_absolute() or path.absolute() != path.resolve(strict=True):
        raise ValueError("current source directory witness refuses an aliased locator")
    if path == Path(path.anchor):
        return _physical_directory(path)
    # Identity witnesses do not enumerate this directory. Hold it as an
    # ancestor of an unexamined lexical child so the existing search-only
    # policy applies, including named-inode closing checks on the directory.
    # Actual Source enumeration still requires its own readable handles.
    with anchored_parent(path / ".native-directory-identity") as descriptor:
        if descriptor is None:
            raise ValueError("current source directory witness has a missing ancestor")
        observed = os.fstat(descriptor)
        result = observed.st_dev, observed.st_ino
    remaining(deadline)
    return result


def _observe_source_directory_identities(root: Path, records: SourceRecords, deadline: float) -> DirectoryIdentities:
    """Hold actual source/ancestor identities once, before current file snapshots.

    Output/runtime children are excluded. Source directory and lexical ancestor
    inode identities survive allowed output writes, but replacements with
    unchanged hardlinked leaves or empty directories cannot hide in digests.
    """
    paths = {root, *root.parents}
    for relative, kind, _ in records:
        remaining(deadline)
        path = root / relative
        paths.update(path.parents)
        if kind == "directory":
            paths.add(path)
    if len(paths) > MAX_FILES:
        raise ValueError("current source directory witnesses exceed the existing entry bound")
    observed = tuple((path, _anchored_directory_identity(path, deadline)) for path in sorted(paths))
    _verify_source_directory_identities(observed, deadline)
    return observed


def _verify_source_directory_identities(identities: DirectoryIdentities, deadline: float) -> None:
    """Require the same actual directories; never replace expected identities."""
    for path, expected in identities:
        if _anchored_directory_identity(path, deadline) != expected:
            raise ValueError("current source/ancestor directory was physically replaced")
    remaining(deadline)


def _pure_source_records(root: Path, reader: SnapshotReader, deadline: float) -> SourceRecords:
    """Reuse complete readiness source exclusions, preserving directories/names."""
    remaining(deadline)
    roots, excluded = _public_roots(root)
    declared_roots = frozenset(roots)

    def admit_path(path: Path) -> None:
        relative = path.relative_to(root).as_posix()
        reader.public_path(
            relative + "/.reference-directory-policy" if path in declared_roots and path.is_dir() else relative
        )

    records: list[tuple[str, str, str]] = []
    total_bytes = 0
    for base in roots:
        remaining(deadline)
        for name, kind, digest in tree_records(
            base,
            source=True,
            excluded_roots=excluded,
            excluded_names=_READINESS_SOURCE_METADATA_NAMES,
            path_admission=admit_path,
        ):
            remaining(deadline)
            path = base if name == "." else base / name
            relative = path.relative_to(root).as_posix()
            if kind not in {"file", "directory"}:
                raise ValueError("native mirror has a missing or unsupported canonical source entry")
            records.append((relative, kind, digest))
            if len(records) > MAX_FILES:
                raise ValueError("native mirror source inventory exceeds the existing bound")
            if kind == "file":
                snapshot = reader.read(relative)
                total_bytes += len(snapshot.content)
                if snapshot.sha256 != digest or total_bytes > MAX_REFERENCE_BYTES:
                    raise ValueError("native mirror source changed or exceeds the existing held-byte bound")
    result = tuple(sorted(records))
    if len({row[0] for row in result}) != len(result) or not reader.unchanged():
        raise ValueError("native mirror repeats or changes an admitted source path")
    remaining(deadline)
    return result


def _verify_current_source_modes(
    root: Path, reader: SnapshotReader, git: GitReference, records: SourceRecords, deadline: float
) -> FixtureAdmission:
    """Census current fixture DATA before checking raw-Git or declared modes."""
    fixtures = admit_source_fixtures(root, reader, git, deadline)
    fixture_files = dict(fixtures.files)
    blobs = committed_blobs(git)
    for relative, kind, _ in records:
        remaining(deadline)
        if kind != "file":
            continue
        binding = blobs.get(relative)
        if binding is not None:
            executable = binding[0].mode == "100755"
        elif relative in fixture_files:
            executable = fixture_files[relative][2]
        else:
            raise ValueError("native current source lacks a committed blob or admitted fixture body")
        metadata = reader.read(relative).path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or bool(metadata.st_mode & 0o111) != executable:
            raise ValueError("native current mirror source type/mode differs from its admitted source")
    fixtures.verify(deadline)
    return fixtures


@dataclass(frozen=True)
class NativeSourceContext:
    """Held immutable reference plus exact current full-Git source correspondence."""

    bindings: NativeExternalSourceBindings
    reference: PublicReference
    current_source_reader: SnapshotReader
    source_records: SourceRecords
    current_source_directories: DirectoryIdentities
    fresh_pycache_prefix: Path | None

    def _verify_current_source(self, current_reader: SnapshotReader, deadline: float) -> None:
        """Exact current-only guard, used again after every closing custody call."""
        root = self.bindings.current_root
        _verify_source_directory_identities(self.current_source_directories, deadline)
        records = _pure_source_records(root, self.current_source_reader, deadline)
        if records != self.source_records:
            raise ValueError("native current mirror directory/negative/file source inventory differs")
        fixtures = _verify_current_source_modes(root, self.current_source_reader, self.reference.git, records, deadline)
        if (fixtures.files, fixtures.absent_groups) != (
            self.reference.fixtures.files,
            self.reference.fixtures.absent_groups,
        ):
            raise ValueError("native current fixture census differs from admitted original source")
        for relative, kind, _ in records:
            remaining(deadline)
            if kind != "file":
                continue
            actual = self.current_source_reader.read(relative)
            if actual.content != self.reference.read(relative):
                raise ValueError("native current mirror source bytes differ from admitted original source")
        if not self.current_source_reader.unchanged() or not current_reader.unchanged():
            raise ValueError("native current source/artifact snapshots changed during correspondence")
        if _physical_directory(root) != self.bindings.current_root_identity:
            raise ValueError("native current mirror was replaced during correspondence")
        _verify_source_directory_identities(self.current_source_directories, deadline)
        fixtures.verify(deadline)
        remaining(deadline)

    def verify_correspondence(
        self,
        reference: PublicReference,
        current_root: Path,
        current_reader: SnapshotReader,
        deadline: float,
    ) -> None:
        """Fit SourceCorrespondence without a no-op or output-derived authority."""
        with self._correspondence_guard(reference, current_root, current_reader, deadline):
            pass

    @contextmanager
    def _correspondence_guard(
        self,
        reference: PublicReference,
        current_root: Path,
        current_reader: SnapshotReader,
        deadline: float,
    ) -> Iterator[None]:
        """Bracket fixed synchronous held-DATA checks, never a child or capability.

        Each invocation opens and closes the complete original correspondence.
        No verified token, caller-selected callback or reusable result is yielded.
        """
        remaining(deadline)
        bindings = self.bindings
        if (
            reference is not self.reference
            or current_root != bindings.current_root
            or current_reader.root != current_root
        ):
            raise ValueError("native source correspondence was supplied a different original/current binding")
        if _physical_directory(current_root) != bindings.current_root_identity:
            raise ValueError("native current mirror root was physically replaced")
        _verify_selected_sdk(bindings, self.fresh_pycache_prefix)
        reference.verify_unchanged(deadline=deadline)
        before_git = inventory(current_root, bindings.expected_commit, deadline)
        if before_git != reference.git:
            raise ValueError("native current mirror Root/index/pin membership differs from admitted original source")
        self._verify_current_source(current_reader, deadline)
        try:
            yield None
        finally:
            if self.bindings is not bindings or self.reference is not reference or current_reader.root != current_root:
                raise ValueError("native source correspondence binding changed inside its lexical checks")
            if inventory(current_root, bindings.expected_commit, deadline) != before_git:
                raise ValueError("native current mirror Git custody changed during correspondence")
            reference.verify_unchanged(deadline=deadline)
            _verify_selected_sdk(bindings, self.fresh_pycache_prefix)
            if inventory(current_root, bindings.expected_commit, deadline) != before_git:
                raise ValueError("native current mirror Git custody changed during closing source/SDK checks")
            # No reference/SDK custody or native Git verification call follows.
            # In particular, mutation during the last native Git query is observed.
            self._verify_current_source(current_reader, deadline)

    def descriptor(self, scope: str, *, deadline: float) -> bytes:
        """Emit a supervisor-retained observation after actual original admission.

        An outer original process must bind these exact bytes to spec/run/PID,
        selected bootstrap and its supervised result. This is not a capability
        factory for receipt readers and never transports a membership tuple.
        """
        if scope not in PUBLIC_PROJECT_NAMES:
            raise ValueError("native source descriptor requires an exact public scope")
        self.verify_correspondence(
            self.reference,
            self.bindings.current_root,
            self.current_source_reader,
            deadline,
        )
        return self._descriptor_data(scope, deadline=deadline)

    def _descriptor_data(self, scope: str, *, deadline: float) -> bytes:
        """Format held observation DATA; callers supply their fresh enclosing guard."""
        if scope not in PUBLIC_PROJECT_NAMES:
            raise ValueError("native source descriptor requires an exact public scope")
        value = {
            "schema_version": DESCRIPTOR_SCHEMA,
            "run_id": self.bindings.run_id,
            "scope": scope,
            "original_source": {
                "root": str(self.reference.root),
                "commit": self.reference.commit,
                "source_identity": self.reference.source_identity,
                "root_identity": list(self.reference.root_identity),
            },
            "current_mirror": {
                "root": str(self.bindings.current_root),
                "root_identity": list(self.bindings.current_root_identity),
                "source_records_digest": canonical_digest(self.source_records),
                "source_directory_identities_digest": canonical_digest(
                    tuple((str(path), identity) for path, identity in self.current_source_directories)
                ),
                "correspondence_kind": "actual-native-git-and-exact-pure-source",
            },
            "selected_sdk": {
                "package_root": str(self.bindings.selected_sdk_package_root),
                "implementation_sha256": hashlib.sha256(self.bindings.expected_implementation_bytes).hexdigest(),
            },
        }
        remaining(deadline)
        return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def admit_external_native_source(
    bindings: NativeExternalSourceBindings,
    *,
    deadline: float,
    fresh_pycache_prefix: Path | None = None,
) -> NativeSourceContext:
    """Admit once per original caller/worker/reader operation under its clock.

    This calls the existing real PublicReference API. Its committed bytes,
    literal version, full roster, selected SDK equality and pin checks are
    unchanged. Missing external input is handled by the caller's blocked path.
    Archives/partial mirrors without actual native Root custody remain blocked.
    """
    remaining(deadline)
    if re.fullmatch(r"[0-9a-f]{32}", bindings.run_id) is None:
        raise ValueError("native external source binding needs the supervisor's exact run identity")
    if len(bindings.current_root_identity) != 2 or any(
        type(value) is not int or value < 0 for value in bindings.current_root_identity
    ):
        raise ValueError("native mirror physical identity must be independently supervisor-observed")
    _physical_directory(bindings.original_source_root)
    if bindings.current_root == bindings.original_source_root:
        raise ProjectionSourceUnsupported("native regeneration requires a separate immutable OriginalSourceRoot")
    if _physical_directory(bindings.current_root) != bindings.current_root_identity:
        raise ValueError("native current mirror differs from its supervisor-nominated physical root")
    _verify_selected_sdk(bindings, fresh_pycache_prefix)
    reference = admit_public_reference(
        bindings.original_source_root,
        expected_commit=bindings.expected_commit,
        expected_source_identity=bindings.expected_source_identity,
        deadline=deadline,
        fresh_pycache_prefix=fresh_pycache_prefix,
    )
    source_records = tuple(row for row in reference.records if row[1] != "deliverable")
    source_directories = _observe_source_directory_identities(bindings.current_root, source_records, deadline)
    context = NativeSourceContext(
        bindings,
        reference,
        SnapshotReader(bindings.current_root),
        source_records,
        source_directories,
        fresh_pycache_prefix,
    )
    context.verify_correspondence(reference, bindings.current_root, context.current_source_reader, deadline)
    return context


def admit_explicitly_bound_native_source(
    current_root: Path,
    *,
    environment: Mapping[str, str],
    current_root_identity: tuple[int, int],
    selected_sdk_package_root: Path,
    expected_implementation_bytes: bytes,
    run_id: str,
    deadline: float,
    fresh_pycache_prefix: Path | None = None,
) -> NativeSourceContext | None:
    """Use the existing all-or-none external DATA binding; never infer one."""
    remaining(deadline)
    binding = reference_binding(environment)
    if binding is None:
        return None
    source_root, expected_commit, expected_source_identity = binding
    context = admit_external_native_source(
        NativeExternalSourceBindings(
            source_root,
            expected_commit,
            expected_source_identity,
            current_root,
            current_root_identity,
            selected_sdk_package_root,
            expected_implementation_bytes,
            run_id,
        ),
        deadline=deadline,
        fresh_pycache_prefix=fresh_pycache_prefix,
    )
    if reference_binding(environment) != binding:
        raise ValueError("native external DATA binding changed during original admission")
    remaining(deadline)
    return context


def validate_original_source_descriptor(
    raw: bytes,
    *,
    externally_bound_sha256: str,
    run_id: str,
    scope: str,
    deadline: float,
) -> dict[str, Any]:
    """Validate externally held exact original transport bytes; grant no authority.

    The expected hash/run/scope belong to the enclosing authenticated original
    supervisor/process binding, never the same producer descriptor or JSON.
    A later reader must independently admit its current NativeSourceContext.
    """
    remaining(deadline)
    if re.fullmatch(r"[0-9a-f]{32}", run_id) is None or scope not in PUBLIC_PROJECT_NAMES:
        raise ValueError("original native descriptor needs externally bound exact run/scope")
    if (
        re.fullmatch(r"[0-9a-f]{64}", externally_bound_sha256) is None
        or hashlib.sha256(raw).hexdigest() != externally_bound_sha256
    ):
        raise ValueError("original native source descriptor differs from the external supervisor binding")
    value = json_object_from_bytes(raw)
    expected_fields = {
        "schema_version",
        "run_id",
        "scope",
        "original_source",
        "current_mirror",
        "selected_sdk",
    }
    if (
        set(value) != expected_fields
        or value["schema_version"] != DESCRIPTOR_SCHEMA
        or value["run_id"] != run_id
        or value["scope"] != scope
    ):
        raise ValueError("original native source descriptor schema/run/scope differs")
    schemas = {
        "original_source": {"root", "commit", "source_identity", "root_identity"},
        "current_mirror": {
            "root",
            "root_identity",
            "source_records_digest",
            "source_directory_identities_digest",
            "correspondence_kind",
        },
        "selected_sdk": {"package_root", "implementation_sha256"},
    }
    for key, fields in schemas.items():
        if not isinstance(value[key], dict) or set(value[key]) != fields:
            raise ValueError("original native source descriptor has incomplete or additional binding fields")
    for key in ("original_source", "current_mirror"):
        root = value[key]["root"]
        identity = value[key]["root_identity"]
        if (
            not isinstance(root, str)
            or not root
            or "\0" in root
            or not isinstance(identity, list)
            or len(identity) != 2
            or any(type(item) is not int or item < 0 for item in identity)
        ):
            raise ValueError("original native source descriptor has invalid root/physical identity labels")
    if value["current_mirror"]["root"] == value["original_source"]["root"]:
        raise ValueError("original native descriptor aliases the immutable and mutable roots")
    commit = value["original_source"]["commit"]
    if not isinstance(commit, str) or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit) is None:
        raise ValueError("original native descriptor commit is not a full external identity")
    for key, name in (
        ("original_source", "source_identity"),
        ("current_mirror", "source_records_digest"),
        ("current_mirror", "source_directory_identities_digest"),
        ("selected_sdk", "implementation_sha256"),
    ):
        digest = value[key][name]
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("original native descriptor has an invalid source/provider digest")
    sdk_root = value["selected_sdk"]["package_root"]
    if not isinstance(sdk_root, str) or not sdk_root or "\0" in sdk_root:
        raise ValueError("original native descriptor has an invalid SDK origin label")
    if value["current_mirror"]["correspondence_kind"] != "actual-native-git-and-exact-pure-source":
        raise ValueError("original native source descriptor claims unsupported mirror correspondence")
    remaining(deadline)
    return value

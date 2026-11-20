"""Complete committed public source DATA, distinct from the loaded platform SDK."""

from __future__ import annotations

import os
import re
import stat
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.implementation_custody import capture_implementation_custody, verify_implementation_custody
from infrastructure.core.pipeline.artifacts._inventory import collect_stable_output_inventory
from infrastructure.core.pipeline.fingerprint_files import _relative_name
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_reference_git import (
    GitReference,
    MAX_FILES,
    inventory,
    remaining,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.public_source_body_admission import (
    FixtureAdmission,
    admit_source_bodies,
)
from infrastructure.project.public_template_contract import validate_public_template_contract
from infrastructure.reporting.readiness_receipts import _deliverable_fingerprint, _public_roots, _public_source_trees
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

MAX_REFERENCE_BYTES = 512 * 1024 * 1024
_BINDING_KEYS = (
    "TEMPLATE_PUBLIC_REFERENCE_ROOT",
    "TEMPLATE_PUBLIC_REFERENCE_COMMIT",
    "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT",
)
# A disposable pipeline copy admits the same original DATA for discovery and
# imports without claiming native-origin tool custody, so it binds through its
# own key family. Rendering still uses the local toolchain in that copy.
PIPELINE_REFERENCE_KEYS = (
    "TEMPLATE_PIPELINE_REFERENCE_ROOT",
    "TEMPLATE_PIPELINE_REFERENCE_COMMIT",
    "TEMPLATE_PIPELINE_REFERENCE_FINGERPRINT",
)


def _identity(path: Path) -> tuple[int, int, int, int, int]:
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("public reference directory is missing, linked or replaced")
    return metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns


def _directory(reader: SnapshotReader, relative: str) -> Path:
    """Apply existing public-path policy to a directory without inventing a file."""
    return reader.public_path(relative + "/.reference-directory-policy").parent


def _path_admission(reader: SnapshotReader) -> Callable[[Path], None]:
    """Apply lexical policy inside the no-follow, closing-checked tree walker.

    ``tree_records`` holds and verifies every directory and file it traverses.
    Re-resolving each path here duplicates that physical traversal for every
    ancestor of every member. Direct directory/byte and deliverable consumers
    still use ``public_path``/``read`` with their independent physical checks.
    """
    roots = frozenset(_public_roots(reader.root)[0])

    def admitted(path: Path) -> None:
        relative = _relative_name(path, reader.root)
        if path in roots and path.is_dir():
            reader._public_lexical_path(relative + "/.reference-directory-policy")
        else:
            reader._public_lexical_path(relative)

    return admitted


def _canonical_inventory(root: Path) -> tuple[tuple[str, str, str], ...]:
    """Return the canonical inventory without hashing stable deliverable bodies."""
    return _observe_reference(root, fingerprint=False)[0]


def _observe_reference(root: Path, *, fingerprint: bool) -> tuple[tuple[tuple[str, str, str], ...], str | None]:
    """Derive the roster and optional fingerprint from the same fresh Source census."""
    reader = SnapshotReader(root)
    observed = []
    trees = []
    for relative_root, tree in _public_source_trees(root, path_admission=_path_admission(reader)):
        if fingerprint:
            trees.append((relative_root, tree))
        base = root / relative_root
        for name, kind, digest in tree:
            path = base if name == "." else base / name
            observed.append((_relative_name(path, root), kind, digest))
            if len(observed) > MAX_FILES:
                raise ValueError("canonical public source DATA exceeds its entry bound")
    deliverables = {}
    for project in PUBLIC_PROJECT_NAMES:
        output = root / "projects" / project / "output"
        if output.exists():
            stable = collect_stable_output_inventory(output)
            if stable.issues:
                raise ValueError("public reference stable deliverable inventory is unavailable")
            for path in stable.files:
                relative = _relative_name(path, root)
                reader.public_path(relative)
                observed.append((relative, "deliverable", ""))
                if len(observed) > MAX_FILES:
                    raise ValueError("canonical public reference exceeds its entry bound")
            if fingerprint:
                deliverables[project] = _deliverable_fingerprint(root, output, stable.files)
        elif fingerprint:
            deliverables[project] = canonical_digest([])
    result = tuple(sorted(observed))
    if len({row[0] for row in result}) != len(result):
        raise ValueError("canonical source DATA repeats an admitted path")
    source_identity = (
        canonical_digest({"sources": canonical_digest(trees), "deliverables": deliverables}) if fingerprint else None
    )
    return result, source_identity


@dataclass(frozen=True)
class PublicReference:
    """Held actual reference bytes and separate actual loaded SDK custody.

    `root` is read-only source DATA for existing Path consumers. It must never be
    placed on an import path. Acceptance must call verify_unchanged after those
    consumers run; held read() bytes are preferable where a byte API exists.
    """

    root: Path
    commit: str
    source_identity: str
    reader: SnapshotReader
    fixtures: FixtureAdmission
    git: GitReference
    records: tuple[tuple[str, str, str], ...]
    directories: tuple[tuple[str, tuple[int, int, int, int, int]], ...]
    root_identity: tuple[int, int]
    implementation: dict[str, Any]
    fresh_pycache_prefix: Path | None

    def read(self, relative: str) -> bytes:
        """Return only already admitted immutable public source/deliverable bytes."""
        if not isinstance(relative, str) or not relative or "\\" in relative or "\0" in relative:
            raise ValueError("source DATA read needs its original relative lexical path")
        lexical = Path(relative)
        if lexical.is_absolute() or ".." in lexical.parts or lexical.as_posix() != relative:
            raise ValueError("source DATA read is outside its original relative lexical inventory")
        path = self.root / lexical
        if path not in self.reader.snapshots:
            raise ValueError("source DATA read is outside the complete admitted inventory")
        return self.reader.snapshots[path].content

    def verify_unchanged(self, *, deadline: float) -> None:
        """Refuse physical replacement, ABA source edits, inventory drift and SDK drift."""
        remaining(deadline)
        if _identity(self.root)[:2] != self.root_identity or not self.reader.unchanged():
            raise ValueError("public source DATA changed after admission")
        for relative, expected in self.directories:
            if _identity(_directory(self.reader, relative)) != expected:
                raise ValueError("public source DATA directory changed after admission")
        records, source_identity = _observe_reference(self.root, fingerprint=True)
        if records != self.records:
            raise ValueError("complete public source DATA inventory changed after admission")
        if source_identity != self.source_identity:
            raise ValueError("complete public source DATA fingerprint changed after admission")
        if inventory(self.root, self.commit, deadline) != self.git:
            raise ValueError("native committed public source DATA custody changed")
        self.fixtures.verify(deadline)
        verify_implementation_custody(self.implementation, fresh_pycache_prefix=self.fresh_pycache_prefix)
        if not self.reader.unchanged():
            raise ValueError("public source DATA changed during final custody verification")
        remaining(deadline)


def admit_public_reference(
    root: Path,
    *,
    expected_commit: str,
    expected_source_identity: str,
    deadline: float,
    fresh_pycache_prefix: Path | None = None,
) -> PublicReference:
    """Admit a complete real Git reference against external harness bindings.

    This function does not compute and self-approve either expected identity.
    A source archive without a source-bound tracked inventory is unsupported.
    Synchronous inventory/byte operations need an enclosing supervised caller
    for a hard whole-operation/resource bound, as existing custody APIs do.
    """
    remaining(deadline)
    if not isinstance(expected_source_identity, str) or re.fullmatch(r"[0-9a-f]{64}", expected_source_identity) is None:
        raise ValueError("public reference needs its harness-admitted source fingerprint")
    root = root.absolute()
    if root.resolve(strict=True) != root:
        raise ValueError("public reference refuses symlink root components")
    physical = _identity(root)[:2]
    git = inventory(root, expected_commit, deadline)
    reader = SnapshotReader(root)
    if not validate_public_template_contract(root).passed:
        raise ValueError("source DATA requires the complete canonical public exemplar roster")
    metadata = tomllib.loads(reader.read("pyproject.toml").content.decode("utf-8"))
    if (
        metadata.get("project", {}).get("name") != "research-project-template"
        or not isinstance(metadata.get("project", {}).get("version"), str)
        or re.fullmatch(r"(?:4|5)\.\d+\.\d+", metadata["project"]["version"]) is None
    ):
        raise ValueError("public reference requires genuine platform 4 release source metadata")
    for required in ("uv.lock", ".python-version"):
        reader.read(required)
    implementation = capture_implementation_custody(fresh_pycache_prefix=fresh_pycache_prefix)
    import infrastructure

    if getattr(infrastructure, "__version__", None) != metadata["project"]["version"]:
        raise ValueError("public reference requires the actual selected SDK to match admitted Source metadata")
    if RuntimeScope(root, "root").source_identity(path_admission=_path_admission(reader)) != expected_source_identity:
        raise ValueError("public reference source differs from its external admitted fingerprint")
    records = _canonical_inventory(root)
    files = {relative for relative, kind, _ in records if kind in {"file", "deliverable"}}
    for project in PUBLIC_PROJECT_NAMES:
        base = root / "projects" / project
        manuscript = resolve_source_manuscript_dir(base).relative_to(root).as_posix() + "/"
        scripts = "projects/" + project + "/scripts/"
        if not any(name.startswith(manuscript) and name.endswith(".md") for name in files) or not any(
            name.startswith(scripts) and name.endswith(".py") for name in files
        ):
            raise ValueError("complete source DATA requires every actual public manuscript and script scope")
    _, fixtures = admit_source_bodies(root, reader, git, records, deadline)
    directories = []
    total = 0
    observed_python = {}
    for relative, kind, digest in records:
        remaining(deadline)
        if kind == "missing":
            raise ValueError("complete source DATA has a missing canonical source root")
        if kind == "directory":
            directories.append((relative, _identity(_directory(reader, relative))))
            continue
        actual = reader.read(relative)
        total += len(actual.content)
        if total > MAX_REFERENCE_BYTES:
            raise ValueError("complete public source DATA exceeds its held-byte bound")
        if kind == "file" and actual.sha256 != digest:
            raise ValueError("public source DATA changed between inventory and held byte admission")
        if relative.startswith("infrastructure/") and relative.endswith(".py"):
            observed_python[relative] = actual.sha256
    selected_python = {
        name: value for name, value in implementation["files"].items() if name.startswith("infrastructure/")
    }
    if observed_python != selected_python:
        raise ValueError("source DATA Python bytes differ from the actual selected SDK")
    reference = PublicReference(
        root,
        expected_commit,
        expected_source_identity,
        reader,
        fixtures,
        git,
        records,
        tuple(directories),
        physical,
        implementation,
        fresh_pycache_prefix,
    )
    reference.verify_unchanged(deadline=deadline)
    return reference


def reference_binding(environment: Mapping[str, str] | None = None) -> tuple[Path, str, str] | None:
    """Read all explicit DATA bindings together; never infer a revision from a path."""
    environment = os.environ if environment is None else environment
    for keys in (_BINDING_KEYS, PIPELINE_REFERENCE_KEYS):
        values = [environment.get(key, "") for key in keys]
        if not any(values):
            continue
        if not all(isinstance(value, str) and value for value in values):
            raise ValueError("public reference requires explicit root, commit and fingerprint together")
        return Path(values[0]), values[1], values[2]
    return None


__all__ = ["PIPELINE_REFERENCE_KEYS", "PublicReference", "admit_public_reference", "reference_binding"]

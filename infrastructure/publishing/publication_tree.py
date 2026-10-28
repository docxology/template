"""Reviewed source removals with retained evidence and recoverable quarantine."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import time
import uuid
from dataclasses import dataclass
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import (
    _close_all,
    _directory_identity_matches,
    _open_parent,
    _relative_target,
    atomic_write_bytes_confined,
    read_bytes_confined,
)

INVENTORY_NAME = ".template-publication-tree.json"
_SCHEMA = "template-publication-tree/1"
_PLAN_SCHEMA = "template-publication-removals/1"
_SHA = re.compile(r"[0-9a-f]{64}")
_REPOSITORY = re.compile(r"https://github\.com/[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}")
_BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")
_IMMUTABLE = frozenset(
    {"output", "history", "archive", "releases", "deposits", "registrations", "registration", "frozen"}
)
_PUBLICATION_SUFFIXES = frozenset({".pdf", ".epub", ".docx", ".pptx", ".zip", ".whl", ".tar", ".gz"})
_FROZEN = _IMMUTABLE - {"output"}


@dataclass(frozen=True)
class PublicationLimits:
    """Finite admission/work limits; rollback gets its own finite cleanup budget."""

    timeout_seconds: float = 60
    max_files: int = 50_000
    max_depth: int = 32
    max_total_bytes: int = 2 * 1024 * 1024 * 1024


class _Budget:
    def __init__(self, limits: PublicationLimits | None = None) -> None:
        self.limits = limits or PublicationLimits()
        if (
            type(self.limits.timeout_seconds) not in {int, float}
            or not math.isfinite(self.limits.timeout_seconds)
            or self.limits.timeout_seconds <= 0
            or any(
                type(value) is not int or value <= 0
                for value in (self.limits.max_files, self.limits.max_depth, self.limits.max_total_bytes)
            )
        ):
            raise ValueError("publication limits must be positive and finite")
        self.deadline = time.monotonic() + self.limits.timeout_seconds
        self.bytes = 0

    def check(self, size: int = 0) -> None:
        self.bytes += size
        if self.bytes > self.limits.max_total_bytes or time.monotonic() >= self.deadline:
            raise ValueError("publication work exceeds its finite deadline or byte budget")


def _bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def review_plan_sha256(plan: dict[str, Any]) -> str:
    """Digest the exact reviewable plan; generating it never approves it."""
    return hashlib.sha256(_bytes(plan)).hexdigest()


@dataclass(frozen=True)
class PublicationTarget:
    """Public destination identity independent of temporary checkout paths."""

    repository: str
    branch: str

    def payload(self) -> dict[str, str]:
        if not _REPOSITORY.fullmatch(self.repository) or (
            not _BRANCH.fullmatch(self.branch)
            or any(part.startswith(".") or part.endswith(".lock") for part in self.branch.split("/"))
            or ".." in self.branch
            or "//" in self.branch
            or self.branch.endswith(("/", "."))
        ):
            raise ValueError("publication removal destination must be an exact public GitHub repository and branch")
        return {"repository": self.repository, "branch": self.branch}


@dataclass(frozen=True)
class PublicationUpdate:
    """Managed-source parity and preserved extra evidence are separate facts."""

    plan: dict[str, Any]
    removed: tuple[str, ...]
    stale_managed: tuple[str, ...]
    preserved: tuple[str, ...]
    managed_export_parity: bool
    exact_tree_parity: bool


def _path(value: str) -> Path:
    if not isinstance(value, str):
        raise ValueError("publication inventory paths must be strings")
    path = Path(value)
    if any(part.casefold() == ".git" for part in path.parts):
        raise ValueError("publication content must not contain Git control files")
    if (
        not isinstance(value, str)
        or not value
        or path.is_absolute()
        or value != path.as_posix()
        or any(part in {".", ".."} or part.casefold() == ".git" for part in path.parts)
        or "\\" in value
        or "\0" in value
        or any(part.casefold() == INVENTORY_NAME.casefold() for part in path.parts)
        or any(
            part == ".env" or part.startswith(".env.") and not part.endswith((".example", ".template"))
            for part in path.parts
        )
    ):
        raise ValueError("publication inventory must contain only canonical public file paths")
    return path


def _protected(relative: str) -> bool:
    path = _path(relative)
    return path.suffix.casefold() in _PUBLICATION_SUFFIXES or any(
        part.casefold() in _IMMUTABLE or part.casefold().startswith("frozen_") for part in path.parts
    )


def _immutable(relative: str) -> bool:
    return any(part.casefold() in _FROZEN or part.casefold().startswith("frozen_") for part in _path(relative).parts)


def _root(root: Path) -> tuple[Path, tuple[int, int]]:
    root = root.absolute()
    metadata = root.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or ".." in root.parts:
        raise ValueError("publication tree must be a real directory without parent traversal")
    return root, (metadata.st_dev, metadata.st_ino)


def _entries(root: Path, budget: _Budget, *, source: bool = False) -> Iterator[tuple[str, bool]]:
    """Bound directory iteration before accumulation and refuse changed ancestors."""
    root, identity = _root(root)
    pending: list[tuple[str, ...]] = [()]
    count = 0
    while pending:
        parts = pending.pop()
        budget.check()
        if len(parts) > budget.limits.max_depth:
            raise ValueError("publication tree exceeds its finite depth limit")
        descriptor, opened = _open_parent(root, parts, create=False, expected_root_identity=identity)
        try:
            with os.scandir(descriptor) as entries:
                for entry in entries:
                    budget.check()
                    count += 1
                    if count > budget.limits.max_files:
                        raise ValueError("publication tree exceeds its finite entry limit")
                    relative = Path(*parts, entry.name).as_posix()
                    if not source and relative.casefold() == INVENTORY_NAME.casefold() and relative != INVENTORY_NAME:
                        raise ValueError("publication inventory name aliases are reserved across platforms")
                    if entry.name.casefold() == ".git":
                        if source:
                            raise ValueError("publication source must not contain Git control files")
                        continue
                    if source:
                        _path(relative)
                    directory = stat.S_ISDIR(entry.stat(follow_symlinks=False).st_mode)
                    yield relative, directory
                    if directory:
                        pending.append((*parts, entry.name))
            if not _directory_identity_matches(root, parts, descriptor, identity):
                raise ValueError("publication directory changed during bounded traversal")
        finally:
            _close_all(opened)


def _names(root: Path, budget: _Budget) -> set[str]:
    """List extras without opening their content; never walk Git or symlink trees."""
    return {name for name, directory in _entries(root, budget) if not directory and name != INVENTORY_NAME}


def _file(root: Path, relative: str, identity: tuple[int, int], budget: _Budget | None = None) -> dict[str, Any]:
    path = root / _path(relative)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("publication managed files must be real regular files")
    if budget is not None:
        budget.check(before.st_size)
    content = read_bytes_confined(root, path, max_bytes=64 * 1024 * 1024, expected_root_identity=identity)
    after = path.lstat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise ValueError("publication managed file changed during observation")
    return {"sha256": hashlib.sha256(content).hexdigest(), "mode": 0o755 if after.st_mode & 0o111 else 0o644}


def _records(root: Path, budget: _Budget) -> dict[str, dict[str, Any]]:
    root, identity = _root(root)
    names = {name for name, directory in _entries(root, budget, source=True) if not directory}
    if not names:
        raise ValueError("publication source export must be nonempty")
    return {name: _file(root, name, identity, budget) for name in sorted(names)}


def publication_export_sha256(source: Path, *, limits: PublicationLimits | None = None) -> str:
    """Bind the entire consumed export, including paths and executable modes."""
    return hashlib.sha256(_bytes(_records(source, _Budget(limits)))).hexdigest()


def copy_publication_source(source: Path, destination: Path, *, limits: PublicationLimits | None = None) -> None:
    """Materialize one bounded no-follow public source observation."""
    budget = _Budget(limits)
    source, identity = _root(source)
    destination, destination_identity = _root(destination)
    expected = _records(source, budget)
    for relative, record in expected.items():
        budget.check()
        content = read_bytes_confined(
            source, source / relative, max_bytes=64 * 1024 * 1024, expected_root_identity=identity
        )
        if hashlib.sha256(content).hexdigest() != record["sha256"]:
            raise ValueError("publication source changed during materialization")
        atomic_write_bytes_confined(
            destination,
            destination / relative,
            content,
            mode=record["mode"],
            expected_root_identity=destination_identity,
        )
    if _records(source, budget) != expected:
        raise ValueError("publication source changed during materialization")


def _inventory(
    root: Path, target: PublicationTarget, budget: _Budget | None = None
) -> tuple[dict[str, dict[str, Any]], str]:
    budget = budget or _Budget()
    path = root / INVENTORY_NAME
    if not path.exists() and not path.is_symlink():
        return {}, hashlib.sha256(b"").hexdigest()
    raw = read_bytes_confined(root, path, max_bytes=8 * 1024 * 1024)
    budget.check(len(raw))
    payload = json.loads(raw)
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schema_version", "destination", "files"}
        or payload["schema_version"] != _SCHEMA
        or payload["destination"] != target.payload()
        or not isinstance(payload["files"], dict)
        or len(payload["files"]) > budget.limits.max_files
    ):
        raise ValueError("publication ownership inventory differs from its destination or schema")
    for relative, record in payload["files"].items():
        budget.check()
        _path(relative)
        if (
            not isinstance(record, dict)
            or set(record) != {"sha256", "mode"}
            or not isinstance(record["sha256"], str)
            or not _SHA.fullmatch(record["sha256"])
            or type(record["mode"]) is not int
            or record["mode"] not in {0o644, 0o755}
        ):
            raise ValueError("publication ownership inventory has invalid file evidence")
    return payload["files"], hashlib.sha256(raw).hexdigest()


def prepare_removal_plan(
    source: Path,
    destination: Path,
    target: PublicationTarget,
    *,
    limits: PublicationLimits | None = None,
    _budget: _Budget | None = None,
) -> dict[str, Any]:
    """Describe the exact diff; prior provenance alone supplies no removal authority."""
    budget = _budget or _Budget(limits)
    desired = _records(source, budget)
    destination, identity = _root(destination)
    previous, previous_sha = _inventory(destination, target, budget)
    names = _names(destination, budget)
    observed = {
        name: _file(destination, name, identity, budget) if name in names else None
        for name in sorted(previous.keys() | desired.keys())
    }
    stale = previous.keys() - desired.keys()
    if any(_immutable(name) and observed[name] is not None and observed[name] != desired[name] for name in desired):
        raise ValueError("immutable publication history or frozen records cannot be overwritten")
    removable = {}
    retained = []
    for name in sorted(stale):
        if observed[name] is None:
            raise ValueError("previously managed publication file is missing; reconcile it before planning")
        if _protected(name):
            retained.append(name)
        elif observed[name] != previous[name]:
            raise ValueError("stale managed publication file differs from its original ownership evidence")
        else:
            removable[name] = observed[name]
    return {
        "schema_version": _PLAN_SCHEMA,
        "destination": target.payload(),
        "prior_inventory_sha256": previous_sha,
        "prior_owned_files": previous,
        "observed_managed_files": observed,
        "desired_export_files": desired,
        "desired_export_sha256": hashlib.sha256(_bytes(desired)).hexdigest(),
        "removals": removable,
        "retained_immutable": retained,
        "destination_only": sorted(names - previous.keys() - desired.keys()),
    }


def _restore(
    parent: int, quarantine_parent: int, filename: str, budget: _Budget, expected: dict[str, Any] | None = None
) -> bool:
    """Publish independently owned rollback bytes without clobbering a target."""
    source = copied = -1
    temporary = f".publication-rollback-{uuid.uuid4().hex}"
    try:
        source = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=quarantine_parent)
        original = os.fstat(source)
        if not stat.S_ISREG(original.st_mode) or original.st_size > 64 * 1024 * 1024:
            return False
        budget.check(original.st_size)
        copied = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        consumed = 0
        digest = hashlib.sha256()
        while content := os.read(source, 1024 * 1024):
            budget.check()
            consumed += len(content)
            if consumed > original.st_size:
                return False
            digest.update(content)
            pending = memoryview(content)
            while pending:
                budget.check()
                written = os.write(copied, pending)
                if written <= 0:
                    return False
                pending = pending[written:]
        after = os.fstat(source)
        located = os.stat(filename, dir_fd=quarantine_parent, follow_symlinks=False)

        def identity(item: os.stat_result) -> tuple[int, int, int, int, int]:
            return item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns

        if (
            consumed != original.st_size
            or identity(original) != identity(after)
            or identity(after) != identity(located)
        ):
            return False
        mode = 0o755 if original.st_mode & 0o111 else 0o644
        if expected is not None and {"sha256": digest.hexdigest(), "mode": mode} != expected:
            return False
        os.fchmod(copied, mode)
        os.fsync(copied)
        copied_identity = os.fstat(copied)
        temporary_identity = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
        if (copied_identity.st_dev, copied_identity.st_ino) != (temporary_identity.st_dev, temporary_identity.st_ino):
            return False
        os.link(temporary, filename, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        published = os.stat(filename, dir_fd=parent, follow_symlinks=False)
        if (copied_identity.st_dev, copied_identity.st_ino) != (published.st_dev, published.st_ino):
            return False
        os.fsync(parent)
        return True
    except (OSError, ValueError):
        return False
    finally:
        if source >= 0:
            os.close(source)
        if copied >= 0:
            # Only the private temporary name is removed; public/quarantine bytes stay retained.
            try:
                owned = os.fstat(copied)
                current = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
                if (owned.st_dev, owned.st_ino) == (current.st_dev, current.st_ino):
                    os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
            finally:
                os.close(copied)


def _quarantine_file(
    destination: Path,
    quarantine: Path,
    relative: str,
    expected: dict[str, Any],
    destination_identity: tuple[int, int],
    quarantine_identity: tuple[int, int],
) -> None:
    root, parts, filename = _relative_target(destination, destination / _path(relative))
    parent, opened = _open_parent(root, parts, create=False, expected_root_identity=destination_identity)
    quarantine_root, quarantine_parts, _ = _relative_target(quarantine, quarantine / relative)
    try:
        moved_parent, moved_opened = _open_parent(
            quarantine_root, quarantine_parts, create=True, expected_root_identity=quarantine_identity
        )
    except BaseException:
        _close_all(opened)
        raise
    moved = False
    try:
        original = os.stat(filename, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(original.st_mode) or _file(destination, relative, destination_identity) != expected:
            raise ValueError("reviewed publication file changed before quarantine")
        if not _directory_identity_matches(
            root, parts, parent, destination_identity
        ) or not _directory_identity_matches(quarantine_root, quarantine_parts, moved_parent, quarantine_identity):
            raise ValueError("publication removal ancestor changed before quarantine")
        os.rename(filename, filename, src_dir_fd=parent, dst_dir_fd=moved_parent)
        moved = True
        observed = os.stat(filename, dir_fd=moved_parent, follow_symlinks=False)
        if (
            (original.st_dev, original.st_ino, original.st_size, original.st_mtime_ns)
            != (observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns)
            or _file(quarantine, relative, quarantine_identity) != expected
            or not _directory_identity_matches(root, parts, parent, destination_identity)
            or not _directory_identity_matches(quarantine_root, quarantine_parts, moved_parent, quarantine_identity)
        ):
            raise ValueError("publication file or ancestor changed during quarantine; retained rollback evidence")
        os.fsync(parent)
        os.fsync(moved_parent)
    except BaseException as error:
        if moved and (
            not _directory_identity_matches(root, parts, parent, destination_identity)
            or not _directory_identity_matches(quarantine_root, quarantine_parts, moved_parent, quarantine_identity)
            or not _restore(parent, moved_parent, filename, _Budget())
        ):
            raise ValueError(
                "publication removal refused; concurrent destination retained and quarantine needs recovery"
            ) from error
        raise
    finally:
        _close_all(moved_opened)
        _close_all(opened)


def _restore_files(
    destination: Path,
    quarantine: Path,
    names: list[str],
    records: dict[str, Any],
    destination_identity: tuple[int, int],
    quarantine_identity: tuple[int, int],
) -> None:
    budget = _Budget()
    for relative in reversed(names):
        budget.check()
        root, parts, filename = _relative_target(destination, destination / relative)
        parent, opened = _open_parent(root, parts, create=False, expected_root_identity=destination_identity)
        moved_root, moved_parts, _ = _relative_target(quarantine, quarantine / relative)
        try:
            moved_parent, moved_opened = _open_parent(
                moved_root, moved_parts, create=False, expected_root_identity=quarantine_identity
            )
        except BaseException:
            _close_all(opened)
            raise
        try:
            original = os.stat(filename, dir_fd=moved_parent, follow_symlinks=False)
            if _file(quarantine, relative, quarantine_identity, budget) != records[relative]:
                raise ValueError("publication quarantine differs from reviewed rollback bytes")
            if (
                not _directory_identity_matches(root, parts, parent, destination_identity)
                or not _directory_identity_matches(moved_root, moved_parts, moved_parent, quarantine_identity)
                or not _restore(parent, moved_parent, filename, budget, records[relative])
            ):
                raise ValueError("publication rollback refused an occupied target; quarantine remains recoverable")
            restored = os.stat(filename, dir_fd=parent, follow_symlinks=False)
            if (original.st_dev, original.st_ino) == (restored.st_dev, restored.st_ino) or (
                _file(destination, relative, destination_identity, budget) != records[relative]
            ):
                raise ValueError("publication rollback changed during restoration; both locations remain retained")
        finally:
            _close_all(moved_opened)
            _close_all(opened)


def restore_publication_quarantine(
    destination: Path,
    quarantine: Path,
    target: PublicationTarget,
    plan: dict[str, Any],
    reviewed_plan_sha256: str,
) -> tuple[str, ...]:
    """Recover the reviewed bytes without overwriting concurrent destination work."""
    budget = _Budget()
    destination, destination_identity = _root(destination)
    quarantine, identity = _root(quarantine)
    if (
        plan.get("schema_version") != _PLAN_SCHEMA
        or plan.get("destination") != target.payload()
        or review_plan_sha256(plan) != reviewed_plan_sha256
        or not isinstance(plan.get("removals"), dict)
    ):
        raise ValueError("publication rollback requires the destination-bound reviewed plan")
    names = list(plan["removals"])
    for relative in names:
        if _protected(relative) or _file(quarantine, relative, identity, budget) != plan["removals"][relative]:
            raise ValueError("publication quarantine differs from reviewed rollback bytes")
    _restore_files(destination, quarantine, names, plan["removals"], destination_identity, identity)
    return tuple(names)


def _validate_updated_tree(
    destination: Path,
    target: PublicationTarget,
    plan: dict[str, Any],
    removed: tuple[str, ...],
    budget: _Budget,
    *,
    inventory_written: bool,
) -> None:
    """Recheck managed bytes and all names while leaving unrelated bytes unopened."""
    destination, identity = _root(destination)
    expected = {
        name: record
        for name, record in plan["observed_managed_files"].items()
        if record is not None and name not in removed
    }
    expected.update(plan["desired_export_files"])
    if _names(destination, budget) != expected.keys() | set(plan["destination_only"]):
        raise ValueError("publication destination names changed; exact parity cannot be established")
    if any(_file(destination, name, identity, budget) != record for name, record in expected.items()):
        raise ValueError("publication managed destination changed before promotion")
    inventory, digest = _inventory(destination, target, budget)
    if inventory_written:
        ownership = {name: record for name, record in plan["prior_owned_files"].items() if name not in removed}
        ownership.update(plan["desired_export_files"])
        if inventory != ownership:
            raise ValueError("publication ownership changed before promotion")
    elif digest != plan["prior_inventory_sha256"]:
        raise ValueError("publication ownership changed during update")


def validate_publication_update(
    destination: Path,
    target: PublicationTarget,
    update: PublicationUpdate,
    *,
    limits: PublicationLimits | None = None,
) -> None:
    """Refuse promotion if managed bytes, ownership, or any destination names drift."""
    if update.plan["destination"] != target.payload():
        raise ValueError("publication update belongs to a different destination")
    _validate_updated_tree(destination, target, update.plan, update.removed, _Budget(limits), inventory_written=True)


def update_publication_tree(
    source: Path,
    destination: Path,
    target: PublicationTarget,
    *,
    removal_plan: dict[str, Any] | None = None,
    reviewed_plan_sha256: str | None = None,
    quarantine_root: Path | None = None,
    limits: PublicationLimits | None = None,
) -> PublicationUpdate:
    """Update regular source bytes; remove only an exact explicitly reviewed diff."""
    budget = _Budget(limits)
    source, source_identity = _root(source)
    destination, destination_identity = _root(destination)
    plan = prepare_removal_plan(source, destination, target, _budget=budget)
    if (
        removal_plan is None
        and reviewed_plan_sha256 is not None
        or removal_plan is not None
        and (
            not isinstance(reviewed_plan_sha256, str)
            or not _SHA.fullmatch(reviewed_plan_sha256)
            or review_plan_sha256(removal_plan) != reviewed_plan_sha256
            or removal_plan != plan
        )
    ):
        raise ValueError("publication removals require the exact current plan and explicitly reviewed SHA-256")
    removed: list[str] = []
    quarantine: Path | None = None
    quarantine_identity: tuple[int, int] | None = None
    if removal_plan is not None and plan["removals"]:
        if quarantine_root is None:
            raise ValueError("reviewed publication removals require retained quarantine outside the destination")
        quarantine_root, quarantine_root_identity = _root(quarantine_root)
        if quarantine_root.is_relative_to(source) or quarantine_root.is_relative_to(destination):
            raise ValueError("publication quarantine must remain outside the source and destination")
        quarantine = quarantine_root / uuid.uuid4().hex
        held, opened = _open_parent(
            quarantine_root, (quarantine.name,), create=True, expected_root_identity=quarantine_root_identity
        )
        try:
            os.fchmod(held, 0o700)
            metadata = os.fstat(held)
            quarantine_identity = (metadata.st_dev, metadata.st_ino)
        finally:
            _close_all(opened)
        journal = {
            "schema_version": _PLAN_SCHEMA,
            "reviewed_plan_sha256": reviewed_plan_sha256,
            "quarantine": quarantine.name,
            "plan": plan,
        }
        atomic_write_bytes_confined(
            quarantine_root,
            quarantine_root / f"{quarantine.name}.json",
            _bytes(journal),
            mode=0o400,
            expected_root_identity=quarantine_root_identity,
        )
    previous, _ = _inventory(destination, target, budget)
    try:
        if prepare_removal_plan(source, destination, target, _budget=budget) != plan:
            raise ValueError("publication source or destination changed before update")
        if quarantine is not None:
            assert quarantine_identity is not None
            for relative, expected in plan["removals"].items():
                budget.check()
                _quarantine_file(destination, quarantine, relative, expected, destination_identity, quarantine_identity)
                removed.append(relative)
        for relative, expected in plan["desired_export_files"].items():
            budget.check()
            content = read_bytes_confined(
                source, source / relative, max_bytes=64 * 1024 * 1024, expected_root_identity=source_identity
            )
            if hashlib.sha256(content).hexdigest() != expected["sha256"]:
                raise ValueError("publication source changed while writing export")
            atomic_write_bytes_confined(
                destination,
                destination / relative,
                content,
                mode=expected["mode"],
                expected_root_identity=destination_identity,
            )
        if _records(source, budget) != plan["desired_export_files"] or any(
            _file(destination, relative, destination_identity, budget) != expected
            for relative, expected in plan["desired_export_files"].items()
        ):
            raise ValueError("publication source/export changed during update")
        _validate_updated_tree(destination, target, plan, tuple(removed), budget, inventory_written=False)
        inventory = {name: record for name, record in previous.items() if name not in removed}
        inventory.update(plan["desired_export_files"])
        atomic_write_bytes_confined(
            destination,
            destination / INVENTORY_NAME,
            _bytes({"schema_version": _SCHEMA, "destination": target.payload(), "files": inventory}),
            expected_root_identity=destination_identity,
        )
        _validate_updated_tree(destination, target, plan, tuple(removed), budget, inventory_written=True)
    except BaseException:
        if quarantine is not None:
            assert quarantine_identity is not None
            _restore_files(
                destination, quarantine, removed, plan["removals"], destination_identity, quarantine_identity
            )
        raise
    stale = tuple(name for name in plan["removals"] if name not in removed)
    preserved = tuple(sorted(set(plan["destination_only"]) | set(plan["retained_immutable"])))
    return PublicationUpdate(plan, tuple(removed), stale, preserved, not stale, not stale and not preserved)


__all__ = [
    "INVENTORY_NAME",
    "PublicationTarget",
    "PublicationLimits",
    "copy_publication_source",
    "PublicationUpdate",
    "prepare_removal_plan",
    "publication_export_sha256",
    "review_plan_sha256",
    "restore_publication_quarantine",
    "update_publication_tree",
    "validate_publication_update",
]

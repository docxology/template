"""Bounded sparse installed-package DATA for the selected Linux Calibre reader.

Package ownership and file inventories are observations, never native process
or loaded-library authority. The caller authenticates their actual ToolAPI.
There is no recursive system-directory census and the app policy is unchanged.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from infrastructure.project.native_reader_runtime_custody import MAX_BYTES, MAX_FILE, MAX_FILES, _digest, _metadata
from infrastructure.project.public_reference_git import remaining

SCHEMA = "template-native-linux-calibre-package-runtime-v1"
POLICY = "debian-owned-calibre-embedded-qt-offscreen-v1"
ROLE_NAMES = {
    "launcher",
    "debug_launcher",
    "package_query",
    "interpreter",
    "calibre_module",
    "qt_module",
    "platform_plugin",
}


def canonical_linux_member(label: object) -> Path:
    """Reject ambiguous package-query labels before any physical observation."""
    if not isinstance(label, str):
        raise ValueError("Calibre package member must be an absolute canonical label")
    path = Path(label)
    if not path.is_absolute() or str(path) != label or ".." in path.parts or any(c in label for c in "\0\n\r*?["):
        raise ValueError("Calibre package member must be an absolute canonical label")
    return path


def _package_members(packages: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(packages, list) or not 1 <= len(packages) <= 256:
        raise ValueError("Calibre needs a bounded nonempty installed-package roster")
    result: dict[str, tuple[str, ...]] = {}
    total = 0
    for package in packages:
        if not isinstance(package, dict) or set(package) != {"package", "version", "architecture", "status", "members"}:
            raise ValueError("Calibre package record fieldset differs")
        name = package["package"]
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9][a-z0-9-]*)?", name) is None
            or name in result
            or not isinstance(package["version"], str)
            or not package["version"]
            or not isinstance(package["architecture"], str)
            or re.fullmatch(r"[a-z0-9][a-z0-9-]*", package["architecture"]) is None
            or package["status"] != "install ok installed"
            or not isinstance(package["members"], list)
            or not package["members"]
            or package["members"] != sorted(set(package["members"]))
        ):
            raise ValueError("Calibre package owner/status/member roster malformed")
        for member in package["members"]:
            canonical_linux_member(member)
        total += len(package["members"])
        if total > MAX_FILES:
            raise ValueError("Calibre full package membership exceeds existing node bound")
        result[name] = tuple(package["members"])
    if [p["package"] for p in packages] != sorted(result):
        raise ValueError("Calibre package order is not canonical")
    return result


def _parents(path: Path) -> tuple[Path, ...]:
    return tuple(reversed(path.parents))


def _held_parent(path: Path) -> tuple[int, list[tuple[int, dict[str, int]]]]:
    """Hold canonical ancestors without allowing a directory traversal census."""
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    held = [(fd, _metadata(os.fstat(fd)))]
    try:
        for part in path.parent.parts[1:]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            held.append((fd, _metadata(os.fstat(fd))))
        return fd, held
    except BaseException:
        for descriptor, _ in reversed(held):
            os.close(descriptor)
        raise


def observe_linux_calibre_packages(
    packages: list[dict[str, Any]], roles: dict[str, str], *, deadline: float
) -> dict[str, Any]:
    """Read only the exact complete package membership selected by real tools."""
    remaining(deadline)
    ownership = _package_members(packages)
    members = {name for paths in ownership.values() for name in paths}
    if set(roles) != ROLE_NAMES or any(
        canonical_linux_member(label).as_posix() not in members for label in roles.values()
    ):
        raise ValueError("Calibre role is absent from the selected complete package membership")
    paths = {canonical_linux_member(label) for label in members}
    paths.update(parent for path in tuple(paths) for parent in _parents(path))
    if len(paths) > MAX_FILES:
        raise ValueError("Calibre sparse package/ancestor closure exceeds existing node bound")
    rows: list[dict[str, Any]] = []
    total = 0
    for path in sorted(paths, key=str):
        remaining(deadline)
        parent, held = _held_parent(path)
        try:
            value = os.fstat(parent) if path == Path("/") else os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            facts = _metadata(value)
            row: dict[str, Any] = {"path": str(path), "metadata": facts}
            if stat.S_ISDIR(value.st_mode):
                row["kind"] = "directory"
            elif stat.S_ISLNK(value.st_mode):
                label = os.readlink(path.name, dir_fd=parent)
                target = path.resolve(strict=True)
                if target not in paths:
                    raise ValueError("Calibre package alias target is absent from complete selected closure")
                row.update(kind="alias", label=label, target=str(target))
            elif stat.S_ISREG(value.st_mode):
                total += value.st_size
                if value.st_size > MAX_FILE or total > MAX_BYTES:
                    raise ValueError("Calibre package bytes exceed existing reader bounds")
                descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
                try:
                    before = _metadata(os.fstat(descriptor))
                    digest, count = hashlib.sha256(), 0
                    while block := os.read(descriptor, 1024 * 1024):
                        remaining(deadline)
                        count += len(block)
                        if count > MAX_FILE:
                            raise ValueError("Calibre package member grew beyond reader bound")
                        digest.update(block)
                    if before != facts or before != _metadata(os.fstat(descriptor)) or count != value.st_size:
                        raise ValueError("Calibre package bytes changed during held read")
                    row.update(kind="file", sha256=digest.hexdigest())
                finally:
                    os.close(descriptor)
            else:
                raise ValueError("Calibre selected package contains an unsupported node")
            after = os.fstat(parent) if path == Path("/") else os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if facts != _metadata(after) or any(before != _metadata(os.fstat(fd)) for fd, before in held):
                raise ValueError("Calibre package member/ancestor changed during held read")
            rows.append(row)
        finally:
            for descriptor, _ in reversed(held):
                os.close(descriptor)
    raw = {
        "schema_version": SCHEMA,
        "policy": POLICY,
        "packages": packages,
        "roles": roles,
        "files": rows,
        "bytes": total,
    }
    raw["digest"] = _digest(raw)
    validate_linux_calibre_packages(raw, raw)
    remaining(deadline)
    return raw


def validate_linux_calibre_packages(before: dict[str, Any], after: dict[str, Any]) -> None:
    """Validate retained DATA only, including complete sparse alias closure."""
    if before != after:
        raise ValueError("Calibre complete installed-package custody changed")
    raw = before
    if (
        set(raw) != {"schema_version", "policy", "packages", "roles", "files", "bytes", "digest"}
        or raw["schema_version"] != SCHEMA
        or raw["policy"] != POLICY
        or raw["digest"] != _digest({k: v for k, v in raw.items() if k != "digest"})
    ):
        raise ValueError("Calibre package schema/policy/digest differs")
    ownership = _package_members(raw["packages"])
    members = {name for paths in ownership.values() for name in paths}
    paths = {canonical_linux_member(label) for label in members}
    paths.update(parent for path in tuple(paths) for parent in _parents(path))
    rows = raw["files"]
    if not isinstance(rows, list) or len(rows) > MAX_FILES or [r["path"] for r in rows] != sorted(map(str, paths)):
        raise ValueError("Calibre full package and sparse ancestor roster differs")
    indexed, total = {}, 0
    for row in rows:
        path = canonical_linux_member(row["path"])
        facts = row["metadata"]
        if (
            not isinstance(facts, dict)
            or set(facts) != {"dev", "ino", "mode", "size", "mtime_ns", "ctime_ns"}
            or any(type(v) is not int or v < 0 for v in facts.values())
        ):
            raise ValueError("Calibre package member metadata malformed")
        kind = row["kind"]
        fields = {"path", "kind", "metadata"}
        if kind == "file":
            fields.add("sha256")
            if (
                not stat.S_ISREG(facts["mode"])
                or facts["size"] > MAX_FILE
                or re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is None
            ):
                raise ValueError("Calibre package file byte identity malformed")
            total += facts["size"]
        elif kind == "alias":
            fields.update({"target", "label"})
            canonical_linux_member(row["target"])
            if (
                not stat.S_ISLNK(facts["mode"])
                or not isinstance(row["label"], str)
                or not row["label"]
                or "\0" in row["label"]
            ):
                raise ValueError("Calibre package alias malformed")
        elif kind != "directory" or not stat.S_ISDIR(facts["mode"]):
            raise ValueError("Calibre package member kind differs")
        if set(row) != fields or (str(path) not in members and kind != "directory"):
            raise ValueError("Calibre sparse ancestor grants a non-directory member")
        indexed[str(path)] = row
    for row in rows:
        path = Path(row["path"])
        if any(indexed[str(parent)]["kind"] != "directory" for parent in _parents(path)):
            raise ValueError("Calibre package ancestor is not an admitted directory")
        if row["kind"] == "alias":
            label = Path(row["label"])
            components: list[str] = []
            for part in (label if label.is_absolute() else path.parent / label).parts[1:]:
                if part == "..":
                    if not components:
                        raise ValueError("Calibre retained alias escapes filesystem root")
                    components.pop()
                elif part != ".":
                    components.append(part)
                    member = indexed.get("/" + "/".join(components), {})
                    if member.get("kind") == "alias":
                        components = list(Path(member["target"]).parts[1:])
            if "/" + "/".join(components) != row["target"] or indexed.get(row["target"], {}).get("kind") not in {
                "file",
                "directory",
            }:
                raise ValueError("Calibre alias label/target differs from retained closure")
    roles = raw["roles"]
    if not isinstance(roles, dict) or set(roles) != ROLE_NAMES:
        raise ValueError("Calibre selected launcher/interpreter/Qt/plugin role roster differs")
    for label in roles.values():
        if label not in members or indexed.get(label, {}).get("kind") != "file":
            raise ValueError("Calibre selected runtime role lacks actual regular package bytes")
    if type(raw["bytes"]) is not int or total != raw["bytes"] or total > MAX_BYTES:
        raise ValueError("Calibre full selected package byte count differs")


def linux_calibre_body_projection(raw: dict[str, Any]) -> dict[str, Any]:
    """Exact package bodies/roles for independently observed Current comparison.

    Linux package membership labels stay exact; physical inode/time identity may
    differ on another runner. Arbitrary prefix remapping is deliberately absent.
    """
    validate_linux_calibre_packages(raw, raw)
    return {
        "schema_version": raw["schema_version"],
        "policy": raw["policy"],
        "packages": raw["packages"],
        "roles": raw["roles"],
        "files": [
            {
                "path": row["path"],
                "kind": row["kind"],
                **(
                    {"sha256": row["sha256"], "bytes": row["metadata"]["size"]}
                    if row["kind"] == "file"
                    else {"label": row["label"], "target": row["target"]}
                    if row["kind"] == "alias"
                    else {}
                ),
            }
            for row in raw["files"]
        ],
    }

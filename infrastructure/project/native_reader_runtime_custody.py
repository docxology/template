"""Complete bounded native app file observations, independent of loaded-memory claims.

Retained hashes prove integrity; authenticated producer custody establishes origin.
No executable/library bytes are redistributed and replay never reads app paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import time
from pathlib import Path
from typing import Any

SCHEMA = "template-native-reader-runtime-v1"
MAX_FILES = 20000
MAX_BYTES = 2 * 1024 * 1024 * 1024
MAX_FILE = 512 * 1024 * 1024


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _metadata(value: os.stat_result) -> dict[str, int]:
    return {key: getattr(value, "st_" + key) for key in ("dev", "ino", "mode", "size", "mtime_ns", "ctime_ns")}


def _directory(path: Path) -> int:
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def observe_native_reader_runtime(
    executable: Path, *, deadline: float, consumed_members: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Observe full positively identified .app; unknown system closure is blocked."""
    app = next((p for p in executable.absolute().parents if p.name.endswith(".app")), None)
    if app is None:
        raise ValueError("native reader runtime requires a source-declared dedicated app/resource prefix")
    root = app.resolve(strict=True)
    actual = executable.resolve(strict=True)
    if not actual.is_relative_to(root):
        raise ValueError("native reader executable escapes original app")
    rows: list[dict[str, Any]] = []
    total = 0

    def visit(fd: int, prefix: str) -> None:
        nonlocal total
        before = _metadata(os.fstat(fd))
        names = sorted(os.listdir(fd))
        for name in names:
            if time.monotonic() >= deadline:
                raise TimeoutError("native reader census exhausted original deadline")
            if len(rows) >= MAX_FILES:
                raise ValueError("native reader full census exceeds count bound")
            relative = prefix + name
            value = os.stat(name, dir_fd=fd, follow_symlinks=False)
            row: dict[str, Any] = {"path": relative, "metadata": _metadata(value)}
            if stat.S_ISLNK(value.st_mode):
                label = os.readlink(name, dir_fd=fd)
                target = (root / relative).resolve(strict=True)
                if not target.is_relative_to(root):
                    raise ValueError("native reader alias escapes complete app")
                row.update(kind="alias", label=label, target=target.relative_to(root).as_posix())
            elif stat.S_ISDIR(value.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    if _metadata(os.fstat(child)) != row["metadata"]:
                        raise ValueError("native reader directory changed before held read")
                    row["kind"] = "directory"
                    rows.append(row)
                    visit(child, relative + "/")
                finally:
                    os.close(child)
                continue
            elif stat.S_ISREG(value.st_mode):
                total += value.st_size
                if value.st_size > MAX_FILE or total > MAX_BYTES:
                    raise ValueError("native reader file census exceeds byte bound")
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    original = _metadata(os.fstat(child))
                    digest = hashlib.sha256()
                    count = 0
                    while block := os.read(child, 1024 * 1024):
                        if time.monotonic() >= deadline:
                            raise TimeoutError("native reader hashing exhausted original deadline")
                        count += len(block)
                        if count > MAX_FILE:
                            raise ValueError("native reader file grew beyond bound")
                        digest.update(block)
                    if original != row["metadata"] or original != _metadata(os.fstat(child)) or count != value.st_size:
                        raise ValueError("native reader file changed during held read")
                    row.update(kind="file", sha256=digest.hexdigest())
                finally:
                    os.close(child)
            else:
                raise ValueError("native reader app contains unsupported node")
            if row["metadata"] != _metadata(os.stat(name, dir_fd=fd, follow_symlinks=False)):
                raise ValueError("native reader member changed during census")
            rows.append(row)
        if names != sorted(os.listdir(fd)) or before != _metadata(os.fstat(fd)):
            raise ValueError("native reader directory census changed")

    fd = _directory(root)
    try:
        root_metadata = _metadata(os.fstat(fd))
        visit(fd, "")
    finally:
        os.close(fd)
    raw = {
        "schema_version": SCHEMA,
        "root": str(root),
        "executable": str(actual),
        "root_metadata": root_metadata,
        "files": sorted(rows, key=lambda row: row["path"]),
        "bytes": total,
        "consumed_members": sorted(consumed_members),
    }
    raw["digest"] = _digest(raw)
    binary = next((r for r in rows if r["path"] == actual.relative_to(root).as_posix()), None)
    if binary is None:
        raise ValueError("native reader executable missing from complete app")
    validate_native_reader_runtime(
        raw, raw, executable_sha256=binary.get("sha256", ""), consumed_members=consumed_members
    )
    return raw


def validate_native_reader_runtime(
    before: dict[str, Any], after: dict[str, Any], *, executable_sha256: str, consumed_members: tuple[str, ...] = ()
) -> None:
    """Read original records only; consumed labels require separate genuine trace."""
    if before != after:
        raise ValueError("native reader before/after complete app identity changed")
    raw = before
    if (
        set(raw)
        != {"schema_version", "root", "executable", "root_metadata", "files", "bytes", "consumed_members", "digest"}
        or raw["schema_version"] != SCHEMA
        or raw["digest"] != _digest({k: v for k, v in raw.items() if k != "digest"})
    ):
        raise ValueError("native reader original schema/digest differs")
    root, executable = Path(raw["root"]), Path(raw["executable"])
    if not root.is_absolute() or not executable.is_relative_to(root) or not root.name.endswith(".app"):
        raise ValueError("native reader original dedicated app labels differ")
    root_facts = raw["root_metadata"]
    if (
        set(root_facts) != {"dev", "ino", "mode", "size", "mtime_ns", "ctime_ns"}
        or any(type(v) is not int for v in root_facts.values())
        or not stat.S_ISDIR(root_facts["mode"])
    ):
        raise ValueError("native reader original app root metadata malformed")
    rows = raw["files"]
    if not isinstance(rows, list) or not rows or len(rows) > MAX_FILES:
        raise ValueError("native reader full inventory absent/unbounded")
    indexed = {}
    total = 0
    for row in rows:
        path = Path(row["path"])
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or path.as_posix() != row["path"]
            or row["path"] in indexed
        ):
            raise ValueError("native reader member escapes/duplicates")
        facts = row["metadata"]
        if (
            set(facts) != {"dev", "ino", "mode", "size", "mtime_ns", "ctime_ns"}
            or any(type(v) is not int for v in facts.values())
            or facts["size"] < 0
        ):
            raise ValueError("native reader member metadata malformed")
        indexed[row["path"]] = row
        if row["kind"] == "file":
            if (
                set(row) != {"path", "kind", "metadata", "sha256"}
                or not stat.S_ISREG(facts["mode"])
                or facts["size"] > MAX_FILE
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
            ):
                raise ValueError("native reader original regular file malformed")
            total += facts["size"]
        elif row["kind"] == "directory":
            if set(row) != {"path", "kind", "metadata"} or not stat.S_ISDIR(facts["mode"]):
                raise ValueError("native reader original directory malformed")
        elif row["kind"] == "alias":
            target = Path(row["target"])
            if (
                set(row) != {"path", "kind", "metadata", "target", "label"}
                or not stat.S_ISLNK(facts["mode"])
                or target.is_absolute()
                or ".." in target.parts
                or not target.parts
            ):
                raise ValueError("native reader original alias malformed")
        else:
            raise ValueError("native reader member kind unknown")
    for row in rows:
        if row["kind"] == "alias":
            if indexed.get(row["target"], {}).get("kind") not in {"file", "directory"}:
                raise ValueError("native reader alias target omitted from full census")
            label = Path(row["label"])
            if label.is_absolute():
                try:
                    parts = label.relative_to(root).parts
                except ValueError as error:
                    raise ValueError("native reader retained alias label escapes app") from error
            else:
                parts = (Path(row["path"]).parent / label).parts
            resolved: list[str] = []
            for part in parts:
                if part == ".":
                    continue
                if part == "..":
                    if not resolved:
                        raise ValueError("native reader retained alias label escapes app")
                    resolved.pop()
                    continue
                resolved.append(part)
                member = indexed.get("/".join(resolved), {})
                if member.get("kind") == "alias":
                    resolved = list(Path(member["target"]).parts)
            if "/".join(resolved) != row["target"]:
                raise ValueError("native reader alias label differs from retained target")
        for parent in Path(row["path"]).parents:
            if parent == Path("."):
                break
            if indexed.get(parent.as_posix(), {}).get("kind") != "directory":
                raise ValueError("native reader full directory closure omitted")
    binary = indexed.get(executable.relative_to(root).as_posix(), {})
    if total != raw["bytes"] or total > MAX_BYTES or binary.get("sha256") != executable_sha256:
        raise ValueError("native reader executable/full byte custody differs")
    if raw["consumed_members"] != sorted(consumed_members) or any(
        indexed.get(name, {}).get("kind") != "file" for name in consumed_members
    ):
        raise ValueError("native reader actual consumed member absent from admitted census")


def retain_native_reader_runtime(root: Path, raw: dict[str, Any], *, run_id: str) -> dict[str, str]:
    """Share identical observed manifest bytes within one original admitted run."""
    from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    if re.fullmatch(r"[0-9a-f]{32}", run_id) is None or re.fullmatch(r"[0-9a-f]{64}", raw.get("digest", "")) is None:
        raise ValueError("native runtime retention requires exact original run/digest")
    directory = evidence_directory(root, root / "output/readiness/native-reader-runtimes" / run_id)
    if directory.exists():
        fd = _directory(directory)
        try:
            facts = os.fstat(fd)
            if stat.S_IMODE(facts.st_mode) != 0o700 or facts.st_uid != os.getuid():
                raise ValueError("shared native runtime directory lost private owner custody")
        finally:
            os.close(fd)
    else:
        create_private_native_directory(root, directory)
    path = directory / f"{raw['digest']}.json"
    if path.exists():
        snapshot = SnapshotReader(root).read(path.relative_to(root).as_posix())
        if snapshot.json_object() != raw:
            raise ValueError("retained original native runtime manifest changed")
        return {"path": snapshot.relative, "sha256": snapshot.sha256}
    return write_json(root, path, raw)


def replay_retained_native_reader_runtime(
    before_binding: dict[str, str],
    after_binding: dict[str, str],
    *,
    read_artifact: Any,
    run_id: str,
    executable: str,
    executable_sha256: str,
    consumed_members: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Validate the exact original run's shared manifest; never open tool paths."""
    from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

    observations = []
    for binding in (before_binding, after_binding):
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
            raise ValueError("native runtime requires exact retained artifact bindings")
        content = read_artifact(binding)
        raw = json_object_from_bytes(content)
        if (
            re.fullmatch(r"[0-9a-f]{32}", run_id) is None
            or binding["path"] != f"output/readiness/native-reader-runtimes/{run_id}/{raw.get('digest')}.json"
            or hashlib.sha256(content).hexdigest() != binding["sha256"]
            or raw.get("executable") != executable
        ):
            raise ValueError("native reader runtime belongs to another run/tool or changed bytes")
        observations.append(raw)
    validate_native_reader_runtime(
        observations[0], observations[1], executable_sha256=executable_sha256, consumed_members=consumed_members
    )
    return observations[0]


def require_native_reader_plugin_trace(raw: dict[str, Any], stderr: str, member: str) -> None:
    """Associate retained member bytes with an actual Qt loaded-library record."""
    original = str(Path(raw["root"]) / member)
    expected = f'qt.core.library: "{original}" loaded library'
    if not isinstance(stderr, str) or expected not in {line.strip() for line in stderr.splitlines()}:
        raise ValueError("native reader did not retain actual consumed plugin trace")

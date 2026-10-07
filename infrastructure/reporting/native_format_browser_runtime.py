"""Bounded complete installed browser application byte inventory, standard library only."""

from __future__ import annotations

import hashlib
import json
import stat
import time
from pathlib import Path
from typing import Any

RUNTIME_SCHEMA = "template-native-browser-application-runtime-v1"
MAX_FILES = 10000
MAX_BYTES = 2 * 1024 * 1024 * 1024


def observe_runtime(executable: Path, *, deadline: float) -> dict[str, Any]:
    """Hash actual renderer/framework/resource bytes before and after execution."""
    root = next((path for path in executable.parents if path.name.endswith(".app")), None)
    if root is None:
        candidate = executable.resolve().parent
        if not (candidate / "resources.pak").is_file():
            raise ValueError("complete browser runtime requires a dedicated app/resource bundle")
        root = candidate
    root = root.resolve(strict=True)
    rows: list[dict[str, Any]] = []
    total = 0
    for path in sorted(root.rglob("*")):
        if time.monotonic() >= deadline:
            raise TimeoutError("browser runtime inventory exhausted original deadline")
        if len(rows) >= MAX_FILES:
            raise ValueError("browser application file count exceeds finite bound")
        relative = path.relative_to(root).as_posix()
        before = path.lstat()
        if stat.S_ISLNK(before.st_mode):
            target = path.resolve(strict=True)
            if not target.is_relative_to(root):
                raise ValueError("browser application alias escapes its declared bundle")
            rows.append({"path": relative, "kind": "alias", "target": target.relative_to(root).as_posix()})
        elif stat.S_ISREG(before.st_mode):
            total += before.st_size
            if before.st_size > 512 * 1024 * 1024 or total > MAX_BYTES:
                raise ValueError("browser application bytes exceed finite bound")
            digest = hashlib.sha256()
            with path.open("rb") as file:
                while block := file.read(1024 * 1024):
                    digest.update(block)
            after = path.lstat()

            def identity(value: Any) -> tuple[int, ...]:
                return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)

            if identity(before) != identity(after):
                raise ValueError("browser application bytes changed during inventory")
            rows.append({"path": relative, "kind": "file", "bytes": before.st_size, "sha256": digest.hexdigest()})
        elif not stat.S_ISDIR(before.st_mode):
            raise ValueError("browser application contains unsupported filesystem node")
    actual = executable.resolve(strict=True)
    if not actual.is_relative_to(root):
        raise ValueError("browser executable escapes its runtime bundle")
    payload = {
        "schema_version": RUNTIME_SCHEMA,
        "root": str(root),
        "executable": str(actual),
        "files": rows,
        "bytes": total,
    }
    payload["digest"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload


def validate_runtime(raw: dict[str, Any], executable: str, digest: str) -> None:
    """Validate portable original runtime identities without producer path reads."""
    import re

    if raw.get("schema_version") != RUNTIME_SCHEMA or raw.get("executable") != executable:
        raise ValueError("browser runtime executable/schema differs")
    root = Path(raw["root"])
    if not root.is_absolute() or not Path(executable).is_relative_to(root):
        raise ValueError("browser runtime original labels are not confined")
    rows = raw.get("files")
    if not isinstance(rows, list) or not rows or len(rows) > MAX_FILES:
        raise ValueError("browser runtime original inventory is absent/unbounded")
    names = set()
    total = 0
    binaries = {}
    for row in rows:
        path = Path(row["path"])
        if path.is_absolute() or ".." in path.parts or not path.parts or path.as_posix() in names:
            raise ValueError("browser runtime original member escapes/duplicates")
        names.add(path.as_posix())
        if row["kind"] == "file":
            if (
                set(row) != {"path", "kind", "bytes", "sha256"}
                or type(row["bytes"]) is not int
                or not 0 <= row["bytes"] <= 512 * 1024 * 1024
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
            ):
                raise ValueError("browser runtime original file identity is invalid")
            binaries[row["path"]] = row["sha256"]
            total += row["bytes"]
        elif row["kind"] == "alias":
            target = Path(row["target"])
            if set(row) != {"path", "kind", "target"} or target.is_absolute() or ".." in target.parts:
                raise ValueError("browser runtime original alias escapes")
        else:
            raise ValueError("browser runtime original member kind is invalid")
    if (
        total > MAX_BYTES
        or total != raw["bytes"]
        or binaries.get(Path(executable).relative_to(root).as_posix()) != digest
    ):
        raise ValueError("browser runtime original executable/byte inventory differs")
    payload = {key: value for key, value in raw.items() if key != "digest"}
    if (
        raw.get("digest")
        != hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    ):
        raise ValueError("browser runtime original inventory digest differs")

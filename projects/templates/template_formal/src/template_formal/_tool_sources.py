"""Bounded source snapshots for standalone formal tools.

Held no-follow descriptors bind every admitted ancestor and regular file.
Tools consume private copies of these bytes rather than mutable source paths.
"""

from __future__ import annotations

import os
import stat
import time
from collections.abc import Callable
from pathlib import Path

_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
_FILE_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)


def _budget(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise TimeoutError("formal source admission exhausted the total deadline")


def _identity(observation: os.stat_result) -> tuple[int, int, int]:
    return observation.st_dev, observation.st_ino, observation.st_mode


def _content_identity(observation: os.stat_result) -> tuple[int, ...]:
    return (*_identity(observation), observation.st_size, observation.st_mtime_ns, observation.st_ctime_ns)


def _open_ancestors(path: Path, deadline: float) -> list[tuple[int, int | None, str]]:
    """Hold the lexical absolute chain; public link aliases are never resolved."""
    path = path.absolute()
    if ".." in path.parts:
        raise ValueError("formal source refuses lexical parent traversal")
    if len(path.parts) > 128:
        raise ValueError("formal source exceeds its ancestor depth bound")
    held: list[tuple[int, int | None, str]] = [(os.open(path.anchor, _DIRECTORY_FLAGS), None, "")]
    try:
        for component in path.parts[1:]:
            _budget(deadline)
            parent = held[-1][0]
            before = os.stat(component, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode):
                raise ValueError("formal source custody refuses directory and ancestor symlinks or non-directories")
            descriptor = os.open(component, _DIRECTORY_FLAGS, dir_fd=parent)
            held.append((descriptor, parent, component))
            if _identity(before) != _identity(os.fstat(descriptor)):
                raise ValueError("formal source ancestor changed during admission")
        return held
    except BaseException:
        for descriptor, _, _ in reversed(held):
            os.close(descriptor)
        raise


def _verify_chain(held: list[tuple[int, int | None, str]]) -> None:
    for descriptor, parent, component in held:
        if parent is not None and _identity(os.fstat(descriptor)) != _identity(
            os.stat(component, dir_fd=parent, follow_symlinks=False)
        ):
            raise ValueError("formal source ancestor changed during admission")


def _read(parent: int, name: str, deadline: float, max_bytes: int) -> bytes:
    _budget(deadline)
    before = os.stat(name, dir_fd=parent, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
        raise ValueError("formal source must be a bounded regular file; symlinks and nonregular files are refused")
    descriptor = os.open(name, _FILE_FLAGS, dir_fd=parent)
    try:
        if _content_identity(before) != _content_identity(os.fstat(descriptor)):
            raise ValueError("formal source file changed during admission")
        chunks: list[bytes] = []
        size = 0
        while True:
            _budget(deadline)
            chunk = os.read(descriptor, min(65536, max_bytes + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("formal source exceeds its byte bound")
        if size != before.st_size or _content_identity(before) != _content_identity(os.fstat(descriptor)):
            raise ValueError("formal source file changed during admission")
        if _content_identity(before) != _content_identity(os.stat(name, dir_fd=parent, follow_symlinks=False)):
            raise ValueError("formal source file path changed during admission")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def snapshot_file(path: Path, *, deadline: float, max_bytes: int = 8 * 1024 * 1024) -> bytes:
    """Admit one bounded regular file with its complete held ancestor chain."""
    held = _open_ancestors(path.absolute().parent, deadline)
    try:
        content = _read(held[-1][0], path.name, deadline, max_bytes)
        _verify_chain(held)
        _budget(deadline)
        return content
    finally:
        for descriptor, _, _ in reversed(held):
            os.close(descriptor)


def snapshot_tree(
    root: Path,
    *,
    deadline: float,
    exclude: Callable[[tuple[str, ...]], bool],
    max_entries: int = 4096,
    max_file_bytes: int = 8 * 1024 * 1024,
    max_total_bytes: int = 64 * 1024 * 1024,
    max_depth: int = 64,
) -> dict[str, bytes]:
    """Capture a finite tree, refusing every admitted nonregular entry."""
    held = _open_ancestors(root, deadline)
    records: dict[str, bytes] = {}
    entries = total = 0

    def walk(descriptor: int, parts: tuple[str, ...]) -> None:
        nonlocal entries, total
        _budget(deadline)
        before = os.fstat(descriptor)
        names: list[str] = []
        with os.scandir(descriptor) as inventory:
            for entry in inventory:
                _budget(deadline)
                entries += 1
                if entries > max_entries:
                    raise ValueError("formal source exceeds its entry bound")
                names.append(entry.name)
        for name in sorted(names):
            _budget(deadline)
            relative = (*parts, name)
            if exclude(relative):
                continue
            if len(relative) > max_depth:
                raise ValueError("formal source exceeds its depth bound")
            observation = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISDIR(observation.st_mode):
                child = os.open(name, _DIRECTORY_FLAGS, dir_fd=descriptor)
                held.append((child, descriptor, name))
                try:
                    if _identity(observation) != _identity(os.fstat(child)):
                        raise ValueError("formal source directory changed during admission")
                    walk(child, relative)
                    _verify_chain(held)
                finally:
                    held.pop()
                    os.close(child)
            else:
                content = _read(descriptor, name, deadline, max_file_bytes)
                total += len(content)
                if total > max_total_bytes:
                    raise ValueError("formal source exceeds its total byte bound")
                records["/".join(relative)] = content
        if _content_identity(before) != _content_identity(os.fstat(descriptor)):
            raise ValueError("formal source directory changed during admission")
        _verify_chain(held)

    try:
        walk(held[-1][0], ())
        _budget(deadline)
        return records
    finally:
        for descriptor, _, _ in reversed(held):
            os.close(descriptor)


def materialize(snapshot: dict[str, bytes], destination: Path) -> None:
    """Write admitted relative paths into a private owned tool workspace."""
    for relative, content in snapshot.items():
        if Path(relative).is_absolute() or any(part in {"", ".", ".."} for part in relative.split("/")):
            raise ValueError("frozen tool input must have an admitted relative path")
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o400)

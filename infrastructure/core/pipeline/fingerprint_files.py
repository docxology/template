"""Held-directory filesystem observations for content fingerprints."""

from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_ANCESTOR_FLAGS = getattr(os, "O_PATH", os.O_RDONLY) | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_FILE_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
_DIGESTS: dict[tuple[object, ...], str] = {}


def observation(value: os.stat_result) -> tuple[int, ...]:
    """Include identity, content-change clocks, permissions, and length."""
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns, value.st_mode)


def verify_directory(parent: int, name: str, descriptor: int) -> None:
    """Refuse detached or substituted directory paths."""
    expected = os.fstat(descriptor)
    observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
    if not stat.S_ISDIR(observed.st_mode) or (expected.st_dev, expected.st_ino) != (observed.st_dev, observed.st_ino):
        raise ValueError("Fingerprint directory changed during observation")


@contextmanager
def open_directory(parent: int, name: str) -> Iterator[int]:
    """Open one real directory relative to its already-held parent."""
    try:
        descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent)
    except OSError as exc:
        raise ValueError(f"Fingerprint refuses symlink or non-directory component: {name}") from exc
    try:
        yield descriptor
        verify_directory(parent, name, descriptor)
    finally:
        os.close(descriptor)


@contextmanager
def anchored_parent(path: Path) -> Iterator[int | None]:
    """Hold the lexical ancestor chain without following a symlink anywhere.

    A missing ancestor is an explicit missing-path observation. Existing
    ancestors are rechecked even in that case. Callers use canonical absolute
    paths; platform aliases such as a symlinked temporary root must be resolved
    deliberately before nominating a fingerprint boundary.
    """
    path = path.absolute()
    if ".." in path.parts:
        raise ValueError("Fingerprint paths cannot contain parent traversal")
    descriptors = [os.open(path.anchor, _ANCESTOR_FLAGS)]
    bindings: list[tuple[int, str, int]] = []
    current: int | None = descriptors[0]
    try:
        for name in path.parent.parts[1:]:
            assert current is not None
            try:
                child = os.open(name, _ANCESTOR_FLAGS, dir_fd=current)
            except FileNotFoundError:
                current = None
                break
            except OSError as exc:
                raise ValueError(f"Fingerprint refuses symlink or non-directory ancestor: {name}") from exc
            descriptors.append(child)
            bindings.append((current, name, child))
            current = child
        yield current
        for parent, name, descriptor in reversed(bindings):
            verify_directory(parent, name, descriptor)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def digest_file(path: Path, parent: int, name: str, original: os.stat_result, *, max_bytes: int | None = None) -> str:
    """Hash exact file bytes, reusing only an unchanged OS file observation."""
    if not stat.S_ISREG(original.st_mode):
        raise ValueError(f"Content identity requires a regular file: {path}")
    if max_bytes is not None and original.st_size > max_bytes:
        raise ValueError("Fingerprint file exceeds its read budget")
    expected = observation(original)
    key = (str(path.absolute()), *expected)
    result = _DIGESTS.get(key)
    if result is None:
        descriptor = os.open(name, _FILE_FLAGS, dir_fd=parent)
        try:
            before = os.fstat(descriptor)
            if observation(before) != expected or not stat.S_ISREG(before.st_mode):
                raise ValueError(f"Content changed before fingerprint read: {path}")
            digest = hashlib.sha256()
            size = 0
            while chunk := os.read(
                descriptor, 1024 * 1024 if max_bytes is None else min(1024 * 1024, max_bytes + 1 - size)
            ):
                size += len(chunk)
                if max_bytes is not None and size > max_bytes:
                    raise ValueError("Fingerprint file exceeds its read budget")
                digest.update(chunk)
            if observation(os.fstat(descriptor)) != expected:
                raise ValueError(f"Content changed during fingerprint read: {path}")
            result = digest.hexdigest()
        finally:
            os.close(descriptor)
    if observation(os.stat(name, dir_fd=parent, follow_symlinks=False)) != expected:
        raise ValueError(f"Content changed during fingerprint observation: {path}")
    if len(_DIGESTS) >= 16384:
        _DIGESTS.clear()
    _DIGESTS[key] = result
    return result

"""Race-safe confined atomic writes for security-sensitive evidence."""

from __future__ import annotations

import os
import secrets
import stat
from contextlib import suppress
from pathlib import Path

_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)


def _relative_target(root: Path, target: Path) -> tuple[Path, tuple[str, ...], str]:
    lexical_root = root.absolute()
    lexical_target = target.absolute()
    try:
        relative = lexical_target.relative_to(lexical_root)
    except ValueError as exc:
        raise ValueError(f"write target escapes confinement root: {target}") from exc
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"write target must name a confined file: {target}")
    try:
        root_mode = lexical_root.lstat().st_mode
    except OSError as exc:
        raise ValueError(f"confinement root is unavailable: {lexical_root}") from exc
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise ValueError(f"confinement root must be a real directory: {lexical_root}")
    return lexical_root, relative.parts[:-1], relative.parts[-1]


def _open_directory(parent_fd: int, name: str, *, create: bool) -> int:
    try:
        return os.open(name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
    except FileNotFoundError:
        if not create:
            raise
        try:
            os.mkdir(name, mode=0o755, dir_fd=parent_fd)
        except FileExistsError:
            pass
        try:
            return os.open(name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        except OSError as exc:
            raise ValueError(f"refusing symlink component or non-directory write component: {name}") from exc
    except OSError as exc:
        raise ValueError(f"refusing symlink component or non-directory write component: {name}") from exc


def _open_parent(root: Path, parent_parts: tuple[str, ...], *, create: bool) -> tuple[int, list[int]]:
    try:
        root_fd = os.open(root, _DIRECTORY_FLAGS)
    except OSError as exc:
        raise ValueError(f"cannot open confinement root without following symlinks: {root}") from exc
    opened = [root_fd]
    current = root_fd
    try:
        for part in parent_parts:
            current = _open_directory(current, part, create=create)
            opened.append(current)
    except BaseException:
        for descriptor in reversed(opened):
            os.close(descriptor)
        raise
    return current, opened


def _close_all(descriptors: list[int]) -> None:
    for descriptor in reversed(descriptors):
        with suppress(OSError):
            os.close(descriptor)


def _directory_identity_matches(root: Path, parent_parts: tuple[str, ...], expected_fd: int) -> bool:
    try:
        current, opened = _open_parent(root, parent_parts, create=False)
    except (OSError, ValueError):
        return False
    try:
        expected = os.fstat(expected_fd)
        observed = os.fstat(current)
        return (expected.st_dev, expected.st_ino) == (observed.st_dev, observed.st_ino)
    finally:
        _close_all(opened)


def _reject_existing_symlink(parent_fd: int, filename: str) -> None:
    try:
        metadata = os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode):
        raise ValueError(f"refusing to replace symlink write target: {filename}")
    if stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"refusing to replace directory write target: {filename}")


def _create_temporary(parent_fd: int, filename: str) -> tuple[int, str]:
    for _ in range(64):
        temporary = f".{filename}.{secrets.token_hex(12)}.tmp"
        try:
            return os.open(temporary, _FILE_FLAGS, 0o600, dir_fd=parent_fd), temporary
        except FileExistsError:
            continue
    raise OSError("could not allocate a unique confined temporary file")


def _write_all(descriptor: int, content: str) -> None:
    remaining = memoryview(content.encode("utf-8"))
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("short write while persisting confined evidence")
        remaining = remaining[written:]
    os.fchmod(descriptor, 0o644)
    os.fsync(descriptor)


def atomic_write_text_confined(root: Path, target: Path, content: str) -> None:
    """Atomically write UTF-8 text using held directory descriptors.

    Every path component is opened with ``O_NOFOLLOW``. The final rename is
    relative to the already-open parent descriptor, so replacing a parent with
    an attacker-controlled symlink cannot redirect the write outside *root*.
    Directory identity checks make such a rename fail visibly rather than
    reporting success for a now-detached directory.
    """
    lexical_root, parent_parts, filename = _relative_target(root, target)
    parent_fd, opened = _open_parent(lexical_root, parent_parts, create=True)
    temporary_fd = -1
    temporary_name = ""
    try:
        _reject_existing_symlink(parent_fd, filename)
        temporary_fd, temporary_name = _create_temporary(parent_fd, filename)
        _write_all(temporary_fd, content)
        os.close(temporary_fd)
        temporary_fd = -1
        if not _directory_identity_matches(lexical_root, parent_parts, parent_fd):
            raise ValueError("write parent changed during confined atomic write")
        os.replace(
            temporary_name,
            filename,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temporary_name = ""
        os.fsync(parent_fd)
        if not _directory_identity_matches(lexical_root, parent_parts, parent_fd):
            raise ValueError("write parent changed during confined atomic write")
    finally:
        if temporary_fd >= 0:
            with suppress(OSError):
                os.close(temporary_fd)
        if temporary_name:
            with suppress(OSError):
                os.unlink(temporary_name, dir_fd=parent_fd)
        _close_all(opened)


__all__ = ["atomic_write_text_confined"]

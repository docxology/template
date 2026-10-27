"""Race-safe confined atomic writes for security-sensitive evidence."""

from __future__ import annotations

import os
import math
import secrets
import stat
import time
from contextlib import suppress, contextmanager
from collections.abc import Iterator
from pathlib import Path

_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_ANCESTOR_FLAGS = getattr(os, "O_PATH", os.O_RDONLY) | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)


def _relative_target(root: Path, target: Path) -> tuple[Path, tuple[str, ...], str]:
    lexical_root = root.absolute()
    lexical_target = target.absolute()
    if ".." in lexical_root.parts:
        raise ValueError("confinement root cannot contain parent traversal")
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


def _open_directory(parent_fd: int, name: str, *, create: bool, ancestor: bool = False) -> int:
    flags = _ANCESTOR_FLAGS if ancestor else _DIRECTORY_FLAGS
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        if not create:
            raise
        try:
            os.mkdir(name, mode=0o755, dir_fd=parent_fd)
        except FileExistsError:
            pass
        try:
            return os.open(name, flags, dir_fd=parent_fd)
        except OSError as exc:
            raise ValueError(f"refusing symlink component or non-directory write component: {name}") from exc
    except OSError as exc:
        raise ValueError(f"refusing symlink component or non-directory write component: {name}") from exc


def _open_parent(
    root: Path,
    parent_parts: tuple[str, ...],
    *,
    create: bool,
    expected_root_identity: tuple[int, int] | None = None,
) -> tuple[int, list[int]]:
    """Hold every lexical ancestor, including ancestors of the nominated root."""
    if expected_root_identity is not None and (
        type(expected_root_identity) is not tuple
        or len(expected_root_identity) != 2
        or any(type(value) is not int or value < 0 for value in expected_root_identity)
    ):
        raise ValueError("expected_root_identity must be an exact nonnegative integer pair")
    # Strict ancestors need search only. The selected root and its descendants
    # keep readable handles, including the final parent used by fsync.
    root_parts = root.parts[1:]
    try:
        anchor_fd = os.open(root.anchor, _ANCESTOR_FLAGS if root_parts else _DIRECTORY_FLAGS)
    except OSError as exc:
        raise ValueError(f"cannot open confinement root without following symlinks: {root}") from exc
    opened = [anchor_fd]
    current = anchor_fd
    bindings: list[tuple[int, str, int]] = []
    try:
        for index, part in enumerate(root_parts):
            child = _open_directory(current, part, create=False, ancestor=index < len(root_parts) - 1)
            bindings.append((current, part, child))
            current = child
            opened.append(current)
        admitted_root = os.fstat(current)
        if (
            expected_root_identity is not None
            and (admitted_root.st_dev, admitted_root.st_ino) != expected_root_identity
        ):
            raise ValueError("confinement root changed after admission")
        for part in parent_parts:
            child = _open_directory(current, part, create=create)
            bindings.append((current, part, child))
            current = child
            opened.append(current)
        for parent, name, descriptor in reversed(bindings):
            expected = os.fstat(descriptor)
            observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(observed.st_mode) or (expected.st_dev, expected.st_ino) != (
                observed.st_dev,
                observed.st_ino,
            ):
                raise ValueError("confinement ancestor changed while opening the held parent")
    except BaseException:
        for descriptor in reversed(opened):
            os.close(descriptor)
        raise
    return current, opened


def _close_all(descriptors: list[int]) -> None:
    for descriptor in reversed(descriptors):
        with suppress(OSError):
            os.close(descriptor)


def _directory_identity_matches(
    root: Path,
    parent_parts: tuple[str, ...],
    expected_fd: int,
    expected_root_identity: tuple[int, int] | None = None,
) -> bool:
    try:
        current, opened = _open_parent(root, parent_parts, create=False, expected_root_identity=expected_root_identity)
    except OSError, ValueError:
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


def _create_temporary(parent_fd: int) -> tuple[int, str]:
    for _ in range(64):
        # A valid destination can already approach the filesystem's component
        # limit, especially with multibyte names. Keep the sibling temporary
        # name independent of it while retaining exclusive random allocation.
        temporary = f".template-write-{secrets.token_hex(12)}.tmp"
        try:
            return os.open(temporary, _FILE_FLAGS, 0o600, dir_fd=parent_fd), temporary
        except FileExistsError:
            continue
    raise OSError("could not allocate a unique confined temporary file")


def _write_all(descriptor: int, content: bytes, mode: int = 0o644) -> None:
    remaining = memoryview(content)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("short write while persisting confined evidence")
        remaining = remaining[written:]
    os.fchmod(descriptor, mode)
    os.fsync(descriptor)


def atomic_write_text_confined(
    root: Path,
    target: Path,
    content: str,
    *,
    mode: int = 0o644,
    expected_root_identity: tuple[int, int] | None = None,
) -> None:
    """Atomically write UTF-8 text using held directory descriptors.

    Every path component is opened with ``O_NOFOLLOW``. The final rename is
    relative to the already-open parent descriptor, so replacing a parent with
    an attacker-controlled symlink cannot redirect the write outside *root*.
    Directory identity checks make such a rename fail visibly rather than
    reporting success for a now-detached directory.
    ``mode`` sets the final permissions before publication; the default remains
    readable publication evidence (0644).
    """
    atomic_write_bytes_confined(
        root, target, content.encode("utf-8"), mode=mode, expected_root_identity=expected_root_identity
    )


def atomic_write_bytes_confined(
    root: Path,
    target: Path,
    content: bytes,
    *,
    mode: int = 0o644,
    expected_root_identity: tuple[int, int] | None = None,
) -> None:
    """Atomically persist exact binary bytes with the text writer's confinement."""
    _atomic_write_bytes_confined(root, target, content, mode=mode, expected_root_identity=expected_root_identity)


def atomic_write_bytes_confined_observed(
    root: Path,
    target: Path,
    content: bytes,
    *,
    mode: int = 0o644,
    expected_root_identity: tuple[int, int] | None = None,
) -> tuple[int, int, int, int, int]:
    """Return the actual held written inode identity, never prior-target CAS.

    The temporary file descriptor remains open through publication and final
    parent/name validation. A later path replacement cannot supply this inode.
    This API does not compare-and-swap or attest which prior target was replaced.
    """
    return _atomic_write_bytes_confined(root, target, content, mode=mode, expected_root_identity=expected_root_identity)


def _atomic_write_bytes_confined(
    root: Path,
    target: Path,
    content: bytes,
    *,
    mode: int = 0o644,
    expected_root_identity: tuple[int, int] | None = None,
) -> tuple[int, int, int, int, int]:
    """Atomically persist exact binary bytes with the text writer's confinement."""
    if not isinstance(content, bytes):
        raise TypeError("confined binary evidence must be bytes")
    lexical_root, parent_parts, filename = _relative_target(root, target)
    parent_fd, opened = _open_parent(
        lexical_root, parent_parts, create=True, expected_root_identity=expected_root_identity
    )
    temporary_fd = -1
    temporary_name = ""
    try:
        _reject_existing_symlink(parent_fd, filename)
        temporary_fd, temporary_name = _create_temporary(parent_fd)
        _write_all(temporary_fd, content, mode)
        if not _directory_identity_matches(lexical_root, parent_parts, parent_fd, expected_root_identity):
            raise ValueError("write parent changed during confined atomic write")
        os.replace(
            temporary_name,
            filename,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temporary_name = ""
        os.fsync(parent_fd)
        if not _directory_identity_matches(lexical_root, parent_parts, parent_fd, expected_root_identity):
            raise ValueError("write parent changed during confined atomic write")
        written = os.fstat(temporary_fd)
        named = os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
        identity = (written.st_dev, written.st_ino, written.st_size, written.st_mtime_ns, written.st_ctime_ns)
        if (
            not stat.S_ISREG(named.st_mode)
            or identity != (named.st_dev, named.st_ino, named.st_size, named.st_mtime_ns, named.st_ctime_ns)
            or written.st_size != len(content)
        ):
            raise ValueError("published target differs from the actual held written inode")
        return identity
    finally:
        if temporary_fd >= 0:
            with suppress(OSError):
                os.close(temporary_fd)
        if temporary_name:
            with suppress(OSError):
                os.unlink(temporary_name, dir_fd=parent_fd)
        _close_all(opened)


def read_bytes_confined(
    root: Path,
    target: Path,
    *,
    max_bytes: int = 8 * 1024 * 1024,
    expected_root_identity: tuple[int, int] | None = None,
) -> bytes:
    """Read a bounded regular file without following replaced path components."""
    lexical_root, parts, name = _relative_target(root, target)
    parent, opened = _open_parent(lexical_root, parts, create=False, expected_root_identity=expected_root_identity)
    descriptor = -1
    try:
        descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK, dir_fd=parent)
        original = os.fstat(descriptor)
        if not stat.S_ISREG(original.st_mode):
            raise ValueError("Confined evidence must be a regular file")
        chunks: list[bytes] = []
        size = 0
        while chunk := os.read(descriptor, min(65536, max_bytes + 1 - size)):
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("Confined evidence exceeds its read budget")
            chunks.append(chunk)
        observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
        actual = os.fstat(descriptor)
        if (
            (observed.st_dev, observed.st_ino) != (actual.st_dev, actual.st_ino)
            or (original.st_size, original.st_mtime_ns, original.st_ctime_ns)
            != (actual.st_size, actual.st_mtime_ns, actual.st_ctime_ns)
            or not _directory_identity_matches(lexical_root, parts, parent, expected_root_identity)
        ):
            raise ValueError("Evidence path changed during confined read")
        return b"".join(chunks)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        _close_all(opened)


def read_text_confined(
    root: Path,
    target: Path,
    *,
    max_bytes: int = 8 * 1024 * 1024,
    expected_root_identity: tuple[int, int] | None = None,
) -> str:
    """Read bounded UTF-8 evidence through the confined file descriptor."""
    return read_bytes_confined(root, target, max_bytes=max_bytes, expected_root_identity=expected_root_identity).decode(
        "utf-8"
    )


def _open_control_lock(
    root: Path,
    parts: tuple[str, ...],
    name: str,
    parent: int,
    deadline: float,
    expected_root_identity: tuple[int, int] | None = None,
) -> int:
    """Open one stable lock inode, bounding simultaneous first-creation races."""
    flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
    while True:
        if not _directory_identity_matches(root, parts, parent, expected_root_identity):
            raise ValueError("Control directory changed during lock creation")
        try:
            try:
                return os.open(name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
            except FileExistsError:
                return os.open(name, flags, dir_fd=parent)
        except FileNotFoundError:
            # APFS can briefly return ENOENT when concurrent creators select the
            # same new name. Retry only while the held parent remains canonical.
            if not _directory_identity_matches(root, parts, parent, expected_root_identity):
                raise ValueError("Control directory changed during lock creation") from None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Control lock creation deadline expired") from None
            time.sleep(min(0.005, remaining))


def _check_control_lock(
    root: Path,
    parts: tuple[str, ...],
    name: str,
    parent: int,
    descriptor: int,
    expected_root_identity: tuple[int, int] | None = None,
) -> None:
    """Refuse a detached directory or a substituted lock inode."""
    if not _directory_identity_matches(root, parts, parent, expected_root_identity):
        raise ValueError("Control directory changed during lock acquisition")
    try:
        observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError as exc:
        raise ValueError("Control lock target changed during acquisition") from exc
    actual = os.fstat(descriptor)
    if not stat.S_ISREG(observed.st_mode) or (observed.st_dev, observed.st_ino) != (actual.st_dev, actual.st_ino):
        raise ValueError("Control lock target changed during acquisition")


@contextmanager
def confined_file_lock(
    root: Path,
    target: Path,
    *,
    timeout: float = 10.0,
    expected_root_identity: tuple[int, int] | None = None,
) -> Iterator[None]:
    """Hold a finite POSIX lock on a confined regular control file."""
    import fcntl

    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Control lock timeout must be finite and positive")
    deadline = time.monotonic() + timeout
    lexical_root, parts, name = _relative_target(root, target)
    parent, opened = _open_parent(lexical_root, parts, create=True, expected_root_identity=expected_root_identity)
    descriptor = -1
    try:
        descriptor = _open_control_lock(lexical_root, parts, name, parent, deadline, expected_root_identity)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("Control lock must be a regular file")
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Control lock deadline expired")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Control lock deadline expired") from None
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        _check_control_lock(lexical_root, parts, name, parent, descriptor, expected_root_identity)
        yield
        _check_control_lock(lexical_root, parts, name, parent, descriptor, expected_root_identity)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        _close_all(opened)


def append_text_confined(
    root: Path,
    target: Path,
    content: str,
    *,
    expected_root_identity: tuple[int, int] | None = None,
) -> None:
    """Append a durable complete record under a separate finite file lock.

    When supplied, ``expected_root_identity`` is the device/inode pair of the
    caller's held admitted directory. Every IO phase checks its actual opened
    root against that pair before creating any output directory.
    """
    with confined_file_lock(
        root, target.with_name(target.name + ".append.lock"), expected_root_identity=expected_root_identity
    ):
        try:
            previous = read_text_confined(root, target, expected_root_identity=expected_root_identity)
        except FileNotFoundError:
            previous = ""
        atomic_write_text_confined(
            root, target, previous + content, mode=0o600, expected_root_identity=expected_root_identity
        )


def unlink_confined(root: Path, target: Path) -> None:
    """Remove only a confined regular file, preserving replacement diagnostics."""
    lexical_root, parts, name = _relative_target(root, target)
    parent, opened = _open_parent(lexical_root, parts, create=False)
    try:
        _reject_existing_symlink(parent, name)
        if not _directory_identity_matches(lexical_root, parts, parent):
            raise ValueError("Control directory changed before unlink")
        try:
            os.unlink(name, dir_fd=parent)
        except FileNotFoundError:
            pass
    finally:
        _close_all(opened)


__all__ = [
    "atomic_write_text_confined",
    "atomic_write_bytes_confined",
    "atomic_write_bytes_confined_observed",
    "read_text_confined",
    "read_bytes_confined",
    "append_text_confined",
    "unlink_confined",
    "confined_file_lock",
]

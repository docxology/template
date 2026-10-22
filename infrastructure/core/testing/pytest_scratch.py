"""Fresh owned pytest fixtures outside Source and installed runtime trees."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile


def _unlock_fixture_directories(descriptor: int) -> None:
    """Restore owner access only through held no-follow fixture directory FDs."""
    held = os.fstat(descriptor)
    if not stat.S_ISDIR(held.st_mode) or (hasattr(os, "getuid") and held.st_uid != os.getuid()):
        raise ValueError("pytest scratch cannot change permissions of a foreign fixture directory")
    os.fchmod(descriptor, stat.S_IMODE(held.st_mode) | 0o700)
    for name in os.listdir(descriptor):
        named = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        if stat.S_ISDIR(named.st_mode):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            try:
                opened = os.fstat(child)
                if (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino):
                    raise ValueError("pytest scratch fixture directory changed before held cleanup")
                _unlock_fixture_directories(child)
            finally:
                os.close(child)


def _verify_parent_locator(base: Path, parent_fd: int) -> None:
    """The pytest pathname must still select the actually held physical parent."""
    held, named = os.fstat(parent_fd), base.lstat()
    if (
        not stat.S_ISDIR(named.st_mode)
        or base.resolve(strict=True) != base
        or (held.st_dev, held.st_ino) != (named.st_dev, named.st_ino)
    ):
        raise ValueError("pytest scratch parent changed physical ownership; cleanup refused")


@contextmanager
def external_pytest_scratch(root: Path, *, token: str) -> Iterator[Path]:
    """Mint private fixtures; cleanup traverses only the originally held inode."""
    if not isinstance(token, str) or not token:
        raise ValueError("pytest scratch requires the actual execution nonce")
    if (
        not shutil.rmtree.avoids_symlink_attacks
        or os.listdir not in os.supports_fd
        or any(call not in os.supports_dir_fd for call in (os.open, os.stat, os.unlink, os.rmdir))
        or os.stat not in os.supports_follow_symlinks
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
    ):
        raise ValueError("pytest scratch requires physical directory descriptor cleanup")
    base = Path(tempfile.gettempdir()).resolve(strict=True)
    source, runtime = root.resolve(strict=True), Path(sys.prefix).resolve(strict=True)
    if (
        base.is_relative_to(source)
        or base.is_relative_to(runtime)
        or any((parent / ".git").exists() for parent in (base, *base.parents))
    ):
        raise ValueError("pytest scratch must be outside Source, Git and selected runtime trees")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent_fd = os.open(base, flags)
    try:
        _verify_parent_locator(base, parent_fd)
        prefix = "template-pytest-" + hashlib.sha256(token.encode()).hexdigest()[:16] + "-"
        directory = Path(tempfile.mkdtemp(prefix=prefix, dir=base))
        held = directory.lstat()
        if (
            not stat.S_ISDIR(held.st_mode)
            or directory.resolve(strict=True) != directory
            or stat.S_IMODE(held.st_mode) != 0o700
            or (hasattr(os, "getuid") and held.st_uid != os.getuid())
        ):
            raise ValueError("pytest scratch was not created as its actual private physical directory")
        identity = held.st_dev, held.st_ino
        directory_fd = os.open(directory.name, flags, dir_fd=parent_fd)
        try:
            opened = os.fstat(directory_fd)
            if (opened.st_dev, opened.st_ino) != identity:
                raise ValueError("pytest scratch changed before its actual directory descriptor opened")
            _verify_parent_locator(base, parent_fd)
            if directory.resolve(strict=True) != directory:
                raise ValueError("pytest scratch lost its actual physical pathname before pytest")
            try:
                yield directory
            finally:
                _verify_parent_locator(base, parent_fd)
                named = os.stat(directory.name, dir_fd=parent_fd, follow_symlinks=False)
                if not stat.S_ISDIR(named.st_mode) or (named.st_dev, named.st_ino) != identity:
                    raise ValueError("pytest scratch changed physical ownership; cleanup refused")
                # Never reopen the top pathname for traversal. A replacement
                # between this check and enumeration cannot expose its contents.
                # Real installed-wheel fixtures retain read-only resolver
                # metadata. Restore their owner access only after pytest ends.
                _unlock_fixture_directories(directory_fd)
                for name in os.listdir(directory_fd):
                    child = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    if stat.S_ISDIR(child.st_mode):
                        shutil.rmtree(name, dir_fd=directory_fd)
                    else:
                        os.unlink(name, dir_fd=directory_fd)
                _verify_parent_locator(base, parent_fd)
                named = os.stat(directory.name, dir_fd=parent_fd, follow_symlinks=False)
                if not stat.S_ISDIR(named.st_mode) or (named.st_dev, named.st_ino) != identity:
                    raise ValueError("pytest scratch changed physical ownership; cleanup refused")
                os.rmdir(directory.name, dir_fd=parent_fd)
                _verify_parent_locator(base, parent_fd)
        finally:
            os.close(directory_fd)
    finally:
        os.close(parent_fd)

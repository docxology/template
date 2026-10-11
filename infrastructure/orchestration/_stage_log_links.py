"""Held absolute lifecycle-link admission for project logging."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from infrastructure.core.pipeline.fingerprint_files import anchored_parent, observation

_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_MAX_LINK_HOPS = 32


def _check_links(bindings: list[tuple[int, str, tuple[int, ...]]]) -> None:
    for parent, name, expected in bindings:
        if observation(os.stat(name, dir_fd=parent, follow_symlinks=False)) != expected:
            raise ValueError("Lifecycle project link changed during log admission")


@contextmanager
def admitted_lifecycle_log_root(lexical: Path) -> Iterator[tuple[Path, tuple[int, int]]]:
    """Hold bounded absolute leaf hops through the canonical append operation.

    Managed mirrors point to absolute lifecycle entries, which can themselves
    point to self-versioned checkouts. Relative targets and links in ancestors
    are outside this logging exception. No mutable lexical resolver selects
    the admitted destination.
    """
    current = lexical.absolute()
    seen: set[Path] = set()
    bindings: list[tuple[int, str, tuple[int, ...]]] = []
    with ExitStack() as held:
        for hops in range(_MAX_LINK_HOPS + 1):
            if current in seen:
                raise ValueError("Lifecycle project link cycle is refused")
            seen.add(current)
            parent = held.enter_context(anchored_parent(current))
            if parent is None:
                raise ValueError("Lifecycle project parent is unavailable")
            before = os.stat(current.name, dir_fd=parent, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode):
                if hops == _MAX_LINK_HOPS:
                    raise ValueError("Lifecycle project link hop limit exceeded")
                target = Path(os.readlink(current.name, dir_fd=parent))
                if not target.is_absolute() or target.anchor != "/" or ".." in target.parts:
                    raise ValueError("Lifecycle logging requires absolute targets without parent traversal")
                bindings.append((parent, current.name, observation(before)))
                _check_links(bindings)
                current = target
                continue
            if not stat.S_ISDIR(before.st_mode):
                raise ValueError("Lifecycle project log root must be a real directory")
            descriptor = os.open(current.name, _DIRECTORY_FLAGS, dir_fd=parent)
            held.callback(os.close, descriptor)
            admitted = os.fstat(descriptor)
            if observation(admitted) != observation(before):
                raise ValueError("Lifecycle project root changed before log admission")
            identity = (admitted.st_dev, admitted.st_ino)
            _check_links(bindings)
            yield current, identity
            _check_links(bindings)
            after = os.stat(current.name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(after.st_mode) or (after.st_dev, after.st_ino) != identity:
                raise ValueError("Lifecycle project root changed during log append")
            return
    raise ValueError("Lifecycle project log root is unavailable")

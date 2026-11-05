"""Confined, serialized mutations of human decision state."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Concatenate, ParamSpec, Protocol, TypeVar

from infrastructure.core.files.secure_write import confined_file_lock


class _OutputOwner(Protocol):
    project_output_dir: Path


P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T", bound=_OutputOwner)


def locked_state(function: Callable[Concatenate[T, P], R]) -> Callable[Concatenate[T, P], R]:
    """Serialize review and consumption without extending the project execution lock."""

    @wraps(function)
    def wrapped(owner: T, *args: P.args, **kwargs: P.kwargs) -> R:
        root = owner.project_output_dir
        if root.is_symlink():
            raise ValueError("Human decision output root cannot be a symlink")
        root.mkdir(parents=True, exist_ok=True)
        with confined_file_lock(root, root / ".pipeline/hitl-state.lock", timeout=10):
            return function(owner, *args, **kwargs)

    return wrapped


__all__ = ["locked_state"]

"""Compatibility imports for native Current replay, owned by reporting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infrastructure.reporting.native_analysis_current import (
        NativeCurrentFailed,
        NativeCurrentInterrupted,
        NativeCurrentTimedOut,
        SCHEMA,
        replay_current_native_analysis,
    )

__all__ = [
    "NativeCurrentFailed",
    "NativeCurrentInterrupted",
    "NativeCurrentTimedOut",
    "SCHEMA",
    "replay_current_native_analysis",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from infrastructure.reporting import native_analysis_current

    return getattr(native_analysis_current, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

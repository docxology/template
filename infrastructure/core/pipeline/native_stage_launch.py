"""Compatibility imports for fixed native stage launch, owned by reporting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infrastructure.reporting.native_tool_producer import NativeStageLaunch, launch_owned_native_stage

__all__ = ["NativeStageLaunch", "launch_owned_native_stage"]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from infrastructure.reporting import native_tool_producer

    return getattr(native_tool_producer, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

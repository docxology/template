"""Rendering-owned seam through which a live native owner supplies tool custody.

Rendering never imports the reporting layer (``RENDERING-LAYERING-1``). The
layer that owns a live native producer installs its Pandoc, Mermaid and TeX
section launchers here for exactly that owner's lifetime, and rendering looks
them up at its call sites. A launcher method returns the real custody function
and rendering calls it from its own frame, so caller-identity checks inside the
custody function still observe the genuine rendering caller.

With no launchers installed, an environment that nominates a native public
reference origin is refused instead of silently rendering on the ordinary
path; otherwise the caller keeps its ordinary subprocess behavior. Installing
launchers grants no authority: each custody function still verifies its own
live owner, admitted Source and stage before launching anything.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from infrastructure.rendering.security import IsolatedCompletedProcess

NATIVE_ORIGIN_KEYS: tuple[str, ...] = (
    "TEMPLATE_PUBLIC_REFERENCE_ROOT",
    "TEMPLATE_PUBLIC_REFERENCE_COMMIT",
    "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT",
)


class SourceNativePandoc(Protocol):
    """Run one combined Pandoc writer under native custody; False means not handled."""

    def __call__(
        self,
        command: list[str],
        combined: Path,
        source_files: list[Path],
        *,
        writer: str,
        environment: dict[str, str] | None = None,
    ) -> bool: ...


class SourceNativeMermaid(Protocol):
    """Run one Mermaid production launch under native custody; None means not handled."""

    def __call__(
        self,
        command: list[str],
        source_path: Path,
        output_path: Path,
        *,
        role: str,
        raw_source: str,
        input_paths: tuple[Path, ...],
        environment: dict[str, str],
        timeout: int,
    ) -> IsolatedCompletedProcess | None: ...


class NativeTexSectionPass(Protocol):
    """Run one section compiler pass under native custody; None means not handled."""

    def __call__(
        self,
        command: list[str],
        tex: Path,
        output: Path,
        *,
        environment: dict[str, str],
    ) -> subprocess.CompletedProcess[str] | None: ...


class NativeRenderCustody(Protocol):
    """Launchers supplied by the layer that owns a live native producer."""

    def pandoc_launcher(self) -> SourceNativePandoc: ...

    def mermaid_launcher(self) -> SourceNativeMermaid: ...

    def tex_section_launcher(self) -> NativeTexSectionPass: ...


_INSTALLED: ContextVar[NativeRenderCustody | None] = ContextVar("template_native_render_custody", default=None)


@contextmanager
def installed_native_render_custody(custody: NativeRenderCustody) -> Iterator[None]:
    """Expose *custody* to rendering for the enclosing owner's context only."""
    token = _INSTALLED.set(custody)
    try:
        yield
    finally:
        _INSTALLED.reset(token)


def native_render_custody(refusal: str) -> NativeRenderCustody | None:
    """Return the installed launchers, refusing a native-origin call without them.

    Args:
        refusal: Caller-specific message raised when a native public reference
            origin is nominated but no live owner installed custody launchers.

    Returns:
        The installed launchers, or ``None`` for an ordinary rendering call.
    """
    custody = _INSTALLED.get()
    if custody is None and any(os.environ.get(key) for key in NATIVE_ORIGIN_KEYS):
        raise ValueError(refusal)
    return custody


__all__ = [
    "NATIVE_ORIGIN_KEYS",
    "NativeRenderCustody",
    "NativeTexSectionPass",
    "SourceNativeMermaid",
    "SourceNativePandoc",
    "installed_native_render_custody",
    "native_render_custody",
]

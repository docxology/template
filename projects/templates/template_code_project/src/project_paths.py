"""Resolve project root and standard output paths."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT_OVERRIDE: ContextVar[Path | None] = ContextVar("template_code_project_root", default=None)


@contextmanager
def project_root_context(project_root: Path) -> Iterator[Path]:
    """Temporarily route all exemplar output helpers to ``project_root``."""
    root = Path(project_root).resolve()
    token = _PROJECT_ROOT_OVERRIDE.set(root)
    try:
        yield root
    finally:
        _PROJECT_ROOT_OVERRIDE.reset(token)


def resolve_project_root(package_name: str) -> Path:
    """Process resolve project root."""
    override = _PROJECT_ROOT_OVERRIDE.get()
    if override is not None:
        return override
    mod = sys.modules.get(package_name)
    if mod is not None and hasattr(mod, "project_root"):
        return Path(mod.project_root)
    return _DEFAULT_ROOT


def project_output_dirs(project_root: Path | None = None) -> dict[str, Path]:
    """Return common output directories for the code exemplar."""
    root = project_root or _DEFAULT_ROOT
    output = root / "output"
    return {
        "output": output,
        "figures": output / "figures",
        "data": output / "data",
        "reports": output / "reports",
        "web": output / "web",
    }

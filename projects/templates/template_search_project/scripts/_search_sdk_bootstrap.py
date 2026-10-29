"""Select the declared runtime SDK before exposing project domain imports."""

from __future__ import annotations

import importlib
import os
import sys
import sysconfig
from pathlib import Path


def select_platform_sdk(project_root: Path) -> None:
    """Refuse authored or changed cached providers; restore caller import paths."""
    project_root = project_root.resolve(strict=True)
    providers = tuple(Path(sysconfig.get_path(kind)).resolve(strict=True) for kind in ("purelib", "platlib"))

    def own_source(path: Path) -> bool:
        resolved = path.resolve()
        return resolved.is_relative_to(project_root) and not any(
            resolved.is_relative_to(provider) for provider in providers
        )

    def verify_origins() -> None:
        for name, module in tuple(sys.modules.items()):
            if name == "infrastructure" or name.startswith("infrastructure."):
                origin = getattr(module, "__file__", None)
                if not isinstance(origin, str) or own_source(Path(origin).resolve(strict=True)):
                    raise ImportError("own project source cannot provide the declared platform SDK")
                declared_origin = getattr(getattr(module, "__spec__", None), "origin", None)
                if not isinstance(declared_origin, str) or Path(origin).resolve(strict=True) != Path(
                    declared_origin
                ).resolve(strict=True):
                    raise ImportError("the selected SDK module source origin changed")

    original = sys.path[:]
    try:
        sys.path[:] = [entry for entry in original if not own_source(Path(entry or os.getcwd()))]
        verify_origins()
        sdk = importlib.import_module("infrastructure")
        verify_origins()
        if sdk.__version__ != "4.4.0":
            raise ImportError("scripts require the declared platform 4.4.0 SDK")
    finally:
        sys.path[:] = original

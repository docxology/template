"""Pytest configuration for template_autoscientists."""

from __future__ import annotations

import os
import sys
import site
from pathlib import Path

import importlib


def _select_platform_sdk() -> None:
    """Keep pytest's own source paths separate from the selected environment SDK."""
    project = Path(__file__).resolve().parent.parent
    site_roots = tuple(Path(path).resolve() for path in site.getsitepackages())

    def own_source(path: Path) -> bool:
        resolved = path.resolve()
        return resolved.is_relative_to(project) and not any(resolved.is_relative_to(site) for site in site_roots)

    def verify_sdk_origins() -> None:
        for name, module in tuple(sys.modules.items()):
            if name == "infrastructure" or name.startswith("infrastructure."):
                origin = getattr(module, "__file__", None)
                if not isinstance(origin, str) or own_source(Path(origin)):
                    raise ImportError("own project source cannot provide the declared platform SDK")

    original = sys.path[:]
    try:
        sys.path[:] = [entry for entry in original if not own_source(Path(entry or os.getcwd()))]
        verify_sdk_origins()
        sdk = importlib.import_module("infrastructure")
        verify_sdk_origins()
        if getattr(sdk, "__version__", None) != "4.0.1":
            raise ImportError("tests require the declared platform 4.0.1 SDK")
    finally:
        sys.path[:] = original


_select_platform_sdk()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

for path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT / "scripts"):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

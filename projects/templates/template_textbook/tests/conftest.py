"""Pytest configuration for template_textbook tests.

Pins the headless matplotlib backend before any pyplot import and wires the
own source onto ``sys.path`` after selecting the declared development SDK.
Runtime textbook modules remain independent of that test-only dependency.
"""

from __future__ import annotations

import os
import sys
import tomllib
import site
from pathlib import Path

import importlib

# Force headless backend for matplotlib — must run before any matplotlib import.
os.environ.setdefault("MPLBACKEND", "Agg")


def _select_platform_sdk() -> None:
    """Keep pytest's own source paths separate from the selected environment SDK."""
    project = Path(__file__).resolve().parent.parent
    with (project / "pyproject.toml").open("rb") as stream:
        platform_version = tomllib.load(stream)["tool"]["template"]["platform_version"]
    if not isinstance(platform_version, str) or not platform_version.strip():
        raise ImportError("the own project requires a declared platform version")
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
        if getattr(sdk, "__version__", None) != platform_version:
            raise ImportError(f"tests require the declared platform {platform_version} SDK")
    finally:
        sys.path[:] = original


_select_platform_sdk()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

for path in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

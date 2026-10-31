"""Pytest configuration for template_sia."""

from __future__ import annotations

import shutil
import os
import sys
import tomllib
import site
from collections.abc import Callable
from pathlib import Path

import importlib

import pytest


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
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

# Volatile/derived paths that must never be copied into a test sandbox: copying a
# live coverage DB while pytest-cov rewrites it raises a mid-copy FileNotFoundError
# (a real flaky failure that broke the render's Project-Tests stage). Copy source only.
_COPY_IGNORE = shutil.ignore_patterns(
    ".coverage*",
    "coverage_project.json",
    "htmlcov",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "output",
    "*.egg-info",
)


@pytest.fixture
def copy_project_sandbox() -> Callable[[Path], Path]:
    """Return a helper that copies the project into a sandbox directory.

    The helper excludes volatile/derived artifacts (coverage DBs, caches, the
    output tree) so a mid-write coverage file cannot trigger a flaky copy error.
    Exposed as a fixture so every test module shares one guarded copy routine
    without import-time coupling to this module.

    Returns:
        A callable ``copy(dst) -> dst`` that populates ``dst`` from the project tree.
    """

    def _copy(dst: Path) -> Path:
        shutil.copytree(PROJECT_ROOT, dst, ignore=_COPY_IGNORE)
        return dst

    return _copy

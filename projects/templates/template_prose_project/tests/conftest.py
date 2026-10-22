"""Pytest configuration for template_prose_project tests."""

from __future__ import annotations

import os
import sys
import site
from pathlib import Path

import importlib

# Force headless backend for matplotlib in tests — must run before any matplotlib import.
# `docs/rendering_pipeline.md` documents this file as pinning MPLBACKEND=Agg; keep them in sync.
os.environ.setdefault("MPLBACKEND", "Agg")


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
        if getattr(sdk, "__version__", None) != "4.1.0":
            raise ImportError("tests require the declared platform 4.1.0 SDK")
    finally:
        sys.path[:] = original


_select_platform_sdk()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "template_prose_project"))
_TESTS_DIR = Path(__file__).resolve().parent
for _test_dir in (_TESTS_DIR, _TESTS_DIR / "pipeline"):
    if str(_test_dir) not in sys.path:
        sys.path.insert(0, str(_test_dir))

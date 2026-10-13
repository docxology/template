"""Shared sys.path bootstrap for project orchestrator scripts."""

from __future__ import annotations

import os
import site
import importlib
import importlib.util
import sys
from pathlib import Path


def _select_platform_sdk(project: Path) -> None:
    """Bind the declared interpreter SDK before exposing any project-owned source."""
    site_roots = tuple(Path(path).resolve() for path in site.getsitepackages())

    def own_source(path: Path) -> bool:
        resolved = path.resolve()
        return resolved.is_relative_to(project) and not any(resolved.is_relative_to(root) for root in site_roots)

    def verify_origins() -> None:
        for name, module in tuple(sys.modules.items()):
            if name == "infrastructure" or name.startswith("infrastructure."):
                origin = getattr(module, "__file__", None)
                if not isinstance(origin, str) or own_source(Path(origin)):
                    raise ImportError("own project source cannot provide the declared platform SDK")

    original = sys.path[:]
    try:
        sys.path[:] = [entry for entry in original if not own_source(Path(entry or os.getcwd()))]
        verify_origins()
        sdk = importlib.import_module("infrastructure")
        verify_origins()
        if getattr(sdk, "__version__", None) != "4.0.1":
            raise ImportError("project scripts require the declared platform 4.0.1 SDK")
    finally:
        sys.path[:] = original


def bootstrap_project(*, include_infrastructure: bool = False) -> Path:
    """Bind the declared SDK, then expose this project source.

    Returns:
        Project root directory (parent of ``scripts/``).
    """
    root = Path(__file__).resolve().parent.parent
    _select_platform_sdk(root)
    # Kept for caller compatibility; SDK authority comes from the interpreter,
    # never TEMPLATE_REPO_ROOT or a guessed ancestor.
    src = root / "src"
    if "template_literature_meta_analysis" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "template_literature_meta_analysis", src / "__init__.py", submodule_search_locations=[str(src)]
        )
        if spec is None or spec.loader is None:
            raise ImportError("cannot load canonical project source package")
        package = importlib.util.module_from_spec(spec)
        sys.modules["template_literature_meta_analysis"] = package
        spec.loader.exec_module(package)
    return root

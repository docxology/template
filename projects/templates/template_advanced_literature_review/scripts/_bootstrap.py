"""Shared sys.path bootstrap for project orchestrator scripts."""

from __future__ import annotations

import importlib
import os
import site
import sys
import tomllib
from pathlib import Path


def _select_platform_sdk(project: Path) -> None:
    """Bind the declared interpreter SDK before exposing any project-owned source."""
    required = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["template"][
        "platform_version"
    ]
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
        if getattr(sdk, "__version__", None) != required:
            raise ImportError(f"project scripts require the declared platform {required} SDK")
    finally:
        sys.path[:] = original


def bootstrap_project() -> Path:
    """Bind the declared SDK, then expose this project source.

    Returns:
        Project root directory (parent of ``scripts/``).
    """
    root = Path(__file__).resolve().parent.parent
    _select_platform_sdk(root)
    # SDK authority comes from the selected interpreter.
    src = root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
    _consume_project_argument(root)
    return root


def _consume_project_argument(project_root: Path) -> None:
    """Validate and remove the shared ``--project`` context argument.

    Project-local scripts historically inferred their root from ``__file__``.
    The repository methods contract now passes an explicit qualified project
    name to every stage command, so these wrappers accept that argument while
    retaining their existing script-specific argparse surfaces.
    """
    try:
        index = sys.argv.index("--project")
    except ValueError:
        return
    if index + 1 >= len(sys.argv):
        raise SystemExit("--project requires a qualified project name")
    from infrastructure.rendering.manuscript_injection import validate_project_selection

    try:
        validate_project_selection(project_root, sys.argv[index + 1])
    except ValueError as error:
        raise SystemExit(str(error)) from error
    del sys.argv[index : index + 2]

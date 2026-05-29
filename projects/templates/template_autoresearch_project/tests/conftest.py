"""Project test fixtures."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from pathlib import Path
import sys
from typing import Any

import pytest

from src.models import AutoResearchLoopResult

_FIGURE_RENDER_HOOKS = (
    ("src.writers", "render_figure_batch"),
    ("src.figures_process", "write_stage_matrix_figure"),
)


def _current_coverage() -> object | None:
    coverage_module = sys.modules.get("coverage")
    coverage_class = getattr(coverage_module, "Coverage", None)
    return coverage_class.current() if coverage_class is not None else None


def _without_coverage(function: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        coverage_controller = _current_coverage()
        if coverage_controller is not None:
            coverage_controller.stop()  # type: ignore[attr-defined]
        try:
            return function(*args, **kwargs)
        finally:
            if coverage_controller is not None:
                coverage_controller.start()  # type: ignore[attr-defined]

    return wrapped


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root(project_root: Path) -> Path:
    """Return the template repository root.

    Walk upward from the project directory until the directory containing
    ``infrastructure/`` is found. Deriving the root by marker rather than a
    fixed ``parents[N]`` index keeps the fixture correct across lifecycle moves
    of the project under ``projects/`` (notably the ``projects/templates/<name>``
    layout introduced by the 5-folder lifecycle refactor, which a hard-coded
    ``parents[1]`` resolved to ``projects/`` instead of the repo root).
    """
    for candidate in (project_root, *project_root.parents):
        if (candidate / "infrastructure").is_dir():
            return candidate
    raise RuntimeError(
        f"Could not locate repo root: no infrastructure/ directory above {project_root}"
    )


@pytest.fixture(scope="session")
def autoresearch_loop_result(project_root: Path, repo_root: Path) -> AutoResearchLoopResult:
    """Run the full deterministic loop once for read-only output assertions."""
    from importlib import import_module

    from src.loop import run_autoresearch_loop

    originals: dict[tuple[str, str], object] = {}
    for module_name, attribute in _FIGURE_RENDER_HOOKS:
        module = import_module(module_name)
        originals[(module_name, attribute)] = getattr(module, attribute)
        setattr(module, attribute, _without_coverage(getattr(module, attribute)))
    try:
        return run_autoresearch_loop(project_root, repo_root)
    finally:
        for (module_name, attribute), function in originals.items():
            setattr(import_module(module_name), attribute, function)
